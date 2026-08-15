"""SRS generation, persistence, retrieval, and editing (Phase 1C).

The service orchestrates the deterministic mock SRS provider, persists new
versions with sequential version numbers (history is never overwritten,
FR-064), runs deterministic validation, and applies validated user edits.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.exceptions import (
    InvalidGeneratedOutputError,
    InvalidProjectStateError,
    InvalidSRSEditError,
    NoSRSVersionError,
    ProjectContextNotFoundError,
    ProjectNotFoundError,
    SRSVersionNotFoundError,
)
from ..core.exceptions import (
    LLMTimeoutError as ApiLLMTimeoutError,
)
from ..db.models import ModelRun, Project, ProjectContext, SRSVersion
from ..llm.base import (
    LLMOutputError,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMTask,
    LLMTimeoutError,
    load_json_object,
)
from ..llm.registry import resolve_adapter_name
from ..prompts.srs import (
    SRS_SYSTEM_PROMPT,
    SRS_USER_TEMPLATE,
)
from ..rag.chromadb_client import create_chromadb_client
from ..rag.embedding_provider import create_embedding_provider
from ..rag.retrieval import RetrievalContext, Retriever, create_retriever
from ..repositories.context_repository import ProjectContextRepository
from ..repositories.project_repository import ProjectRepository
from ..repositories.srs_repository import SRSVersionRepository
from ..schemas.project import generate_uuid
from ..schemas.srs import (
    SourceReference,
    SRSEditRequest,
    SRSGenerationResponse,
    SRSSchema,
    SRSValidationResponse,
    SRSVersionListResponse,
    SRSVersionRead,
    SRSVersionSummary,
)
from .provenance_service import ModelRunRecorder, resolve_knowledge_base_version
from .srs_output_validation import validate_srs_output
from .srs_validation_service import SRSValidationService

GENERATABLE_STATES: frozenset[str] = frozenset({"draft", "analysed", "clarifying", "generated"})

logger = logging.getLogger(__name__)


class SRSGenerationService:
    """Use cases for SRS generation, retrieval, editing, and validation."""

    def __init__(
        self,
        session: Session,
        provider: LLMProvider,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._settings = settings or Settings()
        self._projects = ProjectRepository(session)
        self._contexts = ProjectContextRepository(session)
        self._versions = SRSVersionRepository(session)
        self._validator = SRSValidationService()
        self._model_runs = ModelRunRecorder(session, self._settings, provider)

        # Lazy-initialized RAG components
        self._retriever: Retriever | None = None
        self._retrieval_context: RetrievalContext | None = None
        self._retrieval_time_ms: int = 0
        self._rag_prompt_chunk_count: int = 0
        self._rag_prompt_context_chars: int = 0

    def _get_retriever(self):
        """Lazy-initialize the retriever."""
        if self._retriever is None:
            chroma = create_chromadb_client(self._settings)
            embedding = create_embedding_provider(self._settings)
            self._retriever = create_retriever(self._settings, chroma, embedding)
        return self._retriever

    def _retrieve_context(self, project_id: str, project_name: str, context) -> RetrievalContext:
        """Retrieve relevant context for the project."""
        project_context = {
            "project_name": project_name,
            "inferred_categories": context.inferred_categories,
            "stakeholders": context.stakeholders,
            "users": context.users,
            "goals": context.goals,
            "constraints": context.constraints,
        }
        return self._get_retriever().retrieve(
            project_context,
            resolve_knowledge_base_version(self._settings),
        )

    # --- Generation -----------------------------------------------------

    def generate_srs(self, project_id: str, use_rag: bool = True) -> SRSGenerationResponse:
        """Generate and persist a new SRS version for a project.

        The provider is called with the enriched project context; the response
        is validated against :class:`SRSSchema` before persistence. A new row
        is always inserted (version_number = previous + 1); existing history is
        never overwritten.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            ProjectContextNotFoundError: If the project has not been analysed.
            InvalidProjectStateError: If the project state forbids generation.
            InvalidGeneratedOutputError: If the provider output fails schema
                validation.
        """
        project = self._projects.get(project_id)
        if project is None:
            raise ProjectNotFoundError()

        if project.status not in GENERATABLE_STATES:
            raise InvalidProjectStateError()

        context = self._contexts.get_latest_for_project(project_id)
        if context is None:
            raise ProjectContextNotFoundError()

        # Build enriched context payload including clarification answers
        enriched_context = context.enriched_context or {}
        clarification_answers = enriched_context.get("clarification_answers", [])

        context_payload = {
            "project_name": project.name,
            "description": project.description,
            "inferred_categories": context.inferred_categories,
            "stakeholders": context.stakeholders,
            "users": context.users,
            "goals": context.goals,
            "constraints": context.constraints,
            "clarification_answers": clarification_answers,
            "version": self._versions.next_version_number(project_id),
        }

        model_run = self._model_runs.start(
            project_id,
            "srs_generation",
            rag_requested=use_rag,
            prompt_template_version="srs-v1",
        )
        try:
            return self._generate_srs_artifact(
                project,
                context,
                context_payload,
                use_rag,
                model_run,
            )
        except Exception as exc:
            self._model_runs.fail(model_run, exc)
            raise

    def _generate_srs_artifact(
        self,
        project: Project,
        context: ProjectContext,
        context_payload: dict[str, Any],
        use_rag: bool,
        model_run: ModelRun,
    ) -> SRSGenerationResponse:
        """Generate one SRS and complete its already-started provenance run."""
        self._retrieval_time_ms = 0
        if use_rag:
            try:
                retrieval_start = time.perf_counter()
                self._retrieval_context = self._retrieve_context(project.id, project.name, context)
                self._retrieval_time_ms = int((time.perf_counter() - retrieval_start) * 1000)
                logger.info(f"Retrieved {self._retrieval_context.total_chunks} chunks for RAG")
            except Exception as e:
                logger.warning(f"RAG retrieval failed, falling back to non-RAG generation: {e}")
                self._retrieval_context = None
                self._retrieval_time_ms = 0
                use_rag = False

        # Build RAG context string
        rag_context_str = ""
        if use_rag and self._retrieval_context:
            rag_context_str = self._assemble_rag_context(self._retrieval_context)
            chunks = self._retrieval_context.chunks
            self._model_runs.record_retrieval(
                model_run,
                knowledge_base_version=self._retrieval_context.kb_version,
                retrieved_chunk_ids=[chunk.chunk_id for chunk in chunks],
                retrieved_document_ids=[
                    str(chunk.metadata.get("source_id", "")).strip()
                    for chunk in chunks
                    if str(chunk.metadata.get("source_id", "")).strip()
                ],
                metadata={
                    "retrieval_time_ms": self._retrieval_time_ms,
                    "retrieved_chunk_count": len(chunks),
                    "rag_prompt_chunks": self._rag_prompt_chunk_count,
                    "rag_prompt_context_chars": self._rag_prompt_context_chars,
                },
            )

        # Build user content with project context and RAG
        user_content = SRS_USER_TEMPLATE.format(
            project_context=json.dumps(context_payload, indent=2),
            rag_context=rag_context_str,
        )

        request = LLMRequest(
            task=LLMTask.SRS,
            system_prompt=SRS_SYSTEM_PROMPT,
            user_content=user_content,
            response_schema=SRSSchema,
        )

        response, srs, attempts, generation_time_ms = self._generate_validated_srs(
            request,
            context_payload,
            model_run,
        )
        if use_rag and self._retrieval_context:
            self._repair_source_reference_ids(srs, self._retrieval_context)

        # Run deterministic validation
        validation_issues = validate_srs_output(
            srs, self._retrieval_context.chunks if self._retrieval_context else None
        )
        if validation_issues:
            errors = [i for i in validation_issues if i.severity == "error"]
            if errors:
                error_msg = "; ".join(f"{i.code}: {i.message}" for i in errors)
                raise InvalidGeneratedOutputError(f"Deterministic validation failed: {error_msg}")
            # Log warnings
            for warning in [i for i in validation_issues if i.severity == "warning"]:
                logger.warning(
                    "SRS validation warning [%s]: %s (req: %s)",
                    warning.code,
                    warning.message,
                    warning.requirement_id,
                )

        # Validate citations if RAG was used
        if use_rag and self._retrieval_context:
            from ..rag.retrieval import CitationValidator

            validator = CitationValidator(self._retrieval_context)
            srs = self._validate_citations(srs, validator)

        gen_metadata = {
            "model_variant": self._settings.model_variant,
            "model_name": response.model_name,
            "provider": self._provider.provider_name,
            "generation_time_ms": generation_time_ms,
            "rag_enabled": use_rag and self._retrieval_context is not None,
            "retrieval_context": (
                self._retrieval_context.query_texts if self._retrieval_context else None
            ),
            "retrieved_chunks": (
                self._retrieval_context.total_chunks if self._retrieval_context else 0
            ),
            "retrieval_time_ms": self._retrieval_time_ms,
            "rag_prompt_chunks": self._rag_prompt_chunk_count,
            "rag_prompt_context_chars": self._rag_prompt_context_chars,
            "kb_version": (
                self._retrieval_context.kb_version if self._retrieval_context else None
            ),
            "generation_timestamp": datetime.now(UTC).isoformat(),
            "generation_latency_ms": generation_time_ms,
            "validation_issues": [
                {
                    "code": issue.code,
                    "severity": issue.severity,
                    "section": issue.section,
                    "requirement_id": issue.requirement_id,
                    "message": issue.message,
                }
                for issue in validation_issues
            ],
        }

        version = SRSVersion(
            id=generate_uuid(),
            project_id=project.id,
            version_number=srs.metadata.version,
            srs_json={
                **srs.model_dump(mode="json"),
                "generation_metadata": gen_metadata,
            },
            status="generated",
            model_variant=self._settings.model_variant,
            model_name=response.model_name,
            adapter_name=resolve_adapter_name(self._settings),
            rag_enabled=use_rag and self._retrieval_context is not None,
            generation_metadata=gen_metadata,
            model_run_id=model_run.id,
        )
        self._versions.add(version)
        project.status = "generated"
        self._projects.save(project)

        chunks = self._retrieval_context.chunks if self._retrieval_context else []
        retrieved_chunk_ids = [chunk.chunk_id for chunk in chunks]
        retrieved_document_ids = [
            str(chunk.metadata.get("source_id", "")).strip()
            for chunk in chunks
            if str(chunk.metadata.get("source_id", "")).strip()
        ]
        citation_ids = [
            reference.source_id
            for requirements in srs.requirement_sections().values()
            for requirement in requirements
            for reference in requirement.source_references
        ]
        model_run.model_name = response.model_name
        self._model_runs.succeed(
            model_run,
            artifact_type="srs",
            artifact_ids=[version.id],
            rag_enabled=use_rag and self._retrieval_context is not None,
            knowledge_base_version=(
                self._retrieval_context.kb_version if self._retrieval_context else None
            ),
            retrieved_chunk_ids=retrieved_chunk_ids,
            retrieved_document_ids=retrieved_document_ids,
            citation_ids=citation_ids,
            deterministic_validation_applied=True,
            deterministic_repair_applied=True,
            metadata={
                "retrieval_time_ms": self._retrieval_time_ms,
                "rag_prompt_chunks": self._rag_prompt_chunk_count,
                "rag_prompt_context_chars": self._rag_prompt_context_chars,
                "validation_issue_count": len(validation_issues),
                "generation_attempts": attempts,
                "input_tokens": sum(
                    int(attempt.get("input_tokens") or 0) for attempt in attempts
                ),
                "output_tokens": sum(
                    int(attempt.get("output_tokens") or 0) for attempt in attempts
                ),
            },
        )
        self._session.refresh(version)

        return SRSGenerationResponse(
            project_id=project.id,
            version_id=version.id,
            version_number=version.version_number,
            status=version.status,
        )

    def _assemble_rag_context(self, context: RetrievalContext) -> str:
        """Assemble retrieved chunks into a context block for the LLM prompt."""
        self._rag_prompt_chunk_count = 0
        self._rag_prompt_context_chars = 0
        if not context.chunks:
            return ""

        lines = [
            "--- RETRIEVED CYBERSECURITY KNOWLEDGE ---",
            "",
        ]
        max_context_chars = max(0, self._settings.rag_max_context_chars)
        max_chunk_chars = max(1, self._settings.rag_max_chunk_chars)

        for i, chunk in enumerate(context.chunks):
            meta = chunk.metadata
            source_info = []
            if meta.get("document_title"):
                source_info.append(meta["document_title"])
            if meta.get("section_heading"):
                source_info.append(f"Section: {meta['section_heading']}")
            if meta.get("organisation"):
                source_info.append(meta["organisation"])
            if meta.get("page_number"):
                source_info.append(f"Page: {meta['page_number']}")

            source_str = " | ".join(source_info) if source_info else "Unknown source"

            chunk_text = chunk.text[:max_chunk_chars]
            if len(chunk.text) > max_chunk_chars:
                chunk_text = f"{chunk_text}\n[chunk truncated for prompt budget]"
            chunk_lines = [
                f"[Source {i + 1}: {source_str}] (relevance: {chunk.relevance_score:.3f})",
                f"CHUNK_ID: {chunk.chunk_id}",
                chunk_text,
                "",
            ]
            candidate_lines = lines + chunk_lines + ["--- END RETRIEVED KNOWLEDGE ---"]
            candidate_chars = len("\n".join(candidate_lines))
            if max_context_chars and candidate_chars > max_context_chars:
                break
            lines.extend(chunk_lines)
            self._rag_prompt_chunk_count += 1

        lines.append("--- END RETRIEVED KNOWLEDGE ---")
        assembled = "\n".join(lines)
        self._rag_prompt_context_chars = len(assembled)
        return assembled

    def _validate_citations(self, srs: SRSSchema, validator) -> SRSSchema:
        """Validate and enrich citations in the generated SRS."""
        try:
            # Use the CitationValidator to check all source_references
            # Iterate through all requirements and validate their citations
            for _section_name, requirements in srs.requirement_sections().items():
                for req in requirements:
                    if req.source_references:
                        validated_refs, warnings = validator.validate_citations(
                            [ref.model_dump() for ref in req.source_references]
                        )
                        # Update with validated citations
                        req.source_references = [
                            SourceReference(
                                source_id=str(r.get("source_id", "")),
                                document_title=str(r.get("document_title", "")),
                                section_heading=r.get("section_heading"),
                                relevance_score=float(r.get("relevance_score", 0.0)),
                            )
                            for r in validated_refs
                        ]
                        # Log warnings
                        for w in warnings:
                            logger.warning(f"Citation validation warning: {w}")

            # Re-validate the whole SRS after citation updates
            return SRSSchema.model_validate(srs.model_dump())
        except Exception as e:
            logger.warning(f"Citation validation failed: {e}")
            return srs

    def _repair_source_reference_ids(
        self,
        srs: SRSSchema,
        retrieval_context: RetrievalContext,
    ) -> None:
        """Map near-match citation IDs to exact retrieved chunk IDs."""
        valid_ids = {chunk.chunk_id for chunk in retrieval_context.chunks}
        normalised_lookup = {
            self._normalise_citation_id(chunk_id): chunk_id for chunk_id in valid_ids
        }
        chunk_index_lookup: dict[str, list[str]] = {}
        for chunk_id in valid_ids:
            match = re.search(r"chunk_\d+$", chunk_id)
            if match:
                chunk_index_lookup.setdefault(match.group(0), []).append(chunk_id)

        for _section_name, requirements in srs.requirement_sections().items():
            for req in requirements:
                for ref in req.source_references:
                    if ref.source_id in valid_ids:
                        continue
                    repaired = normalised_lookup.get(self._normalise_citation_id(ref.source_id))
                    if repaired is None:
                        repaired = self._repair_by_unique_chunk_index(
                            ref.source_id,
                            chunk_index_lookup,
                        )
                    if repaired:
                        ref.source_id = repaired
                req.source_references = [
                    ref for ref in req.source_references if ref.source_id in valid_ids
                ]

    def _normalise_citation_id(self, source_id: str) -> str:
        """Normalise citation IDs for matching common model omissions."""
        lowered = source_id.lower().replace("-", "_")
        return re.sub(r"_800(?=_)", "", lowered)

    def _repair_by_unique_chunk_index(
        self,
        source_id: str,
        chunk_index_lookup: dict[str, list[str]],
    ) -> str | None:
        """Repair a citation only when its chunk index has one valid candidate."""
        match = re.search(r"chunk_\d+$", source_id)
        if not match:
            return None
        candidates = chunk_index_lookup.get(match.group(0), [])
        if len(candidates) == 1:
            return candidates[0]
        return None

    # ... rest of the class remains the same (retrieval, editing, validation, etc.)

    # --- Retrieval -------------------------------------------------------

    def get_latest_version(self, project_id: str) -> SRSVersionRead:
        """Return the latest SRS version for a project.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            NoSRSVersionError: If the project has no SRS versions.
        """
        self._require_project(project_id)
        version = self._versions.get_latest_for_project(project_id)
        if version is None:
            raise NoSRSVersionError()
        return self._to_read(version)

    def list_versions(self, project_id: str) -> SRSVersionListResponse:
        """List all SRS versions for a project, newest first."""
        self._require_project(project_id)
        versions = self._versions.list_for_project(project_id)
        return SRSVersionListResponse(
            project_id=project_id,
            versions=[
                SRSVersionSummary(
                    id=v.id,
                    version_number=v.version_number,
                    quality_score=v.quality_score,
                    status=v.status,
                    created_at=v.created_at,
                )
                for v in versions
            ],
        )

    def get_version(self, project_id: str, version_id: str) -> SRSVersionRead:
        """Return a specific SRS version for a project.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            SRSVersionNotFoundError: If the version does not exist or is not
                scoped to the project.
        """
        self._require_project(project_id)
        version = self._versions.get_version(project_id, version_id)
        if version is None:
            raise SRSVersionNotFoundError()
        return self._to_read(version)

    # --- Editing ---------------------------------------------------------

    def edit_version(
        self, project_id: str, version_id: str, request: SRSEditRequest
    ) -> SRSVersionRead:
        """Apply validated user edits to a persisted SRS version.

        Each update targets a requirement section + requirement ID + field.
        After applying all edits, the SRS is re-validated with the
        deterministic rules.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            SRSVersionNotFoundError: If the version does not exist.
            InvalidSRSEditError: If a section, requirement ID, or field is
                invalid, or the resulting SRS fails re-validation.
        """
        self._require_project(project_id)
        version = self._versions.get_version(project_id, version_id)
        if version is None:
            raise SRSVersionNotFoundError()

        srs = self._load_srs(version)

        for update in request.updates:
            requirements = srs.requirement_sections().get(update.section)
            if requirements is None:
                raise InvalidSRSEditError(f"Unknown section {update.section!r}.")
            target = next((r for r in requirements if r.id == update.requirement_id), None)
            if target is None:
                raise InvalidSRSEditError(
                    f"Requirement {update.requirement_id!r} not found in {update.section!r}."
                )
            if not hasattr(target, update.field):
                raise InvalidSRSEditError(
                    f"Field {update.field!r} is not editable on requirements."
                )

            setattr(target, update.field, update.new_value)

        # Re-validate the edited SRS against the full schema; duplicate IDs
        # and invalid values are caught here.
        try:
            SRSSchema.model_validate(srs.model_dump())
        except ValueError as exc:
            raise InvalidSRSEditError(str(exc)) from exc

        version.srs_json = srs.model_dump(mode="json")
        version.status = "draft"
        self._versions.save(version)
        self._session.commit()
        self._session.refresh(version)
        return self._to_read(version)

    # --- Validation ------------------------------------------------------

    def validate_version(self, project_id: str, version_id: str) -> SRSValidationResponse:
        """Run deterministic validation on a stored SRS version.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            SRSVersionNotFoundError: If the version does not exist.
        """
        self._require_project(project_id)
        version = self._versions.get_version(project_id, version_id)
        if version is None:
            raise SRSVersionNotFoundError()

        report = self._validator.validate(version)
        version.quality_score = float(report.overall_score)
        current = version.srs_json if isinstance(version.srs_json, dict) else {}
        version.srs_json = {
            **current,
            "validation_report": report.model_dump(mode="json"),
        }
        self._versions.save(version)
        self._session.commit()

        return SRSValidationResponse(
            srs_version_id=version.id,
            overall_score=report.overall_score,
            issues=report.issues,
        )

    # --- Internal helpers --------------------------------------------------

    def _generate_validated_srs(
        self,
        request: LLMRequest,
        context_payload: dict[str, Any],
        model_run: ModelRun,
    ) -> tuple[LLMResponse, SRSSchema, list[dict[str, Any]], int]:
        """Generate an SRS with one bounded correction using validation details."""
        max_attempts = max(1, self._settings.llm_max_retries + 1)
        attempts: list[dict[str, Any]] = []
        total_started = time.perf_counter()
        current_request = request

        for attempt_number in range(1, max_attempts + 1):
            attempt_started = time.perf_counter()
            try:
                response = self._provider.generate(current_request)
            except LLMTimeoutError as exc:
                raise ApiLLMTimeoutError(str(exc)) from exc

            srs, validation_errors, wrapper_removed = self._validate_srs_response(
                response,
                context_payload,
            )
            attempt = {
                "attempt": attempt_number,
                "status": "valid" if srs is not None else "schema_invalid",
                "validation_errors": validation_errors,
                "wrapper_removed": wrapper_removed,
                "latency_seconds": round(time.perf_counter() - attempt_started, 6),
                "input_tokens": response.prompt_eval_count,
                "output_tokens": response.eval_count,
            }
            attempts.append(attempt)
            self._model_runs.record_attempts(model_run, attempts)

            if srs is not None:
                generation_time_ms = int((time.perf_counter() - total_started) * 1000)
                return response, srs, attempts, generation_time_ms

            if attempt_number >= max_attempts:
                summary = "; ".join(validation_errors[:8]) or "unknown validation failure"
                raise InvalidGeneratedOutputError(
                    f"SRS schema validation failed after {max_attempts} attempts: {summary}"
                )

            error_lines = "\n".join(f"- {error}" for error in validation_errors[:12])
            corrective = (
                "Your previous complete SRS failed strict schema validation.\n"
                f"Validation failures:\n{error_lines}\n"
                "Regenerate the complete SRS and correct every listed failure. "
                "Do not omit required fields, invent citations, or include wrapper text. "
                "Return only the complete JSON object; the canonical schema is enforced "
                "by the response decoder."
            )
            current_request = LLMRequest(
                task=request.task,
                system_prompt=request.system_prompt,
                user_content=f"{request.user_content}\n\n{corrective}",
                response_schema=request.response_schema,
            )

        raise AssertionError("bounded SRS generation loop exited unexpectedly")

    def _require_project(self, project_id: str) -> None:
        """Raise if the project does not exist."""
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError()

    def _parse_srs(self, response: LLMResponse, context_payload: dict[str, Any]) -> SRSSchema:
        """Validate provider output against :class:`SRSSchema`.

        Document metadata is deterministic application data, so the service
        overlays it before validation instead of relying on the model to
        reproduce fields such as ``generated_at`` exactly.
        """
        srs, validation_errors, _wrapper_removed = self._validate_srs_response(
            response,
            context_payload,
        )
        if srs is not None:
            return srs
        summary = "; ".join(validation_errors[:8]) or "unknown validation failure"
        raise InvalidGeneratedOutputError(f"SRS schema validation failed: {summary}")

    def _validate_srs_response(
        self,
        response: LLMResponse,
        context_payload: dict[str, Any],
    ) -> tuple[SRSSchema | None, list[str], bool]:
        """Validate one raw response and return sanitized errors for correction."""
        try:
            payload, wrapper_removed = load_json_object(response.content)
        except LLMOutputError as exc:
            return None, [str(exc)], False

        try:
            normalised = self._normalise_srs_payload(
                payload,
                context_payload,
                response.model_name,
            )
            return SRSSchema.model_validate(normalised), [], wrapper_removed
        except ValidationError as exc:
            return None, self._format_validation_errors(exc), wrapper_removed
        except (TypeError, ValueError) as exc:
            return None, [f"<root>: {str(exc)[:240]}"], wrapper_removed

    @staticmethod
    def _format_validation_errors(error: ValidationError) -> list[str]:
        """Return bounded Pydantic error paths without raw input values."""
        messages = []
        for item in error.errors(
            include_url=False,
            include_context=False,
            include_input=False,
        )[:20]:
            location = ".".join(str(part) for part in item.get("loc", ())) or "<root>"
            message = str(item.get("msg", "validation failed"))[:200]
            messages.append(f"{location}: {message}")
        return messages or ["<root>: validation failed"]

    def _load_generated_object(self, content: str) -> dict[str, Any]:
        """Load the first JSON object from model output.

        Qwen normally follows the "JSON only" instruction, but real local
        models sometimes add a short preface or Markdown fence. This accepts
        the first balanced JSON object and still validates it strictly through
        :class:`SRSSchema` afterwards.
        """
        payload, _wrapper_removed = load_json_object(content)
        return payload

    def _normalise_srs_payload(
        self,
        payload: dict[str, Any],
        context_payload: dict[str, Any],
        model_name: str,
    ) -> dict[str, Any]:
        """Normalise common real-model shapes into the canonical SRS schema."""
        normalised = dict(payload)
        normalised["metadata"] = {
            "project_name": context_payload["project_name"],
            "version": context_payload["version"],
            "generated_at": datetime.now(UTC).isoformat(),
            "model_name": model_name,
            "adapter_name": None,
            "inferred_categories": context_payload["inferred_categories"],
        }

        overview = normalised.get("project_overview")
        if isinstance(overview, str):
            normalised["project_overview"] = {
                "description": context_payload.get("description", overview),
                "purpose": overview,
                "context": context_payload.get("description", overview),
            }
        elif isinstance(overview, dict):
            normalised["project_overview"] = {
                "description": str(
                    overview.get("description") or context_payload.get("description") or ""
                ),
                "purpose": str(
                    overview.get("purpose") or overview.get("summary") or "Specify the system."
                ),
                "context": str(
                    overview.get("context")
                    or context_payload.get("description")
                    or "Local project context."
                ),
            }

        scope = normalised.get("scope")
        if isinstance(scope, str):
            normalised["scope"] = {
                "in_scope": [scope],
                "out_of_scope": [
                    "Active penetration testing",
                    "Exploit execution",
                    "Automatic network configuration changes",
                ],
            }
        elif isinstance(scope, list):
            normalised["scope"] = {"in_scope": [str(item) for item in scope], "out_of_scope": []}

        normalised["stakeholders"] = self._normalise_string_list(
            normalised.get("stakeholders"),
            context_payload.get("stakeholders") or ["Project stakeholders"],
            dict_keys=("name", "role", "stakeholder"),
        )
        normalised["user_roles"] = self._normalise_string_list(
            normalised.get("user_roles"),
            context_payload.get("users") or ["System users"],
            dict_keys=("role", "name", "user_role"),
        )

        section_specs = {
            "functional_requirements": ("functional", "FR"),
            "non_functional_requirements": ("non_functional", "NFR"),
            "security_requirements": ("security", "SEC"),
            "data_requirements": ("data", "DATA"),
            "network_requirements": ("network", "NET"),
        }
        for section, (category, prefix) in section_specs.items():
            normalised[section] = self._normalise_requirements(
                normalised.get(section),
                category,
                prefix,
            )

        architecture = normalised.get("architecture_summary")
        if isinstance(architecture, str):
            normalised["architecture_summary"] = {
                "overview": architecture,
                "components": [
                    {
                        "name": "Network Access Control",
                        "description": "Controls network access and segmentation policies.",
                        "responsibilities": ["Enforce access policies"],
                    },
                    {
                        "name": "Monitoring and Logging",
                        "description": "Collects events and supports security review.",
                        "responsibilities": ["Detect suspicious activity"],
                    },
                ],
                "data_flows": [],
                "deployment_notes": "",
            }
        elif isinstance(architecture, dict):
            components = architecture.get("components") or []
            if not isinstance(components, list) or not components:
                components = [
                    {
                        "name": "Core Security Platform",
                        "description": "Provides core cybersecurity capabilities.",
                        "responsibilities": ["Support protected operation"],
                    }
                ]
            normalised["architecture_summary"] = {
                "overview": str(architecture.get("overview") or architecture.get("summary") or ""),
                "components": [self._normalise_architecture_component(item) for item in components],
                "data_flows": [
                    str(item) for item in architecture.get("data_flows", []) if str(item).strip()
                ],
                "deployment_notes": str(architecture.get("deployment_notes") or ""),
            }

        normalised["threats"] = self._normalise_threats(normalised.get("threats"))
        normalised["mitigations"] = self._normalise_mitigations(normalised.get("mitigations"))
        normalised["testing_strategy"] = self._normalise_testing(normalised.get("testing_strategy"))
        normalised["risks"] = self._normalise_risks(normalised.get("risks"))

        for key in ("assumptions", "unresolved_questions"):
            if not isinstance(normalised.get(key), list):
                normalised[key] = []
            normalised[key] = [str(item) for item in normalised[key] if str(item).strip()]
        normalised["references"] = (
            normalised.get("references") if isinstance(normalised.get("references"), list) else []
        )
        normalised["validation_report"] = None

        allowed_fields = set(SRSSchema.model_fields)
        return {key: value for key, value in normalised.items() if key in allowed_fields}

    def _normalise_string_list(
        self,
        value: Any,
        fallback: list[str],
        dict_keys: tuple[str, ...],
    ) -> list[str]:
        """Normalise model-generated list values into non-empty strings."""
        if not isinstance(value, list) or not value:
            return fallback

        items = []
        for item in value:
            if isinstance(item, dict):
                text = next((str(item[key]) for key in dict_keys if item.get(key)), "")
                if not text:
                    text = "; ".join(f"{key}: {val}" for key, val in item.items() if val)
            else:
                text = str(item)
            if text.strip():
                items.append(text.strip())
        return items or fallback

    def _normalise_requirements(
        self,
        requirements: Any,
        category: str,
        prefix: str,
    ) -> list[dict[str, Any]]:
        """Normalise model-generated requirements into requirement objects."""
        if not isinstance(requirements, list):
            return []
        return [
            self._normalise_requirement(item, index + 1, category, prefix)
            for index, item in enumerate(requirements)
        ]

    def _normalise_requirement(
        self,
        item: Any,
        index: int,
        category: str,
        prefix: str,
    ) -> dict[str, Any]:
        """Normalise one requirement from either a dict or a string."""
        generated_id = f"{prefix}-{index:03d}"
        if isinstance(item, dict):
            source = item
            statement = str(source.get("statement") or source.get("description") or "")
            req_id = str(source.get("id") or source.get("requirement_id") or generated_id)
            title = str(source.get("title") or f"Requirement {req_id}")
            rationale = str(source.get("rationale") or "Required by the project context.")
            acceptance = str(
                source.get("acceptance_criteria")
                or f"Verify that {statement.rstrip('.')} is implemented."
            )
            priority = str(source.get("priority") or "must").lower()
            confidence = str(source.get("confidence") or "medium").lower()
            dependencies = (
                source.get("dependencies") if isinstance(source.get("dependencies"), list) else []
            )
            source_references = self._normalise_source_references(source.get("source_references"))
        else:
            text = str(item).strip()
            match = re.search(rf"\b{re.escape(prefix)}-\d{{3}}\b", text)
            req_id = match.group(0) if match else generated_id
            statement = text.split(":", 1)[1].strip() if ":" in text else text
            title = f"Requirement {req_id}"
            rationale = "Generated from the project context by the local model."
            acceptance = f"Verify that {statement.rstrip('.')} is implemented."
            priority = "must"
            confidence = "medium"
            dependencies = []
            source_references = []

        if not re.fullmatch(r"[A-Z]{2,4}-\d{3}", req_id):
            req_id = generated_id
        if not statement.lower().startswith("the system shall"):
            statement = f"The system shall {statement[:1].lower()}{statement[1:]}"
        statement = self._normalise_shall_usage(statement)
        acceptance = self._normalise_shall_usage(acceptance)
        rationale = self._normalise_rationale(rationale, statement, category)
        if priority not in {"must", "should", "could"}:
            priority = "must"
        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"

        return {
            "id": req_id,
            "category": category,
            "title": title,
            "statement": statement,
            "rationale": rationale,
            "priority": priority,
            "acceptance_criteria": acceptance,
            "dependencies": [str(item) for item in dependencies],
            "source_references": source_references,
            "confidence": confidence,
            "user_confirmed": False,
        }

    def _normalise_source_references(self, value: Any) -> list[dict[str, Any]]:
        """Normalise model-generated citation objects without inventing sources."""
        if not isinstance(value, list):
            return []

        references = []
        for item in value:
            if not isinstance(item, dict):
                continue
            source_id = str(item.get("source_id") or item.get("chunk_id") or "").strip()
            if not source_id:
                continue
            relevance = item.get("relevance_score", 0.0)
            try:
                relevance_score = float(relevance)
            except (TypeError, ValueError):
                relevance_score = 0.0
            references.append(
                {
                    "source_id": source_id,
                    "document_title": str(item.get("document_title") or "Retrieved source"),
                    "section_heading": item.get("section_heading"),
                    "relevance_score": min(max(relevance_score, 0.0), 1.0),
                }
            )
        return references

    def _normalise_rationale(self, rationale: str, statement: str, category: str) -> str:
        """Repair generic rationale text and mark unsupported numbers as assumptions."""
        generic_patterns = [
            r"generated from the project context by the local model",
            r"generated from project context",
            r"by the local model",
            r"required by the project context",
            r"based on the project context",
            r"derived from the project context",
        ]
        repaired = rationale.strip()
        if any(re.search(pattern, repaired, flags=re.IGNORECASE) for pattern in generic_patterns):
            repaired = (
                "Needed to address the stated cybersecurity goals and inferred "
                f"{category.replace('_', ' ')} risks for this project."
            )

        numeric_patterns = [
            r"\b\d+\s*(?:ms|milliseconds?|seconds?|s)\b",
            r"\b99\.9\d?%\b",
            r"\b\d{4,}\s*(?:connections?|users?|requests?|TPS|RPS)\b",
            r"\b\d{1,3}%\s*(?:scalability|capacity|utilization)\b",
            r"\b\d+\s*(?:hours?|days?|weeks?)\s*"
            r"(?:patch|update|retention|backup|rotation)\b",
            r"\b(?:256|128|192|512)\s*-?\s*bit\b",
            r"\b\d+\s*(?:MB|GB|TB)\s*(?:per\s+)?(?:day|hour|month)\b",
        ]
        combined = f"{statement} {repaired}"
        contains_numeric_constraint = any(
            re.search(pattern, combined, flags=re.IGNORECASE) for pattern in numeric_patterns
        )
        has_provenance = any(
            keyword in repaired.lower()
            for keyword in [
                "user specified",
                "user requirement",
                "clarification",
                "from user",
                "retrieved",
                "source",
                "document",
                "standard",
                "guideline",
                "assumption",
                "assumed",
                "estimated",
                "assumption requiring",
            ]
        )
        if contains_numeric_constraint and not has_provenance:
            repaired = (
                f"{repaired} Numeric values are assumptions requiring stakeholder "
                "confirmation unless separately backed by a cited source."
            )

        return repaired

    def _normalise_shall_usage(self, text: str) -> str:
        """Keep only the first modal shall to satisfy requirement language rules."""
        matches = list(re.finditer(r"\bshall\b", text, flags=re.IGNORECASE))
        if len(matches) <= 1:
            return text
        first = matches[0]
        prefix = text[: first.end()]
        suffix = re.sub(r"\bshall\b", "must", text[first.end() :], flags=re.IGNORECASE)
        return f"{prefix}{suffix}"

    def _normalise_architecture_component(self, item: Any) -> dict[str, Any]:
        """Normalise one architecture component."""
        if isinstance(item, dict):
            responsibilities = item.get("responsibilities")
            if not isinstance(responsibilities, list) or not responsibilities:
                responsibilities = ["Support the architecture"]
            return {
                "name": str(item.get("name") or "Architecture Component"),
                "description": str(
                    item.get("description") or "Component in the target architecture."
                ),
                "responsibilities": [
                    str(value) for value in responsibilities if str(value).strip()
                ],
            }
        return {
            "name": str(item)[:80] or "Architecture Component",
            "description": str(item) or "Component in the target architecture.",
            "responsibilities": ["Support the architecture"],
        }

    def _normalise_threats(self, threats: Any) -> list[dict[str, Any]]:
        """Normalise threats into threat objects."""
        if not isinstance(threats, list):
            return []
        normalised = []
        for index, item in enumerate(threats, start=1):
            if isinstance(item, dict):
                normalised.append(
                    {
                        "threat_id": str(item.get("threat_id") or f"THR-{index:03d}"),
                        "name": str(item.get("name") or f"Threat {index}"),
                        "description": str(
                            item.get("description") or item.get("name") or "Threat."
                        ),
                        "category": item.get("category"),
                        "severity": str(item.get("severity") or "medium").lower(),
                        "affected_assets": item.get("affected_assets")
                        if isinstance(item.get("affected_assets"), list)
                        else [],
                        "mitigations": item.get("mitigations")
                        if isinstance(item.get("mitigations"), list)
                        else [],
                    }
                )
            else:
                text = str(item).strip()
                normalised.append(
                    {
                        "threat_id": f"THR-{index:03d}",
                        "name": text[:80] or f"Threat {index}",
                        "description": text or "Threat identified by the local model.",
                        "category": None,
                        "severity": "medium",
                        "affected_assets": [],
                        "mitigations": [],
                    }
                )
        return normalised

    def _normalise_mitigations(self, mitigations: Any) -> list[dict[str, Any]]:
        """Normalise mitigations into mitigation objects."""
        if not isinstance(mitigations, list):
            return []
        normalised = []
        for index, item in enumerate(mitigations, start=1):
            if isinstance(item, dict):
                normalised.append(
                    {
                        "mitigation_id": str(item.get("mitigation_id") or f"MIT-{index:03d}"),
                        "description": str(item.get("description") or "Mitigation."),
                        "related_requirement_ids": item.get("related_requirement_ids")
                        if isinstance(item.get("related_requirement_ids"), list)
                        else [],
                    }
                )
            else:
                normalised.append(
                    {
                        "mitigation_id": f"MIT-{index:03d}",
                        "description": str(item) or "Mitigation identified by the local model.",
                        "related_requirement_ids": [],
                    }
                )
        return normalised

    def _normalise_testing(self, testing_strategy: Any) -> list[dict[str, Any]]:
        """Normalise testing strategy into testing recommendation objects."""
        items = testing_strategy if isinstance(testing_strategy, list) else [testing_strategy]
        normalised = []
        for index, item in enumerate([item for item in items if item], start=1):
            if isinstance(item, dict):
                normalised.append(
                    {
                        "recommendation_id": str(
                            item.get("recommendation_id") or f"TEST-{index:03d}"
                        ),
                        "description": str(item.get("description") or "Test recommendation."),
                        "type": str(item.get("type") or "system"),
                        "related_requirement_ids": item.get("related_requirement_ids")
                        if isinstance(item.get("related_requirement_ids"), list)
                        else [],
                    }
                )
            else:
                normalised.append(
                    {
                        "recommendation_id": f"TEST-{index:03d}",
                        "description": str(item),
                        "type": "system",
                        "related_requirement_ids": [],
                    }
                )
        return normalised

    def _normalise_risks(self, risks: Any) -> list[dict[str, Any]]:
        """Normalise risks into risk objects."""
        if not isinstance(risks, list):
            return []
        normalised = []
        for index, item in enumerate(risks, start=1):
            if isinstance(item, dict):
                normalised.append(
                    {
                        "risk_id": str(item.get("risk_id") or f"RISK-{index:03d}"),
                        "description": str(item.get("description") or "Project risk."),
                        "likelihood": str(item.get("likelihood") or "medium"),
                        "impact": str(item.get("impact") or "medium"),
                        "mitigation": str(item.get("mitigation") or ""),
                    }
                )
            else:
                normalised.append(
                    {
                        "risk_id": f"RISK-{index:03d}",
                        "description": str(item),
                        "likelihood": "medium",
                        "impact": "medium",
                        "mitigation": "",
                    }
                )
        return normalised

    def _load_srs(self, version: SRSVersion) -> SRSSchema:
        """Deserialize stored srs_json into a validated SRSSchema."""
        try:
            return SRSSchema.model_validate(version.srs_json)
        except ValueError as exc:
            raise InvalidGeneratedOutputError(str(exc)) from exc

    def _to_read(self, version: SRSVersion) -> SRSVersionRead:
        """Serialize an ORM version into the read model."""
        srs = None
        if isinstance(version.srs_json, dict):
            srs = SRSSchema.model_validate(version.srs_json)
        return SRSVersionRead(
            id=version.id,
            project_id=version.project_id,
            version_number=version.version_number,
            status=version.status,
            quality_score=version.quality_score,
            created_at=version.created_at,
            srs=srs,
        )

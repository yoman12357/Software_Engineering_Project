"""Canonical Phase 5 four-configuration evaluation runner.

Each configuration starts an in-process CyberSRS API with isolated settings,
so all variants execute the production service pipeline without request-header
overrides or four duplicated implementations.
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

import httpx
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import select

from src.core.config import Settings
from src.db.database import Database
from src.db.models import ModelRun, Phase5CaseResult, Phase5EvaluationRun
from src.llm.base import LLMProvider, LLMRequest, LLMResponse, LLMTask
from src.llm.registry import resolve_adapter_name, resolve_model_name
from src.main import create_app
from src.schemas.project import generate_uuid

from .metrics import compute_category_accuracy
from .phase5_metrics import (
    ConfigVariant,
    compute_phase5_aggregate,
    evaluate_output,
    generate_comparison_markdown,
    parse_raw_output,
)

CANONICAL_DATASET = Path("ai/evaluation/dataset.json")
DEFAULT_OUTPUT_DIR = Path("ai/evaluation/phase5_results")
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class CapturingProvider(LLMProvider):
    """Transparent provider decorator that retains raw outputs for evaluation."""

    def __init__(self, delegate: LLMProvider) -> None:
        super().__init__(delegate.model_name)
        self._delegate = delegate
        self.provider_name = delegate.provider_name
        self.outputs: dict[LLMTask, str] = {}
        self.attempt_outputs: dict[LLMTask, list[str]] = {}

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Delegate generation and retain the unmodified response text."""
        response = self._delegate.generate(request)
        self.outputs.setdefault(request.task, response.content)
        self.attempt_outputs.setdefault(request.task, []).append(response.content)
        return response

    def parse_structured(self, response: LLMResponse, schema: type[SchemaT]) -> SchemaT:
        """Use the wrapped provider's parser and normalization behavior."""
        return self._delegate.parse_structured(response, schema)

    def generate_with_validation(
        self,
        request: LLMRequest,
        schema: type[SchemaT],
        max_retries: int | None = None,
    ) -> SchemaT:
        """Preserve the wrapped provider's corrective validation retries."""
        return self._delegate.generate_with_validation(request, schema, max_retries)

    def reset(self) -> None:
        """Discard outputs captured for the previous evaluation case."""
        self.outputs.clear()
        self.attempt_outputs.clear()


def validate_official_dataset_path(dataset_path: str | Path) -> Path:
    """Reject training/validation files as official Phase 5 input."""
    path = Path(dataset_path).resolve()
    forbidden = {
        Path("ai/finetuning/data/train.jsonl").resolve(),
        Path("ai/finetuning/data/validation.jsonl").resolve(),
    }
    if path in forbidden or "finetuning" in {part.lower() for part in path.parts}:
        raise ValueError(
            "Phase 5 requires a held-out evaluation dataset; fine-tuning data is forbidden."
        )
    return path


def ollama_model_available(settings: Settings, model_name: str) -> tuple[bool, str | None]:
    """Check the local Ollama registry without triggering generation or fallback."""
    try:
        response = httpx.get(
            f"{settings.ollama_base_url.rstrip('/')}/api/tags",
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return False, f"Ollama unavailable ({type(exc).__name__})"
    names = {
        str(item.get("name") or item.get("model") or "")
        for item in response.json().get("models", [])
    }
    accepted_names = {model_name, f"{model_name}:latest"}
    if names.isdisjoint(accepted_names):
        return False, f"Ollama model '{model_name}' is unavailable"
    return True, None


class Phase5EvaluationRunner:
    """Run held-out cases through the production API for selected configurations."""

    def __init__(
        self,
        *,
        dataset_path: str | Path = CANONICAL_DATASET,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
        configs: tuple[ConfigVariant, ...] | None = None,
        settings: Settings | None = None,
        availability_check: Callable[[Settings, str], tuple[bool, str | None]] = (
            ollama_model_available
        ),
    ) -> None:
        self.dataset_path = validate_official_dataset_path(dataset_path)
        self.output_root = Path(output_dir)
        self.configs = configs or ConfigVariant.all()
        self.settings = settings or Settings()
        self.availability_check = availability_check
        self.run_id = (
            f"phase5-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-"
            f"{uuid.uuid4().hex[:8]}"
        )
        self.started_at = datetime.now(UTC)
        self.run_dir = self.output_root / self.run_id
        self.database_url = f"sqlite:///{(self.run_dir / 'evaluation.sqlite').as_posix()}"

    def load_dataset(self) -> list[dict[str, Any]]:
        """Load and minimally validate the frozen held-out JSON cases."""
        payload = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list) or not all(
            isinstance(case, dict) and {"id", "description"} <= set(case)
            for case in payload
        ):
            raise ValueError("Phase 5 dataset must be a JSON list of held-out cases.")
        return payload

    def run_all(
        self,
        *,
        case_ids: list[str] | None = None,
        max_cases: int | None = None,
    ) -> dict[str, Any]:
        """Execute selected configurations and always write portable artifacts."""
        cases = self.load_dataset()
        if case_ids:
            wanted = set(case_ids)
            cases = [case for case in cases if case["id"] in wanted]
        if max_cases is not None:
            cases = cases[:max_cases]

        self.run_dir.mkdir(parents=True, exist_ok=False)
        database = Database(self.database_url)
        database.init_db()
        database.engine.dispose()

        case_results: list[dict[str, Any]] = []
        config_summaries: list[dict[str, Any]] = []
        for config in self.configs:
            config_results, summary = self._run_config(config, cases)
            case_results.extend(config_results)
            config_summaries.append(summary)

        completed_at = datetime.now(UTC)
        statuses = {item["status"] for item in config_summaries}
        if statuses == {"COMPLETED"}:
            overall_status = "COMPLETED"
        elif "COMPLETED" in statuses or "PARTIAL" in statuses:
            overall_status = "PARTIAL"
        elif statuses == {"UNAVAILABLE"}:
            overall_status = "UNAVAILABLE"
        else:
            overall_status = "FAILED"
        summary = {
            "evaluation_run_id": self.run_id,
            "status": overall_status,
            "started_at": self.started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "dataset": self.dataset_path.as_posix(),
            "held_out_case_count": len(cases),
            "configurations": config_summaries,
        }
        self._write_artifacts(summary, case_results, config_summaries)
        return summary

    def _settings_for(self, config: ConfigVariant, case_count: int) -> Settings:
        """Build isolated settings while retaining deployment-specific RAG paths."""
        values = self.settings.model_dump()
        values.update(
            {
                "database_url": self.database_url,
                "llm_provider": "ollama",
                "model_variant": config.model_variant,
                "rag_enabled": config.rag_enabled,
                "max_projects": max(self.settings.max_projects, case_count + 10),
            }
        )
        configured = Settings(_env_file=None, **values)
        configured.model_name = resolve_model_name(configured)
        return configured

    def _run_config(
        self, config: ConfigVariant, cases: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute one matrix cell or record an explicit unavailable status."""
        settings = self._settings_for(config, len(cases))
        model_name = resolve_model_name(settings)
        evaluation_run_id = f"{self.run_id}-{config.value}"
        available, error = self.availability_check(settings, model_name)
        if not available:
            status = "UNAVAILABLE"
            self._persist_run(
                evaluation_run_id, config, model_name, status, error, [], None
            )
            return [], {
                "evaluation_run_id": evaluation_run_id,
                "configuration": config.label,
                "model_variant": config.model_variant,
                "model_name": model_name,
                "rag_enabled": config.rag_enabled,
                "status": status,
                "error": error,
                "total_cases": 0,
                "successful_cases": 0,
                "raw_metrics": None,
                "final_metrics": None,
                "latency": None,
            }

        app = create_app(settings)
        results: list[dict[str, Any]] = []
        try:
            with TestClient(app) as client:
                provider = CapturingProvider(app.state.srs_llm_provider)
                app.state.srs_llm_provider = provider
                # Keep the legacy state alias aligned for older integrations.
                app.state.llm_provider = provider
                for case in cases:
                    results.append(
                        self._run_case(
                            client, provider, case, config, evaluation_run_id, model_name
                        )
                    )
        except Exception as exc:
            error = f"Configuration failed ({type(exc).__name__})"

        aggregate = compute_phase5_aggregate(config, results)
        successful_cases = sum(result["status"] == "COMPLETED" for result in results)
        if error is not None or successful_cases == 0:
            status = "FAILED"
        elif successful_cases == len(results):
            status = "COMPLETED"
        else:
            status = "PARTIAL"
        aggregate.update(
            {
                "evaluation_run_id": evaluation_run_id,
                "model_name": model_name,
                "status": status,
                "error": error,
            }
        )
        self._persist_run(
            evaluation_run_id, config, model_name, status, error, results, aggregate
        )
        return results, aggregate

    def _run_case(
        self,
        client: TestClient,
        provider: CapturingProvider,
        case: dict[str, Any],
        config: ConfigVariant,
        evaluation_run_id: str,
        model_name: str,
    ) -> dict[str, Any]:
        """Run one held-out case through analysis, clarification, and SRS services."""
        provider.reset()
        started = time.perf_counter()
        timings: dict[str, float] = {}
        errors: dict[str, str | None] = {"analysis": None, "clarification": None, "srs": None}

        project_response = client.post(
            "/api/v1/projects",
            json={
                "name": f"Phase 5 {case['id']} {config.label}",
                "description": case["description"],
            },
        )
        project_response.raise_for_status()
        project_id = project_response.json()["id"]

        analysis_response, timings["analysis_seconds"] = self._timed_post(
            client, f"/api/v1/projects/{project_id}/analyse"
        )
        analysis = (
            analysis_response.json().get("analysis", {})
            if analysis_response.is_success
            else {}
        )
        if not analysis_response.is_success:
            errors["analysis"] = self._safe_error(analysis_response)

        clarification_response, timings["clarification_seconds"] = self._timed_post(
            client, f"/api/v1/projects/{project_id}/clarifications/generate"
        )
        questions = (
            clarification_response.json().get("questions", [])
            if clarification_response.is_success
            else []
        )
        if not clarification_response.is_success:
            errors["clarification"] = self._safe_error(clarification_response)
        if questions:
            answers = [
                {"question_id": question["id"], "answer_text": "", "skipped": True}
                for question in questions
            ]
            client.post(
                f"/api/v1/projects/{project_id}/clarifications", json={"answers": answers}
            )

        srs_response, timings["srs_seconds"] = self._timed_post(
            client, f"/api/v1/projects/{project_id}/srs/generate"
        )
        final_payload: dict[str, Any] | None = None
        provenance: dict[str, Any] = {}
        validation_score: int | None = None
        version_id: str | None = None
        if srs_response.is_success:
            version_id = srs_response.json()["version_id"]
            stored = client.get(
                f"/api/v1/projects/{project_id}/srs/versions/{version_id}"
            )
            if stored.is_success:
                final_payload = stored.json().get("srs")
            provenance_response = client.get(
                f"/api/v1/projects/{project_id}/srs/versions/{version_id}/provenance"
            )
            if provenance_response.is_success:
                provenance = provenance_response.json().get("model_run") or {}
            validation = client.post(
                f"/api/v1/projects/{project_id}/srs/versions/{version_id}/validate"
            )
            if validation.is_success:
                validation_score = validation.json().get("overall_score")
        else:
            errors["srs"] = self._safe_error(srs_response)

        run_snapshot = self._model_run_snapshot(project_id, "srs_generation")
        provenance = {**run_snapshot, **provenance}

        raw_content = provider.outputs.get(LLMTask.SRS)
        attempt_outputs = provider.attempt_outputs.get(LLMTask.SRS, [])
        retry_content = attempt_outputs[1] if len(attempt_outputs) > 1 else None
        raw_payload, raw_json_valid = parse_raw_output(raw_content)
        retry_payload, retry_json_valid = parse_raw_output(retry_content)
        retrieved_ids = list(provenance.get("retrieved_chunk_ids", []))
        raw_metrics = evaluate_output(
            raw_payload,
            json_valid=raw_json_valid,
            clarification_count=len(questions),
            retrieved_chunk_ids=retrieved_ids,
        ).to_dict()
        final_metrics = evaluate_output(
            final_payload,
            json_valid=final_payload is not None,
            clarification_count=len(questions),
            retrieved_chunk_ids=retrieved_ids,
        ).to_dict()
        final_metrics["validation_score"] = validation_score
        final_metrics["deterministic_validation_applied"] = provenance.get(
            "deterministic_validation_applied"
        )
        final_metrics["deterministic_repair_applied"] = provenance.get(
            "deterministic_repair_applied"
        )
        retry_metrics = (
            evaluate_output(
                retry_payload,
                json_valid=retry_json_valid,
                clarification_count=len(questions),
                retrieved_chunk_ids=retrieved_ids,
            ).to_dict()
            if retry_content is not None
            else None
        )

        timings["total_seconds"] = time.perf_counter() - started
        inferred = analysis.get("inferred_categories", [])
        actual_rag_enabled = bool(provenance.get("rag_enabled", False))
        generation_attempts = provenance.get("generation_attempts", [])
        first_attempt = generation_attempts[0] if generation_attempts else {}
        retry_attempt = generation_attempts[1] if len(generation_attempts) > 1 else {}
        if config.rag_enabled and final_payload is not None and not actual_rag_enabled:
            errors["srs"] = "RAG was requested but retrieval was not used"

        return {
            "evaluation_run_id": evaluation_run_id,
            "configuration": config.label,
            "model_variant": config.model_variant,
            "model_name": provenance.get("model_name", model_name),
            "rag_enabled": config.rag_enabled,
            "rag_enabled_used": actual_rag_enabled,
            "case_id": case["id"],
            "expected_categories": case.get("expected_categories", []),
            "project_id": project_id,
            "srs_version_id": version_id,
            "status": (
                "COMPLETED"
                if final_payload is not None
                and (not config.rag_enabled or actual_rag_enabled)
                else "FAILED"
            ),
            "timestamp": datetime.now(UTC).isoformat(),
            "raw_output": raw_content,
            "raw_attempts": attempt_outputs,
            "retry_output": retry_content,
            "final_output": final_payload,
            "raw_metrics": raw_metrics,
            "retry_metrics": retry_metrics,
            "final_metrics": final_metrics,
            "generation_attempts": generation_attempts,
            "first_attempt_status": first_attempt.get("status"),
            "first_attempt_validation_errors": first_attempt.get(
                "validation_errors", []
            ),
            "retry_status": retry_attempt.get("status"),
            "retry_validation_errors": retry_attempt.get("validation_errors", []),
            "token_usage": {
                "input_tokens": sum(
                    int(item.get("input_tokens") or 0)
                    for item in generation_attempts
                ),
                "output_tokens": sum(
                    int(item.get("output_tokens") or 0)
                    for item in generation_attempts
                ),
            },
            "retrieval_metadata": {
                "knowledge_base_version": provenance.get("knowledge_base_version"),
                "retrieved_chunk_ids": retrieved_ids,
                "retrieved_document_ids": provenance.get("retrieved_document_ids", []),
                "citation_ids": provenance.get("citation_ids", []),
                "retrieval_time_ms": provenance.get("retrieval_time_ms", 0),
                "rag_prompt_chunks": provenance.get("rag_prompt_chunks", 0),
                "rag_prompt_context_chars": provenance.get(
                    "rag_prompt_context_chars", 0
                ),
            },
            "latencies": timings,
            "inferred_categories": inferred,
            "category_accuracy": compute_category_accuracy(
                inferred, case.get("expected_categories", [])
            ),
            "errors": errors,
        }

    def _model_run_snapshot(self, project_id: str, operation_type: str) -> dict[str, Any]:
        """Read safe model-run telemetry for successful or failed evaluation cases."""
        database = Database(self.database_url)
        try:
            with database.session_factory() as session:
                run = session.scalar(
                    select(ModelRun)
                    .where(
                        ModelRun.project_id == project_id,
                        ModelRun.operation_type == operation_type,
                    )
                    .order_by(ModelRun.started_at.desc())
                )
                if run is None:
                    return {}
                metadata = run.metadata_json or {}
                return {
                    "model_name": run.model_name,
                    "rag_enabled": run.rag_enabled,
                    "knowledge_base_version": run.knowledge_base_version,
                    "retrieved_chunk_ids": run.retrieved_chunk_ids or [],
                    "retrieved_document_ids": run.retrieved_document_ids or [],
                    "citation_ids": run.citation_ids or [],
                    "status": run.status,
                    "generation_attempts": metadata.get("generation_attempts", []),
                    "retrieval_time_ms": metadata.get("retrieval_time_ms", 0),
                    "rag_prompt_chunks": metadata.get("rag_prompt_chunks", 0),
                    "rag_prompt_context_chars": metadata.get(
                        "rag_prompt_context_chars", 0
                    ),
                    "deterministic_validation_applied": metadata.get(
                        "deterministic_validation_applied"
                    ),
                    "deterministic_repair_applied": metadata.get(
                        "deterministic_repair_applied"
                    ),
                }
        finally:
            database.engine.dispose()

    @staticmethod
    def _timed_post(client: TestClient, path: str) -> tuple[httpx.Response, float]:
        """POST to a production endpoint and return wall-clock latency."""
        started = time.perf_counter()
        response = client.post(path)
        return response, time.perf_counter() - started

    @staticmethod
    def _safe_error(response: httpx.Response) -> str:
        """Return a bounded API error without response internals."""
        try:
            detail = response.json().get("detail", "request failed")
        except (json.JSONDecodeError, AttributeError):
            detail = "request failed"
        return f"HTTP {response.status_code}: {str(detail)[:200]}"

    def _persist_run(
        self,
        evaluation_run_id: str,
        config: ConfigVariant,
        model_name: str,
        status: str,
        error: str | None,
        results: list[dict[str, Any]],
        aggregate: dict[str, Any] | None,
    ) -> None:
        """Persist one configuration and its metric-only case records."""
        database = Database(self.database_url)
        with database.session_factory() as session:
            run = Phase5EvaluationRun(
                id=generate_uuid(),
                run_id=evaluation_run_id,
                config=config.value,
                model_variant=config.model_variant,
                rag_enabled=config.rag_enabled,
                model_name=model_name,
                adapter_name=resolve_adapter_name(self._settings_for(config, len(results))),
                total_cases=len(results),
                successful_cases=sum(result["status"] == "COMPLETED" for result in results),
                aggregate_metrics=aggregate or {},
                started_at=self.started_at,
                completed_at=datetime.now(UTC),
                status=status.lower(),
                error_message=error,
            )
            session.add(run)
            session.flush()
            for result in results:
                retrieval = result["retrieval_metadata"]
                timings = result["latencies"]
                session.add(
                    Phase5CaseResult(
                        id=generate_uuid(),
                        evaluation_run_id=run.id,
                        case_id=result["case_id"],
                        description="held-out case; see portable artifact",
                        expected_categories=result["expected_categories"],
                        config=config.value,
                        model_variant=config.model_variant,
                        rag_enabled=config.rag_enabled,
                        model_name=result["model_name"],
                        adapter_name=run.adapter_name,
                        raw_metrics=result["raw_metrics"],
                        final_metrics=result["final_metrics"],
                        analysis_latency_seconds=timings["analysis_seconds"],
                        clarification_latency_seconds=timings["clarification_seconds"],
                        srs_latency_seconds=timings["srs_seconds"],
                        total_latency_seconds=timings["total_seconds"],
                        retrieval_chunk_count=len(retrieval["retrieved_chunk_ids"]),
                        retrieval_latency_ms=int(retrieval.get("retrieval_time_ms", 0)),
                        kb_version=retrieval["knowledge_base_version"],
                        inferred_categories=result["inferred_categories"],
                        category_accuracy=result["category_accuracy"],
                        analysis_error=result["errors"]["analysis"],
                        clarification_error=result["errors"]["clarification"],
                        srs_error=result["errors"]["srs"],
                        model_variant_used=config.model_variant,
                        rag_enabled_used=result["rag_enabled_used"],
                        model_name_used=result["model_name"],
                        adapter_name_used=run.adapter_name,
                        generation_timestamp=datetime.fromisoformat(result["timestamp"]),
                        generation_latency_ms=int(timings["srs_seconds"] * 1000),
                    )
                )
            session.commit()
        database.engine.dispose()

    def _write_artifacts(
        self,
        summary: dict[str, Any],
        case_results: list[dict[str, Any]],
        config_summaries: list[dict[str, Any]],
    ) -> None:
        """Write the canonical portable Phase 5 artifact set."""
        (self.run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        (self.run_dir / "per_case_results.json").write_text(
            json.dumps(case_results, indent=2), encoding="utf-8"
        )
        (self.run_dir / "comparison.md").write_text(
            generate_comparison_markdown(config_summaries), encoding="utf-8"
        )


def parse_configs(value: str) -> tuple[ConfigVariant, ...]:
    """Map CLI spelling to the canonical Phase 5 configuration enum."""
    mapping = {
        "base": ConfigVariant.BASE,
        "base-rag": ConfigVariant.BASE_RAG,
        "finetuned": ConfigVariant.FINETUNED,
        "finetuned-rag": ConfigVariant.FINETUNED_RAG,
    }
    return ConfigVariant.all() if value == "all" else (mapping[value],)


def main() -> int:
    """Run Phase 5 from the command line."""
    parser = argparse.ArgumentParser(description="CyberSRS Phase 5 evaluation")
    parser.add_argument(
        "--config",
        choices=("base", "base-rag", "finetuned", "finetuned-rag", "all"),
        default="all",
    )
    parser.add_argument("--case-ids", nargs="+")
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--dataset", default=str(CANONICAL_DATASET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    runner = Phase5EvaluationRunner(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        configs=parse_configs(args.config),
    )
    result = runner.run_all(case_ids=args.case_ids, max_cases=args.max_cases)
    print(f"Phase 5 artifacts: {runner.run_dir}")
    completed = {"COMPLETED", "PARTIAL"}
    return 0 if any(c["status"] in completed for c in result["configurations"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

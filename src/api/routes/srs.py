"""SRS API endpoints per API_CONTRACT.md §5 (Phase 1C)."""

import json
import logging
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...core.config import Settings
from ...core.exceptions import ApiError
from ...llm.base import LLMProvider
from ...rag.chromadb_client import create_chromadb_client
from ...schemas.srs import (
    SRSEditRequest,
    SRSGenerationProgressEvent,
    SRSGenerationResponse,
    SRSRegenerateSectionRequest,
    SRSValidationResponse,
    SRSVersionListResponse,
    SRSVersionRead,
)
from ...services.srs_generation_service import SRSGenerationService
from ..dependencies import (
    enforce_request_body_size,
    get_app_settings,
    get_db,
    get_srs_llm_provider,
)

router = APIRouter(prefix="/projects", tags=["srs"])
logger = logging.getLogger(__name__)


def _srs_service(db: Session, provider: LLMProvider, settings: Settings) -> SRSGenerationService:
    """Construct an SRS service bound to the request session and provider."""
    return SRSGenerationService(db, provider, settings)


def _chroma_client(settings: Settings):
    """Create ChromaDB client."""
    return create_chromadb_client(settings)


def _project_chroma_client(settings: Settings):
    """Create the isolated project-document ChromaDB client."""
    return create_chromadb_client(
        settings.model_copy(update={"chroma_collection": settings.project_chroma_collection})
    )


@router.post("/{project_id}/srs/generate", response_model=SRSGenerationResponse)
def generate_srs(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSGenerationResponse:
    """Generate a new SRS version for the project."""
    return _srs_service(db, provider, settings).generate_srs(
        project_id, use_rag=settings.rag_enabled
    )


def _sse_progress(event: SRSGenerationProgressEvent) -> str:
    """Serialize one validated generation event as SSE data."""
    return f"data: {json.dumps(event.model_dump(mode='json'))}\n\n"


@router.post("/{project_id}/srs/generate/stream")
def stream_srs_generation(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> StreamingResponse:
    """Stream deterministic progress while keeping model output schema-gated."""

    def events() -> Iterator[str]:
        yield _sse_progress(
            SRSGenerationProgressEvent(
                phase="preparing", progress=5, message="Preparing project context."
            )
        )
        yield _sse_progress(
            SRSGenerationProgressEvent(
                phase="retrieving",
                progress=20,
                message="Retrieving relevant local security knowledge.",
            )
        )
        yield _sse_progress(
            SRSGenerationProgressEvent(
                phase="generating", progress=40, message="Generating structured SRS JSON."
            )
        )
        try:
            result = _srs_service(db, provider, settings).generate_srs(
                project_id, use_rag=settings.rag_enabled
            )
        except ApiError as exc:
            yield _sse_progress(
                SRSGenerationProgressEvent(
                    phase="failed",
                    progress=100,
                    message=exc.message,
                    error_code=exc.code,
                )
            )
            return
        except Exception:
            logger.exception("Unexpected failure during streamed SRS generation")
            yield _sse_progress(
                SRSGenerationProgressEvent(
                    phase="failed",
                    progress=100,
                    message="SRS generation failed unexpectedly. Please retry.",
                    error_code="internal_error",
                )
            )
            return
        yield _sse_progress(
            SRSGenerationProgressEvent(
                phase="validating",
                progress=90,
                message="Validating and persisting the generated specification.",
            )
        )
        yield _sse_progress(
            SRSGenerationProgressEvent(
                phase="completed",
                progress=100,
                message="SRS generation completed.",
                result=result,
            )
        )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{project_id}/srs", response_model=SRSVersionRead)
def get_latest_srs(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSVersionRead:
    """Retrieve the latest SRS version for the project."""
    return _srs_service(db, provider, settings).get_latest_version(project_id)


@router.get("/{project_id}/srs/versions", response_model=SRSVersionListResponse)
def list_srs_versions(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSVersionListResponse:
    """List all SRS versions for a project."""
    return _srs_service(db, provider, settings).list_versions(project_id)


@router.get("/{project_id}/srs/versions/{version_id}", response_model=SRSVersionRead)
def get_srs_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSVersionRead:
    """Retrieve a specific SRS version for the project."""
    return _srs_service(db, provider, settings).get_version(project_id, version_id)


@router.put("/{project_id}/srs/versions/{version_id}", response_model=SRSVersionRead)
def edit_srs_version(
    project_id: str,
    version_id: str,
    payload: SRSEditRequest,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
    _: None = Depends(enforce_request_body_size),
) -> SRSVersionRead:
    """Apply validated user edits to an SRS version."""
    return _srs_service(db, provider, settings).edit_version(project_id, version_id, payload)


@router.post(
    "/{project_id}/srs/versions/{version_id}/regenerate",
    response_model=SRSVersionRead,
)
def regenerate_srs_section(
    project_id: str,
    version_id: str,
    payload: SRSRegenerateSectionRequest,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
    _: None = Depends(enforce_request_body_size),
) -> SRSVersionRead:
    """Regenerate one selected section as a new SRS version."""
    return _srs_service(db, provider, settings).regenerate_section(
        project_id,
        version_id,
        payload,
    )


@router.post(
    "/{project_id}/srs/versions/{version_id}/validate",
    response_model=SRSValidationResponse,
)
def validate_srs_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSValidationResponse:
    """Run deterministic validation on an SRS version."""
    return _srs_service(db, provider, settings).validate_version(project_id, version_id)


@router.get("/{project_id}/srs/versions/{version_id}/sources")
def get_srs_sources(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
):
    """Get all source chunks cited by an SRS version."""
    version = _srs_service(db, provider, settings).get_version(project_id, version_id)
    srs_model = version.srs
    if srs_model is None:
        return {"sources": []}

    srs_data = srs_model.model_dump()

    # Collect all unique chunk_ids cited from requirements
    chunk_ids = set()
    section_keys = [
        "functional_requirements",
        "non_functional_requirements",
        "security_requirements",
        "data_requirements",
        "network_requirements",
    ]
    for key in section_keys:
        for req in srs_data.get(key, []):
            if isinstance(req, dict):
                for ref in req.get("source_references", []):
                    source_id = ref.get("source_id")
                    if source_id:
                        chunk_ids.add(source_id)

    if not chunk_ids:
        return {"sources": []}

    # Fetch chunks from ChromaDB by their chunk IDs
    chroma = _chroma_client(settings)
    all_chunks = chroma.get_chunks_by_ids(sorted(chunk_ids))
    project_chunks = _project_chroma_client(settings).get_chunks_by_ids(sorted(chunk_ids))
    all_chunks.extend(
        chunk
        for chunk in project_chunks
        if str(chunk.get("metadata", {}).get("project_id", "")) == project_id
    )

    return {"sources": all_chunks}


@router.get("/{project_id}/srs/versions/{version_id}/sources/{chunk_id}")
def get_srs_source_chunk(
    project_id: str,
    version_id: str,
    chunk_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
):
    """Get a specific source chunk by ID."""
    version = _srs_service(db, provider, settings).get_version(project_id, version_id)
    srs_model = version.srs
    if srs_model is None:
        from ...core.exceptions import SRSVersionNotFoundError

        raise SRSVersionNotFoundError()

    srs_data = srs_model.model_dump()

    # Verify the chunk_id is cited in this SRS
    section_keys = [
        "functional_requirements",
        "non_functional_requirements",
        "security_requirements",
        "data_requirements",
        "network_requirements",
    ]
    found = False
    for key in section_keys:
        for req in srs_data.get(key, []):
            if isinstance(req, dict):
                for ref in req.get("source_references", []):
                    if ref.get("source_id") == chunk_id:
                        found = True
                        break

    if not found:
        from ...core.exceptions import SRSVersionNotFoundError

        raise SRSVersionNotFoundError()

    # Fetch from ChromaDB by its chunk ID
    chroma = _chroma_client(settings)
    chunks = chroma.get_chunks_by_ids([chunk_id])
    if not chunks:
        chunks = [
            chunk
            for chunk in _project_chroma_client(settings).get_chunks_by_ids([chunk_id])
            if str(chunk.get("metadata", {}).get("project_id", "")) == project_id
        ]
    if not chunks:
        from ...core.exceptions import SRSVersionNotFoundError

        raise SRSVersionNotFoundError()

    return chunks[0]


@router.get("/{project_id}/srs/versions/{version_id}/export/pdf")
def export_srs_pdf(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    """Export an SRS version as a downloadable PDF."""
    from fastapi.responses import Response

    from ...services.pdf_export_service import PDFExportService

    service = PDFExportService(db, settings)
    pdf_bytes, filename = service.export_to_pdf(project_id, version_id)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )

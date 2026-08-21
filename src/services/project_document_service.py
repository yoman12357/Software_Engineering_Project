"""Secure local lifecycle for project-scoped reference documents."""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.exceptions import (
    InvalidProjectDocumentError,
    ProjectDocumentLimitError,
    ProjectDocumentNotFoundError,
    ProjectNotFoundError,
    UnsupportedProjectDocumentError,
)
from ..db.models import ProjectDocument
from ..rag.chromadb_client import create_chromadb_client
from ..rag.chunking import chunk_sections
from ..rag.embedding_provider import create_embedding_provider
from ..rag.parsers import DocumentParserError, get_parser
from ..repositories.project_document_repository import ProjectDocumentRepository
from ..repositories.project_repository import ProjectRepository
from ..schemas.project import generate_uuid

ALLOWED_EXTENSIONS = frozenset({".pdf", ".md", ".markdown", ".txt", ".csv"})
MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".csv": "text/csv",
}


class ProjectDocumentService:
    """Validate, parse, index, retrieve, and delete project documents."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._projects = ProjectRepository(session)
        self._documents = ProjectDocumentRepository(session)

    def upload(
        self,
        project_id: str,
        original_filename: str,
        content: bytes,
        supplied_media_type: str | None,
    ) -> ProjectDocument:
        """Safely store, parse, and optionally index one uploaded file."""
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError()
        existing = self._documents.list_for_project(project_id)
        if len(existing) >= self._settings.max_project_documents:
            raise ProjectDocumentLimitError("This project has reached its document limit.")
        if not content or len(content) > self._settings.max_upload_bytes:
            raise ProjectDocumentLimitError("The uploaded file is empty or too large.")

        display_name = Path(original_filename or "").name.strip()
        if not display_name or "\x00" in display_name or len(display_name) > 255:
            raise UnsupportedProjectDocumentError("The uploaded filename is invalid.")
        extension = Path(display_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise UnsupportedProjectDocumentError()
        self._validate_signature(extension, content, supplied_media_type)

        document_id = generate_uuid()
        upload_root = Path(self._settings.upload_dir).expanduser().resolve()
        project_dir = (upload_root / project_id).resolve()
        if upload_root not in project_dir.parents:
            raise UnsupportedProjectDocumentError("The project upload path is invalid.")
        project_dir.mkdir(parents=True, exist_ok=True)
        stored_path = (project_dir / f"{document_id}{extension}").resolve()
        if project_dir not in stored_path.parents:
            raise UnsupportedProjectDocumentError("The document upload path is invalid.")
        stored_path.write_bytes(content)

        try:
            content_sha256 = hashlib.sha256(content).hexdigest()
            parsed = get_parser(stored_path, self._settings).parse(stored_path, self._settings)
            extracted_text = parsed.text.strip()
            if not extracted_text:
                raise InvalidProjectDocumentError(
                    "The uploaded document contains no readable text."
                )
            chunks = chunk_sections(parsed.sections, self._settings, document_id)
            chunk_count = self._index_document(
                document_id, project_id, display_name, content_sha256, chunks
            )
            document = ProjectDocument(
                id=document_id,
                project_id=project_id,
                original_filename=display_name,
                stored_path=str(stored_path),
                media_type=MEDIA_TYPES[extension],
                file_extension=extension,
                file_size_bytes=len(content),
                sha256=content_sha256,
                status="ready",
                extracted_text=extracted_text,
                chunk_count=chunk_count,
            )
            self._documents.add(document)
            self._session.commit()
            self._session.refresh(document)
            return document
        except (
            ProjectDocumentLimitError,
            UnsupportedProjectDocumentError,
            InvalidProjectDocumentError,
        ):
            stored_path.unlink(missing_ok=True)
            raise
        except DocumentParserError as exc:
            stored_path.unlink(missing_ok=True)
            raise InvalidProjectDocumentError() from exc
        except Exception:
            stored_path.unlink(missing_ok=True)
            self._session.rollback()
            raise

    def list_for_project(self, project_id: str) -> list[ProjectDocument]:
        """List documents for an existing project."""
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError()
        return self._documents.list_for_project(project_id)

    def get_context(self, project_id: str) -> str:
        """Return bounded extracted document context for deterministic prompting."""
        remaining = self._settings.max_project_document_context_chars
        blocks: list[str] = []
        for document in self._documents.list_for_project(project_id):
            if remaining <= 0:
                break
            header = f"\n--- PROJECT DOCUMENT: {document.original_filename} ---\n"
            body = document.extracted_text[: max(0, remaining - len(header))]
            if body:
                blocks.append(header + body)
                remaining -= len(header) + len(body)
        return "".join(blocks)

    def delete(self, project_id: str, document_id: str) -> None:
        """Delete a document, its local file, and any project vector chunks."""
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError()
        document = self._documents.get(project_id, document_id)
        if document is None:
            raise ProjectDocumentNotFoundError()
        if self._settings.rag_enabled and document.chunk_count:
            project_settings = self._settings.model_copy(
                update={"chroma_collection": self._settings.project_chroma_collection}
            )
            create_chromadb_client(project_settings).delete_source(document.id)
        stored_path = Path(document.stored_path).resolve()
        upload_root = Path(self._settings.upload_dir).expanduser().resolve()
        if upload_root in stored_path.parents:
            stored_path.unlink(missing_ok=True)
        self._documents.delete(document)
        self._session.commit()

    def _index_document(
        self,
        document_id: str,
        project_id: str,
        title: str,
        content_sha256: str,
        chunks: list,
    ) -> int:
        """Index chunks in the isolated project collection when RAG is enabled."""
        if not self._settings.rag_enabled or not chunks:
            return 0
        project_settings = self._settings.model_copy(
            update={"chroma_collection": self._settings.project_chroma_collection}
        )
        embeddings = create_embedding_provider(project_settings).embed_sync(
            [chunk.text for chunk in chunks]
        )
        return create_chromadb_client(project_settings).upsert_chunks(
            document_id,
            chunks,
            {
                "title": title,
                "project_id": project_id,
                "document_scope": "project",
                "file_hash_sha256": content_sha256,
            },
            embeddings,
        )

    @staticmethod
    def _validate_signature(
        extension: str, content: bytes, supplied_media_type: str | None
    ) -> None:
        """Reject obvious extension/content mismatches and binary text uploads."""
        if extension == ".pdf" and not content.startswith(b"%PDF-"):
            raise UnsupportedProjectDocumentError("The file is not a valid PDF upload.")
        if extension != ".pdf" and b"\x00" in content[:4096]:
            raise UnsupportedProjectDocumentError("Binary data is not accepted as a text document.")
        if supplied_media_type and supplied_media_type == "application/x-msdownload":
            raise UnsupportedProjectDocumentError()

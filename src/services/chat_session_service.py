"""Business logic for local chat-session persistence."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..core.exceptions import ChatSessionNotFoundError, ProjectNotFoundError
from ..db.models import ChatMessageRecord, ChatSession, Project
from ..repositories.chat_session_repository import ChatSessionRepository
from ..schemas.chat_session import (
    ChatSessionRead,
    ChatSessionUpdate,
    ChatSessionWrite,
    StoredChatMessage,
)


class ChatSessionService:
    """Create, restore, update, list, and delete resumable chat sessions."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repository = ChatSessionRepository(session)

    @staticmethod
    def _message_read(message: ChatMessageRecord) -> StoredChatMessage:
        """Convert an ORM message into its API representation."""
        return StoredChatMessage(
            id=message.id,
            role=message.role,
            content=message.content,
            type=message.message_type,
            metadata=message.metadata_json,
            timestamp=message.timestamp,
        )

    def _read(self, chat_session: ChatSession) -> ChatSessionRead:
        """Convert an ORM chat session into its API representation."""
        return ChatSessionRead(
            id=chat_session.id,
            project_id=chat_session.project_id,
            name=chat_session.name,
            messages=[self._message_read(message) for message in chat_session.messages],
            stage=chat_session.stage,
            analysis=chat_session.analysis_json,
            clarification_questions=chat_session.clarification_questions_json,
            srs=chat_session.srs_json,
            srs_version_id=chat_session.srs_version_id,
            pending_project_description=chat_session.pending_project_description,
            pinned_at=chat_session.pinned_at,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
        )

    def save(self, session_id: str, payload: ChatSessionWrite) -> ChatSessionRead:
        """Create or replace a full session snapshot in one transaction."""
        if payload.project_id and self._session.get(Project, payload.project_id) is None:
            raise ProjectNotFoundError()
        chat_session = self._repository.get(session_id)
        if chat_session is None:
            chat_session = ChatSession(id=session_id)
            self._repository.add(chat_session)
        chat_session.project_id = payload.project_id
        chat_session.name = payload.name.strip()
        chat_session.stage = payload.stage
        chat_session.analysis_json = payload.analysis
        chat_session.clarification_questions_json = payload.clarification_questions
        chat_session.srs_json = payload.srs
        chat_session.srs_version_id = payload.srs_version_id
        chat_session.pending_project_description = payload.pending_project_description
        chat_session.updated_at = datetime.now(UTC)
        chat_session.messages = [
            ChatMessageRecord(
                id=message.id,
                role=message.role,
                content=message.content,
                message_type=message.type,
                metadata_json=message.metadata,
                timestamp=message.timestamp,
            )
            for message in payload.messages
        ]
        self._session.commit()
        return self._read(self._repository.get(session_id) or chat_session)

    def get(self, session_id: str) -> ChatSessionRead:
        """Return one complete session or raise a stable not-found error."""
        chat_session = self._repository.get(session_id)
        if chat_session is None:
            raise ChatSessionNotFoundError()
        return self._read(chat_session)

    def list_recent(self, limit: int) -> list[ChatSessionRead]:
        """List recent sessions in sidebar order."""
        return [self._read(item) for item in self._repository.list_recent(limit)]

    def update(self, session_id: str, payload: ChatSessionUpdate) -> ChatSessionRead:
        """Rename and/or pin a session."""
        chat_session = self._repository.get(session_id)
        if chat_session is None:
            raise ChatSessionNotFoundError()
        if payload.name is not None:
            chat_session.name = payload.name.strip()
        if payload.pinned is not None:
            chat_session.pinned_at = datetime.now(UTC) if payload.pinned else None
        chat_session.updated_at = datetime.now(UTC)
        self._session.commit()
        return self._read(chat_session)

    def delete(self, session_id: str) -> None:
        """Permanently delete a session and its messages."""
        chat_session = self._repository.get(session_id)
        if chat_session is None:
            raise ChatSessionNotFoundError()
        self._repository.delete(chat_session)
        self._session.commit()

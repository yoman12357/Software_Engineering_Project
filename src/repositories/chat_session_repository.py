"""Data-access operations for persisted chat sessions."""

from sqlalchemy import case, select
from sqlalchemy.orm import Session, selectinload

from ..db.models import ChatSession


class ChatSessionRepository:
    """Persistence helpers for chat sessions and their messages."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, session_id: str) -> ChatSession | None:
        """Return one session with ordered messages, if it exists."""
        statement = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return self._session.scalar(statement)

    def list_recent(self, limit: int) -> list[ChatSession]:
        """Return pinned sessions first, followed by newest activity."""
        statement = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .order_by(
                case((ChatSession.pinned_at.is_not(None), 0), else_=1),
                ChatSession.pinned_at.desc(),
                ChatSession.updated_at.desc(),
            )
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def add(self, chat_session: ChatSession) -> None:
        """Add a new chat session to the current transaction."""
        self._session.add(chat_session)

    def delete(self, chat_session: ChatSession) -> None:
        """Delete a chat session and its messages."""
        self._session.delete(chat_session)

"""Conversation session persistence utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import ConversationMessage, ConversationSession


class ConversationStore:
    """Store for chat sessions and messages."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        *,
        project_id: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> ConversationSession:
        session = ConversationSession(
            project_id=project_id,
            summary=summary,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def list_sessions(
        self,
        *,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSession]:
        stmt: Select = (
            select(ConversationSession)
            .order_by(ConversationSession.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if project_id:
            stmt = stmt.where(ConversationSession.project_id == project_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_session(self, session_id: str, include_messages: bool = True) -> Optional[ConversationSession]:
        stmt = select(ConversationSession).where(ConversationSession.id == session_id)
        if include_messages:
            stmt = stmt.options(joinedload(ConversationSession.messages))
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        modality: str = "text",
        timestamp: Optional[datetime] = None,
    ) -> ConversationMessage:
        session = await self.get_session(session_id, include_messages=False)
        if not session:
            raise NoResultFound(f"Conversation session {session_id} not found")

        message = ConversationMessage(
            session_id=session_id,
            role=role,
            content=content,
            modality=modality,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def end_session(
        self,
        session_id: str,
        *,
        summary: Optional[str] = None,
        generated_plans: Optional[list[str]] = None,
    ) -> ConversationSession:
        session = await self.get_session(session_id, include_messages=False)
        if not session:
            raise NoResultFound(f"Conversation session {session_id} not found")

        session.ended_at = datetime.now(timezone.utc)
        if summary is not None:
            session.summary = summary
        if generated_plans is not None:
            session.generated_plans = generated_plans

        await self.session.flush()
        return session

    async def delete_session(self, session_id: str) -> None:
        session = await self.get_session(session_id, include_messages=False)
        if not session:
            raise NoResultFound(f"Conversation session {session_id} not found")
        await self.session.delete(session)
        await self.session.flush()

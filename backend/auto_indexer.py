"""Automated indexing hooks for projects, plans, and conversations."""

from __future__ import annotations

import asyncio
import weakref
from datetime import datetime
from typing import Any, Iterable, Mapping, Optional

from loguru import logger

try:
    from .devplan_processor import DevPlanProcessor
    from .project_indexer import ProjectIndexer
except ImportError:  # pragma: no cover - standalone execution support
    from devplan_processor import DevPlanProcessor
    from project_indexer import ProjectIndexer


class AutoIndexer:
    """Background helper that keeps vector stores in sync with domain events."""

    def __init__(
        self,
        *,
        devplan_processor: Optional[DevPlanProcessor] = None,
        project_indexer: Optional[ProjectIndexer] = None,
    ) -> None:
        self.devplan_processor = devplan_processor or DevPlanProcessor()
        self.project_indexer = project_indexer or ProjectIndexer()
        self._rag_handlers: "weakref.WeakSet[Any]" = weakref.WeakSet()

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    def register_rag_handler(self, handler: Any) -> None:
        """Allow RAG handlers to receive reload notifications after indexing."""
        if handler is None:
            return
        self._rag_handlers.add(handler)

    # ------------------------------------------------------------------
    # Event hooks
    # ------------------------------------------------------------------
    async def on_plan_created(self, plan: Any, *, content: str) -> None:
        payload = self._plan_payload(plan)
        await asyncio.to_thread(self.devplan_processor.process_plan, payload, content=content)
        await self._notify_rag_handlers(plan_index=True)

    async def on_plan_updated(self, plan: Any, *, content: str) -> None:
        await self.on_plan_created(plan, content=content)

    async def on_plan_deleted(self, plan_id: str) -> None:
        removed = await asyncio.to_thread(self.devplan_processor.remove_plan, plan_id)
        if removed:
            await self._notify_rag_handlers(plan_index=True)

    async def on_project_created(self, project: Any) -> None:
        payload = self._project_payload(project)
        await asyncio.to_thread(self.project_indexer.index_project, payload)
        await self._notify_rag_handlers(project_index=True)

    async def on_project_updated(self, project: Any) -> None:
        await self.on_project_created(project)

    async def on_project_deleted(self, project_id: str) -> None:
        removed = await asyncio.to_thread(self.project_indexer.remove_project, project_id)
        if removed:
            await self._notify_rag_handlers(project_index=True)

    async def on_conversation_ended(self, conversation: Any) -> None:
        payload = self._conversation_payload(conversation)
        await asyncio.to_thread(self.project_indexer.index_conversation, payload)
        await self._notify_rag_handlers(project_index=True)

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    async def _notify_rag_handlers(self, *, plan_index: bool = False, project_index: bool = False) -> None:
        for handler in list(self._rag_handlers):
            if handler is None:
                continue
            try:
                if plan_index and hasattr(handler, "reload_plan_vector_store"):
                    await asyncio.to_thread(handler.reload_plan_vector_store)
                if project_index and hasattr(handler, "reload_project_vector_store"):
                    await asyncio.to_thread(handler.reload_project_vector_store)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to notify RAG handler of index update: %s", exc)

    def _plan_payload(self, plan: Any) -> dict[str, Any]:
        if isinstance(plan, Mapping):
            metadata = dict(plan.get("metadata") or {})
            return {
                "id": plan.get("id"),
                "project_id": plan.get("project_id"),
                "title": plan.get("title"),
                "status": plan.get("status"),
                "metadata": metadata,
                "current_version": plan.get("current_version", 1),
                "conversation_id": plan.get("conversation_id"),
                "created_at": self._datetime_to_iso(plan.get("created_at")),
                "updated_at": self._datetime_to_iso(plan.get("updated_at")),
            }

        metadata = getattr(plan, "metadata_dict", {}) or {}
        return {
            "id": getattr(plan, "id", None),
            "project_id": getattr(plan, "project_id", None),
            "title": getattr(plan, "title", None),
            "status": getattr(plan, "status", None),
            "metadata": dict(metadata),
            "current_version": getattr(plan, "current_version", 1),
            "conversation_id": getattr(plan, "conversation_id", None),
            "created_at": self._datetime_to_iso(getattr(plan, "created_at", None)),
            "updated_at": self._datetime_to_iso(getattr(plan, "updated_at", None)),
        }

    def _project_payload(self, project: Any) -> dict[str, Any]:
        if isinstance(project, Mapping):
            tags = project.get("tags") or []
            return {
                "id": project.get("id") or project.get("project_id"),
                "name": project.get("name"),
                "description": project.get("description"),
                "status": project.get("status"),
                "tags": list(tags) if isinstance(tags, Iterable) and not isinstance(tags, (str, bytes)) else [tags],
                "plan_count": project.get("plan_count", 0),
                "conversation_count": project.get("conversation_count", 0),
                "updated_at": self._datetime_to_iso(project.get("updated_at")),
                "repository_path": project.get("repository_path"),
            }

        tags = getattr(project, "tags", []) or []
        if isinstance(tags, Iterable) and not isinstance(tags, (str, bytes)):
            tag_list = list(tags)
        else:
            tag_list = [tags]

        return {
            "id": getattr(project, "id", None),
            "name": getattr(project, "name", None),
            "description": getattr(project, "description", None),
            "status": getattr(project, "status", None),
            "tags": tag_list,
            "plan_count": getattr(project, "plan_count", 0),
            "conversation_count": getattr(project, "conversation_count", 0),
            "updated_at": self._datetime_to_iso(getattr(project, "updated_at", None)),
            "repository_path": getattr(project, "repository_path", None),
        }

    def _conversation_payload(self, conversation: Any) -> dict[str, Any]:
        if isinstance(conversation, Mapping):
            messages = conversation.get("messages") or []
            return {
                "id": conversation.get("id") or conversation.get("session_id"),
                "project_id": conversation.get("project_id"),
                "summary": conversation.get("summary"),
                "generated_plans": conversation.get("generated_plans") or [],
                "started_at": self._datetime_to_iso(conversation.get("started_at")),
                "ended_at": self._datetime_to_iso(conversation.get("ended_at")),
                "message_count": len(messages) if messages else conversation.get("message_count"),
            }

        messages = getattr(conversation, "messages", None)
        return {
            "id": getattr(conversation, "id", None),
            "project_id": getattr(conversation, "project_id", None),
            "summary": getattr(conversation, "summary", None),
            "generated_plans": getattr(conversation, "generated_plans", []) or [],
            "started_at": self._datetime_to_iso(getattr(conversation, "started_at", None)),
            "ended_at": self._datetime_to_iso(getattr(conversation, "ended_at", None)),
            "message_count": len(messages) if isinstance(messages, list) else None,
        }

    @staticmethod
    def _datetime_to_iso(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value


_AUTO_INDEXER: Optional[AutoIndexer] = None


def get_auto_indexer() -> AutoIndexer:
    global _AUTO_INDEXER
    if _AUTO_INDEXER is None:
        _AUTO_INDEXER = AutoIndexer()
    return _AUTO_INDEXER

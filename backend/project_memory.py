"""High-level project memory aggregation for planning context."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

from loguru import logger

try:
    from .storage.conversation_store import ConversationStore
    from .storage.plan_store import DevPlanStore
    from .storage.project_store import ProjectStore
except ImportError:  # pragma: no cover - allow standalone execution
    from storage.conversation_store import ConversationStore
    from storage.plan_store import DevPlanStore
    from storage.project_store import ProjectStore

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .rag_handler import RAGHandler  # noqa: F401


class ProjectMemorySystem:
    """Aggregates projects, plans, conversations, and semantic neighbours."""

    def __init__(
        self,
        *,
        project_store: ProjectStore,
        plan_store: DevPlanStore,
        conversation_store: ConversationStore,
        rag_handler: Optional[Any] = None,
    ) -> None:
        self.project_store = project_store
        self.plan_store = plan_store
        self.conversation_store = conversation_store
        self.rag_handler = rag_handler

    async def get_project_context(self, project_id: str, *, similar_limit: int = 3) -> Dict[str, Any]:
        project_task = asyncio.create_task(self.project_store.get_project_with_stats(project_id))
        plans_task = asyncio.create_task(self.plan_store.list_plans(project_id=project_id, limit=20))
        conversations_task = asyncio.create_task(self.conversation_store.list_sessions(project_id=project_id, limit=20))

        project = await project_task
        plans = await plans_task
        conversations = await conversations_task

        if not project:
            raise ValueError(f"Project {project_id} not found")

        similar = self._search_similar_projects(project, k=similar_limit) if self.rag_handler else []
        conversation_summary = self._summarize_conversations(conversations)
        key_decisions = self._extract_key_decisions(plans)
        lessons = self._extract_lessons(conversations)

        return {
            "project": self._project_payload(project),
            "plans": [self._plan_payload(plan) for plan in plans],
            "conversation_summary": conversation_summary,
            "similar_projects": similar,
            "key_decisions": key_decisions,
            "lessons_learned": lessons,
        }

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _search_similar_projects(self, project: Any, *, k: int) -> List[Dict[str, Any]]:
        if not self.rag_handler:
            return []
        query = f"Projects similar to {getattr(project, 'name', project)}"
        try:
            results = self.rag_handler.search(query, k=k, metadata_filter={"type": "project"})
            if not isinstance(results, list):
                return []
            return results
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.debug("Project similarity search failed: %s", exc)
            return []

    def _summarize_conversations(self, conversations: Iterable[Any]) -> List[Dict[str, Any]]:
        summary: List[Dict[str, Any]] = []
        for convo in conversations:
            item = {
                "id": getattr(convo, "id", None),
                "project_id": getattr(convo, "project_id", None),
                "summary": getattr(convo, "summary", "") or "",
                "generated_plans": list(getattr(convo, "generated_plans", []) or []),
                "started_at": self._safe_iso(getattr(convo, "started_at", None)),
                "ended_at": self._safe_iso(getattr(convo, "ended_at", None)),
            }
            summary.append(item)
        return summary

    def _extract_key_decisions(self, plans: Iterable[Any]) -> List[str]:
        decisions: List[str] = []
        for plan in plans:
            metadata = getattr(plan, "metadata_dict", {}) or {}
            if isinstance(plan, dict):  # pragma: no cover - fallback
                metadata = plan.get("metadata", {}) or {}
            for key in ("key_decisions", "decisions", "milestones"):
                value = metadata.get(key)
                if isinstance(value, list):
                    decisions.extend(str(item) for item in value)
                elif isinstance(value, str) and value.strip():
                    decisions.append(value.strip())
        return decisions[:10]

    def _extract_lessons(self, conversations: Iterable[Any]) -> List[str]:
        lessons: List[str] = []
        for convo in conversations:
            summary = getattr(convo, "summary", "") or ""
            if "lesson" in summary.lower():
                lessons.append(summary)
        return lessons[:5]

    def _plan_payload(self, plan: Any) -> Dict[str, Any]:
        return {
            "id": getattr(plan, "id", None),
            "title": getattr(plan, "title", None),
            "status": getattr(plan, "status", None),
            "current_version": getattr(plan, "current_version", None),
            "updated_at": self._safe_iso(getattr(plan, "updated_at", None)),
        }

    def _project_payload(self, project: Any) -> Dict[str, Any]:
        tags = getattr(project, "tags", []) or []
        if isinstance(tags, (list, tuple, set)):
            tag_list = list(tags)
        elif isinstance(tags, str):
            tag_list = [tags]
        else:  # pragma: no cover
            tag_list = []
        return {
            "id": getattr(project, "id", None),
            "name": getattr(project, "name", None),
            "status": getattr(project, "status", None),
            "plan_count": getattr(project, "plan_count", 0),
            "conversation_count": getattr(project, "conversation_count", 0),
            "tags": tag_list,
            "updated_at": self._safe_iso(getattr(project, "updated_at", None)),
        }

    @staticmethod
    def _safe_iso(value: Any) -> Optional[str]:
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:  # pragma: no cover
                return None
        if isinstance(value, str):
            return value
        return None

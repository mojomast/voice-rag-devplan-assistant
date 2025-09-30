from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

try:
    from .storage.conversation_store import ConversationStore
    from .storage.plan_store import DevPlanStore
    from .storage.project_store import ProjectStore
except ImportError:  # pragma: no cover - allow direct module execution in tests
    from storage.conversation_store import ConversationStore
    from storage.plan_store import DevPlanStore
    from storage.project_store import ProjectStore

if TYPE_CHECKING:  # pragma: no cover
    try:
        from .rag_handler import RAGHandler
    except ImportError:  # pragma: no cover
        from rag_handler import RAGHandler


@dataclass
class PlanningContext:
    """Structured context blob passed to the planning agent."""

    project: Optional[Dict[str, Any]] = None
    recent_plans: List[Dict[str, Any]] = field(default_factory=list)
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    rag_sources: List[Dict[str, Any]] = field(default_factory=list)
    rag_answer: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)

    def as_prompt_section(self) -> str:
        project_section = "None" if not self.project else json_like(self.project)
        plans_section = "\n".join(json_like(plan) for plan in self.recent_plans) or "None"
        messages_section = "\n".join(
            f"[{msg['role']}] {msg['content']}" for msg in self.recent_messages
        ) or "None"
        sources_section = "\n".join(json_like(src) for src in self.rag_sources) or "None"
        suggestions_section = "\n".join(self.suggestions) or "None"

        rag_summary = self.rag_answer or "None"

        return (
            f"Project Summary:\n{project_section}\n\n"
            f"Recent Plans:\n{plans_section}\n\n"
            f"Conversation Snippet:\n{messages_section}\n\n"
            f"RAG Summary:\n{rag_summary}\n\n"
            f"RAG Sources:\n{sources_section}\n\n"
            f"Agent Suggestions:\n{suggestions_section}"
        )


def json_like(payload: Dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in payload.items())


class PlanningContextManager:
    """Builds relevant context from storage + RAG for the planning agent."""

    def __init__(
        self,
        *,
        project_store: ProjectStore,
        plan_store: DevPlanStore,
        conversation_store: ConversationStore,
        rag_handler: Optional["RAGHandler"] = None,
    ) -> None:
        self.project_store = project_store
        self.plan_store = plan_store
        self.conversation_store = conversation_store
        self.rag_handler = rag_handler

    async def build_context(
        self,
        *,
        query: str,
        project_id: Optional[str],
        session_id: Optional[str],
        max_messages: int = 6,
        max_plans: int = 3,
    ) -> PlanningContext:
        project_task = None
        if project_id:
            project_task = asyncio.create_task(self.project_store.get_project_with_stats(project_id))

        plans_task = asyncio.create_task(
            self.plan_store.list_plans(project_id=project_id, limit=max_plans)
        )

        conversation_task = None
        if session_id:
            conversation_task = asyncio.create_task(
                self.conversation_store.get_session(session_id, include_messages=True)
            )

        project = await project_task if project_task else None
        plans = await plans_task
        conversation = await conversation_task if conversation_task else None

        recent_messages: List[Dict[str, Any]] = []
        if conversation and conversation.messages:
            for message in conversation.messages[-max_messages:]:
                recent_messages.append(
                    {
                        "id": message.id,
                        "role": message.role,
                        "content": message.content,
                        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                        "modality": message.modality,
                    }
                )

        project_summary = None
        if project:
            project_summary = {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "plan_count": project.plan_count,
                "conversation_count": project.conversation_count,
                "tags": project.tags,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            }

        plan_summaries: List[Dict[str, Any]] = []
        for plan in plans:
            plan_summaries.append(
                {
                    "id": plan.id,
                    "title": plan.title,
                    "status": plan.status,
                    "current_version": plan.current_version,
                    "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
                }
            )

        rag_answer = None
        rag_sources: List[Dict[str, Any]] = []
        suggestions: List[str] = []

        if self.rag_handler:
            loop = asyncio.get_running_loop()
            try:
                rag_result = await loop.run_in_executor(
                    None, lambda: self.rag_handler.ask_question(f"Summarise similar work: {query}")
                )
                rag_answer = rag_result.get("answer") if isinstance(rag_result, dict) else None
                rag_sources = rag_result.get("sources", []) if isinstance(rag_result, dict) else []
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.debug(f"RAG lookup failed: {exc}")

        if rag_answer:
            suggestions.append(rag_answer)
        if project_summary and project_summary.get("tags"):
            suggestions.append(
                "Existing project tags: " + ", ".join(project_summary["tags"])
            )

        return PlanningContext(
            project=project_summary,
            recent_plans=plan_summaries,
            recent_messages=recent_messages,
            rag_sources=rag_sources,
            rag_answer=rag_answer,
            suggestions=suggestions,
        )

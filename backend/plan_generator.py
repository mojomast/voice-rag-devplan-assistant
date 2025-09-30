from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

try:
    from .config import settings
    from .context_manager import PlanningContext
    from .models import DevPlan
    from .requesty_client import RequestyClient
    from .storage.plan_store import DevPlanStore
except ImportError:  # pragma: no cover - enable direct imports in tests
    from config import settings
    from context_manager import PlanningContext
    from models import DevPlan
    from requesty_client import RequestyClient
    from storage.plan_store import DevPlanStore


@dataclass
class PlanDraft:
    title: str
    content: str
    summary: str
    metadata: Dict[str, Any]


class DevPlanGenerator:
    """Generates and persists structured development plans via the LLM."""

    def __init__(self, *, plan_store: DevPlanStore, llm_client: RequestyClient) -> None:
        self.plan_store = plan_store
        self.llm_client = llm_client

    async def generate_plan(
        self,
        *,
        project_id: str,
        conversation_id: Optional[str],
        context: PlanningContext,
        plan_brief: Optional[str],
    ) -> DevPlan:
        messages = self._build_plan_prompt(context=context, plan_brief=plan_brief)
        raw_response = await self.llm_client.achat_completion(
            messages,
            temperature=settings.PLANNING_TEMPERATURE,
            max_tokens=settings.PLANNING_MAX_TOKENS,
            model=settings.REQUESTY_PLANNING_MODEL,
        )

        draft = self._parse_plan_response(raw_response, plan_brief=plan_brief)

        plan = await self.plan_store.create_plan(
            project_id=project_id,
            title=draft.title,
            content=draft.content,
            conversation_id=conversation_id,
            metadata=draft.metadata,
            change_summary=draft.summary,
        )

        logger.info("Created development plan %s for project %s", plan.id, project_id)
        return plan

    def _build_plan_prompt(
        self,
        *,
        context: PlanningContext,
        plan_brief: Optional[str],
    ) -> list[dict[str, str]]:
        system_message = (
            "You are an expert development planning assistant. "
            "Produce a complete development plan in Markdown using the following JSON schema:"
            " {plan_title: string, plan_summary: string, plan_markdown: string, metadata: object}. "
            "Ensure the markdown includes the sections: Overview & Goals, Requirements & Constraints, "
            "Architecture & Design, Implementation Phases (with tasks, estimates, and dependencies), "
            "Testing Strategy, Deployment Plan, Maintenance & Monitoring."
        )

        context_section = context.as_prompt_section()
        brief = plan_brief or "Use the conversation context to infer project goals and deliver a comprehensive plan."

        user_message = (
            f"Context:\n{context_section}\n\n"
            f"Plan Brief:\n{brief}\n\n"
            "Respond ONLY with valid JSON matching the schema."
        )

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def _parse_plan_response(self, response: str, plan_brief: Optional[str]) -> PlanDraft:
        try:
            payload = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Plan response was not JSON; returning markdown fallback")
            title = self._infer_title(response, fallback=plan_brief)
            return PlanDraft(
                title=title,
                content=response.strip(),
                summary="Generated without structured payload",
                metadata={},
            )

        plan_markdown = payload.get("plan_markdown") or payload.get("content") or ""
        if not plan_markdown:
            logger.warning("Plan payload missing markdown content; using summary as fallback")
            plan_markdown = payload.get("plan_summary", "No plan content provided.")

        title = payload.get("plan_title") or self._infer_title(plan_markdown, fallback=plan_brief)
        summary = payload.get("plan_summary") or "Development plan generated via agent."
        metadata = payload.get("metadata") or {}

        return PlanDraft(title=title, content=plan_markdown.strip(), summary=summary, metadata=metadata)

    @staticmethod
    def _infer_title(content: str, fallback: Optional[str]) -> str:
        for line in content.splitlines():
            if line.startswith("#"):
                return line.lstrip("# ").strip() or (fallback or "Development Plan")
        return fallback or "Development Plan"

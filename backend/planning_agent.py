from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

try:
    from .config import settings
    from .context_manager import PlanningContext, PlanningContextManager
    from .plan_generator import DevPlanGenerator
    from .requesty_client import RequestyClient
    from .storage.conversation_store import ConversationStore
except ImportError:  # pragma: no cover - allow direct imports in tests
    from config import settings
    from context_manager import PlanningContext, PlanningContextManager
    from plan_generator import DevPlanGenerator
    from requesty_client import RequestyClient
    from storage.conversation_store import ConversationStore


@dataclass
class AgentResult:
    reply: str
    actions: Dict[str, Any]
    plan: Optional[Any]  # DevPlan returned from store
    context: PlanningContext


class PlanningAgent:
    """High-level orchestrator for planning conversations."""

    def __init__(
        self,
        *,
        context_manager: PlanningContextManager,
        plan_generator: DevPlanGenerator,
        conversation_store: ConversationStore,
        llm_client: RequestyClient,
    ) -> None:
        self.context_manager = context_manager
        self.plan_generator = plan_generator
        self.conversation_store = conversation_store
        self.llm_client = llm_client

    async def handle_message(
        self,
        *,
        message: str,
        session_id: str,
        project_id: Optional[str],
    ) -> AgentResult:
        conversation = await self.conversation_store.get_session(session_id, include_messages=True)
        if not conversation:
            raise ValueError(f"Conversation session {session_id} not found")

        context = await self.context_manager.build_context(
            query=message,
            project_id=project_id,
            session_id=session_id,
        )

        prompt_messages = self._build_prompt_messages(conversation, message, context)
        raw_reply = await self.llm_client.achat_completion(
            prompt_messages,
            temperature=settings.PLANNING_TEMPERATURE,
            max_tokens=settings.PLANNING_MAX_TOKENS,
            model=settings.REQUESTY_PLANNING_MODEL,
        )

        parsed = self._parse_agent_response(raw_reply)
        reply_text = parsed.get("assistant_reply") or raw_reply
        actions = parsed.get("actions", {})

        plan = None
        if actions.get("create_plan"):
            if not project_id:
                logger.info("Plan creation requested but no project specified; skipping plan generation")
                actions["create_plan"] = False
                actions["reason"] = "project_id_missing"
            else:
                plan = await self.plan_generator.generate_plan(
                    project_id=project_id,
                    conversation_id=conversation.id,
                    context=context,
                    plan_brief=actions.get("plan_brief") or message,
                )

        return AgentResult(reply=reply_text, actions=actions, plan=plan, context=context)

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------
    def _build_prompt_messages(self, conversation, latest_message: str, context: PlanningContext) -> list[dict[str, str]]:
        history_lines = []
        for message in conversation.messages[-8:]:  # limit history to avoid long prompts
            prefix = "User" if message.role == "user" else "Assistant"
            history_lines.append(f"{prefix}: {message.content}")

        history_section = "\n".join(history_lines) or "No prior conversation"
        context_section = context.as_prompt_section()

        system_instructions = (
            "You are the PlanningAgent inside a development planning assistant. "
            "Always respond with valid JSON using the schema {assistant_reply: string, actions: object}. "
            "If the user is ready for a plan, set actions.create_plan to true and include plan_brief." 
            "If plan creation should be deferred, set create_plan to false." 
            "Respond with helpful planning guidance in assistant_reply."
        )

        user_payload = (
            f"Conversation History:\n{history_section}\n\n"
            f"Planning Context:\n{context_section}\n\n"
            f"Latest User Message:\n{latest_message}\n\n"
            "Return JSON only."
        )

        return [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_payload},
        ]

    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        try:
            payload = json.loads(response)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            logger.debug("Agent response not JSON, returning fallback structure")
        return {"assistant_reply": response, "actions": {"create_plan": False}}

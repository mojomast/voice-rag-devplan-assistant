from __future__ import annotations

import json
import time
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
        start_time = time.time()
        
        logger.info(
            "Planning agent handling message",
            extra={
                "session_id": session_id,
                "project_id": project_id,
                "message_length": len(message),
            }
        )
        
        conversation = await self.conversation_store.get_session(session_id, include_messages=True)
        if not conversation:
            logger.error("Conversation session not found", extra={"session_id": session_id})
            raise ValueError(f"Conversation session {session_id} not found")

        # Build context with timing
        context_start = time.time()
        context = await self.context_manager.build_context(
            query=message,
            project_id=project_id,
            session_id=session_id,
        )
        context_time = time.time() - context_start
        logger.debug(f"Context building took {context_time:.3f}s")

        # Build prompt and call LLM with timing
        prompt_messages = self._build_prompt_messages(conversation, message, context)
        llm_start = time.time()
        raw_reply = await self.llm_client.achat_completion(
            prompt_messages,
            temperature=settings.PLANNING_TEMPERATURE,
            max_tokens=settings.PLANNING_MAX_TOKENS,
            model=settings.REQUESTY_PLANNING_MODEL,
        )
        llm_time = time.time() - llm_start
        logger.info(
            "LLM agent response received",
            extra={
                "model": settings.REQUESTY_PLANNING_MODEL,
                "response_time_seconds": llm_time,
                "response_length": len(raw_reply),
            }
        )

        # Parse response
        parsed = self._parse_agent_response(raw_reply)
        reply_text = parsed.get("assistant_reply") or raw_reply
        actions = parsed.get("actions", {})
        
        is_json = isinstance(parsed, dict) and "actions" in parsed
        logger.debug(
            "Agent response parsed",
            extra={
                "is_json": is_json,
                "create_plan": actions.get("create_plan", False),
            }
        )

        # Plan generation if requested
        plan = None
        plan_gen_time = 0.0
        if actions.get("create_plan"):
            if not project_id:
                logger.warning(
                    "Plan creation requested but no project specified",
                    extra={"session_id": session_id}
                )
                actions["create_plan"] = False
                actions["reason"] = "project_id_missing"
            else:
                plan_start = time.time()
                plan = await self.plan_generator.generate_plan(
                    project_id=project_id,
                    conversation_id=conversation.id,
                    context=context,
                    plan_brief=actions.get("plan_brief") or message,
                )
                plan_gen_time = time.time() - plan_start
                logger.info(
                    "Development plan generated",
                    extra={
                        "plan_id": plan.id,
                        "plan_title": plan.title,
                        "generation_time_seconds": plan_gen_time,
                    }
                )

        total_time = time.time() - start_time
        logger.info(
            "Planning agent completed",
            extra={
                "total_time_seconds": total_time,
                "context_time_seconds": context_time,
                "llm_time_seconds": llm_time,
                "plan_gen_time_seconds": plan_gen_time,
                "plan_generated": plan is not None,
            }
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

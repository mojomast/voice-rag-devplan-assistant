"""Planning chat API routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..context_manager import PlanningContextManager
from ..database import get_session
from ..plan_generator import DevPlanGenerator
from ..planning_agent import PlanningAgent
from ..rag_handler import RAGHandler
from ..requesty_client import RequestyClient
from ..schemas.planning import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationDetail,
    ConversationSummary,
)
from ..storage.conversation_store import ConversationStore
from ..storage.plan_store import DevPlanStore
from ..storage.project_store import ProjectStore

router = APIRouter(prefix="/planning", tags=["planning"])

_rag_handler: Optional[RAGHandler] = None


def _get_rag_handler() -> Optional[RAGHandler]:
    global _rag_handler
    if _rag_handler is None:
        try:
            _rag_handler = RAGHandler()
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning(f"Failed to initialise RAGHandler for planning agent: {exc}")
            _rag_handler = None
    return _rag_handler


def _build_agent(session: AsyncSession) -> PlanningAgent:
    conversation_store = ConversationStore(session)
    project_store = ProjectStore(session)
    plan_store = DevPlanStore(session)
    rag_handler = _get_rag_handler()
    requesty = RequestyClient()

    context_manager = PlanningContextManager(
        project_store=project_store,
        plan_store=plan_store,
        conversation_store=conversation_store,
        rag_handler=rag_handler,
    )

    plan_generator = DevPlanGenerator(plan_store=plan_store, llm_client=requesty)

    return PlanningAgent(
        context_manager=context_manager,
        plan_generator=plan_generator,
        conversation_store=conversation_store,
        llm_client=requesty,
    )


@router.post("/chat", response_model=ChatMessageResponse)
async def planning_chat(
    payload: ChatMessageRequest,
    session: AsyncSession = Depends(get_session),
):
    store = ConversationStore(session)

    conversation = None
    if payload.session_id:
        conversation = await store.get_session(payload.session_id)
    if conversation is None:
        conversation = await store.create_session(project_id=payload.project_id)

    await store.add_message(
        conversation.id,
        role="user",
        content=payload.message,
        modality=payload.modality,
    )

    # Reload conversation with messages so the agent sees latest state
    conversation = await store.get_session(conversation.id, include_messages=True)

    agent = _build_agent(session)
    result = await agent.handle_message(
        message=payload.message,
        session_id=conversation.id,
        project_id=payload.project_id,
    )

    assistant_reply = result.reply
    plan = result.plan

    await store.add_message(
        conversation.id,
        role="assistant",
        content=assistant_reply,
        modality="text",
    )

    generated_plan_id = None
    if plan:
        generated_plan_id = plan.id
        if plan.id not in conversation.generated_plans:
            conversation.generated_plans.append(plan.id)
        await session.flush()

    return ChatMessageResponse(
        session_id=conversation.id,
        response=assistant_reply,
        generated_plan_id=generated_plan_id,
    )


@router.get("/sessions", response_model=List[ConversationSummary])
async def list_sessions(session: AsyncSession = Depends(get_session)):
    store = ConversationStore(session)
    sessions = await store.list_sessions()
    return [ConversationSummary.from_orm(item) for item in sessions]


@router.get("/sessions/{session_id}", response_model=ConversationDetail)
async def get_session_detail(session_id: str, session: AsyncSession = Depends(get_session)):
    store = ConversationStore(session)
    conversation = await store.get_session(session_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    messages = [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "modality": message.modality,
            "timestamp": message.timestamp,
        }
        for message in conversation.messages
    ]
    summary = ConversationSummary.from_orm(conversation)
    return ConversationDetail(
        **summary.dict(),
        messages=messages,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, session: AsyncSession = Depends(get_session)):
    store = ConversationStore(session)
    await store.delete_session(session_id)
    return None


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_plan_from_session(
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_session),
):
    _ = request  # Placeholder usage for Phase 1
    return {
        "status": "pending",
        "message": "Planning agent generation will be available in Phase 2.",
    }

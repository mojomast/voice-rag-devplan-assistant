import json
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.context_manager import PlanningContextManager  # type: ignore  # noqa: E402
from backend.planning_agent import PlanningAgent  # type: ignore  # noqa: E402
from backend.plan_generator import DevPlanGenerator  # type: ignore  # noqa: E402
from backend.storage.conversation_store import ConversationStore  # type: ignore  # noqa: E402
from backend.storage.plan_store import DevPlanStore  # type: ignore  # noqa: E402
from backend.storage.project_store import ProjectStore  # type: ignore  # noqa: E402
from backend.database import Base  # type: ignore  # noqa: E402


class StubLLM:
    """Stub client that returns predefined responses for async chat calls."""

    def __init__(self, replies):
        self._replies = list(replies)

    async def achat_completion(self, *args, **kwargs):
        if not self._replies:
            raise RuntimeError("No more stub replies")
        return self._replies.pop(0)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as db_session:
        yield db_session

    await engine.dispose()


@pytest.mark.asyncio
async def test_planning_agent_generates_plan(session):
    project_store = ProjectStore(session)
    plan_store = DevPlanStore(session)
    conversation_store = ConversationStore(session)

    project = await project_store.create_project(name="AI Planner")
    conversation = await conversation_store.create_session(project_id=project.id)
    await conversation_store.add_message(conversation.id, role="user", content="We need a roadmap")

    stub_llm = StubLLM([
        json.dumps(
            {
                "assistant_reply": "I'll draft a plan now.",
                "actions": {"create_plan": True, "plan_brief": "Create AI roadmap"},
            }
        ),
        json.dumps(
            {
                "plan_title": "AI Roadmap",
                "plan_summary": "Summary of actions",
                "plan_markdown": "# Overview\n- Item",
            }
        ),
    ])

    context_manager = PlanningContextManager(
        project_store=project_store,
        plan_store=plan_store,
        conversation_store=conversation_store,
        rag_handler=None,
    )

    plan_generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    agent = PlanningAgent(
        context_manager=context_manager,
        plan_generator=plan_generator,
        conversation_store=conversation_store,
        llm_client=stub_llm,
    )

    result = await agent.handle_message(
        message="Please prepare the plan",
        session_id=conversation.id,
        project_id=project.id,
    )

    assert result.actions["create_plan"] is True
    assert result.plan is not None
    assert result.plan.title == "AI Roadmap"
    assert "draft a plan" in result.reply.lower()


@pytest.mark.asyncio
async def test_planning_agent_handles_non_json_response(session):
    project_store = ProjectStore(session)
    plan_store = DevPlanStore(session)
    conversation_store = ConversationStore(session)

    project = await project_store.create_project(name="Doc Update")
    conversation = await conversation_store.create_session(project_id=project.id)
    await conversation_store.add_message(conversation.id, role="user", content="Help refine plan")

    stub_llm = StubLLM([
        "Here's some thoughts without JSON",  # Agent response
    ])

    context_manager = PlanningContextManager(
        project_store=project_store,
        plan_store=plan_store,
        conversation_store=conversation_store,
        rag_handler=None,
    )

    plan_generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    agent = PlanningAgent(
        context_manager=context_manager,
        plan_generator=plan_generator,
        conversation_store=conversation_store,
        llm_client=stub_llm,
    )

    result = await agent.handle_message(
        message="Outline next steps",
        session_id=conversation.id,
        project_id=project.id,
    )

    assert result.plan is None
    assert result.actions["create_plan"] is False
    assert "thoughts" in result.reply.lower()

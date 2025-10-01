"""Comprehensive unit tests for DevPlanGenerator.

Tests cover:
- Plan generation with structured JSON responses
- Markdown content parsing and extraction
- Fallback handling for non-JSON responses
- Title inference from markdown headers
- Metadata extraction and defaults
- Error handling and edge cases
"""

import json
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.context_manager import PlanningContext  # type: ignore  # noqa: E402
from backend.plan_generator import DevPlanGenerator  # type: ignore  # noqa: E402
from backend.storage.plan_store import DevPlanStore  # type: ignore  # noqa: E402
from backend.storage.project_store import ProjectStore  # type: ignore  # noqa: E402
from backend.database import Base  # type: ignore  # noqa: E402


class StubLLM:
    """Stub client for testing plan generation."""

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
async def test_plan_generator_with_valid_json(session):
    """Test plan generation with valid JSON response."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Test Project")

    stub_llm = StubLLM([
        json.dumps({
            "plan_title": "API Development Plan",
            "plan_summary": "Comprehensive plan for building REST API",
            "plan_markdown": "# API Development Plan\n\n## Overview\nBuild a scalable REST API",
            "metadata": {"estimated_hours": 40, "priority": "high"}
        })
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "REST API project"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Create API plan",
    )

    assert plan is not None
    assert plan.title == "API Development Plan"
    assert plan.project_id == project.id
    # Check the latest version for content
    versions = await plan_store.get_versions(plan.id)
    assert len(versions) > 0
    assert "API Development Plan" in versions[0].content
    assert plan.metadata_dict.get("estimated_hours") == 40
    assert plan.metadata_dict.get("priority") == "high"


@pytest.mark.asyncio
async def test_plan_generator_with_non_json_response(session):
    """Test fallback when LLM returns plain markdown without JSON."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Markdown Project")

    stub_llm = StubLLM([
        "# Database Migration Plan\n\n## Phase 1\nSetup migrations\n\n## Phase 2\nRun migrations"
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Database project"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Migration plan",
    )

    assert plan is not None
    assert plan.title == "Database Migration Plan"  # Inferred from header
    # Check the latest version for content
    versions = await plan_store.get_versions(plan.id)
    assert len(versions) > 0
    assert "Phase 1" in versions[0].content
    assert "Phase 2" in versions[0].content


@pytest.mark.asyncio
async def test_plan_generator_title_inference(session):
    """Test title inference from markdown content."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Title Test")

    # No JSON, but markdown with header
    stub_llm = StubLLM([
        "# Feature Implementation\n\nDetailed implementation steps."
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Feature project"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Feature plan",
    )

    assert plan.title == "Feature Implementation"


@pytest.mark.asyncio
async def test_plan_generator_fallback_title_from_brief(session):
    """Test title fallback to plan_brief when no header found."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="No Header Project")

    stub_llm = StubLLM([
        "This is plan content without any markdown headers."
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Test project"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Custom Plan Brief",
    )

    assert plan.title == "Custom Plan Brief"


@pytest.mark.asyncio
async def test_plan_generator_default_title(session):
    """Test default title when no header or brief available."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Default Title Project")

    stub_llm = StubLLM([
        "Content without headers or title information."
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Test"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief=None,  # No brief provided
    )

    assert plan.title == "Development Plan"  # Default fallback


@pytest.mark.asyncio
async def test_plan_generator_with_empty_markdown(session):
    """Test handling of JSON response with empty markdown field."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Empty Content")

    stub_llm = StubLLM([
        json.dumps({
            "plan_title": "Empty Plan",
            "plan_summary": "This plan has no content",
            "plan_markdown": "",  # Empty content
            "metadata": {}
        })
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Test"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Test",
    )

    assert plan.title == "Empty Plan"
    # Should fallback to summary when markdown is empty
    versions = await plan_store.get_versions(plan.id)
    assert len(versions) > 0
    assert "This plan has no content" in versions[0].content


@pytest.mark.asyncio
async def test_plan_generator_with_alternate_content_key(session):
    """Test handling when JSON uses 'content' instead of 'plan_markdown'."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Alternate Key")

    stub_llm = StubLLM([
        json.dumps({
            "plan_title": "Alternate Format Plan",
            "plan_summary": "Using alternate key",
            "content": "# Plan Content\n\nUsing 'content' key instead",
            "metadata": {"source": "alternate"}
        })
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Test"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Test",
    )

    assert plan.title == "Alternate Format Plan"
    versions = await plan_store.get_versions(plan.id)
    assert len(versions) > 0
    assert "content' key instead" in versions[0].content
    assert plan.metadata_dict.get("source") == "alternate"


@pytest.mark.asyncio
async def test_plan_generator_with_conversation_id(session):
    """Test that conversation_id is properly attached to plan."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Conversation Link")

    stub_llm = StubLLM([
        json.dumps({
            "plan_title": "Linked Plan",
            "plan_summary": "Plan with conversation link",
            "plan_markdown": "# Linked Plan\n\nContent",
            "metadata": {}
        })
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Test"},
        recent_plans=[],
        recent_messages=[{"role": "user", "content": "Discussion context"}],
    )

    conversation_id = "test-conversation-123"

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=conversation_id,
        context=context,
        plan_brief="Test",
    )

    assert plan.conversation_id == conversation_id


@pytest.mark.asyncio
async def test_plan_generator_metadata_defaults(session):
    """Test that missing metadata defaults to empty dict."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Metadata Test")

    stub_llm = StubLLM([
        json.dumps({
            "plan_title": "No Metadata Plan",
            "plan_summary": "Plan without metadata field",
            "plan_markdown": "# Content\n\nSome content",
            # metadata field missing
        })
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Test"},
        recent_plans=[],
        recent_messages=[],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Test",
    )

    assert plan.metadata_dict == {}


@pytest.mark.asyncio
async def test_plan_generator_complex_markdown(session):
    """Test generation with complex markdown structure."""
    plan_store = DevPlanStore(session)
    project_store = ProjectStore(session)

    project = await project_store.create_project(name="Complex Markdown")

    complex_markdown = """# Comprehensive Development Plan

## Overview & Goals
- Goal 1
- Goal 2

## Implementation Phases

### Phase 1: Foundation
- Task 1
- Task 2

### Phase 2: Features
- Feature A
- Feature B

## Testing Strategy
Unit and integration tests.

## Deployment Plan
Deploy to production.
"""

    stub_llm = StubLLM([
        json.dumps({
            "plan_title": "Comprehensive Development Plan",
            "plan_summary": "Multi-phase development plan",
            "plan_markdown": complex_markdown,
            "metadata": {"phases": 2, "tasks": 4}
        })
    ])

    generator = DevPlanGenerator(plan_store=plan_store, llm_client=stub_llm)

    context = PlanningContext(
        project={"name": "Complex project"},
        recent_plans=[],
        recent_messages=[{"role": "user", "content": "Detailed discussion"}],
    )

    plan = await generator.generate_plan(
        project_id=project.id,
        conversation_id=None,
        context=context,
        plan_brief="Comprehensive plan",
    )

    assert plan.title == "Comprehensive Development Plan"
    versions = await plan_store.get_versions(plan.id)
    assert len(versions) > 0
    assert "Phase 1: Foundation" in versions[0].content
    assert "Phase 2: Features" in versions[0].content
    assert "Testing Strategy" in versions[0].content
    assert plan.metadata_dict.get("phases") == 2
    assert plan.metadata_dict.get("tasks") == 4

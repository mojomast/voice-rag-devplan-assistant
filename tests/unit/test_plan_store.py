import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.database import Base
from backend.models import PlanStatus, Project
from backend.storage.plan_store import DevPlanStore
from backend.storage.project_store import ProjectStore


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
async def test_create_plan_with_version(session):
    project_store = ProjectStore(session)
    project = await project_store.create_project(name="Project A")

    plan_store = DevPlanStore(session)
    plan = await plan_store.create_plan(
        project_id=project.id,
        title="Initial Plan",
        content="# Plan",
        status=PlanStatus.DRAFT,
    )

    assert plan.current_version == 1
    versions = await plan_store.get_versions(plan.id)
    assert len(versions) == 1
    assert versions[0].content == "# Plan"


@pytest.mark.asyncio
async def test_create_plan_version(session):
    project_store = ProjectStore(session)
    project = await project_store.create_project(name="Project B")

    plan_store = DevPlanStore(session)
    plan = await plan_store.create_plan(
        project_id=project.id,
        title="Plan",
        content="# v1",
    )

    await plan_store.create_version(plan.id, content="# v2", change_summary="Update")

    versions = await plan_store.get_versions(plan.id)
    assert len(versions) == 2
    assert versions[0].version_number == 2
    assert versions[0].change_summary == "Update"

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.database import Base
from backend.models import ProjectStatus
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
async def test_create_and_retrieve_project(session):
    store = ProjectStore(session)
    project = await store.create_project(name="Test Project", description="Testing")

    assert project.id is not None

    fetched = await store.get_project(project.id)
    assert fetched is not None
    assert fetched.name == "Test Project"


@pytest.mark.asyncio
async def test_list_projects_with_filter(session):
    store = ProjectStore(session)
    await store.create_project(name="Active Project", status=ProjectStatus.ACTIVE)
    await store.create_project(name="Paused Project", status=ProjectStatus.PAUSED)

    active = await store.list_projects(status=ProjectStatus.ACTIVE)
    assert len(active) == 1
    assert active[0].name == "Active Project"

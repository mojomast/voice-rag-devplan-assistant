import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.database import Base
from backend.storage.conversation_store import ConversationStore


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
async def test_conversation_lifecycle(session):
    store = ConversationStore(session)
    conversation = await store.create_session()
    await store.add_message(conversation.id, role="user", content="Hello")
    await store.add_message(conversation.id, role="assistant", content="Hi there")

    fetched = await store.get_session(conversation.id)
    assert fetched is not None
    assert len(fetched.messages) == 2

    await store.end_session(conversation.id, summary="Test")
    ended = await store.get_session(conversation.id, include_messages=False)
    assert ended.summary == "Test"
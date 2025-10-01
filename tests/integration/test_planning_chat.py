"""Integration tests for /planning/chat endpoint.

Tests cover:
- End-to-end conversation flows
- Plan generation through the API
- Session management
- Requesty integration and fallback behavior
- Error handling and edge cases
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database import Base, get_session  # type: ignore  # noqa: E402
from backend.main import app  # type: ignore  # noqa: E402
from backend.storage.project_store import ProjectStore  # type: ignore  # noqa: E402


@pytest_asyncio.fixture
async def test_db():
    """Create a test database and session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async def get_test_session():
        async with SessionLocal() as session:
            yield session

    # Override the dependency
    app.dependency_overrides[get_session] = get_test_session
    
    yield SessionLocal
    
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_project(test_db):
    """Create a test project."""
    async with test_db() as session:
        project_store = ProjectStore(session)
        project = await project_store.create_project(
            name="Test Project",
            description="Integration test project"
        )
        await session.commit()
        return project.id


@pytest.mark.asyncio
async def test_planning_chat_creates_new_session(client, test_project):
    """Test creating new conversation session via chat."""
    # Set TEST_MODE to use deterministic responses
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        response = await client.post(
            "/planning/chat",
            json={
                "message": "I need help planning a feature",
                "project_id": test_project,
                "modality": "text"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert "response" in data
    assert data["response"] is not None
    assert len(data["session_id"]) > 0


@pytest.mark.asyncio
async def test_planning_chat_continues_existing_session(client, test_project):
    """Test continuing an existing conversation session."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        # First message
        response1 = await client.post(
            "/planning/chat",
            json={
                "message": "I need a REST API",
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # Second message in same session
        response2 = await client.post(
            "/planning/chat",
            json={
                "message": "Using Python FastAPI",
                "session_id": session_id,
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should return same session_id
        assert data2["session_id"] == session_id
        assert data2["response"] is not None


@pytest.mark.asyncio
async def test_planning_chat_generates_plan(client, test_project):
    """Test plan generation through chat endpoint."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        # Mock Requesty to return plan creation intent
        mock_response = json.dumps({
            "assistant_reply": "I'll create a plan for you.",
            "actions": {
                "create_plan": True,
                "plan_brief": "REST API development plan"
            }
        })
        
        with patch("backend.requesty_client.RequestyClient.achat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = [
                mock_response,  # Agent decides to create plan
                json.dumps({  # Plan generator creates plan
                    "plan_title": "REST API Plan",
                    "plan_summary": "Build REST API",
                    "plan_markdown": "# REST API Plan\n\n## Overview\nBuild API",
                    "metadata": {}
                })
            ]
            
            response = await client.post(
                "/planning/chat",
                json={
                    "message": "Create a development plan for REST API",
                    "project_id": test_project,
                    "modality": "text"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_plan_id" in data
        assert data["generated_plan_id"] is not None
        assert "session_id" in data


@pytest.mark.asyncio
async def test_planning_chat_without_project_id(client):
    """Test chat without project_id (should still work)."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        response = await client.post(
            "/planning/chat",
            json={
                "message": "General planning question",
                "modality": "text"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert "response" in data
    # No plan should be generated without project_id
    assert data.get("generated_plan_id") is None


@pytest.mark.asyncio
async def test_planning_chat_with_voice_modality(client, test_project):
    """Test chat with voice modality."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        response = await client.post(
            "/planning/chat",
            json={
                "message": "Voice transcribed message",
                "project_id": test_project,
                "modality": "voice"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] is not None


@pytest.mark.asyncio
async def test_list_planning_sessions(client, test_project):
    """Test listing conversation sessions."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        # Create a few sessions
        await client.post(
            "/planning/chat",
            json={
                "message": "First session",
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        await client.post(
            "/planning/chat",
            json={
                "message": "Second session",
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        # List sessions
        response = await client.get("/planning/sessions")
        
        assert response.status_code == 200
        sessions = response.json()
        
        assert isinstance(sessions, list)
        assert len(sessions) >= 2


@pytest.mark.asyncio
async def test_get_session_detail(client, test_project):
    """Test getting session details with messages."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        # Create session with messages
        chat_response = await client.post(
            "/planning/chat",
            json={
                "message": "Test message",
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        session_id = chat_response.json()["session_id"]
        
        # Get session detail
        response = await client.get(f"/planning/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert "messages" in data
        assert len(data["messages"]) >= 2  # User message + assistant response


@pytest.mark.asyncio
async def test_get_nonexistent_session(client):
    """Test getting details of non-existent session."""
    response = await client.get("/planning/sessions/nonexistent-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_session(client, test_project):
    """Test deleting a conversation session."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        # Create session
        chat_response = await client.post(
            "/planning/chat",
            json={
                "message": "Test message",
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        session_id = chat_response.json()["session_id"]
        
        # Delete session
        delete_response = await client.delete(f"/planning/sessions/{session_id}")
        
        assert delete_response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(f"/planning/sessions/{session_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_planning_chat_handles_requesty_fallback(client, test_project):
    """Test that chat handles Requesty fallback gracefully."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        # Mock Requesty to return non-JSON (fallback mode)
        with patch("backend.requesty_client.RequestyClient.achat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "Plain text response without JSON structure"
            
            response = await client.post(
                "/planning/chat",
                json={
                    "message": "Help me plan",
                    "project_id": test_project,
                    "modality": "text"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["response"] == "Plain text response without JSON structure"
        assert data.get("generated_plan_id") is None  # No plan generated in fallback


@pytest.mark.asyncio
async def test_planning_chat_multiple_messages_in_conversation(client, test_project):
    """Test multi-turn conversation flow."""
    with patch.dict(os.environ, {"TEST_MODE": "1"}):
        # First turn
        response1 = await client.post(
            "/planning/chat",
            json={
                "message": "I want to build a REST API",
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        session_id = response1.json()["session_id"]
        
        # Second turn
        response2 = await client.post(
            "/planning/chat",
            json={
                "message": "It should use Python FastAPI",
                "session_id": session_id,
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        # Third turn
        response3 = await client.post(
            "/planning/chat",
            json={
                "message": "With PostgreSQL database",
                "session_id": session_id,
                "project_id": test_project,
                "modality": "text"
            }
        )
        
        # All should succeed with same session
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert response2.json()["session_id"] == session_id
        assert response3.json()["session_id"] == session_id
        
        # Get session detail to verify all messages
        detail_response = await client.get(f"/planning/sessions/{session_id}")
        messages = detail_response.json()["messages"]
        
        # Should have 6 messages: 3 user + 3 assistant
        assert len(messages) == 6


@pytest.mark.asyncio
async def test_planning_chat_invalid_payload(client):
    """Test chat with invalid payload."""
    response = await client.post(
        "/planning/chat",
        json={
            # Missing required 'message' field
            "project_id": "some-id",
            "modality": "text"
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_generate_plan_endpoint_placeholder(client, test_project):
    """Test the /planning/generate endpoint (Phase 2 placeholder)."""
    response = await client.post(
        "/planning/generate",
        json={
            "message": "Generate plan",
            "project_id": test_project,
            "modality": "text"
        }
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "status" in data
    assert data["status"] == "pending"

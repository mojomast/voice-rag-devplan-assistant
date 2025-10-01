import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend import requesty_client  # type: ignore  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture(autouse=True)
def restore_requesty_settings():
    original_router_key = requesty_client.settings.ROUTER_API_KEY
    original_requesty_key = requesty_client.settings.REQUESTY_API_KEY
    original_openai_key = requesty_client.settings.OPENAI_API_KEY
    original_test_mode = requesty_client.settings.TEST_MODE
    yield
    requesty_client.settings.ROUTER_API_KEY = original_router_key
    requesty_client.settings.REQUESTY_API_KEY = original_requesty_key
    requesty_client.settings.OPENAI_API_KEY = original_openai_key
    requesty_client.settings.TEST_MODE = original_test_mode


def test_router_chat_completion_uses_qualified_model(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "router-key", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", False, raising=False)

    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Router reply"))]
    fake_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20)

    fake_router_client = MagicMock()
    fake_router_client.chat.completions.create.return_value = fake_response

    with patch("backend.requesty_client.OpenAI", return_value=fake_router_client):
        client = requesty_client.RequestyClient()
        reply = client.chat_completion([{"role": "user", "content": "Hello"}], model="glm-4.5")

    fake_router_client.chat.completions.create.assert_called_once()
    kwargs = fake_router_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "requesty/glm-4.5"
    assert reply == "Router reply"


def test_requesty_api_key_aliases_router_usage(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "REQUESTY_API_KEY", "legacy-requesty", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", False, raising=False)

    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Legacy router reply"))]
    fake_response.usage = MagicMock(prompt_tokens=5, completion_tokens=15)

    fake_router_client = MagicMock()
    fake_router_client.chat.completions.create.return_value = fake_response

    with patch("backend.requesty_client.OpenAI", return_value=fake_router_client) as mock_openai:
        client = requesty_client.RequestyClient()
        reply = client.chat_completion([{"role": "user", "content": "Hello"}])

    mock_openai.assert_called_once()
    kwargs = mock_openai.call_args.kwargs
    assert kwargs["api_key"] == "legacy-requesty"
    assert "router.requesty.ai" in kwargs.get("base_url", "")
    fake_router_client.chat.completions.create.assert_called_once()
    assert client.use_router is True
    assert reply == "Legacy router reply"


def test_chat_completion_returns_deterministic_payload_in_test_mode(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", True, raising=False)

    client = requesty_client.RequestyClient()
    payload = client.chat_completion([{"role": "user", "content": "Outline the plan"}])
    parsed = json.loads(payload)

    assert "assistant_reply" in parsed
    assert parsed["actions"]["create_plan"] is False


def test_openai_placeholder_key_disabled(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "your_openai_api_key_here", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", False, raising=False)

    client = requesty_client.RequestyClient()

    assert client.openai_client is None
    reply = client.chat_completion([{"role": "user", "content": "Hello"}])
    assert "[Fallback response]" in reply


def test_openai_failure_downgrades_to_fallback(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "sk-invalid-key", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", False, raising=False)

    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.side_effect = RuntimeError("401 Invalid auth")

    with patch("backend.requesty_client.OpenAI", return_value=mock_openai_client):
        client = requesty_client.RequestyClient()
        reply = client.chat_completion([{"role": "user", "content": "Plan"}])

    assert "[Fallback response]" in reply
    assert client.openai_client is None


def test_chat_completion_falls_back_to_openai_model(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "sk-live-openai-key", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", False, raising=False)
    monkeypatch.setattr(requesty_client.settings, "LLM_MODEL", "gpt-4o-mini", raising=False)
    monkeypatch.setattr(requesty_client.settings, "REQUESTY_PLANNING_MODEL", "requesty/glm-4.5", raising=False)

    mock_openai = MagicMock()
    fake_response = MagicMock()
    fake_choice = MagicMock()
    fake_choice.message.content = "OpenAI reply"
    fake_response.choices = [fake_choice]
    fake_response.usage = MagicMock(total_tokens=100)
    mock_openai.chat.completions.create.return_value = fake_response

    with patch("backend.requesty_client.OpenAI", return_value=mock_openai):
        client = requesty_client.RequestyClient()
        reply = client.chat_completion([{"role": "user", "content": "Hello"}])

    mock_openai.chat.completions.create.assert_called_once()
    kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert reply == "OpenAI reply"


def test_embed_texts_fallback(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", True, raising=False)

    client = requesty_client.RequestyClient()
    vectors = client.embed_texts(["alpha", "beta"])

    assert len(vectors) == 2
    assert all(len(vec) == 32 for vec in vectors)

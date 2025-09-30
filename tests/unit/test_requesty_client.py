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
    original_openai_key = requesty_client.settings.OPENAI_API_KEY
    original_test_mode = requesty_client.settings.TEST_MODE
    yield
    requesty_client.settings.ROUTER_API_KEY = original_router_key
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


def test_chat_completion_returns_deterministic_payload_in_test_mode(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", True, raising=False)

    client = requesty_client.RequestyClient()
    payload = client.chat_completion([{"role": "user", "content": "Outline the plan"}])
    parsed = json.loads(payload)

    assert "assistant_reply" in parsed
    assert parsed["actions"]["create_plan"] is False


def test_embed_texts_fallback(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "ROUTER_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "TEST_MODE", True, raising=False)

    client = requesty_client.RequestyClient()
    vectors = client.embed_texts(["alpha", "beta"])

    assert len(vectors) == 2
    assert all(len(vec) == 32 for vec in vectors)

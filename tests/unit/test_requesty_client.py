import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

import requesty_client  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture(autouse=True)
def restore_requesty_settings():
    original_requesty_key = requesty_client.settings.REQUESTY_API_KEY
    original_openai_key = requesty_client.settings.OPENAI_API_KEY
    yield
    requesty_client.settings.REQUESTY_API_KEY = original_requesty_key
    requesty_client.settings.OPENAI_API_KEY = original_openai_key


def test_requesty_routes_when_api_key_available(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "REQUESTY_API_KEY", "req-test-key", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Requesty response"}}]
    }

    with patch("requesty_client.requests.post", return_value=mock_response) as mock_post:
        client = requesty_client.RequestyClient()
        result = client.chat_completion([{"role": "user", "content": "Hello"}])

    assert result == "Requesty response"
    mock_post.assert_called_once()
    assert client.use_requesty is True


def test_requesty_fallbacks_without_api_key(monkeypatch):
    monkeypatch.setattr(requesty_client.settings, "REQUESTY_API_KEY", "", raising=False)
    monkeypatch.setattr(requesty_client.settings, "OPENAI_API_KEY", "", raising=False)

    client = requesty_client.RequestyClient()
    assert client.use_requesty is False

    with patch.object(client, "_openai_chat_completion", return_value="Fallback reply") as mock_fallback:
        result = client.chat_completion([{"role": "user", "content": "Hello"}])

    assert result == "Fallback reply"
    mock_fallback.assert_called_once()

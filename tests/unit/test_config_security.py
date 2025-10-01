import sys
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure backend package is importable as a package
sys.path.append(str(Path(__file__).parent.parent.parent))

config_module = import_module("backend.config")
Settings = config_module.Settings
main = import_module("backend.main")


@pytest.fixture(autouse=True)
def restore_admin_token():
    """Ensure global settings token is restored after each test."""
    original_token = main.settings.RUNTIME_ADMIN_TOKEN
    original_test_mode = main.settings.TEST_MODE
    yield
    main.settings.RUNTIME_ADMIN_TOKEN = original_token
    main.settings.TEST_MODE = original_test_mode


def test_settings_default_admin_token_test_mode(monkeypatch):
    """Test that settings generate a default admin token in test mode when none is provided."""
    for env_key in [
        "RUNTIME_ADMIN_TOKEN",
        "ADMIN_API_TOKEN",
        "TEST_ADMIN_TOKEN",
        "TEST_MODE",
        "OPENAI_API_KEY",
        "REQUESTY_API_KEY",
    ]:
        monkeypatch.delenv(env_key, raising=False)

    monkeypatch.setattr(Settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(Settings, "REQUESTY_API_KEY", "", raising=False)
    monkeypatch.setattr(Settings, "TEST_MODE", False, raising=False)

    temp_settings = Settings()

    assert temp_settings.TEST_MODE is True
    assert temp_settings.RUNTIME_ADMIN_TOKEN == "test-admin-token"
    assert temp_settings.validate_admin_token("test-admin-token")


def test_settings_ignores_placeholder_admin_token(monkeypatch):
    """Ensure placeholder admin tokens fall back to the test token in test mode."""
    for env_key in [
        "ADMIN_API_TOKEN",
        "TEST_ADMIN_TOKEN",
        "TEST_MODE",
        "OPENAI_API_KEY",
        "REQUESTY_API_KEY",
    ]:
        monkeypatch.delenv(env_key, raising=False)

    monkeypatch.setenv("RUNTIME_ADMIN_TOKEN", "your-secure-token-here-change-this")
    monkeypatch.setenv("TEST_MODE", "true")

    monkeypatch.setattr(Settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(Settings, "REQUESTY_API_KEY", "", raising=False)

    temp_settings = Settings()

    assert temp_settings.RUNTIME_ADMIN_TOKEN == "test-admin-token"
    assert temp_settings.validate_admin_token("test-admin-token")


def test_update_configuration_requires_admin_token(monkeypatch):
    """Ensure /config/update rejects unauthorized requests and accepts a valid token."""
    monkeypatch.setattr(main.settings, "RUNTIME_ADMIN_TOKEN", "unit-test-token", raising=False)
    monkeypatch.setattr(main.settings, "TEST_MODE", False, raising=False)

    with patch("backend.main.initialize_performance_optimizations", return_value=None), \
        patch("backend.main.initialize_security_system", return_value=None), \
        patch("backend.main.initialize_monitoring_system", return_value=None), \
        patch("backend.main.shutdown_monitoring_system", return_value=None), \
        patch("backend.main.DocumentProcessor") as mock_doc_processor, \
        patch("backend.main.VoiceService") as mock_voice_service, \
        patch("backend.main.reset_rag_handler", return_value=None):

        mock_doc_processor.return_value = MagicMock()
        mock_voice_service.return_value = MagicMock()

        with TestClient(main.app) as client:
            unauth_response = client.post("/config/update", json={"test_mode": True})
            assert unauth_response.status_code == 401
            assert unauth_response.json()["detail"] == "Invalid or missing admin token"

            auth_response = client.post(
                "/config/update",
                json={"test_mode": True},
                headers={"Authorization": "Bearer unit-test-token"},
            )
            assert auth_response.status_code == 200
            assert auth_response.json()["status"] == "success"

            assert main.settings.TEST_MODE is True

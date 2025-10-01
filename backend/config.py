import os
import secrets
from typing import Optional, Set
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from a .env file
load_dotenv()

class Settings:
    """Centralized configuration for the application."""

    SENTINEL_OPENAI_KEYS: Set[str] = {
        "",
        "none",
        "null",
        "placeholder",
        "your_openai_api_key_here",
        "sk-your-actual-openai-key-here",
        "sk-your-actual-openai-key",
        "test-key"
    }

    SENTINEL_REQUESTY_KEYS: Set[str] = {"", "none", "null", "placeholder"}

    SENTINEL_OPENAI_KEYS_LOWER: Set[str] = {value.lower() for value in SENTINEL_OPENAI_KEYS}
    SENTINEL_REQUESTY_KEYS_LOWER: Set[str] = {value.lower() for value in SENTINEL_REQUESTY_KEYS}

    # API Keys (initial raw values; normalized in __init__)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    REQUESTY_API_KEY: str = os.getenv("REQUESTY_API_KEY", "")  # Legacy
    ROUTER_API_KEY: str = os.getenv("ROUTER_API_KEY", "")  # Requesty router

    # Test Mode (will be recalculated in __init__)
    TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"

    # File Paths
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./vector_store")
    DEVPLAN_VECTOR_STORE_PATH: str = os.getenv(
        "DEVPLAN_VECTOR_STORE_PATH",
        os.path.join(VECTOR_STORE_PATH, "devplans"),
    )
    PROJECT_VECTOR_STORE_PATH: str = os.getenv(
        "PROJECT_VECTOR_STORE_PATH",
        os.path.join(VECTOR_STORE_PATH, "projects"),
    )
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH", "./uploads")

    # RAG Settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # LLM Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", 0.7))
    REQUESTY_PLANNING_MODEL: str = os.getenv("REQUESTY_PLANNING_MODEL", "requesty/glm-4.5")
    REQUESTY_EMBEDDING_MODEL: str = os.getenv("REQUESTY_EMBEDDING_MODEL", "requesty/embedding-001")
    PLANNING_MAX_TOKENS: int = int(os.getenv("PLANNING_MAX_TOKENS", 2200))
    PLANNING_TEMPERATURE: float = float(os.getenv("PLANNING_TEMPERATURE", 0.4))

    # Voice Settings
    TTS_MODEL: str = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "alloy")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")
    ENABLE_WAKE_WORD: bool = os.getenv("ENABLE_WAKE_WORD", "False").lower() == "true"
    WAKE_WORD: str = os.getenv("WAKE_WORD", "hey assistant")

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/devplanning.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", 5))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", 10))

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    ADMIN_API_TOKEN_ENV_KEYS: Set[str] = {"RUNTIME_ADMIN_TOKEN", "ADMIN_API_TOKEN"}

    def __init__(self):
        self.OPENAI_API_KEY = self._normalize_key(self.OPENAI_API_KEY, self.SENTINEL_OPENAI_KEYS_LOWER)
        self.REQUESTY_API_KEY = self._normalize_key(self.REQUESTY_API_KEY, self.SENTINEL_REQUESTY_KEYS_LOWER)
        self.ROUTER_API_KEY = self._normalize_key(self.ROUTER_API_KEY, self.SENTINEL_REQUESTY_KEYS_LOWER)

        explicit_test_mode = os.getenv("TEST_MODE")
        if explicit_test_mode is None:
            self.TEST_MODE = not bool(self.OPENAI_API_KEY or self.REQUESTY_API_KEY or self.ROUTER_API_KEY)
        else:
            self.TEST_MODE = explicit_test_mode.lower() == "true"

        self.RUNTIME_ADMIN_TOKEN = self._load_admin_token()

        # Normalize database path if using default SQLite location
        if self.DATABASE_URL.startswith("sqlite"):
            db_path = self.DATABASE_URL.split("///")[-1]
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

        for path in (
            self.VECTOR_STORE_PATH,
            self.DEVPLAN_VECTOR_STORE_PATH,
            self.PROJECT_VECTOR_STORE_PATH,
            self.UPLOAD_PATH,
        ):
            try:
                if path:
                    os.makedirs(path, exist_ok=True)
            except OSError as exc:  # pragma: no cover - best-effort directory creation
                logger.warning("Failed to ensure directory %s: %s", path, exc)

    def _load_admin_token(self) -> str:
        """Load and normalize the runtime admin token."""
        for env_key in self.ADMIN_API_TOKEN_ENV_KEYS:
            value = os.getenv(env_key)
            if value:
                token = value.strip()
                if token:
                    return token

        if self.TEST_MODE:
            test_token = os.getenv("TEST_ADMIN_TOKEN", "test-admin-token").strip()
            logger.warning(
                "RUNTIME_ADMIN_TOKEN not set. Using default test admin token '%s' for local development.",
                test_token
            )
            return test_token

        logger.error(
            "RUNTIME_ADMIN_TOKEN is not configured. Runtime configuration updates will be rejected until it is set."
        )
        return ""

    @staticmethod
    def _normalize_key(value: Optional[str], sentinel_values: Set[str]) -> str:
        if value is None:
            return ""

        normalized = value.strip()
        if normalized.lower() in sentinel_values:
            return ""
        return normalized

    def requires_admin_token(self) -> bool:
        """Determine if admin token validation is required for runtime updates."""
        return bool(self.RUNTIME_ADMIN_TOKEN)

    def validate_admin_token(self, token: Optional[str]) -> bool:
        """Validate the provided admin token against configuration."""
        if not self.requires_admin_token():
            return self.TEST_MODE

        if not token:
            return False

        try:
            return secrets.compare_digest(self.RUNTIME_ADMIN_TOKEN, token.strip())
        except Exception:
            return False

    def update_credentials(
        self,
        openai_api_key: Optional[str] = None,
        requesty_api_key: Optional[str] = None,
        router_api_key: Optional[str] = None,
        test_mode: Optional[bool] = None
    ) -> dict:
        if openai_api_key is not None:
            self.OPENAI_API_KEY = self._normalize_key(openai_api_key, self.SENTINEL_OPENAI_KEYS_LOWER)

        if requesty_api_key is not None:
            self.REQUESTY_API_KEY = self._normalize_key(requesty_api_key, self.SENTINEL_REQUESTY_KEYS_LOWER)

        if router_api_key is not None:
            self.ROUTER_API_KEY = self._normalize_key(router_api_key, self.SENTINEL_REQUESTY_KEYS_LOWER)

        if test_mode is not None:
            self.TEST_MODE = bool(test_mode)
        else:
            if not (self.OPENAI_API_KEY or self.REQUESTY_API_KEY or self.ROUTER_API_KEY):
                self.TEST_MODE = True

        self.validate_settings()

        return {
            "test_mode": self.TEST_MODE,
            "requesty_enabled": bool(self.REQUESTY_API_KEY),
            "router_enabled": bool(self.ROUTER_API_KEY),
            "openai_configured": bool(self.OPENAI_API_KEY)
        }

    def validate_settings(self):
        """Validate that required settings are present"""
        if self.TEST_MODE:
            logger.info("Configuration loaded in TEST_MODE - external API keys are optional")
            return

        if not (self.OPENAI_API_KEY or self.REQUESTY_API_KEY or self.ROUTER_API_KEY):
            raise ValueError("OPENAI_API_KEY, REQUESTY_API_KEY, or ROUTER_API_KEY is required")

        logger.info("Configuration loaded successfully")

# Instantiate settings to be imported by other modules
settings = Settings()
settings.validate_settings()
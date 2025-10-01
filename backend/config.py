import json
import os
import secrets
from typing import Dict, Optional, Set, List
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

    DEFAULT_MODEL_ROUTING: Dict[str, str] = {
        "zai/glm-4.5": "openai/gpt-4o-mini"
    }

    # API Keys (initial raw values; normalized in __init__)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    REQUESTY_API_KEY: str = os.getenv("REQUESTY_API_KEY", "")  # Legacy
    ROUTER_API_KEY: str = os.getenv("ROUTER_API_KEY", "")  # Requesty router
    REQUESTY_MODEL_ROUTING_RAW: str = os.getenv("REQUESTY_MODEL_ROUTING", "")
    REQUESTY_MODEL_ROUTING: Dict[str, str] = {}

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
    REQUESTY_PLANNING_MODEL: str = os.getenv("REQUESTY_PLANNING_MODEL", "zai/glm-4.5")
    REQUESTY_EMBEDDING_MODEL: str = os.getenv("REQUESTY_EMBEDDING_MODEL", "requesty/embedding-001")
    PLANNING_MAX_TOKENS: int = int(os.getenv("PLANNING_MAX_TOKENS", 2200))
    PLANNING_TEMPERATURE: float = float(os.getenv("PLANNING_TEMPERATURE", 0.4))

    # Voice Settings
    TTS_MODEL: str = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "alloy")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")
    ENABLE_WAKE_WORD: bool = os.getenv("ENABLE_WAKE_WORD", "False").lower() == "true"
    WAKE_WORD: str = os.getenv("WAKE_WORD", "hey assistant")
    
    # Additional Voice Settings
    TEMP_AUDIO_DIR: str = os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
    VOICE_LANGUAGE: str = os.getenv("VOICE_LANGUAGE", "en")
    TTS_SPEED: float = float(os.getenv("TTS_SPEED", "1.0"))
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    MAX_AUDIO_DURATION: int = int(os.getenv("MAX_AUDIO_DURATION", "300"))  # 5 minutes
    
    # Enhanced TTS Settings
    TTS_CACHE_DIR: str = os.getenv("TTS_CACHE_DIR", "./cache/tts")
    TTS_CACHE_MAX_SIZE: int = int(os.getenv("TTS_CACHE_MAX_SIZE", "100"))  # Max cache entries
    TTS_CACHE_TTL: int = int(os.getenv("TTS_CACHE_TTL", "604800"))  # 7 days in seconds
    TTS_MAX_TEXT_LENGTH: int = int(os.getenv("TTS_MAX_TEXT_LENGTH", "4096"))  # Max characters
    TTS_DEFAULT_FORMAT: str = os.getenv("TTS_DEFAULT_FORMAT", "mp3")
    TTS_QUALITY: str = os.getenv("TTS_QUALITY", "standard")  # standard, high
    TTS_ENABLE_CACHING: bool = os.getenv("TTS_ENABLE_CACHING", "True").lower() == "true"
    
    # Voice UI Settings
    VOICE_AUTO_PLAY: bool = os.getenv("VOICE_AUTO_PLAY", "False").lower() == "true"
    VOICE_SHOW_METADATA: bool = os.getenv("VOICE_SHOW_METADATA", "True").lower() == "true"
    VOICE_CACHE_STATS: bool = os.getenv("VOICE_CACHE_STATS", "True").lower() == "true"
    
    # Enhanced STT Settings
    STT_STREAMING_CHUNK_SIZE: int = int(os.getenv("STT_STREAMING_CHUNK_SIZE", "1024"))
    STT_STREAMING_BUFFER_SIZE: int = int(os.getenv("STT_STREAMING_BUFFER_SIZE", "8192"))
    STT_STREAMING_MAX_DURATION: int = int(os.getenv("STT_STREAMING_MAX_DURATION", "300"))  # 5 minutes
    STT_SILENCE_THRESHOLD: float = float(os.getenv("STT_SILENCE_THRESHOLD", "0.5"))  # seconds
    STT_ENABLE_LANGUAGE_DETECTION: bool = os.getenv("STT_ENABLE_LANGUAGE_DETECTION", "True").lower() == "true"
    STT_LANGUAGE_CONFIDENCE_THRESHOLD: float = float(os.getenv("STT_LANGUAGE_CONFIDENCE_THRESHOLD", "0.7"))
    STT_SUPPORTED_LANGUAGES: List[str] = os.getenv("STT_SUPPORTED_LANGUAGES", "en,es,fr,de,it,pt,nl,pl,ru,ja,ko,zh,ar").split(",")
    STT_ENABLE_NOISE_REDUCTION: bool = os.getenv("STT_ENABLE_NOISE_REDUCTION", "True").lower() == "true"
    STT_ENABLE_AUDIO_ENHANCEMENT: bool = os.getenv("STT_ENABLE_AUDIO_ENHANCEMENT", "True").lower() == "true"
    STT_NOISE_REDUCTION_STRENGTH: float = float(os.getenv("STT_NOISE_REDUCTION_STRENGTH", "0.8"))
    STT_ENABLE_NORMALIZATION: bool = os.getenv("STT_ENABLE_NORMALIZATION", "True").lower() == "true"
    STT_ENABLE_SPECTRAL_GATING: bool = os.getenv("STT_ENABLE_SPECTRAL_GATING", "True").lower() == "true"
    STT_TRANSCRIPTION_TEMPERATURE: float = float(os.getenv("STT_TRANSCRIPTION_TEMPERATURE", "0.2"))
    STT_ENABLE_WORD_TIMESTAMPS: bool = os.getenv("STT_ENABLE_WORD_TIMESTAMPS", "True").lower() == "true"
    STT_ENABLE_SEGMENT_TIMESTAMPS: bool = os.getenv("STT_ENABLE_SEGMENT_TIMESTAMPS", "True").lower() == "true"
    STT_MAX_AUDIO_LENGTH: int = int(os.getenv("STT_MAX_AUDIO_LENGTH", "600"))  # 10 minutes
    STT_MIN_AUDIO_QUALITY_THRESHOLD: float = float(os.getenv("STT_MIN_AUDIO_QUALITY_THRESHOLD", "0.3"))
    STT_ENABLE_QUALITY_ANALYSIS: bool = os.getenv("STT_ENABLE_QUALITY_ANALYSIS", "True").lower() == "true"

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/devplanning.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", 5))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", 10))

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    REQUIRE_ADMIN_TOKEN: bool = os.getenv("REQUIRE_ADMIN_TOKEN", "True").lower() == "true"

    ADMIN_API_TOKEN_ENV_KEYS: Set[str] = {"RUNTIME_ADMIN_TOKEN", "ADMIN_API_TOKEN"}
    ADMIN_TOKEN_SENTINELS: Set[str] = {
        "",
        "none",
        "null",
        "placeholder",
        "changeme",
        "your-secure-token-here-change-this",
        "your_secure_token_here_change_this",
        "replace-me",
    }
    ADMIN_TOKEN_SENTINELS_LOWER: Set[str] = {value.lower() for value in ADMIN_TOKEN_SENTINELS}

    def __init__(self):
        self.OPENAI_API_KEY = self._normalize_key(self.OPENAI_API_KEY, self.SENTINEL_OPENAI_KEYS_LOWER)
        self.REQUESTY_API_KEY = self._normalize_key(self.REQUESTY_API_KEY, self.SENTINEL_REQUESTY_KEYS_LOWER)
        self.ROUTER_API_KEY = self._normalize_key(self.ROUTER_API_KEY, self.SENTINEL_REQUESTY_KEYS_LOWER)
        self.REQUESTY_MODEL_ROUTING = self._parse_model_routing(self.REQUESTY_MODEL_ROUTING_RAW)

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
            self.TEMP_AUDIO_DIR,
        ):
            try:
                if path:
                    os.makedirs(path, exist_ok=True)
            except OSError as exc:  # pragma: no cover - best-effort directory creation
                logger.warning("Failed to ensure directory %s: %s", path, exc)

    def _parse_model_routing(self, raw: str) -> Dict[str, str]:
        def _normalize_map(source: Dict[str, str]) -> Dict[str, str]:
            normalized: Dict[str, str] = {}
            for key, value in source.items():
                key_str = str(key).strip().lower()
                value_str = str(value).strip()
                if key_str and value_str:
                    normalized[key_str] = value_str
            return normalized

        routing = _normalize_map(self.DEFAULT_MODEL_ROUTING)

        if not raw:
            return routing

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                routing.update(_normalize_map(data))
                return routing
        except json.JSONDecodeError:
            logger.warning("REQUESTY_MODEL_ROUTING environment variable is not valid JSON; using defaults")

        return routing

    def _load_admin_token(self) -> str:
        """Load and normalize the runtime admin token."""
        if not self.REQUIRE_ADMIN_TOKEN:
            logger.warning("REQUIRE_ADMIN_TOKEN is False - admin token validation is DISABLED for testing/development")
            return ""
        
        for env_key in self.ADMIN_API_TOKEN_ENV_KEYS:
            value = os.getenv(env_key)
            if value:
                token = value.strip()
                if token and token.lower() not in self.ADMIN_TOKEN_SENTINELS_LOWER:
                    return token
                if token:
                    logger.warning(
                        "Ignoring placeholder admin token from %s. Configure a secure value to enable runtime updates.",
                        env_key
                    )

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
        if not self.REQUIRE_ADMIN_TOKEN:
            return False
        return bool(self.RUNTIME_ADMIN_TOKEN)

    def validate_admin_token(self, token: Optional[str]) -> bool:
        """Validate the provided admin token against configuration."""
        if not self.REQUIRE_ADMIN_TOKEN:
            return True
        
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
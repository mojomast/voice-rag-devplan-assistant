import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from a .env file
load_dotenv()

class Settings:
    """
    Centralized configuration for the application.
    """
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    REQUESTY_API_KEY: str = os.getenv("REQUESTY_API_KEY")

    # File Paths
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./vector_store")
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH", "./uploads")

    # RAG Settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # LLM Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", 0.7))

    # Voice Settings
    TTS_MODEL: str = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "alloy")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")
    ENABLE_WAKE_WORD: bool = os.getenv("ENABLE_WAKE_WORD", "False").lower() == "true"
    WAKE_WORD: str = os.getenv("WAKE_WORD", "hey assistant")

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def validate_settings(self):
        """Validate that required settings are present"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")

        logger.info("Configuration loaded successfully")

# Instantiate settings to be imported by other modules
settings = Settings()
settings.validate_settings()
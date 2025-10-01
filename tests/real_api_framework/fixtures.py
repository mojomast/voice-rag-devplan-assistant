"""
Fixtures module for Real API Test Framework

Provides pytest fixtures and test data providers for real API testing.
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from .core import RealAPITestFramework, APITestConfig, TestMode
from .security import APIKeyManager, SecureCredentialsStore
from .utils import TestDataGenerator, APIResponseValidator, RetryHandler
from .monitors import CostMonitor, UsageTracker, RateLimitMonitor


class RealAPIFixtureProvider:
    """
    Provides fixtures and test data for real API testing.
    """
    
    def __init__(self):
        self.test_data_generator = TestDataGenerator()
        self.response_validator = APIResponseValidator()
        self.retry_handler = RetryHandler()
    
    def get_openai_client(self):
        """Get configured OpenAI client for testing"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                pytest.skip("OPENAI_API_KEY not configured for real API testing")
            return OpenAI(api_key=api_key)
        except ImportError:
            pytest.skip("OpenAI library not installed")
    
    def get_requesty_client(self):
        """Get configured Requesty client for testing"""
        try:
            sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))
            from requesty_client import RequestyClient
            return RequestyClient()
        except ImportError:
            pytest.skip("Requesty client not available")
    
    def get_voice_service(self):
        """Get configured voice service for testing"""
        try:
            sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))
            from voice_service import VoiceService
            return VoiceService()
        except ImportError:
            pytest.skip("Voice service not available")
    
    def get_rag_handler(self):
        """Get configured RAG handler for testing"""
        try:
            sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))
            from rag_handler import RAGHandler
            return RAGHandler()
        except ImportError:
            pytest.skip("RAG handler not available")


# Pytest fixtures

@pytest.fixture(scope="session")
def real_api_config():
    """Configuration for real API testing"""
    return APITestConfig(
        mode=TestMode.REAL_API,
        max_cost_per_test=0.5,  # Conservative for CI
        max_cost_per_session=5.0,
        cost_warning_threshold=0.7,
        requests_per_minute=30,  # Conservative rate limiting
        requests_per_hour=500,
        retry_attempts=2,
        request_timeout=30.0,
        test_timeout=120.0,
        cache_responses=True,
        cache_duration=1800,  # 30 minutes
        save_test_data=True,
        require_api_keys=True,
        validate_keys=True,
        encrypt_credentials=True,
        enable_cost_tracking=True,
        enable_usage_tracking=True,
        enable_rate_limiting=True,
        log_level="INFO",
        log_requests=True,
        log_responses=False,
        enabled_providers=["openai", "requesty"],
        enabled_categories=[
            "voice_transcription", "text_to_speech", "chat_completion",
            "embeddings", "planning", "rag_queries"
        ]
    )


@pytest.fixture(scope="session")
def real_api_framework(real_api_config):
    """Real API test framework fixture"""
    framework = RealAPITestFramework(real_api_config)
    yield framework
    framework.cleanup()


@pytest.fixture(scope="session")
def api_key_manager():
    """API key manager fixture"""
    store = SecureCredentialsStore()
    manager = APIKeyManager(store)
    yield manager
    # Cleanup if needed


@pytest.fixture
def test_data():
    """Test data fixture"""
    generator = TestDataGenerator()
    return generator.get_test_data()


@pytest.fixture
def openai_client():
    """OpenAI client fixture"""
    provider = RealAPIFixtureProvider()
    return provider.get_openai_client()


@pytest.fixture
def requesty_client():
    """Requesty client fixture"""
    provider = RealAPIFixtureProvider()
    return provider.get_requesty_client()


@pytest.fixture
def voice_service():
    """Voice service fixture"""
    provider = RealAPIFixtureProvider()
    return provider.get_voice_service()


@pytest.fixture
def rag_handler():
    """RAG handler fixture"""
    provider = RealAPIFixtureProvider()
    return provider.get_rag_handler()


@pytest.fixture
def response_validator():
    """Response validator fixture"""
    return APIResponseValidator()


@pytest.fixture
def retry_handler():
    """Retry handler fixture"""
    return RetryHandler()


@pytest.fixture
def sample_audio_file():
    """Sample audio file fixture"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Write minimal WAV header
        f.write(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def sample_text():
    """Sample text fixture"""
    return "Hello, this is a test of the voice transcription system."


@pytest.fixture
def sample_document():
    """Sample document fixture"""
    return """
    Artificial Intelligence in Modern Applications

    Artificial Intelligence (AI) has become an integral part of modern software applications,
    transforming how we interact with technology on a daily basis.

    Key Applications:
    1. Virtual Assistants: Siri, Alexa, and Google Assistant use AI to understand and respond to voice commands
    2. Recommendation Systems: Netflix and Amazon use AI to suggest personalized content
    3. Autonomous Vehicles: Self-driving cars use AI for navigation and safety
    4. Healthcare: AI assists in diagnosis and treatment planning
    5. Finance: AI algorithms detect fraud and optimize trading strategies

    The future of AI looks promising with continued advancements in deep learning,
    natural language processing, and computer vision technologies.
    """


# Test function fixtures

@pytest.fixture
async def test_transcription_function(openai_client, sample_audio_file):
    """Test function for audio transcription"""
    async def transcribe_audio(audio_path: str, language: str = "en") -> Dict[str, Any]:
        try:
            with open(audio_path, "rb") as audio_file:
                response = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )
            
            return {
                "status": "success",
                "text": response.text,
                "language": response.language,
                "duration": response.duration,
                "confidence": getattr(response, 'confidence', 1.0),
                "segments": getattr(response, 'segments', []),
                "usage": {
                    "duration": response.duration
                },
                "provider": "openai",
                "model": "whisper-1",
                "operation": "transcription"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "openai",
                "model": "whisper-1",
                "operation": "transcription"
            }
    
    return transcribe_audio


@pytest.fixture
async def test_tts_function(openai_client):
    """Test function for text-to-speech"""
    async def synthesize_speech(text: str, voice: str = "alloy") -> Dict[str, Any]:
        try:
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            return {
                "status": "success",
                "audio_data": response.content,
                "voice": voice,
                "text_length": len(text),
                "usage": {
                    "character_count": len(text)
                },
                "provider": "openai",
                "model": "tts-1",
                "operation": "tts"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "openai",
                "model": "tts-1",
                "operation": "tts"
            }
    
    return synthesize_speech


@pytest.fixture
async def test_chat_completion_function(openai_client):
    """Test function for chat completion"""
    async def chat_completion(messages: List[Dict], model: str = "gpt-4o-mini") -> Dict[str, Any]:
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return {
                "status": "success",
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "provider": "openai",
                "model": model,
                "operation": "chat_completion"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "openai",
                "model": model,
                "operation": "chat_completion"
            }
    
    return chat_completion


@pytest.fixture
async def test_embedding_function(openai_client):
    """Test function for embeddings"""
    async def create_embedding(text: str, model: str = "text-embedding-3-small") -> Dict[str, Any]:
        try:
            response = openai_client.embeddings.create(
                model=model,
                input=text
            )
            
            return {
                "status": "success",
                "embedding": response.data[0].embedding,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens
                },
                "provider": "openai",
                "model": model,
                "operation": "embedding"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "openai",
                "model": model,
                "operation": "embedding"
            }
    
    return create_embedding


@pytest.fixture
async def test_requesty_chat_function(requesty_client):
    """Test function for Requesty chat completion"""
    async def requesty_chat(messages: List[Dict], model: str = "zai/glm-4.5") -> Dict[str, Any]:
        try:
            response_text = requesty_client.chat_completion(messages, model=model)
            
            return {
                "status": "success",
                "content": response_text,
                "provider": "requesty",
                "model": model,
                "operation": "chat_completion"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "requesty",
                "model": model,
                "operation": "chat_completion"
            }
    
    return requesty_chat


@pytest.fixture
async def test_requesty_embedding_function(requesty_client):
    """Test function for Requesty embeddings"""
    async def requesty_embedding(texts: List[str], model: str = "requesty/embedding-001") -> Dict[str, Any]:
        try:
            embeddings = requesty_client.embed_texts(texts, model=model)
            
            return {
                "status": "success",
                "embeddings": embeddings,
                "provider": "requesty",
                "model": model,
                "operation": "embedding"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "requesty",
                "model": model,
                "operation": "embedding"
            }
    
    return requesty_embedding


# Voice service test fixtures

@pytest.fixture
async def test_voice_transcription_function(voice_service):
    """Test function for voice service transcription"""
    async def voice_transcribe(audio_path: str, language: str = "en") -> Dict[str, Any]:
        try:
            result = voice_service.transcribe_audio(audio_path, language)
            
            return {
                "status": result.get("status", "unknown"),
                "text": result.get("text", ""),
                "language": result.get("language", "unknown"),
                "duration": result.get("duration", 0),
                "confidence": result.get("confidence", 0.0),
                "provider": "voice_service",
                "operation": "transcription",
                "api_calls": [{
                    "provider": "openai",
                    "operation": "transcription",
                    "model": "whisper-1",
                    "success": result.get("status") == "success",
                    "tokens_used": 0,
                    "duration_ms": int(result.get("duration", 0) * 1000)
                }]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "voice_service",
                "operation": "transcription"
            }
    
    return voice_transcribe


@pytest.fixture
async def test_voice_tts_function(voice_service):
    """Test function for voice service TTS"""
    async def voice_synthesize(text: str, voice: str = "alloy") -> Dict[str, Any]:
        try:
            result = voice_service.synthesize_speech(text, voice=voice)
            
            return {
                "status": result.get("status", "unknown"),
                "audio_file": result.get("audio_file", ""),
                "voice": result.get("voice", voice),
                "text_length": len(text),
                "provider": "voice_service",
                "operation": "tts",
                "api_calls": [{
                    "provider": "openai",
                    "operation": "tts",
                    "model": "tts-1",
                    "success": result.get("status") == "success",
                    "tokens_used": len(text),
                    "duration_ms": 0
                }]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "voice_service",
                "operation": "tts"
            }
    
    return voice_synthesize


# RAG handler test fixtures

@pytest.fixture
async def test_rag_query_function(rag_handler):
    """Test function for RAG queries"""
    async def rag_query(query: str) -> Dict[str, Any]:
        try:
            result = rag_handler.ask_question(query)
            
            return {
                "status": result.get("status", "unknown"),
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "query": query,
                "provider": "rag_handler",
                "operation": "query",
                "api_calls": [{
                    "provider": "requesty",
                    "operation": "chat_completion",
                    "model": "zai/glm-4.5",
                    "success": result.get("status") == "success",
                    "tokens_used": len(query) + len(result.get("answer", "")),
                    "duration_ms": 0
                }]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "rag_handler",
                "operation": "query"
            }
    
    return rag_query


# Utility fixtures

@pytest.fixture
def test_scenarios():
    """Test scenarios for comprehensive testing"""
    return {
        "voice_transcription": {
            "short_text": "Hello world",
            "medium_text": "This is a medium length test for voice transcription accuracy.",
            "technical_text": "The API endpoint POST /v1/chat/completions requires JSON payload with messages array.",
            "multilingual": ["Hello world", "Bonjour le monde", "Hola mundo"]
        },
        "text_to_speech": {
            "short_text": "Hello",
            "medium_text": "This is a test of the text to speech synthesis system.",
            "punctuation": "Hello! How are you? I hope you're doing well.",
            "numbers": "The year 2025 has 365 days. The cost is $15.50."
        },
        "chat_completion": {
            "simple": [{"role": "user", "content": "Hello, how are you?"}],
            "technical": [{"role": "user", "content": "Explain how REST APIs work"}],
            "creative": [{"role": "user", "content": "Write a short poem about AI"}],
            "contextual": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What can you help me with?"}
            ]
        },
        "embeddings": {
            "short": "AI",
            "medium": "Artificial intelligence is transforming technology",
            "technical": "Neural networks use backpropagation for learning",
            "multilingual": ["Hello world", "Bonjour le monde", "Hola mundo"]
        }
    }


@pytest.fixture
def cost_tracking_fixture():
    """Fixture for cost tracking validation"""
    class CostTracker:
        def __init__(self):
            self.costs = []
        
        def add_cost(self, provider: str, model: str, operation: str, cost: float):
            self.costs.append({
                "provider": provider,
                "model": model,
                "operation": operation,
                "cost": cost,
                "timestamp": pytest.helpers.current_time()
            })
        
        def get_total_cost(self) -> float:
            return sum(c["cost"] for c in self.costs)
        
        def get_provider_costs(self) -> Dict[str, float]:
            costs = {}
            for cost in self.costs:
                provider = cost["provider"]
                costs[provider] = costs.get(provider, 0) + cost["cost"]
            return costs
    
    return CostTracker()
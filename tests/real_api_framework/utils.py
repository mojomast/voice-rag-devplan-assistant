"""
Utilities module for Real API Test Framework

Provides test data generation, response validation, and helper functions.
"""

import os
import json
import base64
import tempfile
import random
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import uuid
import asyncio
from loguru import logger


@dataclass
class TestData:
    """Test data container"""
    text_samples: List[str]
    audio_files: Dict[str, str]  # name -> path
    documents: Dict[str, str]    # name -> path
    queries: List[str]
    prompts: List[str]
    metadata: Dict[str, Any]


class TestDataGenerator:
    """
    Generates test data for real API testing.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "./tests/real_api_data/test_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Predefined test data
        self.text_samples = [
            "Hello, this is a test of the voice transcription system.",
            "The quick brown fox jumps over the lazy dog.",
            "Artificial intelligence is transforming how we interact with technology.",
            "Machine learning models require large amounts of training data.",
            "Voice recognition has improved significantly in recent years.",
            "Natural language processing enables computers to understand human language.",
            "Deep learning architectures like transformers have revolutionized AI.",
            "Speech synthesis can generate human-like voice from text.",
            "Real-time transcription is useful for meeting notes and accessibility.",
            "Multilingual support is essential for global applications."
        ]
        
        self.test_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain the concept of neural networks.",
            "What are the applications of deep learning?",
            "How is voice recognition technology used?",
            "What is natural language processing?",
            "Describe the difference between AI and machine learning.",
            "How do speech synthesis systems work?",
            "What are the challenges in voice recognition?",
            "How can AI be used in healthcare?"
        ]
        
        self.test_prompts = [
            "Create a development plan for a new feature.",
            "Generate a project roadmap for the next quarter.",
            "Outline the steps for implementing a user authentication system.",
            "Design a database schema for an e-commerce platform.",
            "Plan the architecture for a microservices application.",
            "Create a testing strategy for a web application.",
            "Design a RESTful API for a mobile app.",
            "Plan the deployment process for a cloud application.",
            "Outline security best practices for web development.",
            "Create a performance optimization plan for a database."
        ]
    
    def get_test_data(self) -> TestData:
        """Get comprehensive test data"""
        # Generate audio files if they don't exist
        audio_files = self._ensure_audio_files()
        
        # Generate documents if they don't exist
        documents = self._ensure_documents()
        
        return TestData(
            text_samples=self.text_samples,
            audio_files=audio_files,
            documents=documents,
            queries=self.test_queries,
            prompts=self.test_prompts,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "total_text_samples": len(self.text_samples),
                "total_queries": len(self.test_queries),
                "total_prompts": len(self.test_prompts)
            }
        )
    
    def _ensure_audio_files(self) -> Dict[str, str]:
        """Ensure test audio files exist"""
        audio_dir = self.data_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        
        audio_files = {}
        
        # Create different types of test audio files
        test_configs = [
            {"name": "short_english", "text": "Hello world", "format": "wav"},
            {"name": "medium_english", "text": "This is a medium length test audio file for transcription testing.", "format": "mp3"},
            {"name": "long_english", "text": "This is a longer audio file that contains multiple sentences for testing the transcription capabilities of the system. It includes various punctuation marks and should provide a good test case for the speech recognition accuracy.", "format": "wav"},
            {"name": "technical_content", "text": "The API endpoint for POST requests is located at slash API slash v1 slash chat completions. The request requires a JSON payload with messages field.", "format": "mp3"},
            {"name": "numbers_and_dates", "text": "Today is October 1st, 2025. The API key costs $15.50 per month. Response time is 250 milliseconds.", "format": "wav"}
        ]
        
        for config in test_configs:
            file_path = audio_dir / f"{config['name']}.{config['format']}"
            
            if not file_path.exists():
                # Create a simple audio file (in real implementation, this would use TTS)
                self._create_mock_audio_file(file_path, config['text'])
            
            audio_files[config['name']] = str(file_path)
        
        return audio_files
    
    def _create_mock_audio_file(self, file_path: Path, text: str):
        """Create a mock audio file for testing"""
        # This creates a minimal valid audio file header
        # In a real implementation, this would use actual TTS API
        
        if file_path.suffix == ".wav":
            # Create a minimal WAV file
            wav_data = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00" + text.encode()[:1000]
            file_path.write_bytes(wav_data)
        
        elif file_path.suffix == ".mp3":
            # Create a minimal MP3 file (header only)
            mp3_data = b"\xff\xfb\x90\x00" + text.encode()[:1000]
            file_path.write_bytes(mp3_data)
        
        logger.debug(f"Created mock audio file: {file_path}")
    
    def _ensure_documents(self) -> Dict[str, str]:
        """Ensure test documents exist"""
        doc_dir = self.data_dir / "documents"
        doc_dir.mkdir(exist_ok=True)
        
        documents = {}
        
        # Create different types of test documents
        test_docs = [
            {
                "name": "ai_basics",
                "content": """Artificial Intelligence Basics

Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that can simulate human thinking and behavior.

Key Concepts:
- Machine Learning: Algorithms that improve through experience
- Neural Networks: Computing systems inspired by biological neural networks
- Natural Language Processing: Understanding and generating human language
- Computer Vision: Analyzing and interpreting visual information

Applications:
1. Virtual assistants like Siri and Alexa
2. Recommendation systems on streaming platforms
3. Autonomous vehicles
4. Medical diagnosis systems
5. Fraud detection in banking

The field continues to evolve rapidly with new breakthroughs in deep learning and reinforcement learning."""
            },
            {
                "name": "voice_technology",
                "content": """Voice Technology Overview

Voice technology has become increasingly sophisticated, enabling natural interaction between humans and machines.

Core Components:
1. Automatic Speech Recognition (ASR)
   - Converts spoken language to text
   - Handles different accents and languages
   - Processes real-time streaming audio

2. Text-to-Speech (TTS)
   - Converts text to natural-sounding speech
   - Supports multiple voices and languages
   - Adjusts speed and intonation

3. Natural Language Understanding (NLU)
   - Extracts meaning from spoken commands
   - Handles context and ambiguity
   - Enables conversational AI

Technical Challenges:
- Background noise reduction
- Speaker identification
- Real-time processing
- Multi-language support
- Emotional tone detection

Current Technologies:
- OpenAI Whisper for transcription
- Google Speech-to-Text
- Amazon Transcribe
- Microsoft Azure Speech Services

Future Directions:
- Emotion recognition in voice
- Real-time translation
- Personalized voice synthesis
- Cross-lingual communication"""
            },
            {
                "name": "api_integration",
                "content": """API Integration Guide

This document covers best practices for integrating with external APIs in the voice RAG system.

Authentication:
- OpenAI API: Use Bearer token authentication
- Requesty.ai: Router-based authentication with fallback
- Always validate API keys before use
- Implement key rotation strategies

Rate Limiting:
- Respect provider rate limits
- Implement exponential backoff
- Monitor usage patterns
- Set appropriate timeouts

Error Handling:
- Handle network timeouts gracefully
- Implement retry logic with appropriate delays
- Log errors without exposing sensitive data
- Provide meaningful error messages to users

Cost Optimization:
- Use appropriate model sizes
- Implement response caching
- Monitor token usage
- Set usage limits and alerts

Security Considerations:
- Never commit API keys to version control
- Use environment variables for credentials
- Implement proper key encryption
- Regular security audits

Monitoring:
- Track API response times
- Monitor error rates
- Set up alerts for anomalies
- Regular performance reviews"""
            }
        ]
        
        for doc_config in test_docs:
            file_path = doc_dir / f"{doc_config['name']}.txt"
            
            if not file_path.exists():
                file_path.write_text(doc_config['content'], encoding='utf-8')
            
            documents[doc_config['name']] = str(file_path)
        
        return documents
    
    def generate_random_text(self, min_words: int = 5, max_words: int = 50) -> str:
        """Generate random text for testing"""
        templates = [
            "The {} is important for {} development.",
            "In this {}, we will explore the concept of {}.",
            "Modern {} applications rely heavily on {} technology.",
            "The {} system provides {} capabilities for users.",
            "When implementing {}, consider the {} aspects carefully."
        ]
        
        subjects = ["AI", "machine learning", "voice recognition", "API integration", "data processing"]
        objects = ["efficient", "scalable", "reliable", "secure", "user-friendly"]
        
        template = random.choice(templates)
        subject = random.choice(subjects)
        obj = random.choice(objects)
        
        return template.format(subject, obj)
    
    def generate_test_query(self, category: str = "general") -> str:
        """Generate a test query based on category"""
        if category == "technical":
            return random.choice([
                "How does the API handle authentication?",
                "What are the rate limits for this service?",
                "Explain the error handling mechanism.",
                "How is data encrypted during transmission?",
                "What monitoring tools are available?"
            ])
        elif category == "business":
            return random.choice([
                "What are the cost implications?",
                "How does this scale for enterprise use?",
                "What is the ROI for implementing this?",
                "How does this compare to alternatives?",
                "What are the migration strategies?"
            ])
        else:
            return random.choice(self.test_queries)


class APIResponseValidator:
    """
    Validates API responses for correctness and completeness.
    """
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Dict]:
        """Load validation rules for different API types"""
        return {
            "transcription": {
                "required_fields": ["text", "language"],
                "optional_fields": ["duration", "confidence", "segments"],
                "validators": {
                    "text": self._validate_text,
                    "language": self._validate_language_code,
                    "confidence": self._validate_confidence,
                    "duration": self._validate_duration
                }
            },
            "tts": {
                "required_fields": ["audio_data"],
                "optional_fields": ["voice", "format", "duration"],
                "validators": {
                    "audio_data": self._validate_audio_data,
                    "voice": self._validate_voice_name,
                    "format": self._validate_audio_format
                }
            },
            "chat_completion": {
                "required_fields": ["content"],
                "optional_fields": ["usage", "model", "finish_reason"],
                "validators": {
                    "content": self._validate_text,
                    "usage": self._validate_usage_info,
                    "model": self._validate_model_name
                }
            },
            "embedding": {
                "required_fields": ["embedding"],
                "optional_fields": ["model", "usage"],
                "validators": {
                    "embedding": self._validate_embedding_vector,
                    "model": self._validate_model_name
                }
            }
        }
    
    def validate(self, response: Dict, category: str) -> Dict[str, Any]:
        """
        Validate an API response against category-specific rules.
        
        Args:
            response: The API response to validate
            category: The category of API response (transcription, tts, etc.)
            
        Returns:
            Validation result with status and details
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "category": category,
            "validated_at": datetime.now().isoformat()
        }
        
        rules = self.validation_rules.get(category)
        if not rules:
            validation_result["warnings"].append(f"No validation rules found for category: {category}")
            return validation_result
        
        # Check required fields
        for field in rules["required_fields"]:
            if field not in response:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Run field-specific validators
        for field, validator in rules["validators"].items():
            if field in response:
                try:
                    field_validation = validator(response[field])
                    if not field_validation["valid"]:
                        validation_result["valid"] = False
                        validation_result["errors"].extend(field_validation["errors"])
                    validation_result["warnings"].extend(field_validation.get("warnings", []))
                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Validation error for field {field}: {str(e)}")
        
        return validation_result
    
    def _validate_text(self, text: Any) -> Dict[str, Any]:
        """Validate text field"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if not isinstance(text, str):
            result["valid"] = False
            result["errors"].append("Text must be a string")
            return result
        
        if len(text.strip()) == 0:
            result["valid"] = False
            result["errors"].append("Text cannot be empty")
        
        if len(text) > 100000:  # 100KB limit
            result["warnings"].append("Text is very large, may impact performance")
        
        return result
    
    def _validate_language_code(self, language: Any) -> Dict[str, Any]:
        """Validate language code"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if not isinstance(language, str):
            result["valid"] = False
            result["errors"].append("Language must be a string")
            return result
        
        valid_codes = ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja", "ko", "zh", "ar"]
        if language not in valid_codes:
            result["warnings"].append(f"Unusual language code: {language}")
        
        return result
    
    def _validate_confidence(self, confidence: Any) -> Dict[str, Any]:
        """Validate confidence score"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        try:
            conf_float = float(confidence)
            if not 0.0 <= conf_float <= 1.0:
                result["valid"] = False
                result["errors"].append("Confidence must be between 0.0 and 1.0")
        except (ValueError, TypeError):
            result["valid"] = False
            result["errors"].append("Confidence must be a number")
        
        return result
    
    def _validate_duration(self, duration: Any) -> Dict[str, Any]:
        """Validate duration"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        try:
            duration_float = float(duration)
            if duration_float < 0:
                result["valid"] = False
                result["errors"].append("Duration cannot be negative")
            if duration_float > 3600:  # 1 hour
                result["warnings"].append("Very long duration detected")
        except (ValueError, TypeError):
            result["valid"] = False
            result["errors"].append("Duration must be a number")
        
        return result
    
    def _validate_audio_data(self, audio_data: Any) -> Dict[str, Any]:
        """Validate audio data"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if isinstance(audio_data, bytes):
            if len(audio_data) == 0:
                result["valid"] = False
                result["errors"].append("Audio data cannot be empty")
            elif len(audio_data) < 100:
                result["warnings"].append("Audio data is very small")
        elif isinstance(audio_data, str):
            # Could be base64 encoded
            try:
                decoded = base64.b64decode(audio_data)
                if len(decoded) == 0:
                    result["valid"] = False
                    result["errors"].append("Decoded audio data cannot be empty")
            except Exception:
                result["valid"] = False
                result["errors"].append("Invalid base64 audio data")
        else:
            result["valid"] = False
            result["errors"].append("Audio data must be bytes or base64 string")
        
        return result
    
    def _validate_voice_name(self, voice: Any) -> Dict[str, Any]:
        """Validate voice name"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if not isinstance(voice, str):
            result["valid"] = False
            result["errors"].append("Voice name must be a string")
            return result
        
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice not in valid_voices:
            result["warnings"].append(f"Unusual voice name: {voice}")
        
        return result
    
    def _validate_audio_format(self, format_name: Any) -> Dict[str, Any]:
        """Validate audio format"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if not isinstance(format_name, str):
            result["valid"] = False
            result["errors"].append("Audio format must be a string")
            return result
        
        valid_formats = ["mp3", "wav", "webm", "ogg", "flac"]
        if format_name not in valid_formats:
            result["warnings"].append(f"Unusual audio format: {format_name}")
        
        return result
    
    def _validate_usage_info(self, usage: Any) -> Dict[str, Any]:
        """Validate usage information"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if not isinstance(usage, dict):
            result["valid"] = False
            result["errors"].append("Usage info must be a dictionary")
            return result
        
        # Check for common usage fields
        if "prompt_tokens" in usage:
            try:
                tokens = int(usage["prompt_tokens"])
                if tokens < 0:
                    result["valid"] = False
                    result["errors"].append("Prompt tokens cannot be negative")
            except (ValueError, TypeError):
                result["valid"] = False
                result["errors"].append("Prompt tokens must be an integer")
        
        if "completion_tokens" in usage:
            try:
                tokens = int(usage["completion_tokens"])
                if tokens < 0:
                    result["valid"] = False
                    result["errors"].append("Completion tokens cannot be negative")
            except (ValueError, TypeError):
                result["valid"] = False
                result["errors"].append("Completion tokens must be an integer")
        
        return result
    
    def _validate_model_name(self, model: Any) -> Dict[str, Any]:
        """Validate model name"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if not isinstance(model, str):
            result["valid"] = False
            result["errors"].append("Model name must be a string")
            return result
        
        if len(model.strip()) == 0:
            result["valid"] = False
            result["errors"].append("Model name cannot be empty")
        
        return result
    
    def _validate_embedding_vector(self, embedding: Any) -> Dict[str, Any]:
        """Validate embedding vector"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if not isinstance(embedding, list):
            result["valid"] = False
            result["errors"].append("Embedding must be a list")
            return result
        
        if len(embedding) == 0:
            result["valid"] = False
            result["errors"].append("Embedding vector cannot be empty")
        
        # Check all elements are numbers
        try:
            for i, value in enumerate(embedding):
                float_val = float(value)
                if not -1.0 <= float_val <= 1.0:
                    result["warnings"].append(f"Embedding value at index {i} is outside normal range [-1, 1]")
        except (ValueError, TypeError):
            result["valid"] = False
            result["errors"].append("All embedding values must be numbers")
        
        return result


class RetryHandler:
    """
    Handles retry logic for API requests with exponential backoff.
    """
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """Retry an async function with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    # Last attempt, re-raise the exception
                    raise
                
                # Calculate delay for next attempt
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def retry_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Retry a synchronous function with exponential backoff"""
        import time
        
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    # Last attempt, re-raise the exception
                    raise
                
                # Calculate delay for next attempt
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
        
        raise last_exception
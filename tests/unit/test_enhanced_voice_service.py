import pytest
import tempfile
import os
import sys
import json
import base64
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from voice_service import (
    VoiceService, 
    TTSCacheEntry, 
    AudioFormat, 
    TTSError, 
    AudioFormatError,
    VoiceNotFoundError,
    CacheError
)

class TestEnhancedVoiceService:
    @pytest.fixture
    def voice_service(self):
        """Create a VoiceService instance for testing"""
        with patch('voice_service.settings'):
            service = VoiceService()
            service.test_mode = True  # Force test mode
            return service

    @pytest.fixture
    def sample_audio_file(self):
        """Create a sample audio file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'fake audio data for testing')
            return f.name

    @pytest.fixture
    def sample_cache_entry(self):
        """Create a sample cache entry for testing"""
        return TTSCacheEntry(
            text_hash="test_hash_123",
            voice="alloy",
            audio_data=b"fake audio data",
            mime_type="audio/mpeg",
            created_at=datetime.now(),
            access_count=5,
            last_accessed=datetime.now()
        )

    class TestAudioFormatValidation:
        """Test enhanced audio format validation"""
        
        def test_validate_supported_format(self, voice_service, sample_audio_file):
            """Test validation of supported audio format"""
            result = voice_service.validate_audio_format_enhanced(sample_audio_file)
            
            assert result["valid"] is True
            assert result["format"] == "mp3"
            assert "mime_type" in result
            assert "size" in result
        
        def test_validate_unsupported_format(self, voice_service):
            """Test validation of unsupported audio format"""
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(b"not audio data")
                temp_file = f.name
            
            try:
                result = voice_service.validate_audio_format_enhanced(temp_file)
                
                assert result["valid"] is False
                assert result["error_type"] == "unsupported_format"
                assert "supported_formats" in result
            finally:
                os.unlink(temp_file)
        
        def test_validate_nonexistent_file(self, voice_service):
            """Test validation of non-existent file"""
            result = voice_service.validate_audio_format_enhanced("nonexistent.mp3")
            
            assert result["valid"] is False
            assert result["error_type"] == "file_not_found"
        
        def test_validate_empty_file(self, voice_service):
            """Test validation of empty file"""
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                # Write empty file
                temp_file = f.name
            
            try:
                result = voice_service.validate_audio_format_enhanced(temp_file)
                
                assert result["valid"] is False
                assert result["error_type"] == "corrupted_file"
            finally:
                os.unlink(temp_file)
        
        def test_validate_large_file(self, voice_service):
            """Test validation of file that's too large"""
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                # Write data that exceeds limit (simulate large file)
                f.write(b'x' * (30 * 1024 * 1024))  # 30MB
                temp_file = f.name
            
            try:
                result = voice_service.validate_audio_format_enhanced(temp_file)
                
                assert result["valid"] is False
                assert result["error_type"] == "file_too_large"
                assert "file_size" in result
                assert "max_size" in result
            finally:
                os.unlink(temp_file)

    class TestTTSCaching:
        """Test TTS caching functionality"""
        
        def test_cache_key_generation(self, voice_service):
            """Test cache key generation"""
            key1 = voice_service._get_cache_key("hello world", "alloy")
            key2 = voice_service._get_cache_key("hello world", "alloy")
            key3 = voice_service._get_cache_key("hello world", "echo")
            
            assert key1 == key2  # Same text and voice should generate same key
            assert key1 != key3  # Different voice should generate different key
            assert len(key1) == 32  # MD5 hash length
        
        def test_cache_entry_validity(self, voice_service, sample_cache_entry):
            """Test cache entry validity checking"""
            # Fresh entry should be valid
            assert voice_service._is_cache_entry_valid(sample_cache_entry) is True
            
            # Expired entry should be invalid
            expired_entry = TTSCacheEntry(
                text_hash="test",
                voice="alloy",
                audio_data=b"data",
                mime_type="audio/mpeg",
                created_at=datetime.now() - timedelta(days=10),  # 10 days ago
                access_count=1
            )
            assert voice_service._is_cache_entry_valid(expired_entry) is False
        
        def test_cache_storage_and_retrieval(self, voice_service, sample_cache_entry):
            """Test caching and retrieving audio data"""
            text = "test text for caching"
            voice = "alloy"
            audio_data = b"test audio data"
            mime_type = "audio/mpeg"
            
            # Cache audio data
            voice_service._cache_audio(text, voice, audio_data, mime_type)
            
            # Retrieve cached audio
            cached_entry = voice_service._get_cached_audio(text, voice)
            
            assert cached_entry is not None
            assert cached_entry.audio_data == audio_data
            assert cached_entry.voice == voice
            assert cached_entry.mime_type == mime_type
        
        def test_cache_miss(self, voice_service):
            """Test cache miss scenario"""
            cached_entry = voice_service._get_cached_audio("nonexistent text", "alloy")
            assert cached_entry is None
        
        def test_cache_cleanup(self, voice_service):
            """Test cache cleanup functionality"""
            # Add some entries to cache
            voice_service._cache_audio("test1", "alloy", b"data1", "audio/mpeg")
            voice_service._cache_audio("test2", "echo", b"data2", "audio/mpeg")
            
            # Add expired entry
            expired_entry = TTSCacheEntry(
                text_hash="expired",
                voice="alloy",
                audio_data=b"expired_data",
                mime_type="audio/mpeg",
                created_at=datetime.now() - timedelta(days=10),
                access_count=1
            )
            voice_service._tts_cache["expired"] = expired_entry
            
            # Run cleanup
            voice_service._cleanup_cache()
            
            # Expired entry should be removed
            assert "expired" not in voice_service._tts_cache
            # Valid entries should remain
            assert len(voice_service._tts_cache) >= 2
        
        def test_cache_size_limit(self, voice_service):
            """Test cache size limit enforcement"""
            # Set small cache size for testing
            voice_service.cache_max_size = 2
            
            # Add more entries than limit
            voice_service._cache_audio("test1", "alloy", b"data1", "audio/mpeg")
            voice_service._cache_audio("test2", "echo", b"data2", "audio/mpeg")
            voice_service._cache_audio("test3", "fable", b"data3", "audio/mpeg")
            
            # Cache should not exceed limit
            assert len(voice_service._tts_cache) <= 2

    class TestEnhancedSpeechSynthesis:
        """Test enhanced speech synthesis functionality"""
        
        def test_synthesize_with_caching(self, voice_service):
            """Test speech synthesis with caching enabled"""
            text = "Hello, this is a test"
            voice = "alloy"
            
            # Mock the synthesis to avoid API calls
            with patch.object(voice_service, '_create_fake_audio_file') as mock_create:
                mock_create.return_value = "fake_path.mp3"
                
                # First synthesis
                result1 = voice_service.synthesize_speech(text, voice, use_cache=True)
                
                # Second synthesis should use cache
                result2 = voice_service.synthesize_speech(text, voice, use_cache=True)
                
                # Both should succeed
                assert result1["status"] == "success"
                assert result2["status"] == "success"
                assert result2.get("cached") is True
        
        def test_synthesize_without_caching(self, voice_service):
            """Test speech synthesis with caching disabled"""
            text = "Hello, this is a test"
            voice = "alloy"
            
            with patch.object(voice_service, '_create_fake_audio_file') as mock_create:
                mock_create.return_value = "fake_path.mp3"
                
                result = voice_service.synthesize_speech(text, voice, use_cache=False)
                
                assert result["status"] == "success"
                assert result.get("cached") is False
        
        def test_synthesize_invalid_voice(self, voice_service):
            """Test speech synthesis with invalid voice"""
            text = "Hello, this is a test"
            invalid_voice = "invalid_voice"
            
            result = voice_service.synthesize_speech(text, invalid_voice)
            
            assert result["status"] == "error"
            assert result["error_type"] == "voice_not_supported"
            assert "available_voices" in result
        
        def test_synthesize_empty_text(self, voice_service):
            """Test speech synthesis with empty text"""
            result = voice_service.synthesize_speech("")
            
            assert result["status"] == "error"
            assert result["error_type"] == "invalid_input"
        
        def test_synthesize_text_too_long(self, voice_service):
            """Test speech synthesis with text that's too long"""
            # Create very long text
            long_text = "a" * 5000  # Assuming max length is 4096
            
            result = voice_service.synthesize_speech(long_text)
            
            assert result["status"] == "error"
            assert result["error_type"] == "text_too_long"
        
        def test_synthesize_different_formats(self, voice_service):
            """Test speech synthesis with different output formats"""
            text = "Hello, this is a test"
            voice = "alloy"
            
            for format_type in ["mp3", "opus", "aac", "flac"]:
                with patch.object(voice_service, '_create_fake_audio_file') as mock_create:
                    mock_create.return_value = f"fake_path.{format_type}"
                    
                    result = voice_service.synthesize_speech(
                        text, voice, output_format=format_type
                    )
                    
                    assert result["status"] == "success"

    class TestBase64Synthesis:
        """Test base64 speech synthesis functionality"""
        
        def test_synthesize_to_base64(self, voice_service):
            """Test speech synthesis to base64 format"""
            text = "Hello, this is a test"
            voice = "alloy"
            
            with patch.object(voice_service, '_create_fake_audio_file') as mock_create:
                mock_create.return_value = "fake_path.mp3"
                
                result = voice_service.synthesize_speech_to_base64(text, voice)
                
                assert result["status"] == "success"
                assert "audio_base64" in result
                assert "mime_type" in result
                assert "text_length" in result
                assert "audio_size" in result
        
        def test_synthesize_to_base64_with_metadata(self, voice_service):
            """Test speech synthesis to base64 with metadata"""
            text = "Hello, this is a test"
            voice = "alloy"
            
            with patch.object(voice_service, '_create_fake_audio_file') as mock_create:
                mock_create.return_value = "fake_path.mp3"
                
                result = voice_service.synthesize_speech_to_base64(
                    text, voice, include_metadata=True
                )
                
                assert result["status"] == "success"
                assert "created_at" in result
                assert "format" in result
                assert "model" in result
        
        def test_synthesize_to_base64_caching(self, voice_service):
            """Test base64 synthesis with caching"""
            text = "Hello, this is a test"
            voice = "alloy"
            
            with patch.object(voice_service, '_create_fake_audio_file') as mock_create:
                mock_create.return_value = "fake_path.mp3"
                
                # First synthesis
                result1 = voice_service.synthesize_speech_to_base64(text, voice, use_cache=True)
                
                # Second synthesis should use cache
                result2 = voice_service.synthesize_speech_to_base64(text, voice, use_cache=True)
                
                assert result1["status"] == "success"
                assert result2["status"] == "success"
                assert result2.get("cached") is True

    class TestErrorHandling:
        """Test enhanced error handling"""
        
        def test_tts_error_hierarchy(self):
            """Test TTS error exception hierarchy"""
            # Test that custom exceptions inherit from TTSError
            assert issubclass(AudioFormatError, TTSError)
            assert issubclass(VoiceNotFoundError, TTSError)
            assert issubclass(CacheError, TTSError)
        
        def test_synthesis_error_types(self, voice_service):
            """Test that synthesis errors include proper error types"""
            # Test invalid input error
            result = voice_service.synthesize_speech(None)
            assert result["status"] == "error"
            assert result["error_type"] == "invalid_input"
            
            # Test voice not supported error
            result = voice_service.synthesize_speech("test", "invalid_voice")
            assert result["status"] == "error"
            assert result["error_type"] == "voice_not_supported"
        
        def test_base64_synthesis_error_types(self, voice_service):
            """Test that base64 synthesis errors include proper error types"""
            # Test invalid input error
            result = voice_service.synthesize_speech_to_base64("")
            assert result["status"] == "error"
            assert result["error_type"] == "invalid_input"
            
            # Test voice not supported error
            result = voice_service.synthesize_speech_to_base64("test", "invalid_voice")
            assert result["status"] == "error"
            assert result["error_type"] == "voice_not_supported"

    class TestCacheEntrySerialization:
        """Test cache entry serialization and deserialization"""
        
        def test_cache_entry_to_dict(self, sample_cache_entry):
            """Test cache entry serialization to dictionary"""
            data = sample_cache_entry.to_dict()
            
            assert isinstance(data, dict)
            assert data["text_hash"] == sample_cache_entry.text_hash
            assert data["voice"] == sample_cache_entry.voice
            assert "audio_data" in data
            assert "created_at" in data
            assert "access_count" in data
        
        def test_cache_entry_from_dict(self, sample_cache_entry):
            """Test cache entry deserialization from dictionary"""
            data = sample_cache_entry.to_dict()
            restored_entry = TTSCacheEntry.from_dict(data)
            
            assert restored_entry.text_hash == sample_cache_entry.text_hash
            assert restored_entry.voice == sample_cache_entry.voice
            assert restored_entry.audio_data == sample_cache_entry.audio_data
            assert restored_entry.mime_type == sample_cache_entry.mime_type
            assert restored_entry.access_count == sample_cache_entry.access_count
        
        def test_cache_entry_roundtrip(self, sample_cache_entry):
            """Test cache entry serialization roundtrip"""
            # Serialize and deserialize
            data = sample_cache_entry.to_dict()
            restored_entry = TTSCacheEntry.from_dict(data)
            
            # Should be identical
            assert restored_entry.text_hash == sample_cache_entry.text_hash
            assert restored_entry.voice == sample_cache_entry.voice
            assert restored_entry.audio_data == sample_cache_entry.audio_data

    class TestAudioFormats:
        """Test audio format enumeration"""
        
        def test_audio_format_properties(self):
            """Test AudioFormat enum properties"""
            mp3_format = AudioFormat.MP3
            
            assert mp3_format.extension == "mp3"
            assert mp3_format.mime_type == "audio/mpeg"
            assert mp3_format.supported is True
            assert mp3_format.max_size == 25 * 1024 * 1024
        
        def test_supported_formats_dict(self):
            """Test supported formats dictionary"""
            from voice_service import SUPPORTED_AUDIO_FORMATS
            
            assert isinstance(SUPPORTED_AUDIO_FORMATS, dict)
            assert "mp3" in SUPPORTED_AUDIO_FORMATS
            assert "wav" in SUPPORTED_AUDIO_FORMATS
            assert "webm" in SUPPORTED_AUDIO_FORMATS
            
            # Check that all values are AudioFormat instances
            for format_name, format_obj in SUPPORTED_AUDIO_FORMATS.items():
                assert isinstance(format_obj, AudioFormat)
                assert format_obj.extension == format_name

    @pytest.fixture(autouse=True)
    def cleanup_temp_files(self):
        """Clean up temporary files after each test"""
        yield
        # Clean up any remaining temp files
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            if filename.startswith('voice_') or filename.startswith('tmp'):
                try:
                    os.unlink(os.path.join(temp_dir, filename))
                except:
                    pass
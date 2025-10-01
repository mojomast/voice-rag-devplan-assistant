#!/usr/bin/env python3
"""
Test script to verify enhanced STT functionality
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_stt_config():
    """Test STT configuration"""
    print("Testing STT Configuration...")
    
    try:
        from voice_service import STTConfig
        
        # Test default config
        config = STTConfig()
        assert config.streaming_chunk_size == 1024
        assert config.enable_language_detection is True
        assert config.enable_noise_reduction is True
        assert config.enable_audio_enhancement is True
        
        print("✅ STT Configuration test passed")
        return True
    except Exception as e:
        print(f"❌ STT Configuration test failed: {e}")
        return False

def test_voice_service_initialization():
    """Test VoiceService initialization with enhanced features"""
    print("Testing VoiceService Initialization...")
    
    try:
        from voice_service import VoiceService
        
        # Mock settings to avoid API key requirements
        import unittest.mock
        with unittest.mock.patch('voice_service.settings'):
            service = VoiceService()
            service.test_mode = True
            
            # Check enhanced attributes
            assert hasattr(service, 'stt_config')
            assert hasattr(service, '_streaming_buffers')
            assert hasattr(service, '_streaming_active')
            
            # Check STT config
            assert service.stt_config.enable_language_detection is True
            assert service.stt_config.enable_audio_enhancement is True
            
            print("✅ VoiceService Initialization test passed")
            return True
    except Exception as e:
        print(f"❌ VoiceService Initialization test failed: {e}")
        return False

def test_streaming_functionality():
    """Test streaming audio functionality"""
    print("Testing Streaming Functionality...")
    
    try:
        from voice_service import VoiceService, StreamingAudioChunk
        import unittest.mock
        
        with unittest.mock.patch('voice_service.settings'):
            service = VoiceService()
            service.test_mode = True
            
            # Test starting streaming session
            session_id = "test_session_123"
            result = service.start_streaming_session(session_id)
            
            assert result["status"] == "success"
            assert result["session_id"] == session_id
            assert session_id in service._streaming_active
            
            # Test adding streaming chunk
            audio_data = b"fake audio data"
            result = service.add_streaming_chunk(session_id, audio_data)
            
            assert result["status"] == "success"
            assert result["sequence_number"] == 0
            
            # Test cleanup
            service.cleanup_streaming_session(session_id)
            assert session_id not in service._streaming_active
            
            print("✅ Streaming Functionality test passed")
            return True
    except Exception as e:
        print(f"❌ Streaming Functionality test failed: {e}")
        return False

def test_audio_format_validation():
    """Test enhanced audio format validation"""
    print("Testing Audio Format Validation...")
    
    try:
        from voice_service import VoiceService, SUPPORTED_AUDIO_FORMATS
        import unittest.mock
        
        with unittest.mock.patch('voice_service.settings'):
            service = VoiceService()
            service.test_mode = True
            
            # Test supported formats
            supported_formats = ['mp3', 'wav', 'webm', 'ogg', 'm4a', 'flac']
            for fmt in supported_formats:
                assert fmt in SUPPORTED_AUDIO_FORMATS
            
            # Test validation with non-existent file
            result = service.validate_audio_format_enhanced("nonexistent.mp3")
            assert result["valid"] is False
            assert result["error_type"] == "file_not_found"
            
            print("✅ Audio Format Validation test passed")
            return True
    except Exception as e:
        print(f"❌ Audio Format Validation test failed: {e}")
        return False

def test_error_handling():
    """Test enhanced error handling"""
    print("Testing Error Handling...")
    
    try:
        from voice_service import (
            STTError, StreamingError, LanguageDetectionError,
            AudioEnhancementError, TranscriptionError, AudioProcessingError
        )
        
        # Test error hierarchy
        assert issubclass(StreamingError, STTError)
        assert issubclass(LanguageDetectionError, STTError)
        assert issubclass(AudioEnhancementError, STTError)
        assert issubclass(TranscriptionError, STTError)
        assert issubclass(AudioProcessingError, STTError)
        
        # Test error instantiation
        error = StreamingError("Test streaming error")
        assert str(error) == "Test streaming error"
        
        print("✅ Error Handling test passed")
        return True
    except Exception as e:
        print(f"❌ Error Handling test failed: {e}")
        return False

def test_data_structures():
    """Test enhanced data structures"""
    print("Testing Data Structures...")
    
    try:
        from voice_service import StreamingAudioChunk, TranscriptionResult
        from datetime import datetime
        
        # Test StreamingAudioChunk
        chunk = StreamingAudioChunk(
            data=b"audio data",
            timestamp=datetime.now(),
            sequence_number=1,
            is_final=True
        )
        
        assert chunk.data == b"audio data"
        assert chunk.sequence_number == 1
        assert chunk.is_final is True
        
        # Test to_dict method
        chunk_dict = chunk.to_dict()
        assert "data" in chunk_dict
        assert "timestamp" in chunk_dict
        assert "sequence_number" in chunk_dict
        assert "is_final" in chunk_dict
        
        # Test TranscriptionResult
        result = TranscriptionResult(
            text="Hello world",
            language="en",
            confidence=0.95,
            duration=2.0,
            processing_time=1.5
        )
        
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.confidence == 0.95
        
        # Test to_dict method
        result_dict = result.to_dict()
        assert "text" in result_dict
        assert "language" in result_dict
        assert "enhanced_features" in result_dict
        
        print("✅ Data Structures test passed")
        return True
    except Exception as e:
        print(f"❌ Data Structures test failed: {e}")
        return False

def test_processing_capabilities():
    """Test processing capabilities"""
    print("Testing Processing Capabilities...")
    
    try:
        from voice_service import VoiceService
        import unittest.mock
        
        with unittest.mock.patch('voice_service.settings'):
            service = VoiceService()
            service.test_mode = True
            
            capabilities = service.get_processing_capabilities()
            
            assert isinstance(capabilities, dict)
            assert capabilities["basic_transcription"] is True
            assert capabilities["text_to_speech"] is True
            assert capabilities["streaming_support"] is True
            assert capabilities["language_detection"] is True
            
            print("✅ Processing Capabilities test passed")
            return True
    except Exception as e:
        print(f"❌ Processing Capabilities test failed: {e}")
        return False

def test_configuration_integration():
    """Test configuration integration"""
    print("Testing Configuration Integration...")
    
    try:
        from voice_service import VoiceService
        import unittest.mock
        
        # Mock settings with STT configuration
        mock_settings = unittest.mock.MagicMock()
        mock_settings.STT_STREAMING_CHUNK_SIZE = 2048
        mock_settings.STT_ENABLE_LANGUAGE_DETECTION = False
        mock_settings.STT_ENABLE_NOISE_REDUCTION = True
        mock_settings.STT_SUPPORTED_LANGUAGES = "en,es,fr"
        
        with unittest.mock.patch('voice_service.settings', mock_settings):
            service = VoiceService()
            service.test_mode = True
            
            # Check that configuration is applied
            assert service.stt_config.streaming_chunk_size == 2048
            assert service.stt_config.enable_language_detection is False
            assert service.stt_config.enable_noise_reduction is True
            assert "en" in service.stt_config.supported_languages
            assert "es" in service.stt_config.supported_languages
            
        print("✅ Configuration Integration test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Enhanced STT Functionality Test Suite")
    print("=" * 60)
    
    tests = [
        test_stt_config,
        test_voice_service_initialization,
        test_streaming_functionality,
        test_audio_format_validation,
        test_error_handling,
        test_data_structures,
        test_processing_capabilities,
        test_configuration_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhanced STT functionality tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
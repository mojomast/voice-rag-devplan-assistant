import pytest
import tempfile
import os
import sys
import json
import base64
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from voice_service import (
    VoiceService, 
    STTConfig,
    StreamingAudioChunk,
    TranscriptionResult,
    STTError,
    StreamingError,
    LanguageDetectionError,
    AudioEnhancementError,
    TranscriptionError,
    AudioProcessingError
)

class TestEnhancedSTT:
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
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Write a simple WAV header and some fake audio data
            f.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00')
            f.write(b'\x00' * 1000)  # Add some audio data
            return f.name

    class TestSTTConfig:
        """Test STT configuration"""
        
        def test_stt_config_defaults(self):
            """Test STTConfig default values"""
            config = STTConfig()
            
            assert config.streaming_chunk_size == 1024
            assert config.streaming_buffer_size == 8192
            assert config.streaming_max_duration == 300
            assert config.enable_language_detection is True
            assert config.language_detection_confidence_threshold == 0.7
            assert config.enable_noise_reduction is True
            assert config.enable_audio_enhancement is True
            assert config.enable_normalization is True
            assert config.enable_spectral_gating is True
            assert config.transcription_temperature == 0.2
            assert config.enable_word_timestamps is True
            assert config.enable_segment_timestamps is True
            assert config.max_audio_length == 600
            assert config.min_audio_quality_threshold == 0.3
            assert config.enable_quality_analysis is True
        
        def test_stt_config_from_settings(self, voice_service):
            """Test STTConfig creation from settings"""
            config = voice_service.stt_config
            
            assert isinstance(config, STTConfig)
            assert config.streaming_chunk_size > 0
            assert config.streaming_buffer_size > 0
            assert config.streaming_max_duration > 0

    class TestStreamingAudio:
        """Test streaming audio functionality"""
        
        def test_start_streaming_session(self, voice_service):
            """Test starting a streaming session"""
            session_id = "test_session_123"
            
            result = voice_service.start_streaming_session(session_id)
            
            assert result["status"] == "success"
            assert result["session_id"] == session_id
            assert "config" in result
            assert session_id in voice_service._streaming_active
            assert session_id in voice_service._streaming_buffers
        
        def test_start_duplicate_session(self, voice_service):
            """Test starting a duplicate streaming session"""
            session_id = "test_session_123"
            
            # Start first session
            voice_service.start_streaming_session(session_id)
            
            # Try to start duplicate
            result = voice_service.start_streaming_session(session_id)
            
            assert result["status"] == "error"
            assert result["error_type"] == "session_exists"
        
        def test_add_streaming_chunk(self, voice_service):
            """Test adding audio chunks to streaming session"""
            session_id = "test_session_123"
            audio_data = b"fake audio data"
            
            # Start session
            voice_service.start_streaming_session(session_id)
            
            # Add chunk
            result = voice_service.add_streaming_chunk(session_id, audio_data)
            
            assert result["status"] == "success"
            assert result["sequence_number"] == 0
            assert "timestamp" in result
        
        def test_add_chunk_to_nonexistent_session(self, voice_service):
            """Test adding chunk to non-existent session"""
            result = voice_service.add_streaming_chunk("nonexistent", b"data")
            
            assert result["status"] == "error"
            assert result["error_type"] == "session_not_found"
        
        def test_add_final_chunk(self, voice_service):
            """Test adding final chunk to session"""
            session_id = "test_session_123"
            audio_data = b"final audio data"
            
            # Start session
            voice_service.start_streaming_session(session_id)
            
            # Add final chunk
            result = voice_service.add_streaming_chunk(session_id, audio_data, is_final=True)
            
            assert result["status"] == "success"
            assert voice_service._streaming_active[session_id] is False
        
        def test_cleanup_streaming_session(self, voice_service):
            """Test cleaning up streaming session"""
            session_id = "test_session_123"
            
            # Start session
            voice_service.start_streaming_session(session_id)
            
            # Cleanup
            voice_service.cleanup_streaming_session(session_id)
            
            assert session_id not in voice_service._streaming_active
            assert session_id not in voice_service._streaming_buffers
        
        @pytest.mark.asyncio
        async def test_process_streaming_session(self, voice_service):
            """Test processing streaming session"""
            session_id = "test_session_123"
            
            # Start session
            voice_service.start_streaming_session(session_id)
            
            # Add some chunks
            voice_service.add_streaming_chunk(session_id, b"audio1")
            voice_service.add_streaming_chunk(session_id, b"audio2", is_final=True)
            
            # Process session
            results = []
            async for result in voice_service.process_streaming_session(session_id):
                results.append(result)
            
            assert len(results) > 0
            assert results[0]["session_id"] == session_id

    class TestEnhancedTranscription:
        """Test enhanced transcription functionality"""
        
        @patch('voice_service.VoiceService.transcribe_audio')
        @patch('voice_service.VoiceService.detect_language_enhanced')
        @patch('voice_service.VoiceService.analyze_audio_characteristics')
        @patch('voice_service.VoiceService.enhance_audio_quality')
        def test_transcribe_audio_enhanced_success(self, mock_enhance, mock_analyze, 
                                                  mock_detect, mock_transcribe, voice_service, sample_audio_file):
            """Test successful enhanced transcription"""
            # Setup mocks
            mock_enhance.return_value = {
                "status": "success",
                "enhanced_file": sample_audio_file + "_enhanced"
            }
            mock_detect.return_value = {
                "status": "success",
                "language": "en",
                "confidence": 0.95
            }
            mock_analyze.return_value = {
                "status": "success",
                "quality_metrics": {"snr_estimate_db": 20.0}
            }
            mock_transcribe.return_value = {
                "status": "success",
                "text": "Hello world",
                "language": "en",
                "confidence": 0.9,
                "duration": 2.0,
                "segments": []
            }
            
            # Test enhanced transcription
            result = voice_service.transcribe_audio_enhanced(sample_audio_file)
            
            assert result["status"] == "success"
            assert result["text"] == "Hello world"
            assert result["language"] == "en"
            assert result["enhanced_features"]["audio_enhanced"] is True
            assert result["enhanced_features"]["language_auto_detected"] is True
            assert result["enhanced_features"]["quality_analyzed"] is True
            assert "processing_time" in result
        
        def test_transcribe_audio_enhanced_invalid_input(self, voice_service):
            """Test enhanced transcription with invalid input"""
            result = voice_service.transcribe_audio_enhanced(None)
            
            assert result["status"] == "error"
            assert result["error_type"] == "invalid_input"
            assert "processing_time" in result
        
        def test_transcribe_audio_enhanced_file_not_found(self, voice_service):
            """Test enhanced transcription with non-existent file"""
            result = voice_service.transcribe_audio_enhanced("nonexistent.wav")
            
            assert result["status"] == "error"
            assert result["error_type"] == "file_not_found"

    class TestLanguageDetection:
        """Test enhanced language detection"""
        
        @patch('voice_service.VoiceService.validate_audio_format_enhanced')
        @patch('voice_service.VoiceService.enhance_audio_quality')
        def test_detect_language_enhanced_success(self, mock_enhance, mock_validate, voice_service, sample_audio_file):
            """Test successful language detection"""
            # Setup mocks
            mock_validate.return_value = {"valid": True}
            mock_enhance.return_value = {"status": "success", "enhanced_file": sample_audio_file}
            
            # Mock OpenAI client
            mock_transcript = Mock()
            mock_transcript.language = "en"
            mock_transcript.confidence = 0.95
            mock_transcript.segments = []
            
            voice_service.client = Mock()
            voice_service.client.audio.transcriptions.create.return_value = mock_transcript
            
            result = voice_service.detect_language_enhanced(sample_audio_file)
            
            assert result["status"] == "success"
            assert result["language"] == "en"
            assert result["confidence"] == 0.95
            assert result["supported_language"] is True
            assert "processing_time" in result
        
        def test_detect_language_enhanced_invalid_file(self, voice_service):
            """Test language detection with invalid file"""
            result = voice_service.detect_language_enhanced("nonexistent.wav")
            
            assert result["status"] == "error"
            assert result["language"] == "unknown"
            assert result["confidence"] == 0.0
            assert result["error_type"] == "file_not_found"
        
        def test_analyze_language_consistency(self, voice_service):
            """Test language consistency analysis"""
            segments = [
                Mock(text="hello world"),
                Mock(text="how are you"),
                Mock(text="goodbye")
            ]
            
            result = voice_service._analyze_language_consistency(segments)
            
            assert "consistency_score" in result
            assert "language_changes" in result
            assert "detected_languages" in result
        
        def test_detect_text_language_heuristic(self, voice_service):
            """Test text language detection heuristic"""
            # Test English
            result = voice_service._detect_text_language_heuristic("hello world")
            assert result == "en"
            
            # Test Spanish
            result = voice_service._detect_text_language_heuristic("hola mundo")
            assert result == "es"
            
            # Test French
            result = voice_service._detect_text_language_heuristic("bonjour le monde")
            assert result == "fr"
            
            # Test unknown
            result = voice_service._detect_text_language_heuristic("xyz123")
            assert result is None

    class TestAudioEnhancement:
        """Test audio enhancement functionality"""
        
        @patch('voice_service.AUDIO_PROCESSING_AVAILABLE', True)
        @patch('voice_service.librosa.load')
        @patch('voice_service.sf.write')
        def test_enhance_audio_quality_success(self, mock_sf_write, mock_librosa_load, voice_service, sample_audio_file):
            """Test successful audio enhancement"""
            # Setup mocks
            mock_audio_data = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_librosa_load.return_value = (mock_audio_data, 16000)
            
            result = voice_service.enhance_audio_quality(sample_audio_file)
            
            assert result["status"] == "success"
            assert result["original_file"] == sample_audio_file
            assert "enhanced_file" in result
            assert "enhancements_applied" in result
            assert "original_quality" in result
            assert "enhanced_quality" in result
            assert "quality_improvement" in result
        
        @patch('voice_service.AUDIO_PROCESSING_AVAILABLE', False)
        def test_enhance_audio_quality_unavailable(self, voice_service, sample_audio_file):
            """Test audio enhancement when processing is unavailable"""
            result = voice_service.enhance_audio_quality(sample_audio_file)
            
            assert result["status"] == "error"
            assert result["error_type"] == "processing_unavailable"
        
        def test_load_audio_with_format_handling(self, voice_service):
            """Test audio loading with format handling"""
            with patch('voice_service.librosa.load') as mock_load:
                mock_load.return_value = ([0.1, 0.2, 0.3], 16000)
                
                audio_data, sample_rate = voice_service._load_audio_with_format_handling("test.wav")
                
                assert len(audio_data) == 3
                assert sample_rate == 16000
                mock_load.assert_called_once()
        
        def test_apply_normalization(self, voice_service):
            """Test audio normalization"""
            import numpy as np
            
            # Test with audio that needs normalization
            audio_data = np.array([0.5, 1.0, 0.3])
            normalized = voice_service._apply_normalization(audio_data)
            
            assert len(normalized) == len(audio_data)
            assert np.max(np.abs(normalized)) <= 1.0
        
        def test_apply_spectral_gating(self, voice_service):
            """Test spectral gating"""
            import numpy as np
            
            with patch('voice_service.librosa.stft') as mock_stft, \
                 patch('voice_service.librosa.istft') as mock_istft:
                
                mock_stft.return_value = np.array([[1+1j, 2+2j], [3+3j, 4+4j]])
                mock_istft.return_value = np.array([0.1, 0.2, 0.3])
                
                audio_data = np.array([0.1, 0.2, 0.3])
                result = voice_service._apply_spectral_gating(audio_data, 16000)
                
                assert len(result) == len(audio_data)
        
        def test_calculate_quality_improvement(self, voice_service):
            """Test quality improvement calculation"""
            original = {"snr_estimate": 10.0, "dynamic_range_db": 20.0}
            enhanced = {"snr_estimate": 15.0, "dynamic_range_db": 25.0}
            
            improvement = voice_service._calculate_quality_improvement(original, enhanced)
            
            assert improvement["snr_improvement_db"] == 5.0
            assert improvement["dynamic_range_improvement_db"] == 5.0
            assert "overall_improvement" in improvement

    class TestErrorHandling:
        """Test enhanced error handling"""
        
        def test_stt_error_hierarchy(self):
            """Test STT error exception hierarchy"""
            assert issubclass(StreamingError, STTError)
            assert issubclass(LanguageDetectionError, STTError)
            assert issubclass(AudioEnhancementError, STTError)
            assert issubclass(TranscriptionError, STTError)
            assert issubclass(AudioProcessingError, STTError)
        
        def test_streaming_error_handling(self, voice_service):
            """Test streaming error handling"""
            # Test adding chunk to non-existent session
            result = voice_service.add_streaming_chunk("nonexistent", b"data")
            assert result["status"] == "error"
            assert result["error_type"] == "session_not_found"
        
        def test_language_detection_error_handling(self, voice_service):
            """Test language detection error handling"""
            result = voice_service.detect_language_enhanced("nonexistent.wav")
            assert result["status"] == "error"
            assert result["error_type"] == "file_not_found"
        
        def test_audio_enhancement_error_handling(self, voice_service):
            """Test audio enhancement error handling"""
            with patch('voice_service.AUDIO_PROCESSING_AVAILABLE', False):
                result = voice_service.enhance_audio_quality("test.wav")
                assert result["status"] == "error"
                assert result["error_type"] == "processing_unavailable"

    class TestDataStructures:
        """Test data structures"""
        
        def test_streaming_audio_chunk(self):
            """Test StreamingAudioChunk dataclass"""
            chunk = StreamingAudioChunk(
                data=b"audio data",
                timestamp=datetime.now(),
                sequence_number=1,
                is_final=True
            )
            
            assert chunk.data == b"audio data"
            assert chunk.sequence_number == 1
            assert chunk.is_final is True
            
            # Test to_dict
            chunk_dict = chunk.to_dict()
            assert "data" in chunk_dict
            assert "timestamp" in chunk_dict
            assert "sequence_number" in chunk_dict
            assert "is_final" in chunk_dict
            assert "size" in chunk_dict
        
        def test_transcription_result(self):
            """Test TranscriptionResult dataclass"""
            result = TranscriptionResult(
                text="Hello world",
                language="en",
                confidence=0.95,
                duration=2.0,
                segments=[],
                detected_language="en",
                language_confidence=0.9,
                processing_time=1.5
            )
            
            assert result.text == "Hello world"
            assert result.language == "en"
            assert result.confidence == 0.95
            
            # Test to_dict
            result_dict = result.to_dict()
            assert "text" in result_dict
            assert "language" in result_dict
            assert "confidence" in result_dict
            assert "enhanced_features" in result_dict

    class TestProcessingCapabilities:
        """Test processing capabilities"""
        
        def test_get_processing_capabilities(self, voice_service):
            """Test getting processing capabilities"""
            capabilities = voice_service.get_processing_capabilities()
            
            assert isinstance(capabilities, dict)
            assert capabilities["basic_transcription"] is True
            assert capabilities["text_to_speech"] is True
            assert capabilities["streaming_support"] is True
            assert capabilities["language_detection"] is True
            assert "noise_reduction" in capabilities
            assert "audio_enhancement" in capabilities
            assert "quality_analysis" in capabilities

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
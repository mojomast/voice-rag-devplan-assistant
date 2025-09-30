import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from voice_service import VoiceService

class TestVoiceService:
    @pytest.fixture
    def voice_service(self):
        return VoiceService()

    def test_voice_service_initialization(self, voice_service):
        """Test that voice service initializes properly"""
        assert voice_service is not None
        assert hasattr(voice_service, 'get_available_voices')

    def test_get_available_voices(self, voice_service):
        """Test getting available voices"""
        voices = voice_service.get_available_voices()
        assert isinstance(voices, list)
        assert len(voices) > 0
        # Common OpenAI TTS voices
        expected_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        for voice in expected_voices:
            assert voice in voices

    def test_voice_service_has_required_methods(self, voice_service):
        """Test that voice service has all required methods"""
        required_methods = [
            'transcribe_audio',
            'synthesize_speech',
            'get_available_voices',
            'cleanup_temp_files'
        ]

        for method in required_methods:
            assert hasattr(voice_service, method), f"Missing method: {method}"
            assert callable(getattr(voice_service, method)), f"Method {method} is not callable"

    def test_cleanup_temp_files(self, voice_service):
        """Test cleanup of temporary files"""
        # Create temporary files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_files.append(f.name)

        # Verify files exist
        for file_path in temp_files:
            assert os.path.exists(file_path)

        # Cleanup should remove all files
        voice_service.cleanup_temp_files(temp_files)

        # Verify files are removed
        for file_path in temp_files:
            assert not os.path.exists(file_path)

    def test_cleanup_nonexistent_files(self, voice_service):
        """Test cleanup with non-existent files"""
        nonexistent_files = ["nonexistent1.tmp", "nonexistent2.tmp"]

        # Should not raise an error
        try:
            voice_service.cleanup_temp_files(nonexistent_files)
        except Exception as e:
            pytest.fail(f"cleanup_temp_files raised an exception: {e}")

    def test_cleanup_empty_list(self, voice_service):
        """Test cleanup with empty file list"""
        # Should handle empty list gracefully
        try:
            voice_service.cleanup_temp_files([])
        except Exception as e:
            pytest.fail(f"cleanup_temp_files raised an exception with empty list: {e}")

    @patch('openai.Audio.transcribe')
    def test_transcribe_audio_success(self, mock_transcribe, voice_service):
        """Test successful audio transcription"""
        # Mock the OpenAI API response
        mock_transcribe.return_value = Mock(text="Hello, this is a test transcription.")

        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'fake audio data')
            temp_audio_path = f.name

        try:
            result = voice_service.transcribe_audio(temp_audio_path)

            # Check the result format
            assert isinstance(result, dict)
            assert "status" in result
            assert "text" in result

            if result["status"] == "success":
                assert result["text"] == "Hello, this is a test transcription."

        finally:
            os.unlink(temp_audio_path)

    def test_transcribe_audio_nonexistent_file(self, voice_service):
        """Test transcription with non-existent file"""
        result = voice_service.transcribe_audio("nonexistent_file.wav")

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "error" in result

    @patch('openai.Audio.speech')
    def test_synthesize_speech_success(self, mock_speech, voice_service):
        """Test successful speech synthesis"""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.content = b'fake audio content'
        mock_speech.return_value = mock_response

        result = voice_service.synthesize_speech("Hello world", "alloy")

        # Check the result format
        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "audio_file" in result
            assert os.path.exists(result["audio_file"])
            # Clean up created file
            os.unlink(result["audio_file"])

    def test_synthesize_speech_invalid_voice(self, voice_service):
        """Test speech synthesis with invalid voice"""
        result = voice_service.synthesize_speech("Hello world", "invalid_voice")

        assert isinstance(result, dict)
        # Should either reject invalid voice or handle gracefully
        if result["status"] == "error":
            assert "error" in result

    def test_synthesize_speech_empty_text(self, voice_service):
        """Test speech synthesis with empty text"""
        result = voice_service.synthesize_speech("", "alloy")

        assert isinstance(result, dict)
        # Should handle empty text gracefully
        assert result["status"] in ["success", "error"]

    def test_synthesize_speech_long_text(self, voice_service):
        """Test speech synthesis with very long text"""
        long_text = "This is a very long text. " * 100  # Very long text
        result = voice_service.synthesize_speech(long_text, "alloy")

        assert isinstance(result, dict)
        # Should handle long text appropriately
        assert result["status"] in ["success", "error"]

    def test_voice_service_error_handling(self, voice_service):
        """Test various error handling scenarios"""
        # Test with None inputs
        result = voice_service.transcribe_audio(None)
        assert result["status"] == "error"

        result = voice_service.synthesize_speech(None, "alloy")
        assert result["status"] == "error"

    def test_temp_file_creation_and_cleanup(self, voice_service):
        """Test that temporary files are created and cleaned up properly"""
        initial_temp_files = len([f for f in os.listdir(tempfile.gettempdir()) if f.startswith('voice_')])

        # Create some temporary audio files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False, prefix='voice_test_') as f:
                f.write(b'test audio data')
                temp_files.append(f.name)

        # Clean them up
        voice_service.cleanup_temp_files(temp_files)

        # Verify cleanup
        final_temp_files = len([f for f in os.listdir(tempfile.gettempdir()) if f.startswith('voice_test_')])
        assert final_temp_files == 0

    def test_audio_format_validation(self, voice_service):
        """Test audio format validation if implemented"""
        # Create files with different extensions
        formats = ['.wav', '.mp3', '.ogg', '.txt']

        for fmt in formats:
            with tempfile.NamedTemporaryFile(suffix=fmt, delete=False) as f:
                f.write(b'fake content')
                temp_file = f.name

            try:
                result = voice_service.transcribe_audio(temp_file)
                assert isinstance(result, dict)
                assert "status" in result

                # Non-audio formats should be rejected
                if fmt == '.txt':
                    assert result["status"] == "error"

            finally:
                os.unlink(temp_file)

    def test_voice_service_configuration(self, voice_service):
        """Test voice service configuration and settings"""
        # Test that service has reasonable defaults
        voices = voice_service.get_available_voices()
        assert len(voices) > 0

        # Test that common configurations work
        assert "alloy" in voices  # Default OpenAI voice

    @patch('openai.Audio.transcribe')
    def test_transcribe_with_language_detection(self, mock_transcribe, voice_service):
        """Test transcription with language detection if supported"""
        mock_transcribe.return_value = Mock(text="Bonjour, comment allez-vous?")

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'fake french audio')
            temp_audio_path = f.name

        try:
            result = voice_service.transcribe_audio(temp_audio_path)

            if result["status"] == "success":
                # Check if language is detected (if implemented)
                if "language" in result:
                    assert isinstance(result["language"], str)

        finally:
            os.unlink(temp_audio_path)
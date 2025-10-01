"""
Pytest configuration and fixtures for voice component tests

This module provides common fixtures and configuration for testing
voice UI components.
"""

import pytest
import streamlit as st
import sys
import os
from unittest.mock import Mock, patch
import base64
import json

# Add frontend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))

# Mock streamlit for testing
@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock streamlit functions for testing"""
    
    # Mock all streamlit functions that might be called
    mocks = {
        'markdown': Mock(),
        'info': Mock(),
        'success': Mock(),
        'warning': Mock(),
        'error': Mock(),
        'spinner': Mock(),
        'button': Mock(return_value=False),
        'selectbox': Mock(return_value="alloy"),
        'slider': Mock(return_value=1.0),
        'checkbox': Mock(return_value=True),
        'text_area': Mock(return_value="test text"),
        'text_input': Mock(return_value="test input"),
        'file_uploader': Mock(return_value=None),
        'columns': Mock(return_value=[Mock(), Mock()]),
        'metric': Mock(),
        'progress': Mock(),
        'balloons': Mock(),
        'rerun': Mock(),
        'session_state': {},
        'experimental_get_query_params': Mock(return_value={}),
        'components': Mock(),
        'cache_data': Mock(),
        'cache_resource': Mock(),
    }
    
    # Add v1 components
    mocks['components'].v1 = Mock()
    mocks['components'].v1.html = Mock()
    
    # Patch all streamlit functions
    for name, mock in mocks.items():
        patcher = patch(f'streamlit.{name}', mock)
        patcher.start()
        
    yield mocks
    
    # Cleanup
    for name in mocks:
        if f'streamlit.{name}' in sys.modules:
            del sys.modules[f'streamlit.{name}']


@pytest.fixture
def mock_api_responses():
    """Fixture providing mock API responses"""
    
    class MockAPI:
        def __init__(self):
            self.voices_response = {
                "voices": [
                    {"name": "alloy", "description": "Balanced, neutral voice"},
                    {"name": "echo", "description": "Male voice with clarity"},
                    {"name": "fable", "description": "Expressive, storytelling voice"},
                    {"name": "onyx", "description": "Deep, authoritative voice"},
                    {"name": "nova", "description": "Youthful, energetic voice"},
                    {"name": "shimmer", "description": "Soft, pleasant voice"}
                ]
            }
            
            self.capabilities_response = {
                "capabilities": {
                    "text_to_speech": True,
                    "speech_to_text": True,
                    "noise_reduction": True,
                    "audio_enhancement": True,
                    "base64_processing": True,
                    "streaming_support": True,
                    "language_detection": True
                },
                "configuration": {
                    "tts_model": "tts-1",
                    "whisper_model": "whisper-1",
                    "default_voice": "alloy",
                    "cache_enabled": True,
                    "cache_max_size": 100,
                    "cache_ttl": 604800,
                    "max_text_length": 4096,
                    "default_format": "mp3",
                    "supported_formats": ["mp3", "opus", "aac", "flac"],
                    "test_mode": False
                },
                "available_voices": self.voices_response["voices"]
            }
            
            self.tts_response = {
                "status": "success",
                "audio_base64": base64.b64encode(b"test audio data").decode('utf-8'),
                "mime_type": "audio/mpeg",
                "voice": "alloy",
                "text_length": 15,
                "audio_size": 1024
            }
            
            self.stt_response = {
                "text": "Hello world",
                "language": "en",
                "duration": 2.5,
                "confidence": 0.95,
                "segments": [],
                "status": "success"
            }
            
            self.cache_stats_response = {
                "total_entries": 5,
                "cache_size_bytes": 51200,
                "expired_entries": 1,
                "hit_rate": 85.5,
                "entries": {
                    "entry1": {
                        "voice": "alloy",
                        "text_length": 15,
                        "created_at": "2023-01-01T00:00:00",
                        "access_count": 3,
                        "last_accessed": "2023-01-01T12:00:00",
                        "mime_type": "audio/mpeg"
                    }
                }
            }
    
    return MockAPI()


@pytest.fixture
def mock_audio_data():
    """Fixture providing mock audio data"""
    return {
        "audio_base64": base64.b64encode(b"test audio data for testing").decode('utf-8'),
        "mime_type": "audio/mpeg",
        "voice": "alloy",
        "text_length": 25,
        "audio_size": 2048,
        "duration": "2.5s",
        "filename": "test_audio.mp3"
    }


@pytest.fixture
def mock_voice_settings():
    """Fixture providing mock voice settings"""
    from components.voice_settings_panel import VoiceSettings
    
    return VoiceSettings(
        tts_voice="echo",
        tts_speed=1.5,
        tts_format="mp3",
        enable_caching=True,
        stt_language="es",
        enable_language_detection=True,
        enable_noise_reduction=True,
        enable_audio_enhancement=True,
        recording_format="webm",
        recording_quality="high",
        auto_transcribe=True,
        auto_play_response=False,
        theme="light",
        show_waveform=True,
        show_controls=True,
        keyboard_shortcuts=True
    )


@pytest.fixture
def mock_requests():
    """Fixture providing mock requests"""
    
    class MockRequests:
        def __init__(self):
            self.get = Mock()
            self.post = Mock()
            self.delete = Mock()
            self.put = Mock()
            
            # Setup default successful responses
            self.setup_default_responses()
        
        def setup_default_responses(self):
            """Setup default successful responses"""
            
            # GET responses
            get_response = Mock()
            get_response.status_code = 200
            get_response.json.return_value = {
                "voices": [
                    {"name": "alloy", "description": "Balanced voice"}
                ]
            }
            self.get.return_value = get_response
            
            # POST responses
            post_response = Mock()
            post_response.status_code = 200
            post_response.json.return_value = {
                "status": "success",
                "audio_base64": base64.b64encode(b"test audio").decode('utf-8')
            }
            self.post.return_value = post_response
            
            # DELETE responses
            delete_response = Mock()
            delete_response.status_code = 200
            delete_response.json.return_value = {"message": "Deleted successfully"}
            self.delete.return_value = delete_response
        
        def setup_error_response(self, method='get', status_code=500, error_msg="Internal Server Error"):
            """Setup error response"""
            
            response = Mock()
            response.status_code = status_code
            response.text = error_msg
            response.json.return_value = {"error": error_msg}
            
            if method == 'get':
                self.get.return_value = response
            elif method == 'post':
                self.post.return_value = response
            elif method == 'delete':
                self.delete.return_value = response
        
        def setup_network_error(self, method='get'):
            """Setup network error"""
            
            if method == 'get':
                self.get.side_effect = Exception("Network error")
            elif method == 'post':
                self.post.side_effect = Exception("Network error")
            elif method == 'delete':
                self.delete.side_effect = Exception("Network error")
    
    return MockRequests()


@pytest.fixture
def temp_audio_file():
    """Fixture providing a temporary audio file"""
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        tmp_file.write(b"fake audio data")
        tmp_file_path = tmp_file.name
    
    yield tmp_file_path
    
    # Cleanup
    os.unlink(tmp_file_path)


@pytest.fixture
def mock_session_state():
    """Fixture providing mock session state"""
    return {}


# Test configuration
def pytest_configure(config):
    """Configure pytest"""
    
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    
    # Add markers based on test location
    for item in item:
        # Mark tests in specific files
        if "test_voice_components.py" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        
        # Mark network tests
        if "network" in item.name.lower() or "api" in item.name.lower():
            item.add_marker(pytest.mark.network)


# Custom helpers
class StreamlitTestHelper:
    """Helper class for streamlit testing"""
    
    @staticmethod
    def mock_session_state():
        """Create a mock session state"""
        return {}
    
    @staticmethod
    def create_mock_columns(count=2):
        """Create mock columns"""
        return [Mock() for _ in range(count)]
    
    @staticmethod
    def assert_streamlit_called(mocks, function_name, *args, **kwargs):
        """Assert that a streamlit function was called"""
        if function_name in mocks:
            mocks[function_name].assert_called_with(*args, **kwargs)
    
    @staticmethod
    def create_audio_data(size=1024, mime_type="audio/mpeg"):
        """Create test audio data"""
        return {
            "audio_base64": base64.b64encode(b"x" * size).decode('utf-8'),
            "mime_type": mime_type,
            "audio_size": size
        }


@pytest.fixture
def streamlit_helper():
    """Fixture providing streamlit test helper"""
    return StreamlitTestHelper()


# Database and file system fixtures
@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture providing test data directory"""
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture
def sample_audio_file(test_data_dir):
    """Fixture providing sample audio file path"""
    return os.path.join(test_data_dir, "sample_audio.mp3")


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment"""
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "STREAMLIT_SERVER_HEADLESS" in os.environ:
        del os.environ["STREAMLIT_SERVER_HEADLESS"]


# Logging configuration
@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for tests"""
    import logging
    
    # Set logging level
    logging.basicConfig(level=logging.WARNING)
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
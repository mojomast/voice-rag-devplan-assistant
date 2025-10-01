"""
Tests for voice UI components

This module contains comprehensive tests for all voice UI components,
including unit tests, integration tests, and end-to-end tests.
"""

import pytest
import streamlit as st
import streamlit.testing.v1 as sttest
from unittest.mock import Mock, patch, MagicMock
import json
import base64
import time
from typing import Dict, Any

# Import voice components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))

from components.voice_playback import VoicePlaybackComponent
from components.voice_settings_panel import VoiceSettingsPanel, VoiceSettings
from components.voice_error_handler import VoiceErrorHandler, ErrorCategory, ErrorSeverity
from components.responsive_voice_ui import ResponsiveVoiceUI


class TestVoicePlaybackComponent:
    """Test cases for VoicePlaybackComponent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_url = "http://test-api:8000"
        self.component = VoicePlaybackComponent(self.api_url)
        
    def test_component_initialization(self):
        """Test component initialization"""
        assert self.component.api_url == self.api_url
        assert self.component.playback_history == []
        
    def test_render_voice_playback_with_audio_data(self):
        """Test rendering with audio data"""
        audio_data = {
            "audio_base64": "dGVzdCBhdWRpbyBkYXRh",  # base64 encoded "test audio data"
            "mime_type": "audio/mpeg",
            "voice": "alloy",
            "text_length": 15,
            "audio_size": 1024
        }
        
        result = self.component.render_voice_playback(
            audio_data=audio_data,
            auto_play=False,
            show_controls=True,
            height=200,
            theme="light"
        )
        
        assert result['component_loaded'] is True
        assert result['audio_data'] == audio_data
        assert result['auto_play'] is False
        assert result['theme'] == "light"
        
    def test_render_voice_playback_without_audio_data(self):
        """Test rendering without audio data"""
        result = self.component.render_voice_playback()
        
        assert result['component_loaded'] is True
        assert result['audio_data'] is None
        
    @patch('requests.post')
    def test_synthesize_and_play_success(self, mock_post):
        """Test successful speech synthesis"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "audio_base64": "dGVzdCBhdWRpbyBkYXRh",
            "mime_type": "audio/mpeg",
            "voice": "alloy",
            "text_length": 15,
            "audio_size": 1024
        }
        mock_post.return_value = mock_response
        
        result = self.component.synthesize_and_play(
            text="Hello world",
            voice="alloy",
            auto_play=True
        )
        
        assert result['status'] == 'success'
        assert result['audio_data'] is not None
        assert result['text'] == "Hello world"
        assert result['voice'] == "alloy"
        
    @patch('requests.post')
    def test_synthesize_and_play_api_error(self, mock_post):
        """Test speech synthesis with API error"""
        # Mock API error response
        mock_post.side_effect = Exception("API Error")
        
        result = self.component.synthesize_and_play(
            text="Hello world",
            voice="alloy"
        )
        
        assert result['status'] == 'error'
        assert 'API Error' in result['error']
        assert result['audio_data'] is None
        
    def test_synthesize_and_play_empty_text(self):
        """Test speech synthesis with empty text"""
        result = self.component.synthesize_and_play(text="")
        
        assert result['status'] == 'error'
        assert 'Text is required' in result['error']
        assert result['audio_data'] is None
        
    def test_render_playback_history_empty(self):
        """Test rendering empty playback history"""
        with patch('streamlit.info') as mock_info:
            self.component.render_playback_history()
            mock_info.assert_called_once_with("No playback history yet")
            
    def test_render_playback_history_with_items(self):
        """Test rendering playback history with items"""
        # Add some history items
        self.component.playback_history = [
            {
                "timestamp": time.time(),
                "text": "Hello",
                "voice": "alloy",
                "audio_data": {"audio_base64": "dGVzdA=="}
            }
        ]
        
        with patch('streamlit.subheader') as mock_subheader:
            self.component.render_playback_history()
            mock_subheader.assert_called_once_with("📚 Playback History")
            
    def test_render_audio_analyzer_with_data(self):
        """Test audio analyzer with data"""
        audio_data = {
            "mime_type": "audio/mpeg",
            "voice": "alloy",
            "text_length": 15,
            "audio_size": 1024
        }
        
        with patch('streamlit.subheader') as mock_subheader:
            self.component.render_audio_analyzer(audio_data)
            mock_subheader.assert_called_once_with("📊 Audio Analysis")
            
    def test_render_audio_analyzer_without_data(self):
        """Test audio analyzer without data"""
        # Should not raise any errors
        self.component.render_audio_analyzer(None)


class TestVoiceSettingsPanel:
    """Test cases for VoiceSettingsPanel"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_url = "http://test-api:8000"
        self.panel = VoiceSettingsPanel(self.api_url)
        
    def test_panel_initialization(self):
        """Test panel initialization"""
        assert self.panel.api_url == self.api_url
        assert self.panel.available_voices == []
        assert len(self.panel.supported_languages) > 0
        assert len(self.panel.supported_formats) > 0
        
    @patch('requests.get')
    def test_load_available_voices_success(self, mock_get):
        """Test successful voice loading"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {"name": "alloy", "description": "Balanced voice"},
                {"name": "echo", "description": "Male voice"}
            ]
        }
        mock_get.return_value = mock_response
        
        voices = self.panel.load_available_voices()
        
        assert len(voices) == 2
        assert voices[0]["name"] == "alloy"
        assert self.panel.available_voices == voices
        
    @patch('requests.get')
    def test_load_available_voices_error(self, mock_get):
        """Test voice loading with error"""
        mock_get.side_effect = Exception("Network error")
        
        with patch('streamlit.error') as mock_error:
            voices = self.panel.load_available_voices()
            assert voices == []
            mock_error.assert_called()
            
    @patch('requests.get')
    def test_load_voice_capabilities(self, mock_get):
        """Test loading voice capabilities"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "capabilities": {
                "text_to_speech": True,
                "speech_to_text": True
            },
            "configuration": {
                "tts_model": "tts-1",
                "whisper_model": "whisper-1"
            }
        }
        mock_get.return_value = mock_response
        
        capabilities = self.panel.load_voice_capabilities()
        
        assert capabilities["capabilities"]["text_to_speech"] is True
        assert capabilities["configuration"]["tts_model"] == "tts-1"
        
    def test_render_settings_panel_default_settings(self):
        """Test rendering settings panel with default settings"""
        with patch('streamlit.markdown') as mock_markdown:
            settings = self.panel.render_settings_panel()
            assert isinstance(settings, VoiceSettings)
            assert settings.tts_voice == "alloy"
            assert settings.tts_speed == 1.0
            
    def test_render_settings_panel_custom_settings(self):
        """Test rendering settings panel with custom settings"""
        custom_settings = VoiceSettings(
            tts_voice="echo",
            tts_speed=1.5,
            stt_language="es"
        )
        
        with patch('streamlit.markdown') as mock_markdown:
            settings = self.panel.render_settings_panel(custom_settings)
            assert settings.tts_voice == "echo"
            assert settings.tts_speed == 1.5
            assert settings.stt_language == "es"
            
    @patch('requests.post')
    def test_preview_voice_success(self, mock_post):
        """Test successful voice preview"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "audio_base64": "dGVzdCBhdWRpbyBkYXRh"
        }
        mock_post.return_value = mock_response
        
        with patch('streamlit.spinner') as mock_spinner:
            with patch('streamlit.success') as mock_success:
                self.panel._preview_voice("alloy")
                mock_success.assert_called_with("Voice preview generated successfully!")
                
    @patch('requests.delete')
    def test_clear_cache_success(self, mock_delete):
        """Test successful cache clearing"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        
        with patch('streamlit.spinner') as mock_spinner:
            with patch('streamlit.success') as mock_success:
                self.panel._clear_tts_cache()
                mock_success.assert_called_with("Cache cleared successfully!")
                
    def test_export_settings(self):
        """Test settings export"""
        settings = VoiceSettings(
            tts_voice="echo",
            tts_speed=1.5,
            stt_language="es"
        )
        
        exported = self.panel.export_settings(settings)
        parsed = json.loads(exported)
        
        assert parsed["tts_voice"] == "echo"
        assert parsed["tts_speed"] == 1.5
        assert parsed["stt_language"] == "es"
        
    def test_import_settings_valid_json(self):
        """Test settings import with valid JSON"""
        settings_json = json.dumps({
            "tts_voice": "fable",
            "tts_speed": 2.0,
            "stt_language": "fr"
        })
        
        settings = self.panel.import_settings(settings_json)
        
        assert settings.tts_voice == "fable"
        assert settings.tts_speed == 2.0
        assert settings.stt_language == "fr"
        
    def test_import_settings_invalid_json(self):
        """Test settings import with invalid JSON"""
        invalid_json = "invalid json"
        
        with patch('streamlit.error') as mock_error:
            settings = self.panel.import_settings(invalid_json)
            assert settings.tts_voice == "alloy"  # Should default
            mock_error.assert_called()


class TestVoiceErrorHandler:
    """Test cases for VoiceErrorHandler"""
    
    def setup_method(self):
        """Setup test environment"""
        self.error_handler = VoiceErrorHandler()
        
    def test_error_handler_initialization(self):
        """Test error handler initialization"""
        assert len(self.error_handler.error_history) == 0
        assert len(self.error_handler.error_callbacks) == 0
        assert self.error_handler.max_retries == 3
        
    def test_handle_network_error(self):
        """Test handling network error"""
        error = Exception("Connection timeout")
        
        with patch('streamlit.error') as mock_error:
            voice_error = self.error_handler.handle_error(
                error,
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH
            )
            
            assert voice_error.category == ErrorCategory.NETWORK
            assert voice_error.severity == ErrorSeverity.HIGH
            assert "Network" in voice_error.title
            assert voice_error.retry_possible is True
            assert len(self.error_handler.error_history) == 1
            
    def test_handle_permission_error(self):
        """Test handling permission error"""
        error = PermissionError("Microphone access denied")
        
        with patch('streamlit.error') as mock_error:
            voice_error = self.error_handler.handle_error(
                error,
                category=ErrorCategory.PERMISSION,
                severity=ErrorSeverity.HIGH
            )
            
            assert voice_error.category == ErrorCategory.PERMISSION
            assert "Microphone" in voice_error.title
            assert voice_error.retry_possible is False
            
    def test_handle_api_error(self):
        """Test handling API error"""
        error = ValueError("Invalid API response")
        
        with patch('streamlit.warning') as mock_warning:
            voice_error = self.error_handler.handle_error(
                error,
                category=ErrorCategory.API,
                severity=ErrorSeverity.MEDIUM
            )
            
            assert voice_error.category == ErrorCategory.API
            assert "API" in voice_error.title
            assert voice_error.retry_possible is True
            
    def test_error_callback_registration(self):
        """Test error callback registration"""
        callback = Mock()
        self.error_handler.register_error_callback(ErrorCategory.NETWORK, callback)
        
        assert ErrorCategory.NETWORK in self.error_handler.error_callbacks
        assert callback in self.error_handler.error_callbacks[ErrorCategory.NETWORK]
        
    def test_error_callback_trigger(self):
        """Test error callback triggering"""
        callback = Mock()
        self.error_handler.register_error_callback(ErrorCategory.NETWORK, callback)
        
        error = Exception("Network error")
        self.error_handler.handle_error(
            error,
            category=ErrorCategory.NETWORK,
            show_to_user=False  # Don't display to user during test
        )
        
        # Callback should be triggered
        callback.assert_called_once()
        
    def test_retry_operation(self):
        """Test operation retry"""
        error_id = "test_error_123"
        
        with patch('streamlit.info') as mock_info:
            with patch('streamlit.rerun') as mock_rerun:
                self.error_handler._retry_operation(error_id)
                
                assert self.error_handler.retry_attempts[error_id] == 1
                mock_info.assert_called()
                mock_rerun.assert_called()
                
    def test_retry_max_attempts(self):
        """Test retry maximum attempts"""
        error_id = "test_error_123"
        
        # Set retry count to max
        self.error_handler.retry_attempts[error_id] = self.error_handler.max_retries
        
        with patch('streamlit.warning') as mock_warning:
            self.error_handler._retry_operation(error_id)
            mock_warning.assert_called_with("Maximum retry attempts reached")
            
    def test_get_error_summary_empty(self):
        """Test error summary when no errors"""
        summary = self.error_handler.get_error_summary()
        
        assert summary["total_errors"] == 0
        assert summary["by_category"] == {}
        assert summary["by_severity"] == {}
        
    def test_get_error_summary_with_errors(self):
        """Test error summary with errors"""
        # Add some errors
        self.error_handler.handle_error(
            Exception("Network error"),
            category=ErrorCategory.NETWORK,
            show_to_user=False
        )
        self.error_handler.handle_error(
            Exception("API error"),
            category=ErrorCategory.API,
            show_to_user=False
        )
        
        summary = self.error_handler.get_error_summary()
        
        assert summary["total_errors"] == 2
        assert summary["by_category"]["network"] == 1
        assert summary["by_category"]["api"] == 1
        assert len(summary["recent_errors"]) == 2
        
    def test_clear_error_history(self):
        """Test clearing error history"""
        # Add some errors
        self.error_handler.handle_error(
            Exception("Test error"),
            show_to_user=False
        )
        
        assert len(self.error_handler.error_history) == 1
        
        self.error_handler.clear_error_history()
        
        assert len(self.error_handler.error_history) == 0
        assert len(self.error_handler.retry_attempts) == 0


class TestResponsiveVoiceUI:
    """Test cases for ResponsiveVoiceUI"""
    
    def setup_method(self):
        """Setup test environment"""
        self.ui = ResponsiveVoiceUI()
        
    def test_ui_initialization(self):
        """Test UI initialization"""
        assert self.ui.breakpoints['mobile'] == 768
        assert self.ui.breakpoints['tablet'] == 1024
        assert self.ui.breakpoints['desktop'] == 1200
        assert self.ui.accessibility_features['high_contrast'] is False
        assert self.ui.accessibility_features['large_text'] is False
        
    def test_render_responsive_container(self):
        """Test rendering responsive container"""
        content_html = "<div>Test content</div>"
        
        with patch('streamlit.components.v1.html') as mock_html:
            self.ui.render_responsive_container(content_html, height=400)
            mock_html.assert_called_once()
            
    def test_render_accessible_recorder(self):
        """Test rendering accessible recorder"""
        with patch('streamlit.components.v1.html') as mock_html:
            self.ui.render_accessible_recorder(height=300)
            mock_html.assert_called_once()
            
    def test_render_accessible_playback(self):
        """Test rendering accessible playback"""
        audio_data = {
            "audio_base64": "dGVzdCBhdWRpbyBkYXRh",
            "mime_type": "audio/mpeg"
        }
        
        with patch('streamlit.components.v1.html') as mock_html:
            self.ui.render_accessible_playback(audio_data)
            mock_html.assert_called_once()
            
    def test_render_accessibility_panel(self):
        """Test rendering accessibility panel"""
        with patch('streamlit.markdown') as mock_markdown:
            with patch('streamlit.checkbox') as mock_checkbox:
                features = self.ui.render_accessibility_panel()
                
                assert isinstance(features, dict)
                assert 'high_contrast' in features
                assert 'large_text' in features
                assert 'reduced_motion' in features
                assert 'screen_reader' in features
                
    def test_accessibility_features_update(self):
        """Test accessibility features update"""
        with patch('streamlit.markdown') as mock_markdown:
            with patch('streamlit.checkbox') as mock_checkbox:
                # Mock checkbox return values
                mock_checkbox.side_effect = [True, False, True, False]
                
                features = self.ui.render_accessibility_panel()
                
                assert features['high_contrast'] is True
                assert features['large_text'] is False
                assert features['reduced_motion'] is True
                assert features['screen_reader'] is False


class TestVoiceComponentIntegration:
    """Integration tests for voice components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_url = "http://test-api:8000"
        
    @patch('requests.get')
    @patch('requests.post')
    def test_complete_voice_workflow(self, mock_post, mock_get):
        """Test complete voice workflow from recording to playback"""
        # Mock voice list API
        mock_get.return_value = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "voices": [{"name": "alloy", "description": "Balanced voice"}]
        }
        
        # Mock TTS API
        mock_post.return_value = Mock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "status": "success",
            "audio_base64": "dGVzdCBhdWRpbyBkYXRh",
            "mime_type": "audio/mpeg"
        }
        
        # Initialize components
        playback_component = VoicePlaybackComponent(self.api_url)
        settings_panel = VoiceSettingsPanel(self.api_url)
        
        # Test settings
        settings = settings_panel.render_settings_panel()
        assert settings.tts_voice == "alloy"
        
        # Test synthesis
        result = playback_component.synthesize_and_play(
            text="Hello world",
            voice=settings.tts_voice
        )
        
        assert result['status'] == 'success'
        assert result['audio_data'] is not None
        
    def test_error_handling_integration(self):
        """Test error handling integration across components"""
        error_handler = VoiceErrorHandler()
        playback_component = VoicePlaybackComponent(self.api_url)
        
        # Register error callback
        def test_callback(error):
            assert error.category == ErrorCategory.API
            
        error_handler.register_error_callback(ErrorCategory.API, test_callback)
        
        # Simulate error
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            result = playback_component.synthesize_and_play("test")
            
            assert result['status'] == 'error'
            assert len(error_handler.error_history) == 1


# Test utilities and fixtures
@pytest.fixture
def mock_audio_data():
    """Fixture providing mock audio data"""
    return {
        "audio_base64": base64.b64encode(b"test audio data").decode('utf-8'),
        "mime_type": "audio/mpeg",
        "voice": "alloy",
        "text_length": 15,
        "audio_size": 1024
    }


@pytest.fixture
def mock_voice_settings():
    """Fixture providing mock voice settings"""
    return VoiceSettings(
        tts_voice="echo",
        tts_speed=1.5,
        stt_language="es",
        auto_transcribe=True,
        auto_play_response=False
    )


# Performance tests
class TestVoiceComponentPerformance:
    """Performance tests for voice components"""
    
    def test_voice_playback_performance(self):
        """Test voice playback component performance"""
        component = VoicePlaybackComponent()
        
        # Test with large audio data
        large_audio_data = {
            "audio_base64": base64.b64encode(b"x" * 1024 * 1024).decode('utf-8'),  # 1MB
            "mime_type": "audio/mpeg",
            "voice": "alloy"
        }
        
        start_time = time.time()
        result = component.render_voice_playback(audio_data=large_audio_data)
        end_time = time.time()
        
        # Should render within reasonable time
        assert end_time - start_time < 1.0
        assert result['component_loaded'] is True
        
    def test_settings_panel_performance(self):
        """Test settings panel performance"""
        panel = VoiceSettingsPanel()
        
        start_time = time.time()
        settings = panel.render_settings_panel()
        end_time = time.time()
        
        # Should render within reasonable time
        assert end_time - start_time < 0.5
        assert isinstance(settings, VoiceSettings)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
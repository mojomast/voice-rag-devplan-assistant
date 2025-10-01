import streamlit as st
import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import base64

@dataclass
class VoiceSettings:
    """Data class for voice settings"""
    # TTS Settings
    tts_voice: str = "alloy"
    tts_speed: float = 1.0
    tts_format: str = "mp3"
    enable_caching: bool = True
    
    # STT Settings
    stt_language: str = "auto"
    enable_language_detection: bool = True
    enable_noise_reduction: bool = True
    enable_audio_enhancement: bool = True
    
    # Recording Settings
    recording_format: str = "webm"
    recording_quality: str = "high"
    auto_transcribe: bool = True
    auto_play_response: bool = True
    
    # UI Settings
    theme: str = "light"
    show_waveform: bool = True
    show_controls: bool = True
    keyboard_shortcuts: bool = True

class VoiceSettingsPanel:
    """Enhanced voice settings panel with comprehensive configuration options"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        self.api_url = api_url
        self.available_voices = []
        self.supported_languages = [
            ("auto", "Auto-detect"),
            ("en", "English"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("de", "German"),
            ("it", "Italian"),
            ("pt", "Portuguese"),
            ("nl", "Dutch"),
            ("pl", "Polish"),
            ("ru", "Russian"),
            ("ja", "Japanese"),
            ("ko", "Korean"),
            ("zh", "Chinese"),
            ("ar", "Arabic")
        ]
        self.supported_formats = [
            ("mp3", "MP3 - Best compatibility"),
            ("opus", "Opus - Better compression"),
            ("aac", "AAC - Apple optimized"),
            ("flac", "FLAC - Lossless quality")
        ]
        
    def load_available_voices(self) -> List[Dict]:
        """Load available voices from the API"""
        try:
            response = requests.get(f"{self.api_url}/voice/voices", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.available_voices = data.get("voices", [])
                return self.available_voices
            else:
                st.error(f"Failed to load voices: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error loading voices: {str(e)}")
            return []
    
    def load_voice_capabilities(self) -> Dict:
        """Load voice service capabilities"""
        try:
            response = requests.get(f"{self.api_url}/voice/capabilities", timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}
    
    def render_settings_panel(self, settings: Optional[VoiceSettings] = None) -> VoiceSettings:
        """Render the comprehensive voice settings panel"""
        
        # Initialize settings if not provided
        if settings is None:
            if 'voice_settings' not in st.session_state:
                st.session_state.voice_settings = VoiceSettings()
            settings = st.session_state.voice_settings
        
        # Load voices and capabilities
        if not self.available_voices:
            self.load_available_voices()
        
        capabilities = self.load_voice_capabilities()
        
        st.markdown("## ⚙️ Voice Settings")
        
        # Create tabs for different setting categories
        tab_tts, tab_stt, tab_recording, tab_ui, tab_advanced = st.tabs([
            "🔊 TTS Settings", "🎤 STT Settings", "🎙️ Recording", "🎨 UI Settings", "🔧 Advanced"
        ])
        
        with tab_tts:
            settings = self._render_tts_settings(settings, capabilities)
        
        with tab_stt:
            settings = self._render_stt_settings(settings, capabilities)
        
        with tab_recording:
            settings = self._render_recording_settings(settings)
        
        with tab_ui:
            settings = self._render_ui_settings(settings)
        
        with tab_advanced:
            settings = self._render_advanced_settings(settings, capabilities)
        
        # Save settings to session state
        st.session_state.voice_settings = settings
        
        return settings
    
    def _render_tts_settings(self, settings: VoiceSettings, capabilities: Dict) -> VoiceSettings:
        """Render Text-to-Speech settings"""
        
        st.subheader("🔊 Text-to-Speech Configuration")
        
        # Voice selection
        if self.available_voices:
            voice_options = {f"{v['name']} - {v['description']}": v['name'] for v in self.available_voices}
            selected_voice_display = st.selectbox(
                "Default Voice",
                options=list(voice_options.keys()),
                index=list(voice_options.values()).index(settings.tts_voice) if settings.tts_voice in voice_options.values() else 0,
                help="Choose the default voice for text-to-speech synthesis"
            )
            settings.tts_voice = voice_options[selected_voice_display]
            
            # Voice preview
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 Preview Voice", key="preview_tts_voice"):
                    self._preview_voice(settings.tts_voice)
            
            with col2:
                if st.button("🗑️ Clear TTS Cache", key="clear_tts_cache"):
                    self._clear_tts_cache()
        else:
            st.warning("No voices available. Please check your API configuration.")
            settings.tts_voice = st.selectbox("Default Voice", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
        
        # Speech settings
        col1, col2 = st.columns(2)
        
        with col1:
            settings.tts_speed = st.slider(
                "Speech Speed",
                min_value=0.25,
                max_value=4.0,
                value=settings.tts_speed,
                step=0.25,
                help="Adjust the speed of speech synthesis"
            )
        
        with col2:
            settings.tts_format = st.selectbox(
                "Output Format",
                options=[f[0] for f in self.supported_formats],
                index=[f[0] for f in self.supported_formats].index(settings.tts_format),
                format_func=lambda x: next(f[1] for f in self.supported_formats if f[0] == x),
                help="Audio format for synthesized speech"
            )
        
        # Caching options
        settings.enable_caching = st.checkbox(
            "Enable TTS Caching",
            value=settings.enable_caching,
            help="Cache synthesized audio to improve performance and reduce API calls"
        )
        
        # Show cache statistics
        if settings.enable_caching:
            self._render_cache_stats()
        
        return settings
    
    def _render_stt_settings(self, settings: VoiceSettings, capabilities: Dict) -> VoiceSettings:
        """Render Speech-to-Text settings"""
        
        st.subheader("🎤 Speech-to-Text Configuration")
        
        # Language settings
        col1, col2 = st.columns(2)
        
        with col1:
            language_options = {f[1]: f[0] for f in self.supported_languages}
            selected_language_display = st.selectbox(
                "Default Language",
                options=list(language_options.keys()),
                index=list(language_options.values()).index(settings.stt_language),
                help="Default language for speech recognition"
            )
            settings.stt_language = language_options[selected_language_display]
        
        with col2:
            settings.enable_language_detection = st.checkbox(
                "Auto-detect Language",
                value=settings.enable_language_detection,
                help="Automatically detect the language being spoken"
            )
        
        # Audio enhancement settings
        st.markdown("**Audio Enhancement**")
        
        # Check if advanced processing is available
        advanced_available = capabilities.get("capabilities", {}).get("noise_reduction", False)
        
        if advanced_available:
            settings.enable_noise_reduction = st.checkbox(
                "Enable Noise Reduction",
                value=settings.enable_noise_reduction,
                help="Reduce background noise in audio for better transcription accuracy"
            )
            
            settings.enable_audio_enhancement = st.checkbox(
                "Enable Audio Enhancement",
                value=settings.enable_audio_enhancement,
                help="Apply advanced audio processing techniques to improve quality"
            )
        else:
            st.info("🔧 Advanced audio processing not available. Install librosa and noisereduce for enhanced features.")
            settings.enable_noise_reduction = False
            settings.enable_audio_enhancement = False
        
        # Quality settings
        st.markdown("**Quality Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            quality_threshold = st.slider(
                "Audio Quality Threshold",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Minimum audio quality threshold for processing"
            )
        
        with col2:
            max_duration = st.slider(
                "Max Recording Duration",
                min_value=30,
                max_value=600,
                value=300,
                step=30,
                help="Maximum recording duration in seconds"
            )
        
        return settings
    
    def _render_recording_settings(self, settings: VoiceSettings) -> VoiceSettings:
        """Render recording settings"""
        
        st.subheader("🎙️ Recording Configuration")
        
        # Format and quality
        col1, col2 = st.columns(2)
        
        with col1:
            settings.recording_format = st.selectbox(
                "Recording Format",
                options=["webm", "mp4", "wav", "ogg"],
                index=["webm", "mp4", "wav", "ogg"].index(settings.recording_format),
                help="Audio format for recordings"
            )
        
        with col2:
            settings.recording_quality = st.selectbox(
                "Recording Quality",
                options=["low", "medium", "high", "ultra"],
                index=["low", "medium", "high", "ultra"].index(settings.recording_quality),
                help="Audio quality for recordings (higher quality uses more bandwidth)"
            )
        
        # Auto-processing options
        st.markdown("**Auto-Processing**")
        
        settings.auto_transcribe = st.checkbox(
            "Auto-transcribe after recording",
            value=settings.auto_transcribe,
            help="Automatically transcribe audio after recording stops"
        )
        
        settings.auto_play_response = st.checkbox(
            "Auto-play TTS response",
            value=settings.auto_play_response,
            help="Automatically play text-to-speech responses"
        )
        
        # Recording controls
        st.markdown("**Recording Controls**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            silence_threshold = st.slider(
                "Silence Threshold",
                min_value=0.1,
                max_value=2.0,
                value=0.5,
                step=0.1,
                help="Seconds of silence to stop recording automatically"
            )
        
        with col2:
            chunk_duration = st.slider(
                "Processing Chunk Duration",
                min_value=1,
                max_value=10,
                value=2,
                step=1,
                help="Duration of audio chunks for real-time processing (seconds)"
            )
        
        return settings
    
    def _render_ui_settings(self, settings: VoiceSettings) -> VoiceSettings:
        """Render UI settings"""
        
        st.subheader("🎨 User Interface Configuration")
        
        # Theme settings
        col1, col2 = st.columns(2)
        
        with col1:
            settings.theme = st.selectbox(
                "Theme",
                options=["light", "dark", "auto"],
                index=["light", "dark", "auto"].index(settings.theme),
                help="Visual theme for voice components"
            )
        
        with col2:
            accent_color = st.color_picker(
                "Accent Color",
                value="#007bff",
                help="Primary accent color for UI elements"
            )
        
        # Display options
        st.markdown("**Display Options**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            settings.show_waveform = st.checkbox(
                "Show Audio Waveform",
                value=settings.show_waveform,
                help="Display real-time audio waveform during recording"
            )
        
        with col2:
            settings.show_controls = st.checkbox(
                "Show Enhanced Controls",
                value=settings.show_controls,
                help="Show advanced playback and recording controls"
            )
        
        with col3:
            settings.keyboard_shortcuts = st.checkbox(
                "Enable Keyboard Shortcuts",
                value=settings.keyboard_shortcuts,
                help="Enable keyboard shortcuts for common actions"
            )
        
        # Layout options
        st.markdown("**Layout Options**")
        
        layout_style = st.selectbox(
            "Component Layout",
            options=["compact", "comfortable", "spacious"],
            index=1,
            help="Spacing and size of UI components"
        )
        
        return settings
    
    def _render_advanced_settings(self, settings: VoiceSettings, capabilities: Dict) -> VoiceSettings:
        """Render advanced settings"""
        
        st.subheader("🔧 Advanced Configuration")
        
        # API settings
        st.markdown("**API Configuration**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_timeout = st.slider(
                "API Timeout (seconds)",
                min_value=5,
                max_value=120,
                value=30,
                step=5,
                help="Timeout for API requests"
            )
        
        with col2:
            retry_attempts = st.slider(
                "Retry Attempts",
                min_value=0,
                max_value=5,
                value=3,
                step=1,
                help="Number of retry attempts for failed requests"
            )
        
        # Performance settings
        st.markdown("**Performance Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            concurrent_requests = st.slider(
                "Concurrent Requests",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                help="Maximum number of concurrent API requests"
            )
        
        with col2:
            cache_size = st.slider(
                "Cache Size (MB)",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                help="Maximum cache size for audio files"
            )
        
        # Debug settings
        st.markdown("**Debug Options**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            debug_mode = st.checkbox(
                "Enable Debug Mode",
                value=False,
                help="Show detailed debug information"
            )
        
        with col2:
            verbose_logging = st.checkbox(
                "Verbose Logging",
                value=False,
                help="Enable detailed logging for troubleshooting"
            )
        
        # System information
        st.markdown("**System Information**")
        
        if capabilities:
            st.json({
                "capabilities": capabilities.get("capabilities", {}),
                "configuration": capabilities.get("configuration", {}),
                "available_voices": len(self.available_voices)
            })
        
        # Reset settings
        if st.button("🔄 Reset to Default Settings", type="secondary"):
            if 'voice_settings' in st.session_state:
                del st.session_state.voice_settings
            st.rerun()
        
        return settings
    
    def _preview_voice(self, voice: str):
        """Preview the selected voice"""
        preview_text = "Hello, this is a preview of the selected voice. How does it sound?"
        
        with st.spinner("Generating voice preview..."):
            try:
                response = requests.post(
                    f"{self.api_url}/voice/synthesize/base64",
                    json={
                        "text": preview_text,
                        "voice": voice,
                        "output_format": "mp3",
                        "use_cache": False
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        audio_base64 = data.get("audio_base64")
                        if audio_base64:
                            # Create audio element
                            audio_html = f"""
                            <audio controls autoplay>
                                <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                            """
                            st.markdown(audio_html, unsafe_allow_html=True)
                            st.success("Voice preview generated successfully!")
                        else:
                            st.error("No audio data received")
                    else:
                        st.error(f"Voice synthesis failed: {data.get('error', 'Unknown error')}")
                else:
                    st.error(f"API request failed: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error generating voice preview: {str(e)}")
    
    def _clear_tts_cache(self):
        """Clear the TTS cache"""
        with st.spinner("Clearing cache..."):
            try:
                response = requests.delete(f"{self.api_url}/voice/cache", timeout=10)
                if response.status_code == 200:
                    st.success("Cache cleared successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to clear cache: {response.status_code}")
            except Exception as e:
                st.error(f"Error clearing cache: {str(e)}")
    
    def _render_cache_stats(self):
        """Render cache statistics"""
        try:
            response = requests.get(f"{self.api_url}/voice/cache/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                
                st.markdown("**Cache Statistics**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Cache Entries",
                        stats.get("total_entries", 0)
                    )
                
                with col2:
                    cache_size_mb = stats.get("cache_size_bytes", 0) / (1024 * 1024)
                    st.metric(
                        "Cache Size",
                        f"{cache_size_mb:.2f} MB"
                    )
                
                with col3:
                    hit_rate = stats.get("hit_rate", 0)
                    st.metric(
                        "Hit Rate",
                        f"{hit_rate:.1f}%"
                    )
                
                with col4:
                    st.metric(
                        "Expired Entries",
                        stats.get("expired_entries", 0)
                    )
                
                # Cache management buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🧹 Cleanup Cache", key="cleanup_cache"):
                        with st.spinner("Cleaning up cache..."):
                            try:
                                response = requests.post(f"{self.api_url}/voice/cache/cleanup", timeout=10)
                                if response.status_code == 200:
                                    st.success("Cache cleanup completed!")
                                    time.sleep(1)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Cache cleanup failed: {e}")
                
                with col2:
                    if st.button("📊 Show Cache Details", key="show_cache_details"):
                        if stats.get("entries"):
                            st.json(stats["entries"])
                        else:
                            st.info("No cache entries available")
                            
        except Exception as e:
            st.warning(f"Could not load cache statistics: {e}")
    
    def export_settings(self, settings: VoiceSettings) -> str:
        """Export settings to JSON"""
        return json.dumps({
            "tts_voice": settings.tts_voice,
            "tts_speed": settings.tts_speed,
            "tts_format": settings.tts_format,
            "enable_caching": settings.enable_caching,
            "stt_language": settings.stt_language,
            "enable_language_detection": settings.enable_language_detection,
            "enable_noise_reduction": settings.enable_noise_reduction,
            "enable_audio_enhancement": settings.enable_audio_enhancement,
            "recording_format": settings.recording_format,
            "recording_quality": settings.recording_quality,
            "auto_transcribe": settings.auto_transcribe,
            "auto_play_response": settings.auto_play_response,
            "theme": settings.theme,
            "show_waveform": settings.show_waveform,
            "show_controls": settings.show_controls,
            "keyboard_shortcuts": settings.keyboard_shortcuts
        }, indent=2)
    
    def import_settings(self, settings_json: str) -> VoiceSettings:
        """Import settings from JSON"""
        try:
            data = json.loads(settings_json)
            return VoiceSettings(
                tts_voice=data.get("tts_voice", "alloy"),
                tts_speed=data.get("tts_speed", 1.0),
                tts_format=data.get("tts_format", "mp3"),
                enable_caching=data.get("enable_caching", True),
                stt_language=data.get("stt_language", "auto"),
                enable_language_detection=data.get("enable_language_detection", True),
                enable_noise_reduction=data.get("enable_noise_reduction", True),
                enable_audio_enhancement=data.get("enable_audio_enhancement", True),
                recording_format=data.get("recording_format", "webm"),
                recording_quality=data.get("recording_quality", "high"),
                auto_transcribe=data.get("auto_transcribe", True),
                auto_play_response=data.get("auto_play_response", True),
                theme=data.get("theme", "light"),
                show_waveform=data.get("show_waveform", True),
                show_controls=data.get("show_controls", True),
                keyboard_shortcuts=data.get("keyboard_shortcuts", True)
            )
        except Exception as e:
            st.error(f"Failed to import settings: {e}")
            return VoiceSettings()

def render_voice_settings_panel(
    api_url: str = "http://127.0.0.1:8000",
    settings: Optional[VoiceSettings] = None
) -> VoiceSettings:
    """
    Main function to render the voice settings panel
    
    Args:
        api_url: Backend API URL
        settings: Optional existing settings
        
    Returns:
        Updated VoiceSettings
    """
    panel = VoiceSettingsPanel(api_url)
    return panel.render_settings_panel(settings)

# Example usage
def voice_settings_demo():
    """Demo function showing how to use the voice settings panel"""
    st.title("⚙️ Voice Settings Panel Demo")
    
    # Render the settings panel
    settings = render_voice_settings_panel()
    
    # Show current settings
    st.markdown("---")
    st.subheader("📋 Current Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**TTS Settings**")
        st.write(f"Voice: {settings.tts_voice}")
        st.write(f"Speed: {settings.tts_speed}x")
        st.write(f"Format: {settings.tts_format}")
        st.write(f"Caching: {'Enabled' if settings.enable_caching else 'Disabled'}")
    
    with col2:
        st.markdown("**STT Settings**")
        st.write(f"Language: {settings.stt_language}")
        st.write(f"Auto-detect: {'Enabled' if settings.enable_language_detection else 'Disabled'}")
        st.write(f"Noise Reduction: {'Enabled' if settings.enable_noise_reduction else 'Disabled'}")
        st.write(f"Audio Enhancement: {'Enabled' if settings.enable_audio_enhancement else 'Disabled'}")
    
    # Export/Import functionality
    st.markdown("**Settings Management**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Export Settings"):
            panel = VoiceSettingsPanel()
            settings_json = panel.export_settings(settings)
            st.download_button(
                label="💾 Download Settings",
                data=settings_json,
                file_name="voice_settings.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader(
            "📥 Import Settings",
            type="json",
            help="Upload a settings file to import"
        )
        
        if uploaded_file:
            try:
                settings_json = uploaded_file.read().decode('utf-8')
                panel = VoiceSettingsPanel()
                imported_settings = panel.import_settings(settings_json)
                st.session_state.voice_settings = imported_settings
                st.success("Settings imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to import settings: {e}")
    
    with col3:
        if st.button("🔄 Reset to Defaults"):
            if 'voice_settings' in st.session_state:
                del st.session_state.voice_settings
            st.rerun()

if __name__ == "__main__":
    voice_settings_demo()
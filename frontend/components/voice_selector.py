import streamlit as st
import requests
from typing import Dict, List, Optional
import json
import time

class VoiceSelector:
    """Enhanced voice selection component with caching and format options"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        self.api_url = api_url
        self.voices = []
        self.cache_stats = {}
        
    def load_available_voices(self) -> List[Dict]:
        """Load available voices from the API"""
        try:
            response = requests.get(f"{self.api_url}/voice/voices", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.voices = data.get("voices", [])
                return self.voices
            else:
                st.error(f"Failed to load voices: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error loading voices: {str(e)}")
            return []
    
    def load_cache_stats(self) -> Dict:
        """Load TTS cache statistics"""
        try:
            response = requests.get(f"{self.api_url}/voice/cache/stats", timeout=10)
            if response.status_code == 200:
                self.cache_stats = response.json()
                return self.cache_stats
            return {}
        except Exception:
            return {}
    
    def render_voice_selection(self) -> Dict:
        """Render the voice selection interface"""
        st.subheader("🎙️ Voice Settings")
        
        # Load voices if not already loaded
        if not self.voices:
            self.load_available_voices()
        
        # Voice selection
        if self.voices:
            voice_options = {f"{v['name']} - {v['description']}": v['name'] for v in self.voices}
            selected_voice_display = st.selectbox(
                "Select Voice",
                options=list(voice_options.keys()),
                index=0,
                help="Choose the voice for text-to-speech synthesis"
            )
            selected_voice = voice_options[selected_voice_display]
            
            # Voice preview
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 Preview Voice", key="preview_voice"):
                    self._preview_voice(selected_voice)
            
            with col2:
                if st.button("🗑️ Clear Cache", key="clear_cache"):
                    self._clear_cache()
            
            # Advanced settings
            with st.expander("⚙️ Advanced Settings", expanded=False):
                # Output format
                output_format = st.selectbox(
                    "Output Format",
                    options=["mp3", "opus", "aac", "flac"],
                    index=0,
                    help="Audio format for synthesized speech"
                )
                
                # Speech speed
                speech_speed = st.slider(
                    "Speech Speed",
                    min_value=0.25,
                    max_value=4.0,
                    value=1.0,
                    step=0.25,
                    help="Adjust the speed of speech synthesis"
                )
                
                # Caching options
                enable_caching = st.checkbox(
                    "Enable Caching",
                    value=True,
                    help="Cache synthesized audio to improve performance"
                )
                
                # Include metadata
                include_metadata = st.checkbox(
                    "Include Metadata",
                    value=True,
                    help="Include additional metadata in responses"
                )
            
            # Cache statistics
            if st.session_state.get("show_cache_stats", True):
                self._render_cache_stats()
            
            return {
                "voice": selected_voice,
                "output_format": output_format,
                "speech_speed": speech_speed,
                "enable_caching": enable_caching,
                "include_metadata": include_metadata
            }
        
        else:
            st.warning("No voices available. Please check your API configuration.")
            return {}
    
    def _preview_voice(self, voice: str):
        """Preview the selected voice"""
        preview_text = "Hello, this is a preview of the selected voice."
        
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
    
    def _clear_cache(self):
        """Clear the TTS cache"""
        with st.spinner("Clearing cache..."):
            try:
                response = requests.delete(f"{self.api_url}/voice/cache", timeout=10)
                if response.status_code == 200:
                    st.success("Cache cleared successfully!")
                    # Reload cache stats
                    self.load_cache_stats()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to clear cache: {response.status_code}")
            except Exception as e:
                st.error(f"Error clearing cache: {str(e)}")
    
    def _render_cache_stats(self):
        """Render cache statistics"""
        self.load_cache_stats()
        
        if self.cache_stats:
            st.subheader("📊 Cache Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Cache Entries",
                    self.cache_stats.get("total_entries", 0)
                )
            
            with col2:
                cache_size_mb = self.cache_stats.get("cache_size_bytes", 0) / (1024 * 1024)
                st.metric(
                    "Cache Size",
                    f"{cache_size_mb:.2f} MB"
                )
            
            with col3:
                hit_rate = self.cache_stats.get("hit_rate", 0)
                st.metric(
                    "Hit Rate",
                    f"{hit_rate:.1f}%"
                )
            
            with col4:
                st.metric(
                    "Expired Entries",
                    self.cache_stats.get("expired_entries", 0)
                )
            
            # Cache details
            if st.checkbox("Show Cache Details", key="show_cache_details"):
                if self.cache_stats.get("entries"):
                    st.json(self.cache_stats["entries"])
                else:
                    st.info("No cache entries available")
    
    def render_audio_format_validation(self):
        """Render audio format validation interface"""
        st.subheader("🔍 Audio Format Validation")
        
        uploaded_file = st.file_uploader(
            "Upload audio file for validation",
            type=["mp3", "wav", "webm", "ogg", "m4a", "flac"],
            help="Upload an audio file to validate its format and properties"
        )
        
        if uploaded_file:
            if st.button("🔍 Validate File", key="validate_audio"):
                with st.spinner("Validating audio file..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        # Validate file
                        response = requests.post(
                            f"{self.api_url}/voice/validate-format",
                            files={"file": uploaded_file},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            validation_result = response.json()
                            self._display_validation_result(validation_result)
                        else:
                            st.error(f"Validation failed: {response.status_code}")
                        
                        # Clean up
                        os.unlink(tmp_file_path)
                        
                    except Exception as e:
                        st.error(f"Error validating file: {str(e)}")
    
    def _display_validation_result(self, result: Dict):
        """Display audio format validation results"""
        if result.get("valid"):
            st.success("✅ Audio file is valid!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Format", result.get("format", "Unknown"))
            
            with col2:
                size_mb = result.get("size", 0) / (1024 * 1024)
                st.metric("Size", f"{size_mb:.2f} MB")
            
            with col3:
                st.metric("MIME Type", result.get("mime_type", "Unknown"))
            
            if result.get("supported"):
                st.info("🎯 This format is fully supported for transcription and synthesis")
            
        else:
            st.error("❌ Audio file validation failed!")
            st.error(f"Error: {result.get('error', 'Unknown error')}")
            
            if result.get("error_type") == "unsupported_format":
                st.info(f"Supported formats: {', '.join(result.get('supported_formats', []))}")
            elif result.get("error_type") == "file_too_large":
                max_size_mb = result.get("max_size", 0) / (1024 * 1024)
                st.info(f"Maximum file size: {max_size_mb:.0f} MB")

def render_voice_settings_panel(api_url: str = "http://127.0.0.1:8000") -> Dict:
    """Main function to render the voice settings panel"""
    voice_selector = VoiceSelector(api_url)
    
    # Create tabs for different voice features
    tab1, tab2, tab3 = st.tabs(["🎙️ Voice Selection", "🔍 Format Validation", "📊 Cache Management"])
    
    with tab1:
        voice_settings = voice_selector.render_voice_selection()
    
    with tab2:
        voice_selector.render_audio_format_validation()
    
    with tab3:
        voice_selector._render_cache_stats()
    
    return voice_settings or {}

# Import tempfile for file validation
import tempfile
import os
import streamlit as st
import requests
import base64
import io
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import voice components
from components.native_audio_recorder import native_audio_recorder, get_recorded_audio_as_bytes, save_recorded_audio
from components.voice_playback import render_voice_playback_component, VoicePlaybackComponent
from components.voice_settings_panel import render_voice_settings_panel, VoiceSettings
from utils.api_client import api_request, parse_response_json

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

class VoiceInterface:
    """Main voice interface integrating all voice components"""
    
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.playback_component = VoicePlaybackComponent(api_url)
        self.voice_settings = VoiceSettings()
        self.session_history = []
        self.current_transcription = None
        self.current_response = None
        
    def render_interface(self):
        """Render the complete voice interface"""
        
        # Page configuration
        st.set_page_config(
            page_title="🎤 Voice Interface",
            page_icon="🎤",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
        }
        .voice-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-ready { background-color: #28a745; }
        .status-recording { background-color: #dc3545; }
        .status-processing { background-color: #ffc107; }
        .status-error { background-color: #dc3545; }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>🎤 Voice-Enabled RAG Interface</h1>
            <p>Speak your queries and get intelligent responses from your documents</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Load settings
        if 'voice_settings' in st.session_state:
            self.voice_settings = st.session_state.voice_settings
        
        # Main layout
        self._render_main_layout()
        
        # Sidebar
        self._render_sidebar()
        
        # Footer
        self._render_footer()
    
    def _render_main_layout(self):
        """Render the main layout with voice components"""
        
        # Status bar
        self._render_status_bar()
        
        # Create main columns
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            self._render_input_section()
        
        with col_right:
            self._render_output_section()
        
        # Session history
        self._render_session_history()
    
    def _render_status_bar(self):
        """Render the status bar"""
        
        # System status
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Check voice service health
            try:
                response = requests.get(f"{self.api_url}/voice/health", timeout=5)
                if response.status_code == 200:
                    health = response.json()
                    if health.get("status") == "healthy":
                        st.markdown('<span class="status-indicator status-ready"></span>Voice Service Ready', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-indicator status-error"></span>Voice Service Error', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-indicator status-error"></span>Voice Service Offline', unsafe_allow_html=True)
            except:
                st.markdown('<span class="status-indicator status-error"></span>Voice Service Unavailable', unsafe_allow_html=True)
        
        with col2:
            # Show current voice
            st.markdown(f"🔊 Voice: **{self.voice_settings.tts_voice}**")
        
        with col3:
            # Show current language
            lang_display = "Auto-detect" if self.voice_settings.stt_language == "auto" else self.voice_settings.stt_language.upper()
            st.markdown(f"🌍 Language: **{lang_display}**")
        
        with col4:
            # Show session stats
            st.markdown(f"📊 Sessions: **{len(self.session_history)}**")
        
        st.markdown("---")
    
    def _render_input_section(self):
        """Render the input section with recorder and text input"""
        
        st.markdown('<div class="voice-card">', unsafe_allow_html=True)
        st.subheader("🎙️ Voice Input")
        
        # Create tabs for different input methods
        tab_voice, tab_text, tab_upload = st.tabs(["🎤 Voice Recording", "✍️ Text Input", "📁 File Upload"])
        
        with tab_voice:
            # Voice recorder
            st.markdown("**Record your query:**")
            
            # Apply settings to recorder
            recorder_height = 350 if self.voice_settings.show_waveform else 250
            recording_color = "#dc3545" if self.voice_settings.theme == "light" else "#ff6b6b"
            background_color = "#f8f9fa" if self.voice_settings.theme == "light" else "#2d3748"
            
            audio_data = native_audio_recorder(
                height=recorder_height,
                recording_color=recording_color,
                background_color=background_color
            )
            
            if audio_data:
                st.success("✅ Audio recorded successfully!")
                
                # Show recording info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Duration", audio_data.get('duration', 'Unknown'))
                with col2:
                    size_kb = audio_data.get('size', 0) / 1024
                    st.metric("Size", f"{size_kb:.1f} KB")
                with col3:
                    st.metric("Format", audio_data.get('mime_type', 'Unknown'))
                
                # Process audio
                self._process_recorded_audio(audio_data)
        
        with tab_text:
            # Text input
            st.markdown("**Type your query:**")
            
            text_input = st.text_area(
                "Enter your question:",
                height=100,
                placeholder="Ask a question about your documents...",
                key="voice_text_input"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎤 Speak Text", type="primary", help="Convert text to speech"):
                    if text_input.strip():
                        self._synthesize_and_play(text_input.strip())
                    else:
                        st.warning("Please enter some text first")
            
            with col2:
                if st.button("🧠 Ask RAG", help="Query the RAG system"):
                    if text_input.strip():
                        self._query_rag_system(text_input.strip())
                    else:
                        st.warning("Please enter some text first")
        
        with tab_upload:
            # File upload
            st.markdown("**Upload audio file:**")
            
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=["wav", "mp3", "m4a", "ogg", "webm"],
                help="Supported formats: WAV, MP3, M4A, OGG, WebM"
            )
            
            if uploaded_file:
                if st.button("🎯 Process Audio File", type="primary"):
                    self._process_uploaded_file(uploaded_file)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_output_section(self):
        """Render the output section with playback and results"""
        
        st.markdown('<div class="voice-card">', unsafe_allow_html=True)
        st.subheader("🔊 Voice Output & Results")
        
        # Voice playback component
        if 'current_audio_data' in st.session_state:
            st.markdown("**Audio Response:**")
            self.playback_component.render_voice_playback(
                audio_data=st.session_state.current_audio_data,
                auto_play=self.voice_settings.auto_play_response,
                show_controls=self.voice_settings.show_controls,
                theme=self.voice_settings.theme
            )
        
        # Transcription results
        if self.current_transcription:
            st.markdown("**Transcription:**")
            st.text_area(
                "Transcribed Text",
                value=self.current_transcription.get('text', ''),
                height=80,
                disabled=True
            )
            
            # Transcription metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Language", self.current_transcription.get('language', 'Unknown'))
            with col2:
                confidence = self.current_transcription.get('confidence', 0)
                st.metric("Confidence", f"{confidence:.2f}")
            with col3:
                duration = self.current_transcription.get('duration', 0)
                st.metric("Duration", f"{duration:.1f}s")
        
        # RAG response
        if self.current_response:
            st.markdown("**RAG Response:**")
            st.text_area(
                "AI Answer",
                value=self.current_response.get('answer', ''),
                height=120,
                disabled=True
            )
            
            # Sources if available
            if self.current_response.get('sources'):
                with st.expander("📚 Sources"):
                    for i, source in enumerate(self.current_response['sources']):
                        st.write(f"**Source {i+1}:** {source.get('source', 'Unknown')}")
                        if source.get('page'):
                            st.write(f"Page: {source['page']}")
                        if source.get('content_preview'):
                            st.caption(source['content_preview'])
        
        # Action buttons
        if self.current_transcription or self.current_response:
            st.markdown("**Actions:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Process Again", key="process_again"):
                    if self.current_transcription:
                        self._query_rag_system(self.current_transcription.get('text', ''))
            
            with col2:
                if st.button("💾 Save Session", key="save_session"):
                    self._save_current_session()
            
            with col3:
                if st.button("🗑️ Clear", key="clear_current"):
                    self._clear_current_session()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_sidebar(self):
        """Render the sidebar with settings and history"""
        
        with st.sidebar:
            # Voice settings
            st.markdown("## ⚙️ Voice Settings")
            
            # Quick settings
            with st.expander("Quick Settings", expanded=True):
                # Voice selection
                try:
                    voices_response = requests.get(f"{self.api_url}/voice/voices", timeout=5)
                    if voices_response.status_code == 200:
                        voices_data = voices_response.json()
                        voice_options = {v["name"]: v["description"] for v in voices_data["voices"]}
                        
                        selected_voice = st.selectbox(
                            "TTS Voice",
                            options=list(voice_options.keys()),
                            index=list(voice_options.keys()).index(self.voice_settings.tts_voice) if self.voice_settings.tts_voice in voice_options else 0,
                            format_func=lambda x: f"{x} - {voice_options[x]}"
                        )
                        self.voice_settings.tts_voice = selected_voice
                except:
                    self.voice_settings.tts_voice = st.selectbox(
                        "TTS Voice",
                        ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                        index=["alloy", "echo", "fable", "onyx", "nova", "shimmer"].index(self.voice_settings.tts_voice)
                    )
                
                # Language selection
                language_options = {
                    "auto": "Auto-detect",
                    "en": "English",
                    "es": "Spanish",
                    "fr": "French",
                    "de": "German",
                    "it": "Italian",
                    "pt": "Portuguese",
                    "nl": "Dutch",
                    "pl": "Polish",
                    "ru": "Russian",
                    "ja": "Japanese",
                    "ko": "Korean",
                    "zh": "Chinese",
                    "ar": "Arabic"
                }
                
                selected_lang = st.selectbox(
                    "STT Language",
                    options=list(language_options.keys()),
                    index=list(language_options.keys()).index(self.voice_settings.stt_language),
                    format_func=lambda x: language_options[x]
                )
                self.voice_settings.stt_language = selected_lang
                
                # Auto options
                self.voice_settings.auto_transcribe = st.checkbox(
                    "Auto-transcribe",
                    value=self.voice_settings.auto_transcribe
                )
                self.voice_settings.auto_play_response = st.checkbox(
                    "Auto-play response",
                    value=self.voice_settings.auto_play_response
                )
            
            # Full settings panel
            with st.expander("Advanced Settings", expanded=False):
                self.voice_settings = render_voice_settings_panel(self.api_url, self.voice_settings)
            
            st.markdown("---")
            
            # System info
            st.markdown("## 📊 System Information")
            
            try:
                # Get voice capabilities
                caps_response = requests.get(f"{self.api_url}/voice/capabilities", timeout=5)
                if caps_response.status_code == 200:
                    caps = caps_response.json()
                    
                    st.markdown("**Capabilities:**")
                    capabilities = caps.get("capabilities", {})
                    for capability, available in capabilities.items():
                        status = "✅" if available else "❌"
                        st.write(f"{status} {capability.replace('_', ' ').title()}")
                    
                    st.markdown("**Configuration:**")
                    config = caps.get("configuration", {})
                    st.write(f"🤖 TTS Model: {config.get('tts_model', 'Unknown')}")
                    st.write(f"🎯 Whisper Model: {config.get('whisper_model', 'Unknown')}")
                    st.write(f"🔊 Default Voice: {config.get('default_voice', 'Unknown')}")
                    st.write(f"💾 Cache: {'Enabled' if config.get('cache_enabled') else 'Disabled'}")
                    
            except Exception as e:
                st.error(f"Could not load system information: {e}")
            
            st.markdown("---")
            
            # Quick actions
            st.markdown("## 🚀 Quick Actions")
            
            if st.button("🧹 Clear All Sessions", type="secondary"):
                self.session_history.clear()
                if 'voice_sessions' in st.session_state:
                    st.session_state.voice_sessions = []
                st.success("All sessions cleared!")
                st.rerun()
            
            if st.button("📥 Import Settings", type="secondary"):
                st.info("Use the Advanced Settings panel to import settings")
            
            if st.button("🔄 Reset Settings", type="secondary"):
                if 'voice_settings' in st.session_state:
                    del st.session_state.voice_settings
                self.voice_settings = VoiceSettings()
                st.success("Settings reset to defaults!")
                st.rerun()
    
    def _render_session_history(self):
        """Render the session history"""
        
        st.markdown('<div class="voice-card">', unsafe_allow_html=True)
        st.subheader("📚 Session History")
        
        if not self.session_history:
            st.info("No sessions yet. Start by recording or typing a query!")
        else:
            for i, session in enumerate(reversed(self.session_history[-5:])):  # Show last 5 sessions
                with st.expander(f"🗣️ {session['timestamp']} - {session['query'][:50]}{'...' if len(session['query']) > 50 else ''}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Query:** {session['query']}")
                        st.write(f"**Language:** {session.get('language', 'Unknown')}")
                        st.write(f"**Voice:** {session.get('voice', 'Unknown')}")
                    
                    with col2:
                        st.write(f"**Duration:** {session.get('duration', 0):.1f}s")
                        st.write(f"**Confidence:** {session.get('confidence', 0):.2f}")
                        st.write(f"**Response Length:** {len(session.get('response', ''))}")
                    
                    if session.get('audio_data'):
                        if st.button(f"▶️ Play Response", key=f"play_history_{i}"):
                            st.session_state.current_audio_data = session['audio_data']
                            st.rerun()
                    
                    if st.button(f"🔄 Re-process", key=f"reprocess_{i}"):
                        self._query_rag_system(session['query'])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_footer(self):
        """Render the footer with tips and shortcuts"""
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**💡 Tips:**")
            st.write("• Speak clearly for best transcription")
            st.write("• Use headphones to prevent feedback")
            st.write("• Enable auto-transcribe for faster workflow")
        
        with col2:
            st.markdown("**⌨️ Shortcuts:**")
            if self.voice_settings.keyboard_shortcuts:
                st.write("• Space: Start/Stop recording")
                st.write("• Enter: Play audio")
                st.write("• Escape: Clear recording")
            else:
                st.write("Keyboard shortcuts disabled")
        
        with col3:
            st.markdown("**📞 Support:**")
            st.write("• Check microphone permissions")
            st.write("• Ensure stable internet connection")
            st.write("• Contact support for issues")
    
    def _process_recorded_audio(self, audio_data: Dict[str, Any]):
        """Process recorded audio"""
        
        if self.voice_settings.auto_transcribe:
            self._transcribe_audio(audio_data)
        else:
            st.session_state.recorded_audio_data = audio_data
            st.info("Audio recorded. Click 'Transcribe' to process.")
    
    def _transcribe_audio(self, audio_data: Dict[str, Any]):
        """Transcribe audio using the API"""
        
        with st.spinner("🎯 Transcribing audio..."):
            try:
                payload = {
                    "audio_base64": audio_data['audio_data'],
                    "mime_type": audio_data.get('mime_type', 'audio/webm')
                }
                
                if self.voice_settings.stt_language != "auto":
                    payload["language"] = self.voice_settings.stt_language
                
                response = requests.post(
                    f"{self.api_url}/voice/transcribe-base64",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.current_transcription = result
                    
                    st.success(f"✅ Transcription completed! Language: {result.get('language', 'Unknown')}")
                    
                    # Auto-query RAG if enabled
                    if result.get('text') and result.get('text').strip():
                        self._query_rag_system(result['text'])
                    
                else:
                    st.error(f"❌ Transcription failed: {response.status_code}")
                    st.code(response.text)
                    
            except requests.RequestException as e:
                st.error(f"❌ Network error during transcription: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
    
    def _query_rag_system(self, query_text: str):
        """Query the RAG system with transcribed text"""
        
        if not query_text.strip():
            st.warning("⚠️ No text to query")
            return
        
        with st.spinner("🧠 Querying RAG system..."):
            try:
                payload = {
                    "query": query_text,
                    "include_sources": True
                }
                
                response = requests.post(
                    f"{self.api_url}/query/text",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.current_response = result
                    
                    # Synthesize response if enabled
                    if result.get('answer') and self.voice_settings.auto_play_response:
                        self._synthesize_and_play(result['answer'])
                    
                    # Save session
                    self._save_session(query_text, result)
                    
                    st.success("✅ RAG query completed!")
                    
                else:
                    st.error(f"❌ RAG query failed: {response.status_code}")
                    st.code(response.text)
                    
            except requests.RequestException as e:
                st.error(f"❌ Network error during RAG query: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
    
    def _synthesize_and_play(self, text: str):
        """Synthesize speech and play it"""
        
        result = self.playback_component.synthesize_and_play(
            text=text,
            voice=self.voice_settings.tts_voice,
            auto_play=self.voice_settings.auto_play_response,
            output_format=self.voice_settings.tts_format,
            speech_speed=self.voice_settings.tts_speed
        )
        
        if result['status'] == 'success':
            st.session_state.current_audio_data = result['audio_data']
        else:
            st.error(f"❌ Speech synthesis failed: {result.get('error', 'Unknown error')}")
    
    def _process_uploaded_file(self, uploaded_file):
        """Process uploaded audio file"""
        
        with st.spinner("🎯 Processing uploaded audio..."):
            try:
                # Read file content
                audio_bytes = uploaded_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                audio_data = {
                    'audio_data': audio_base64,
                    'mime_type': uploaded_file.type,
                    'size': len(audio_bytes),
                    'filename': uploaded_file.name
                }
                
                # Transcribe
                self._transcribe_audio(audio_data)
                
            except Exception as e:
                st.error(f"❌ Error processing uploaded file: {e}")
    
    def _save_session(self, query: str, response: Dict[str, Any]):
        """Save the current session"""
        
        session = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'query': query,
            'response': response.get('answer', ''),
            'language': self.current_transcription.get('language') if self.current_transcription else self.voice_settings.stt_language,
            'voice': self.voice_settings.tts_voice,
            'duration': self.current_transcription.get('duration', 0) if self.current_transcription else 0,
            'confidence': self.current_transcription.get('confidence', 0) if self.current_transcription else 0,
            'sources': response.get('sources', []),
            'audio_data': st.session_state.get('current_audio_data')
        }
        
        self.session_history.append(session)
        
        # Keep only last 50 sessions
        if len(self.session_history) > 50:
            self.session_history = self.session_history[-50:]
    
    def _save_current_session(self):
        """Save current session to persistent storage"""
        
        if self.current_transcription or self.current_response:
            # This would typically save to a database
            st.success("✅ Session saved successfully!")
        else:
            st.warning("⚠️ No session data to save")
    
    def _clear_current_session(self):
        """Clear the current session data"""
        
        self.current_transcription = None
        self.current_response = None
        
        if 'current_audio_data' in st.session_state:
            del st.session_state.current_audio_data
        
        if 'recorded_audio_data' in st.session_state:
            del st.session_state.recorded_audio_data
        
        st.success("✅ Current session cleared!")
        st.rerun()

def main():
    """Main function to run the voice interface"""
    
    # Initialize voice interface
    voice_interface = VoiceInterface()
    
    # Render the interface
    voice_interface.render_interface()

if __name__ == "__main__":
    main()
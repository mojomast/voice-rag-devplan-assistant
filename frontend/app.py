import streamlit as st
import requests
import os
import json
from datetime import datetime
import tempfile
import time
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="Voice RAG Q&A",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- Helper Functions ---
def make_api_request(endpoint, method="GET", **kwargs):
    """Make API request with error handling"""
    try:
        url = f"{API_URL}{endpoint}"
        headers = kwargs.pop("headers", {})
        admin_token = st.session_state.get("admin_token") if "admin_token" in st.session_state else ""

        if admin_token:
            headers = {**headers, "Authorization": f"Bearer {admin_token}"}

        if method == "GET":
            response = requests.get(url, timeout=60, headers=headers, **kwargs)
        elif method == "POST":
            response = requests.post(url, timeout=60, headers=headers, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, timeout=60, headers=headers, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response, None
    except requests.exceptions.RequestException as e:
        return None, str(e)

def get_system_status():
    """Get system status from API"""
    response, error = make_api_request("/")
    if error:
        return {"status": "error", "error": error}

    if response and response.status_code == 200:
        return response.json()
    else:
        return {"status": "error", "error": f"HTTP {response.status_code}"}

# --- Main App ---
st.title("🎙️ Voice-Enabled Document Q&A System")
st.markdown("---")

# --- System Status in Header ---
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)

    system_status = get_system_status()

    if "admin_token" not in st.session_state:
        default_token = os.getenv("DEFAULT_ADMIN_TOKEN")
        if default_token:
            st.session_state["admin_token"] = default_token
        elif system_status.get("test_mode"):
            st.session_state["admin_token"] = "test-admin-token"
        else:
            st.session_state["admin_token"] = ""

    with col1:
        if system_status.get("status") == "healthy":
            st.success("✅ System Online")
        else:
            st.error("❌ System Offline")

    with col2:
        if system_status.get("vector_store_exists"):
            doc_count = system_status.get("document_count", 0)
            st.info(f"📚 {doc_count} documents indexed")
        else:
            st.warning("📚 No documents indexed")

    with col3:
        if system_status.get("requesty_enabled"):
            st.success("💰 Requesty.ai enabled")
        else:
            st.warning("💰 Direct OpenAI")

    with col4:
        if system_status.get("test_mode"):
            st.warning("🧪 Test mode active")
        else:
            st.success("🚀 Live mode")

    with col5:
        if system_status.get("wake_word_enabled"):
            st.success("🎙️ Wake word enabled")
        else:
            st.info("🎙️ Push-to-talk only")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Runtime Settings")
    with st.expander("Credentials & Mode", expanded=False):
        current_test_mode = bool(system_status.get("test_mode"))
        st.caption("Update API credentials or toggle offline test mode. Leave fields blank to keep current values.")

        with st.form("runtime_settings_form"):
            default_admin_token = st.session_state.get("admin_token", "")
            requesty_key_input = st.text_input(
                "Requesty API Key",
                type="password",
                placeholder="Leave blank to keep existing",
                help="Provide a new Requesty.ai key or leave blank to keep the current value"
            )
            clear_requesty_key = st.checkbox("Clear Requesty key", value=False)

            openai_key_input = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="Leave blank to keep existing",
                help="Provide a new OpenAI key or leave blank to keep the current value"
            )
            clear_openai_key = st.checkbox("Clear OpenAI key", value=False)

            admin_token_input = st.text_input(
                "Admin Access Token",
                type="password",
                placeholder="Required to authenticate runtime updates",
                help="Token required by the backend to update configuration. Default in test mode: test-admin-token",
                value=default_admin_token
            )

            force_test_mode = st.checkbox("Force Test Mode (offline)", value=current_test_mode)

            apply_settings = st.form_submit_button("Apply Settings", use_container_width=True)

        if apply_settings:
            st.session_state["admin_token"] = admin_token_input.strip()
            payload = {"test_mode": force_test_mode}

            if clear_requesty_key:
                payload["requesty_api_key"] = ""
            elif requesty_key_input:
                payload["requesty_api_key"] = requesty_key_input

            if clear_openai_key:
                payload["openai_api_key"] = ""
            elif openai_key_input:
                payload["openai_api_key"] = openai_key_input

            with st.spinner("Updating configuration..."):
                response, error = make_api_request("/config/update", "POST", json=payload)

            if error:
                st.error(f"Configuration update failed: {error}")
            elif response and response.status_code == 200:
                data = response.json()
                st.success("Runtime configuration updated")
                st.info(
                    f"Test mode: {'ON' if data.get('test_mode') else 'OFF'} | "
                    f"Requesty: {'Enabled' if data.get('requesty_enabled') else 'Disabled'}"
                )
                # Clear chat history to avoid stale context
                if 'chat_history' in st.session_state:
                    st.session_state.chat_history = []
                time.sleep(1)
                st.rerun()
            else:
                if response is None:
                    error_detail = "Unknown error"
                else:
                    try:
                        error_payload = response.json()
                        error_detail = error_payload.get("detail") or response.text
                    except ValueError:
                        error_detail = response.text
                st.error(f"Configuration update failed: {error_detail}")

    st.markdown("---")
    st.header("📄 Document Management")

    # File Upload Section
    uploaded_file = st.file_uploader(
        "Upload a document to add to the knowledge base",
        type=["pdf", "txt", "docx"],
        help="Supported formats: PDF, TXT, DOCX"
    )

    if st.button("📤 Process and Index Document", use_container_width=True):
        if uploaded_file is not None:
            with st.spinner("Processing document... This may take a moment."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response, error = make_api_request("/documents/upload", "POST", files=files)

                if error:
                    st.error(f"Connection error: {error}")
                elif response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    st.info(f"📄 {result['document_count']} pages, {result['chunk_count']} chunks created")
                    time.sleep(1)
                    st.rerun()  # Refresh to update status
                else:
                    st.error(f"❌ Error: {response.status_code} - {response.text}")
        else:
            st.warning("Please upload a file first")

    st.markdown("---")

    # Document Statistics
    st.subheader("📊 Document Statistics")
    response, error = make_api_request("/documents/stats")

    if not error and response and response.status_code == 200:
        stats = response.json()
        if stats.get("exists"):
            st.metric("Documents", stats.get("document_count", 0))
            st.metric("Index Size", f"{stats.get('index_size', 0):,} bytes")
        else:
            st.info("No documents indexed yet")

    # Management Actions
    st.markdown("---")
    st.subheader("🔧 Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear All", use_container_width=True, help="Remove all documents"):
            if st.session_state.get("confirm_clear"):
                response, error = make_api_request("/documents/clear", "DELETE")
                if not error and response and response.status_code == 200:
                    st.success("All documents cleared")
                    st.session_state.clear_confirm = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to clear documents")
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm")

    with col2:
        if st.button("💬 Clear Chat", use_container_width=True, help="Clear conversation history"):
            response, error = make_api_request("/chat/clear", "POST")
            if not error and response and response.status_code == 200:
                st.success("Chat cleared")
                if 'chat_history' in st.session_state:
                    st.session_state.chat_history = []
                time.sleep(1)
                st.rerun()

    # Usage Statistics
    st.markdown("---")
    st.subheader("📈 Usage Stats")

    if st.button("Refresh Stats", use_container_width=True):
        response, error = make_api_request("/usage/stats")

        if not error and response and response.status_code == 200:
            stats = response.json()

            # Requesty.ai stats
            if "requesty" in stats and "error" not in stats["requesty"]:
                st.success("💰 Requesty.ai: Connected")
                # Display usage metrics if available
            else:
                st.warning("💰 Requesty.ai: Not connected")

            # Memory stats
            if "memory" in stats:
                memory = stats["memory"]
                st.info(f"💭 Messages: {memory.get('message_count', 0)}")

    st.markdown("---")
    st.subheader("🧭 Planning Assistant")
    nav_links = [
        ("pages/planning_chat.py", "🗺️ Planning Chat"),
        ("pages/project_browser.py", "📁 Project Browser"),
        ("pages/devplan_viewer.py", "📋 DevPlan Viewer"),
    ]
    if hasattr(st, "page_link"):
        for path, label in nav_links:
            st.page_link(path, label=label)
    else:  # pragma: no cover - legacy fallback for older Streamlit versions
        for path, label in nav_links:
            st.markdown(f"[{label}](/{path})")

# --- Main Chat Interface ---
st.header("💬 Chat with Your Documents")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show sources if available
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.write(f"**{i}.** {source['source']} (Page: {source['page']})")
                        if source.get('content_preview'):
                            st.caption(source['content_preview'])

# --- Input Methods ---
st.markdown("---")

# Create tabs for different input methods
tab_text, tab_voice = st.tabs(["✍️ Text Input", "🎙️ Voice Input"])

with tab_text:
    # Text input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to history and display it
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Rerun to display user message immediately
        st.rerun()

with tab_voice:
    st.info("🎙️ Enhanced Voice Interface")
    st.markdown("Choose your preferred voice input method:")
    
    # Create sub-tabs for different voice input methods
    subtab_recorder, subtab_upload, subtab_interface = st.tabs(["🎤 Native Recorder", "📁 File Upload", "🚀 Full Interface"])
    
    with subtab_recorder:
        # Native audio recorder
        try:
            from components.native_audio_recorder import native_audio_recorder, get_recorded_audio_as_bytes
            
            st.markdown("**Record your query directly:**")
            
            # Get voice settings if available
            voice_settings = st.session_state.get("voice_settings", {})
            theme = voice_settings.get("theme", "light")
            
            # Apply theme settings
            recording_color = "#dc3545" if theme == "light" else "#ff6b6b"
            background_color = "#f8f9fa" if theme == "light" else "#2d3748"
            
            audio_data = native_audio_recorder(
                height=300,
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
                
                # Process buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🎯 Transcribe & Query", type="primary", key="process_recorded"):
                        _process_recorded_audio(audio_data, API_URL)
                
                with col2:
                    if st.button("🔊 Just Transcribe", key="transcribe_only"):
                        _transcribe_audio_only(audio_data, API_URL)
                        
        except ImportError:
            st.error("❌ Native audio recorder not available. Please install the required components.")
    
    with subtab_upload:
        # Traditional file upload
        st.markdown("**Upload an audio file:**")
        
        audio_file = st.file_uploader(
            "Choose audio file",
            type=["wav", "mp3", "m4a", "ogg", "webm"],
            help="Supported formats: WAV, MP3, M4A, OGG, WebM"
        )

        if audio_file:
            # Show file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Name", audio_file.name[:20] + "..." if len(audio_file.name) > 20 else audio_file.name)
            with col2:
                size_mb = audio_file.size / (1024 * 1024)
                st.metric("Size", f"{size_mb:.2f} MB")
            with col3:
                st.metric("Type", audio_file.type)
            
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🎯 Process Voice Query", type="primary", key="process_uploaded"):
                    _process_uploaded_file(audio_file, API_URL)

            with col2:
                if st.button("🔊 Just Transcribe", key="transcribe_uploaded"):
                    _transcribe_uploaded_file(audio_file, API_URL)
    
    with subtab_interface:
        # Link to full voice interface
        st.markdown("**Advanced Voice Interface:**")
        st.info("🚀 For the complete voice experience with enhanced features, use our dedicated voice interface.")
        
        if st.button("🎤 Open Full Voice Interface", type="primary"):
            # This would typically navigate to the voice interface page
            st.markdown("""
            <div style="padding: 20px; background-color: #e3f2fd; border-radius: 10px; text-align: center;">
                <h3>🎤 Full Voice Interface</h3>
                <p>Navigate to the Voice Interface page for:</p>
                <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
                    <li>🎙️ Advanced audio recording with waveform</li>
                    <li>🔊 Enhanced voice playback with controls</li>
                    <li>⚙️ Comprehensive voice settings</li>
                    <li>📚 Session history and management</li>
                    <li>🌍 Multi-language support</li>
                    <li>🎨 Customizable themes and layouts</li>
                </ul>
                <p><strong>Access via: Pages → Voice Interface</strong></p>
            </div>
            """, unsafe_allow_html=True)
    
    # Voice settings panel (collapsed by default)
    with st.expander("⚙️ Voice Settings", expanded=False):
        try:
            from components.voice_settings_panel import render_voice_settings_panel
            
            voice_settings = render_voice_settings_panel(API_URL)
            
            # Store voice settings in session state
            if voice_settings:
                st.session_state["voice_settings"] = voice_settings
                
        except ImportError:
            # Fallback to basic voice selection
            st.markdown("**Basic Voice Selection:**")
            selected_voice = st.selectbox("Voice", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
            st.session_state["basic_voice"] = selected_voice
        except Exception as e:
            st.warning(f"Voice settings unavailable: {str(e)}")
            selected_voice = st.selectbox("Voice", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
            st.session_state["basic_voice"] = selected_voice

# Process text input if it exists
if 'chat_history' in st.session_state and st.session_state.chat_history:
    last_message = st.session_state.chat_history[-1]

    # Only process if the last message is from user and hasn't been processed
    if (last_message["role"] == "user" and
        not last_message.get("processed", False)):

        # Mark as processed to avoid reprocessing
        st.session_state.chat_history[-1]["processed"] = True

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                query_data = {
                    "query": last_message["content"],
                    "include_sources": True
                }

                response, error = make_api_request("/query/text", "POST", json=query_data)

                if error:
                    error_message = f"❌ Connection error: {error}"
                    st.error(error_message)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_message,
                        "processed": True
                    })
                elif response and response.status_code == 200:
                    answer_data = response.json()
                    answer = answer_data.get("answer", "No answer generated")
                    sources = answer_data.get("sources", [])

                    # Display the answer
                    st.markdown(answer)

                    # Display sources if available
                    if sources:
                        with st.expander("📚 Sources"):
                            for i, source in enumerate(sources, 1):
                                st.write(f"**{i}.** {source['source']} (Page: {source['page']})")
                                if source.get('content_preview'):
                                    st.caption(source['content_preview'])

                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "processed": True
                    })
                else:
                    error_message = f"❌ Error: {response.status_code} - {response.text if response else 'No response'}"
                    st.error(error_message)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_message,
                        "processed": True
                    })

# --- Footer ---


if __name__ == "__main__":
    import os
    import sys

    sentinel = "VOICE_RAG_STREAMLIT_BOOTSTRAPPED"
    already_streamlit = os.environ.get("STREAMLIT_SERVER_RUNNING") == "1"
    already_bootstrapped = os.environ.get(sentinel) == "1"

    if not (already_streamlit or already_bootstrapped):
        os.environ[sentinel] = "1"
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
        sys.exit(0)
# Helper functions for voice processing
def _process_recorded_audio(audio_data: Dict[str, Any], api_url: str):
    """Process recorded audio through the complete pipeline"""
    
    with st.spinner("🎯 Processing voice query..."):
        try:
            # Get voice settings
            voice_settings = st.session_state.get("voice_settings", {})
            language = voice_settings.get("stt_language", "auto")
            voice = voice_settings.get("tts_voice", "alloy")
            
            # Step 1: Transcribe audio
            transcribe_payload = {
                "audio_base64": audio_data['audio_data'],
                "mime_type": audio_data.get('mime_type', 'audio/webm')
            }
            
            if language != "auto":
                transcribe_payload["language"] = language
            
            transcribe_response, error = make_api_request("/voice/transcribe-base64", "POST", json=transcribe_payload)
            
            if error or not transcribe_response or transcribe_response.status_code != 200:
                st.error(f"❌ Transcription failed: {error or 'Unknown error'}")
                return
            
            transcribe_result = transcribe_response.json()
            query_text = transcribe_result.get('text', '')
            
            if not query_text.strip():
                st.warning("⚠️ No speech detected in the audio")
                return
            
            # Add user message to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": f"🎙️ {query_text}",
                "transcription": transcribe_result
            })
            
            # Step 2: Query RAG system
            query_payload = {
                "query": query_text,
                "include_sources": True
            }
            
            query_response, error = make_api_request("/query/text", "POST", json=query_payload)
            
            if error or not query_response or query_response.status_code != 200:
                st.error(f"❌ RAG query failed: {error or 'Unknown error'}")
                return
            
            query_result = query_response.json()
            answer = query_result.get('answer', '')
            
            # Step 3: Synthesize response
            tts_payload = {
                "text": answer,
                "voice": voice,
                "output_format": "mp3",
                "use_cache": True
            }
            
            tts_response, error = make_api_request("/voice/synthesize/base64", "POST", json=tts_payload)
            
            if error or not tts_response or tts_response.status_code != 200:
                st.warning("⚠️ Voice synthesis failed, but text response is available")
                audio_base64 = None
            else:
                tts_result = tts_response.json()
                audio_base64 = tts_result.get('audio_base64')
            
            # Add assistant response to chat history
            assistant_message = {
                "role": "assistant",
                "content": answer,
                "sources": query_result.get('sources', []),
                "transcription": transcribe_result
            }
            
            if audio_base64:
                assistant_message["audio_base64"] = audio_base64
                assistant_message["mime_type"] = tts_result.get('mime_type', 'audio/mpeg')
            
            st.session_state.chat_history.append(assistant_message)
            
            st.success("✅ Voice query processed successfully!")
            
            # Play audio if available
            if audio_base64:
                audio_bytes = base64.b64decode(audio_base64)
                st.audio(audio_bytes, format="audio/mpeg")
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing voice query: {str(e)}")

def _transcribe_audio_only(audio_data: Dict[str, Any], api_url: str):
    """Only transcribe audio without querying RAG"""
    
    with st.spinner("🔊 Transcribing audio..."):
        try:
            voice_settings = st.session_state.get("voice_settings", {})
            language = voice_settings.get("stt_language", "auto")
            
            payload = {
                "audio_base64": audio_data['audio_data'],
                "mime_type": audio_data.get('mime_type', 'audio/webm')
            }
            
            if language != "auto":
                payload["language"] = language
            
            response, error = make_api_request("/voice/transcribe-base64", "POST", json=payload)
            
            if error or not response or response.status_code != 200:
                st.error(f"❌ Transcription failed: {error or 'Unknown error'}")
                return
            
            result = response.json()
            transcribed_text = result.get('text', '')
            
            if transcribed_text.strip():
                st.success(f"✅ Transcription completed!")
                st.text_area("Transcribed Text:", value=transcribed_text, height=100, disabled=True)
                
                # Show metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Language", result.get('language', 'Unknown'))
                with col2:
                    confidence = result.get('confidence', 0)
                    st.metric("Confidence", f"{confidence:.2f}")
                with col3:
                    duration = result.get('duration', 0)
                    st.metric("Duration", f"{duration:.1f}s")
                
                # Option to use this text for querying
                if st.button("🧠 Ask RAG System", key="query_from_transcription"):
                    # Add to text input for processing
                    st.session_state.temp_query_text = transcribed_text
                    st.rerun()
            else:
                st.warning("⚠️ No speech detected in the audio")
                
        except Exception as e:
            st.error(f"❌ Error transcribing audio: {str(e)}")

def _process_uploaded_file(uploaded_file, api_url: str):
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
            
            # Process through the voice pipeline
            _process_recorded_audio(audio_data, api_url)
            
        except Exception as e:
            st.error(f"❌ Error processing uploaded file: {str(e)}")

def _transcribe_uploaded_file(uploaded_file, api_url: str):
    """Only transcribe uploaded audio file"""
    
    with st.spinner("🔊 Transcribing uploaded audio..."):
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
            
            # Transcribe only
            _transcribe_audio_only(audio_data, api_url)
            
        except Exception as e:
            st.error(f"❌ Error transcribing uploaded file: {str(e)}")

# Check for temporary query text from transcription
if 'temp_query_text' in st.session_state:
    temp_text = st.session_state.temp_query_text
    del st.session_state.temp_query_text
    
    # Add to chat history and process
    st.session_state.chat_history.append({"role": "user", "content": temp_text})
    st.rerun()

st.markdown("---")
st.caption("💡 Tip: Upload documents first, then ask questions about their content. Use voice input for hands-free interaction. Try the Full Voice Interface for advanced features!")
import streamlit as st
import requests
import base64
import io
import json
from typing import Optional, Dict, Any
import time

# Import the native audio recorder component
from components.native_audio_recorder import native_audio_recorder, get_recorded_audio_as_bytes, save_recorded_audio

# Configuration
API_BASE_URL = st.secrets.get("API_URL", "http://localhost:8000")

def main():
    st.set_page_config(
        page_title="🎤 Voice RAG System",
        page_icon="🎤",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🎤 Voice-Enabled RAG System")
    st.markdown("**Native Device Audio Recording with AI-Powered Document Q&A**")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Settings")

        # Voice settings
        st.subheader("🔊 Voice Settings")

        # Get available voices from backend
        try:
            voices_response = requests.get(f"{API_BASE_URL}/voice/voices", timeout=5)
            if voices_response.status_code == 200:
                voices_data = voices_response.json()
                voice_options = {voice["name"]: voice["description"] for voice in voices_data["voices"]}
            else:
                voice_options = {"alloy": "Default voice"}
        except:
            voice_options = {"alloy": "Default voice"}

        selected_voice = st.selectbox(
            "Select TTS Voice",
            options=list(voice_options.keys()),
            format_func=lambda x: f"{x} - {voice_options[x]}"
        )

        # Recording settings
        st.subheader("🎙️ Recording Settings")
        auto_transcribe = st.checkbox("Auto-transcribe after recording", value=True)
        auto_query = st.checkbox("Auto-query RAG after transcription", value=False)
        language_detection = st.checkbox("Auto-detect language", value=True)

        # Audio settings
        st.subheader("🎛️ Audio Settings")
        component_height = st.slider("Recorder Height", 250, 500, 350)
        recording_color = st.color_picker("Recording Indicator Color", "#dc3545")
        background_color = st.color_picker("Background Color", "#f8f9fa")

    # Main content area
    col1, col2 = st.columns([3, 2])

    with col1:
        st.header("🎙️ Audio Recorder")

        # Native audio recorder component
        audio_data = native_audio_recorder(
            height=component_height,
            recording_color=recording_color,
            background_color=background_color
        )

        # Process recorded audio
        if audio_data:
            st.success("✅ Audio recorded successfully!")

            # Display recording information
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Duration", audio_data.get('duration', 'Unknown'))
            with col_b:
                st.metric("Size", f"{audio_data.get('size', 0) / 1024:.1f} KB")
            with col_c:
                st.metric("Format", audio_data.get('mime_type', 'Unknown'))

            # Action buttons
            st.subheader("🔧 Actions")

            col_x, col_y, col_z = st.columns(3)

            with col_x:
                if st.button("📝 Transcribe Audio", type="primary"):
                    transcribe_audio(audio_data, language_detection)

            with col_y:
                if st.button("🧠 Ask RAG System"):
                    if 'transcription_result' in st.session_state:
                        query_rag_system(st.session_state.transcription_result.get('text', ''))
                    else:
                        st.warning("Please transcribe audio first")

            with col_z:
                if st.button("🎯 Voice Query"):
                    voice_query_pipeline(audio_data, selected_voice)

            # Auto-actions
            if auto_transcribe and 'transcription_done' not in st.session_state:
                st.session_state.transcription_done = True
                transcribe_audio(audio_data, language_detection)

                if auto_query and 'transcription_result' in st.session_state:
                    query_rag_system(st.session_state.transcription_result.get('text', ''))

    with col2:
        st.header("📊 Results")

        # Display transcription results
        if 'transcription_result' in st.session_state:
            st.subheader("📝 Transcription")
            result = st.session_state.transcription_result

            st.text_area(
                "Transcribed Text",
                value=result.get('text', ''),
                height=100,
                disabled=True
            )

            col_detail1, col_detail2 = st.columns(2)
            with col_detail1:
                st.metric("Language", result.get('language', 'Unknown'))
                st.metric("Confidence", f"{result.get('confidence', 0):.2f}")
            with col_detail2:
                st.metric("Duration", f"{result.get('duration', 0):.1f}s")
                st.metric("Source", result.get('source', 'Unknown'))

        # Display RAG results
        if 'rag_result' in st.session_state:
            st.subheader("🧠 RAG Response")
            result = st.session_state.rag_result

            st.text_area(
                "AI Answer",
                value=result.get('answer', ''),
                height=150,
                disabled=True
            )

            # Sources
            if result.get('sources'):
                with st.expander("📚 Sources"):
                    for i, source in enumerate(result['sources']):
                        st.write(f"**Source {i+1}:** {source.get('source', 'Unknown')}")
                        if source.get('page'):
                            st.write(f"Page: {source['page']}")

        # Display voice query results
        if 'voice_query_result' in st.session_state:
            st.subheader("🎤 Complete Voice Query")
            result = st.session_state.voice_query_result

            st.text_area(
                "Query",
                value=result.get('query', ''),
                height=60,
                disabled=True
            )

            st.text_area(
                "Answer",
                value=result.get('answer', ''),
                height=120,
                disabled=True
            )

            # Play audio response
            if result.get('audio_response', {}).get('audio_base64'):
                st.subheader("🔊 Audio Response")
                audio_base64 = result['audio_response']['audio_base64']
                audio_bytes = base64.b64decode(audio_base64)
                st.audio(audio_bytes, format='audio/mp3')

    # System status in footer
    st.markdown("---")
    display_system_status()

def transcribe_audio(audio_data: Dict[str, Any], detect_language: bool = True):
    """Transcribe audio using the backend API"""
    with st.spinner("🎯 Transcribing audio..."):
        try:
            payload = {
                "audio_data": audio_data['audio_data'],
                "mime_type": audio_data.get('mime_type', 'audio/webm')
            }

            if detect_language:
                payload["language"] = None  # Let the API detect

            response = requests.post(
                f"{API_BASE_URL}/voice/transcribe-base64",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.transcription_result = result
                st.success(f"✅ Transcription completed! Detected language: {result.get('language', 'Unknown')}")
            else:
                st.error(f"❌ Transcription failed: {response.status_code}")
                st.code(response.text)

        except requests.RequestException as e:
            st.error(f"❌ Network error during transcription: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

def query_rag_system(query_text: str):
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
                f"{API_BASE_URL}/query/text",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.rag_result = result
                st.success("✅ RAG query completed!")
            else:
                st.error(f"❌ RAG query failed: {response.status_code}")
                st.code(response.text)

        except requests.RequestException as e:
            st.error(f"❌ Network error during RAG query: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

def voice_query_pipeline(audio_data: Dict[str, Any], voice: str):
    """Complete voice query pipeline: audio -> transcription -> RAG -> speech"""
    with st.spinner("🎤 Processing complete voice query pipeline..."):
        try:
            payload = {
                "audio_data": audio_data['audio_data'],
                "mime_type": audio_data.get('mime_type', 'audio/webm')
            }

            response = requests.post(
                f"{API_BASE_URL}/voice/query-base64",
                json=payload,
                timeout=60  # Longer timeout for complete pipeline
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.voice_query_result = result
                st.success("✅ Complete voice query pipeline completed!")

                # Also update individual results
                st.session_state.transcription_result = result.get('transcription', {})
                st.session_state.rag_result = {
                    'answer': result.get('answer', ''),
                    'sources': result.get('sources', [])
                }

            else:
                st.error(f"❌ Voice query pipeline failed: {response.status_code}")
                st.code(response.text)

        except requests.RequestException as e:
            st.error(f"❌ Network error during voice query: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

def display_system_status():
    """Display system status information"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            status = response.json()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                status_color = "🟢" if status.get('status') == 'healthy' else "🔴"
                st.metric("System Status", f"{status_color} {status.get('status', 'Unknown')}")
            with col2:
                doc_status = "✅" if status.get('vector_store_exists') else "❌"
                st.metric("Vector Store", f"{doc_status} {'Ready' if status.get('vector_store_exists') else 'Empty'}")
            with col3:
                st.metric("Documents", status.get('document_count', 0))
            with col4:
                requesty_status = "✅" if status.get('requesty_enabled') else "❌"
                st.metric("Requesty.ai", f"{requesty_status} {'Enabled' if status.get('requesty_enabled') else 'Disabled'}")
        else:
            st.error(f"❌ Cannot connect to backend API (Status: {response.status_code})")
    except:
        st.error("❌ Backend API unavailable")

# Additional utility functions
def reset_session_state():
    """Clear all session state variables"""
    keys_to_clear = ['transcription_result', 'rag_result', 'voice_query_result', 'transcription_done']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# Reset button in sidebar
with st.sidebar:
    st.markdown("---")
    if st.button("🔄 Reset Session", type="secondary"):
        reset_session_state()
        st.rerun()

# Tips and instructions
with st.sidebar:
    st.markdown("---")
    with st.expander("💡 Usage Tips"):
        st.markdown("""
        **Getting Started:**
        1. Click "Start Recording" to record audio
        2. Click "Stop Recording" when done
        3. Use action buttons to process your recording

        **Features:**
        - **Transcribe**: Convert speech to text
        - **Ask RAG**: Query uploaded documents
        - **Voice Query**: Complete pipeline with audio response

        **Keyboard Shortcuts:**
        - `Spacebar`: Start/Stop recording
        - `Enter`: Play recorded audio
        - `Escape`: Clear recording

        **Tips:**
        - Upload documents first for RAG queries
        - Use headphones to prevent feedback
        - Speak clearly for better transcription
        - Enable auto-actions for streamlined workflow
        """)

if __name__ == "__main__":
    main()
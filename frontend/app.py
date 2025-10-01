import streamlit as st
import requests
import os
import json
from datetime import datetime
import tempfile
import time

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
    st.info("🎙️ Voice input feature")
    st.markdown("Upload an audio file to ask a question:")

    audio_file = st.file_uploader(
        "Upload audio file",
        type=["wav", "mp3", "m4a", "ogg"],
        help="Record your question and upload the audio file"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎯 Process Voice Query", disabled=not audio_file):
            if audio_file:
                with st.spinner("Processing voice query..."):
                    files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
                    response, error = make_api_request("/query/voice", "POST", files=files)

                    if error:
                        st.error(f"Connection error: {error}")
                    elif response and response.status_code == 200:
                        # Get the query text from headers
                        query_text = response.headers.get("X-Query-Text", "Voice query")
                        response_text = response.headers.get("X-Response-Text", "Voice response")

                        # Add to chat history
                        st.session_state.chat_history.append({"role": "user", "content": f"🎙️ {query_text}"})
                        st.session_state.chat_history.append({"role": "assistant", "content": response_text})

                        # Play the response audio
                        st.audio(response.content, format="audio/mp3")
                        st.success("Voice query processed successfully!")

                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error processing voice query: {response.status_code}")

    with col2:
        # Voice settings
        st.selectbox("Voice", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

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
        os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", __file__])
st.markdown("---")
st.caption("💡 Tip: Upload documents first, then ask questions about their content. Use voice input for hands-free interaction.")
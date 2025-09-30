import streamlit as st

def apply_mobile_css():
    """Apply CSS for better mobile experience"""
    mobile_css = """
    <style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem;
        }

        .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
            min-height: 50px;
            font-size: 16px;
        }

        .stSelectbox, .stTextInput, .stTextArea {
            margin-bottom: 1rem;
        }

        .stTextInput > div > div > input {
            font-size: 16px;
            min-height: 50px;
        }

        .stTextArea > div > div > textarea {
            font-size: 16px;
            min-height: 120px;
        }

        .stChatMessage {
            margin-bottom: 1rem;
            padding: 1rem;
        }

        /* Larger touch targets for mobile */
        .stFileUploader {
            min-height: 60px;
        }

        .stFileUploader > div {
            padding: 1rem;
        }

        /* Mobile sidebar adjustments */
        .css-1d391kg {
            padding-top: 1rem;
        }

        /* Adjust column spacing on mobile */
        .css-ocqkz7 {
            gap: 0.5rem;
        }

        /* Mobile navigation */
        .css-1rs6os {
            width: 100%;
        }

        /* Better mobile headers */
        h1, h2, h3 {
            text-align: center;
            margin-bottom: 1rem;
        }

        /* Mobile-friendly metrics */
        .metric-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 1rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 1rem;
        }

        /* Better mobile tables */
        .dataframe {
            font-size: 12px;
        }

        /* Mobile chat interface */
        .chat-container {
            max-height: 60vh;
            overflow-y: auto;
        }
    }

    /* Tablet adjustments */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main > div {
            padding: 1.5rem;
        }

        .stButton > button {
            min-height: 45px;
        }
    }

    /* Voice recording visual feedback */
    .recording-indicator {
        animation: pulse 2s infinite;
        background-color: #ff4444;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: inline-block;
        margin-right: 10px;
    }

    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
    }

    /* Voice controls */
    .voice-controls {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 12px;
        margin: 1rem 0;
    }

    .voice-button {
        min-width: 150px;
        min-height: 60px;
        border-radius: 30px;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .voice-button:hover {
        transform: scale(1.05);
    }

    .recording-status {
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
    }

    .recording-active {
        background-color: #ffe6e6;
        color: #d32f2f;
        border: 2px solid #ff4444;
    }

    .recording-inactive {
        background-color: #e8f5e8;
        color: #388e3c;
        border: 2px solid #4caf50;
    }

    /* File upload enhancements */
    .upload-area {
        border: 3px dashed #ccc;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background-color: #fafafa;
        transition: all 0.3s ease;
    }

    .upload-area:hover {
        border-color: #007bff;
        background-color: #f0f8ff;
    }

    .upload-icon {
        font-size: 48px;
        color: #007bff;
        margin-bottom: 1rem;
    }

    /* Progress indicators */
    .progress-container {
        width: 100%;
        background-color: #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }

    .progress-bar {
        height: 20px;
        background-color: #007bff;
        border-radius: 10px;
        transition: width 0.3s ease;
    }

    /* Mobile navigation tabs */
    .mobile-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    .mobile-tab {
        flex: 1;
        min-width: 120px;
        padding: 12px;
        text-align: center;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .mobile-tab.active {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }

    .mobile-tab:hover {
        background-color: #e9ecef;
    }

    .mobile-tab.active:hover {
        background-color: #0056b3;
    }

    /* Responsive grid for stats */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 4px solid #007bff;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #007bff;
        margin-bottom: 0.5rem;
    }

    .stat-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Mobile-friendly alerts */
    .mobile-alert {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 16px;
        line-height: 1.5;
    }

    .mobile-alert.success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .mobile-alert.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .mobile-alert.info {
        background-color: #cce7ff;
        color: #004085;
        border: 1px solid #b3d9ff;
    }

    .mobile-alert.warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }

    /* Floating action button for mobile */
    .fab {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 50%;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
        transition: all 0.3s ease;
    }

    .fab:hover {
        background-color: #0056b3;
        transform: scale(1.1);
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .upload-area {
            background-color: #2d3748;
            border-color: #4a5568;
        }

        .stat-card {
            background-color: #2d3748;
            color: #e2e8f0;
        }

        .mobile-tab {
            background-color: #2d3748;
            color: #e2e8f0;
            border-color: #4a5568;
        }
    }
    </style>
    """
    st.markdown(mobile_css, unsafe_allow_html=True)

def mobile_voice_recorder():
    """Mobile-optimized voice recording interface"""
    st.markdown('<div class="voice-controls">', unsafe_allow_html=True)

    st.markdown("### 🎙️ Voice Recording")

    # Create columns for recording controls
    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("🔴 Start Recording", key="start_record", use_container_width=True):
            st.session_state.recording = True
            st.markdown(
                '<div class="recording-status recording-active">'
                '<span class="recording-indicator"></span>Recording in progress... Speak now!'
                '</div>',
                unsafe_allow_html=True
            )

    with col2:
        if st.button("⏹️ Stop", key="stop_record", use_container_width=True):
            st.session_state.recording = False
            st.markdown(
                '<div class="recording-status recording-inactive">'
                '✅ Recording stopped'
                '</div>',
                unsafe_allow_html=True
            )

    # Recording status indicator
    if hasattr(st.session_state, 'recording') and st.session_state.recording:
        st.markdown(
            '<div class="mobile-alert info">'
            '🎤 Listening... Tap "Stop" when finished speaking.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

def mobile_file_upload():
    """Mobile-optimized file upload interface"""
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    st.markdown('<div class="upload-icon">📱</div>', unsafe_allow_html=True)
    st.markdown("### Upload Document")

    uploaded_file = st.file_uploader(
        "Choose file from your device",
        type=["pdf", "txt", "docx"],
        help="Tap to select from your device storage",
        label_visibility="collapsed"
    )

    if uploaded_file:
        # Show file details
        st.markdown(
            f'<div class="mobile-alert success">'
            f'📄 {uploaded_file.name} ({uploaded_file.size:,} bytes)'
            f'</div>',
            unsafe_allow_html=True
        )

        if st.button("📤 Upload", use_container_width=True, type="primary"):
            # Simulate upload progress
            progress_bar = st.progress(0)
            for i in range(100):
                progress_bar.progress(i + 1)

            st.markdown(
                '<div class="mobile-alert success">'
                '✅ Document uploaded successfully!'
                '</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

def mobile_chat_interface():
    """Mobile-optimized chat interface"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Chat messages area
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    query = st.chat_input("Ask a question about your documents...")

    if query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})

        # Add assistant response (placeholder)
        st.session_state.messages.append({
            "role": "assistant",
            "content": "This is a placeholder response. In the real app, this would be processed by the RAG system."
        })

        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def mobile_stats_dashboard():
    """Mobile-optimized statistics dashboard"""
    st.markdown('<div class="stats-grid">', unsafe_allow_html=True)

    # Sample stats
    stats = [
        {"value": "5", "label": "Documents"},
        {"value": "23", "label": "Queries"},
        {"value": "1.2s", "label": "Avg Response"},
        {"value": "98%", "label": "Success Rate"}
    ]

    cols = st.columns(len(stats))
    for i, stat in enumerate(stats):
        with cols[i]:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-value">{stat["value"]}</div>'
                f'<div class="stat-label">{stat["label"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

def mobile_navigation():
    """Mobile-friendly navigation tabs"""
    tabs = ["💬 Chat", "📄 Upload", "🎤 Voice", "📊 Stats", "⚙️ Settings"]

    st.markdown('<div class="mobile-tabs">', unsafe_allow_html=True)

    # Use selectbox for mobile navigation
    selected_tab = st.selectbox(
        "Navigate",
        tabs,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    return selected_tab

def render_mobile_fab():
    """Render floating action button for quick actions"""
    st.markdown(
        '''
        <button class="fab" onclick="scrollToTop()" title="Scroll to top">
            ⬆️
        </button>
        <script>
        function scrollToTop() {
            window.scrollTo({top: 0, behavior: 'smooth'});
        }
        </script>
        ''',
        unsafe_allow_html=True
    )

def mobile_responsive_layout():
    """Apply mobile-responsive layout adjustments"""
    # Detect mobile device (basic detection)
    user_agent = st.experimental_get_query_params().get('mobile', [False])[0]

    # Apply mobile CSS
    apply_mobile_css()

    # Add viewport meta tag for mobile
    st.markdown(
        '''
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
        ''',
        unsafe_allow_html=True
    )

def mobile_keyboard_optimizations():
    """Add mobile keyboard optimizations"""
    keyboard_js = """
    <script>
    // Prevent zoom on input focus for iOS
    document.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            // Temporarily disable zoom
            const viewport = document.querySelector('meta[name=viewport]');
            if (viewport) {
                viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            }
        }
    });

    document.addEventListener('focusout', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            // Re-enable zoom
            const viewport = document.querySelector('meta[name=viewport]');
            if (viewport) {
                viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=yes';
            }
        }
    });

    // Handle virtual keyboard on mobile
    window.addEventListener('resize', function() {
        // Adjust layout when virtual keyboard appears
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', vh + 'px');
    });
    </script>
    """
    st.markdown(keyboard_js, unsafe_allow_html=True)

def get_device_info():
    """Get basic device information for mobile optimization"""
    device_js = """
    <script>
    const deviceInfo = {
        isMobile: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
        isTablet: /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent),
        isDesktop: !/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
        screenWidth: window.screen.width,
        screenHeight: window.screen.height,
        pixelRatio: window.devicePixelRatio
    };

    // Store in session storage for Python access
    sessionStorage.setItem('deviceInfo', JSON.stringify(deviceInfo));
    </script>
    """
    st.markdown(device_js, unsafe_allow_html=True)

# Export all mobile optimization functions
__all__ = [
    'apply_mobile_css',
    'mobile_voice_recorder',
    'mobile_file_upload',
    'mobile_chat_interface',
    'mobile_stats_dashboard',
    'mobile_navigation',
    'render_mobile_fab',
    'mobile_responsive_layout',
    'mobile_keyboard_optimizations',
    'get_device_info'
]
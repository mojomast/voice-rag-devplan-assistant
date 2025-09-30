import streamlit as st
import streamlit.components.v1 as components
import base64
import io
import json
from typing import Optional, Dict, Any

def native_audio_recorder(
    height: int = 300,
    auto_start: bool = False,
    recording_color: str = "#dc3545",
    background_color: str = "#f8f9fa"
) -> Optional[Dict[str, Any]]:
    """Advanced audio recorder with native device access"""

    audio_recorder_html = f"""
    <div id="audio-recorder-container">
        <div class="recorder-controls">
            <button id="start-btn" class="recorder-btn start-btn">
                🎙️ Start Recording
            </button>
            <button id="stop-btn" class="recorder-btn stop-btn" disabled>
                ⏹️ Stop Recording
            </button>
            <button id="play-btn" class="recorder-btn play-btn" disabled>
                ▶️ Play
            </button>
            <button id="download-btn" class="recorder-btn download-btn" disabled>
                💾 Download
            </button>
            <button id="clear-btn" class="recorder-btn clear-btn" disabled>
                🗑️ Clear
            </button>
        </div>

        <div class="recording-status">
            <div id="status-indicator" class="status-idle">Ready to record</div>
            <div id="timer">00:00</div>
            <div id="audio-level">
                <div class="level-bar">
                    <div id="level-fill"></div>
                </div>
            </div>
        </div>

        <canvas id="visualizer" width="400" height="100"></canvas>
        <audio id="audio-playback" controls style="display: none;"></audio>

        <div class="recording-info" style="display: none;">
            <div class="info-item">
                <span class="info-label">Format:</span>
                <span id="format-info">WebM/Opus</span>
            </div>
            <div class="info-item">
                <span class="info-label">Sample Rate:</span>
                <span id="sample-rate-info">44.1 kHz</span>
            </div>
            <div class="info-item">
                <span class="info-label">Size:</span>
                <span id="size-info">0 KB</span>
            </div>
        </div>
    </div>

    <style>
        #audio-recorder-container {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
            background-color: {background_color};
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .recorder-controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }}

        .recorder-btn {{
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
            min-width: 120px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .start-btn {{
            background: linear-gradient(145deg, #28a745, #20a03a);
            color: white;
        }}
        .start-btn:hover {{
            background: linear-gradient(145deg, #218838, #1e7e34);
            transform: translateY(-1px);
        }}

        .stop-btn {{
            background: linear-gradient(145deg, {recording_color}, #c82333);
            color: white;
        }}
        .stop-btn:hover {{
            background: linear-gradient(145deg, #c82333, #bd2130);
            transform: translateY(-1px);
        }}

        .play-btn {{
            background: linear-gradient(145deg, #007bff, #0056b3);
            color: white;
        }}
        .play-btn:hover {{
            background: linear-gradient(145deg, #0056b3, #004085);
            transform: translateY(-1px);
        }}

        .download-btn {{
            background: linear-gradient(145deg, #6c757d, #545b62);
            color: white;
        }}
        .download-btn:hover {{
            background: linear-gradient(145deg, #545b62, #495057);
            transform: translateY(-1px);
        }}

        .clear-btn {{
            background: linear-gradient(145deg, #ffc107, #e0a800);
            color: #212529;
        }}
        .clear-btn:hover {{
            background: linear-gradient(145deg, #e0a800, #d39e00);
            transform: translateY(-1px);
        }}

        .recorder-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }}

        .recording-status {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        .status-idle {{
            color: #6c757d;
            font-weight: 500;
        }}
        .status-recording {{
            color: {recording_color};
            font-weight: bold;
            animation: pulse 1.5s infinite;
        }}
        .status-ready {{
            color: #28a745;
            font-weight: bold;
        }}

        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
            100% {{ opacity: 1; }}
        }}

        #timer {{
            font-family: 'Courier New', monospace;
            font-size: 20px;
            font-weight: bold;
            color: #495057;
            background: #e9ecef;
            padding: 8px 12px;
            border-radius: 6px;
            min-width: 80px;
            text-align: center;
        }}

        .level-bar {{
            width: 100px;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 0 10px;
        }}

        #level-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #ffc107, {recording_color});
            width: 0%;
            transition: width 0.1s ease;
            border-radius: 4px;
        }}

        #visualizer {{
            width: 100%;
            height: 100px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background: white;
            margin-bottom: 15px;
        }}

        #audio-playback {{
            width: 100%;
            margin-top: 15px;
            border-radius: 8px;
        }}

        .recording-info {{
            display: flex;
            justify-content: space-around;
            margin-top: 15px;
            padding: 12px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        .info-item {{
            text-align: center;
        }}

        .info-label {{
            display: block;
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 4px;
            font-weight: 500;
        }}

        .info-item span:last-child {{
            font-weight: bold;
            color: #495057;
        }}

        .permission-warning {{
            background: #fff3cd;
            color: #856404;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 1px solid #ffeaa7;
        }}

        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 1px solid #f5c6cb;
        }}
    </style>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let audioContext;
        let analyser;
        let microphone;
        let recordingTimer;
        let startTime;
        let animationFrame;
        let recordedBlob;

        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const playBtn = document.getElementById('play-btn');
        const downloadBtn = document.getElementById('download-btn');
        const clearBtn = document.getElementById('clear-btn');
        const statusIndicator = document.getElementById('status-indicator');
        const timer = document.getElementById('timer');
        const visualizer = document.getElementById('visualizer');
        const audioPlayback = document.getElementById('audio-playback');
        const levelFill = document.getElementById('level-fill');
        const recordingInfo = document.querySelector('.recording-info');
        const formatInfo = document.getElementById('format-info');
        const sampleRateInfo = document.getElementById('sample-rate-info');
        const sizeInfo = document.getElementById('size-info');

        // Check for browser support
        function checkBrowserSupport() {{
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                showError('Your browser does not support audio recording. Please use a modern browser.');
                return false;
            }}
            if (!window.MediaRecorder) {{
                showError('MediaRecorder API is not supported in your browser.');
                return false;
            }}
            return true;
        }}

        function showError(message) {{
            const container = document.getElementById('audio-recorder-container');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            container.insertBefore(errorDiv, container.firstChild);
        }}

        function showWarning(message) {{
            const container = document.getElementById('audio-recorder-container');
            const warningDiv = document.createElement('div');
            warningDiv.className = 'permission-warning';
            warningDiv.textContent = message;
            container.insertBefore(warningDiv, container.firstChild);
        }}

        // Initialize audio visualization
        function setupAudioVisualization(stream) {{
            try {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);

                analyser.fftSize = 256;
                analyser.smoothingTimeConstant = 0.3;
                microphone.connect(analyser);

                visualizeAudio();
            }} catch (error) {{
                console.error('Error setting up audio visualization:', error);
            }}
        }}

        function visualizeAudio() {{
            const canvas = visualizer;
            const ctx = canvas.getContext('2d');
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            function draw() {{
                if (!mediaRecorder || mediaRecorder.state !== 'recording') return;

                animationFrame = requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);

                // Clear canvas
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Calculate average volume for level meter
                const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
                const levelPercent = (average / 255) * 100;
                levelFill.style.width = levelPercent + '%';

                // Draw frequency bars
                const barWidth = (canvas.width / bufferLength) * 2.5;
                let barHeight;
                let x = 0;

                for (let i = 0; i < bufferLength; i++) {{
                    barHeight = (dataArray[i] / 255) * canvas.height * 0.8;

                    // Create gradient colors
                    const hue = (i / bufferLength) * 360;
                    ctx.fillStyle = `hsl(${{hue}}, 70%, 60%)`;

                    ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                    x += barWidth + 1;
                }}
            }}

            draw();
        }}

        function updateTimer() {{
            if (!startTime) return;
            const elapsed = Date.now() - startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            timer.textContent = `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
        }}

        function formatFileSize(bytes) {{
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }}

        async function startRecording() {{
            try {{
                // Request microphone access with high-quality settings
                const stream = await navigator.mediaDevices.getUserMedia({{
                    audio: {{
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 44100,
                        channelCount: 2,
                        sampleSize: 16
                    }}
                }});

                setupAudioVisualization(stream);

                // Determine the best supported format
                const mimeTypes = [
                    'audio/webm;codecs=opus',
                    'audio/webm',
                    'audio/ogg;codecs=opus',
                    'audio/mp4',
                    'audio/wav'
                ];

                let selectedMimeType = '';
                for (const mimeType of mimeTypes) {{
                    if (MediaRecorder.isTypeSupported(mimeType)) {{
                        selectedMimeType = mimeType;
                        break;
                    }}
                }}

                if (!selectedMimeType) {{
                    throw new Error('No supported audio format found');
                }}

                mediaRecorder = new MediaRecorder(stream, {{
                    mimeType: selectedMimeType,
                    audioBitsPerSecond: 128000
                }});

                formatInfo.textContent = selectedMimeType.includes('webm') ? 'WebM/Opus' :
                                       selectedMimeType.includes('ogg') ? 'OGG/Opus' :
                                       selectedMimeType.includes('mp4') ? 'MP4/AAC' : 'WAV';

                audioChunks = [];

                mediaRecorder.ondataavailable = function(event) {{
                    if (event.data.size > 0) {{
                        audioChunks.push(event.data);
                    }}
                }};

                mediaRecorder.onstop = function() {{
                    recordedBlob = new Blob(audioChunks, {{ type: selectedMimeType }});
                    const audioUrl = URL.createObjectURL(recordedBlob);

                    audioPlayback.src = audioUrl;
                    audioPlayback.style.display = 'block';
                    recordingInfo.style.display = 'flex';

                    // Update file size info
                    sizeInfo.textContent = formatFileSize(recordedBlob.size);

                    // Convert to base64 and send to Streamlit
                    const reader = new FileReader();
                    reader.onloadend = function() {{
                        const base64Audio = reader.result.split(',')[1];
                        const audioData = {{
                            type: 'audio-recorded',
                            data: base64Audio,
                            mimeType: selectedMimeType,
                            size: recordedBlob.size,
                            duration: timer.textContent
                        }};

                        // Send to Streamlit
                        window.parent.postMessage(audioData, '*');

                        // Also store in session storage for retrieval
                        sessionStorage.setItem('recorded_audio', JSON.stringify(audioData));
                    }};
                    reader.readAsDataURL(recordedBlob);

                    // Enable controls
                    playBtn.disabled = false;
                    downloadBtn.disabled = false;
                    clearBtn.disabled = false;

                    statusIndicator.textContent = 'Recording ready for playback';
                    statusIndicator.className = 'status-ready';
                }};

                mediaRecorder.start(100); // Collect data every 100ms
                startTime = Date.now();
                recordingTimer = setInterval(updateTimer, 100);

                // Update UI
                startBtn.disabled = true;
                stopBtn.disabled = false;
                playBtn.disabled = true;
                downloadBtn.disabled = true;
                clearBtn.disabled = true;

                statusIndicator.textContent = 'Recording in progress...';
                statusIndicator.className = 'status-recording';

            }} catch (err) {{
                console.error('Error accessing microphone:', err);

                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {{
                    showWarning('Microphone access denied. Please allow microphone permissions and reload the page.');
                }} else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {{
                    showError('No microphone found. Please connect a microphone and try again.');
                }} else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {{
                    showError('Microphone is already in use by another application.');
                }} else {{
                    showError('Error accessing microphone: ' + err.message);
                }}
            }}
        }}

        function stopRecording() {{
            if (mediaRecorder && mediaRecorder.state === 'recording') {{
                mediaRecorder.stop();
                clearInterval(recordingTimer);

                // Stop all audio tracks
                mediaRecorder.stream.getTracks().forEach(track => track.stop());

                // Update UI
                startBtn.disabled = false;
                stopBtn.disabled = true;

                // Stop animation
                if (animationFrame) {{
                    cancelAnimationFrame(animationFrame);
                }}

                // Reset level meter
                levelFill.style.width = '0%';

                if (audioContext) {{
                    audioContext.close();
                }}
            }}
        }}

        function playRecording() {{
            if (audioPlayback.src) {{
                audioPlayback.play();
                playBtn.textContent = '⏸️ Playing...';

                audioPlayback.onended = function() {{
                    playBtn.textContent = '▶️ Play';
                }};

                audioPlayback.onpause = function() {{
                    playBtn.textContent = '▶️ Play';
                }};
            }}
        }}

        function downloadRecording() {{
            if (recordedBlob) {{
                const url = URL.createObjectURL(recordedBlob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `recording_${{new Date().toISOString().replace(/[:.]/g, '-')}}.webm`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
        }}

        function clearRecording() {{
            // Reset all states
            audioChunks = [];
            recordedBlob = null;

            // Clear UI
            audioPlayback.src = '';
            audioPlayback.style.display = 'none';
            recordingInfo.style.display = 'none';
            timer.textContent = '00:00';
            levelFill.style.width = '0%';

            // Clear canvas
            const ctx = visualizer.getContext('2d');
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, visualizer.width, visualizer.height);

            // Reset buttons
            playBtn.disabled = true;
            downloadBtn.disabled = true;
            clearBtn.disabled = true;
            playBtn.textContent = '▶️ Play';

            // Reset status
            statusIndicator.textContent = 'Ready to record';
            statusIndicator.className = 'status-idle';

            // Clear session storage
            sessionStorage.removeItem('recorded_audio');

            // Notify Streamlit
            window.parent.postMessage({{
                type: 'audio-cleared'
            }}, '*');
        }}

        // Event listeners
        startBtn.addEventListener('click', startRecording);
        stopBtn.addEventListener('click', stopRecording);
        playBtn.addEventListener('click', playRecording);
        downloadBtn.addEventListener('click', downloadRecording);
        clearBtn.addEventListener('click', clearRecording);

        // Initialize
        if (checkBrowserSupport()) {{
            // Check for microphone permissions
            navigator.permissions.query({{name: 'microphone'}}).then(function(result) {{
                if (result.state === 'denied') {{
                    showWarning('Microphone access is denied. Please enable microphone permissions in your browser settings.');
                    startBtn.disabled = true;
                }} else if (result.state === 'prompt') {{
                    showWarning('Click "Start Recording" to grant microphone access.');
                }}

                result.onchange = function() {{
                    if (result.state === 'granted') {{
                        location.reload(); // Reload to clear warnings
                    }}
                }};
            }}).catch(function(err) {{
                console.log('Permission query not supported:', err);
            }});

            // Auto-start if requested
            if ({str(auto_start).lower()}) {{
                setTimeout(startRecording, 1000);
            }}
        }}

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.target.tagName.toLowerCase() === 'input') return;

            switch(e.key) {{
                case ' ': // Spacebar
                    e.preventDefault();
                    if (!startBtn.disabled) {{
                        startRecording();
                    }} else if (!stopBtn.disabled) {{
                        stopRecording();
                    }}
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (!playBtn.disabled) {{
                        playRecording();
                    }}
                    break;
                case 'Escape':
                    e.preventDefault();
                    if (!clearBtn.disabled) {{
                        clearRecording();
                    }}
                    break;
            }}
        }});
    </script>
    """

    # Render the component and capture return value
    component_value = components.html(audio_recorder_html, height=height)

    # Try to get recorded audio data from browser
    try:
        # Check if there's recorded audio data in the browser session
        import streamlit as st
        if 'recorded_audio_data' not in st.session_state:
            st.session_state.recorded_audio_data = None

        # Handle component return value
        if component_value and isinstance(component_value, dict):
            if component_value.get('type') == 'audio-recorded':
                st.session_state.recorded_audio_data = {
                    'audio_data': component_value.get('data'),
                    'mime_type': component_value.get('mimeType', 'audio/webm'),
                    'size': component_value.get('size', 0),
                    'duration': component_value.get('duration', '00:00')
                }
                return st.session_state.recorded_audio_data
            elif component_value.get('type') == 'audio-cleared':
                st.session_state.recorded_audio_data = None
                return None

        return st.session_state.recorded_audio_data

    except Exception as e:
        st.error(f"Error handling audio recording: {e}")
        return None

def get_recorded_audio_as_bytes(audio_data: Dict[str, Any]) -> Optional[bytes]:
    """Convert base64 audio data to bytes"""
    if not audio_data or not audio_data.get('audio_data'):
        return None

    try:
        import base64
        return base64.b64decode(audio_data['audio_data'])
    except Exception as e:
        st.error(f"Error converting audio data: {e}")
        return None

def save_recorded_audio(audio_data: Dict[str, Any], filename: str = None) -> Optional[str]:
    """Save recorded audio to a file"""
    if not audio_data:
        return None

    audio_bytes = get_recorded_audio_as_bytes(audio_data)
    if not audio_bytes:
        return None

    try:
        import os
        from datetime import datetime

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = ".webm" if "webm" in audio_data.get('mime_type', '') else ".wav"
            filename = f"recording_{timestamp}{extension}"

        # Ensure the uploads directory exists
        upload_dir = "temp_audio"
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(audio_bytes)

        return filepath

    except Exception as e:
        st.error(f"Error saving audio file: {e}")
        return None

# Example usage component
def audio_recorder_demo():
    """Demo component showing how to use the native audio recorder"""
    st.title("🎤 Native Audio Recorder Demo")

    st.markdown("""
    This component provides advanced audio recording capabilities with:
    - **Real-time visualization** of audio waveforms
    - **High-quality recording** with noise cancellation
    - **Multiple format support** (WebM/Opus, OGG, MP4, WAV)
    - **Audio level monitoring** with visual feedback
    - **Keyboard shortcuts** (Spacebar: record/stop, Enter: play, Escape: clear)
    - **Download functionality** for recorded audio
    """)

    # Configuration options
    with st.sidebar:
        st.header("Recording Settings")
        height = st.slider("Component Height", 250, 500, 300)
        auto_start = st.checkbox("Auto-start recording", False)
        recording_color = st.color_picker("Recording Color", "#dc3545")
        background_color = st.color_picker("Background Color", "#f8f9fa")

    # Main recorder component
    audio_data = native_audio_recorder(
        height=height,
        auto_start=auto_start,
        recording_color=recording_color,
        background_color=background_color
    )

    # Display recording information
    if audio_data:
        st.success("✅ Audio recorded successfully!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Duration", audio_data.get('duration', 'Unknown'))
        with col2:
            st.metric("File Size", f"{audio_data.get('size', 0) / 1024:.1f} KB")
        with col3:
            st.metric("Format", audio_data.get('mime_type', 'Unknown'))

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Save to File"):
                filepath = save_recorded_audio(audio_data)
                if filepath:
                    st.success(f"Audio saved to: {filepath}")

        with col2:
            if st.button("🔄 Process with AI"):
                with st.spinner("Processing audio..."):
                    audio_bytes = get_recorded_audio_as_bytes(audio_data)
                    if audio_bytes:
                        # Here you would integrate with your voice service
                        st.info("Audio ready for AI processing!")
                        st.code(f"Audio data: {len(audio_bytes)} bytes")

        with col3:
            if st.button("📤 Upload to Backend"):
                # Here you would upload to your backend API
                st.info("Upload functionality would be implemented here")

    else:
        st.info("📼 Record some audio using the controls above")

    # Tips and keyboard shortcuts
    with st.expander("💡 Tips & Keyboard Shortcuts"):
        st.markdown("""
        **Keyboard Shortcuts:**
        - `Spacebar`: Start/Stop recording
        - `Enter`: Play recorded audio
        - `Escape`: Clear recording

        **Recording Tips:**
        - Ensure microphone permissions are granted
        - Use headphones to prevent feedback
        - Record in a quiet environment for best quality
        - The visualizer shows real-time audio levels
        """)

if __name__ == "__main__":
    audio_recorder_demo()
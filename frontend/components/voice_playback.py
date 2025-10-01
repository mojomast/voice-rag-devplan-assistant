import streamlit as st
import streamlit.components.v1 as components
import base64
import io
import json
import time
from typing import Optional, Dict, Any, List
import requests

class VoicePlaybackComponent:
    """Enhanced voice playback component for TTS audio with advanced controls"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        self.api_url = api_url
        self.playback_history = []
        
    def render_voice_playback(
        self,
        audio_data: Optional[Dict[str, Any]] = None,
        auto_play: bool = False,
        show_controls: bool = True,
        height: int = 200,
        theme: str = "light"
    ) -> Dict[str, Any]:
        """
        Render enhanced voice playback component
        
        Args:
            audio_data: Dictionary containing audio information (base64 data, mime_type, etc.)
            auto_play: Whether to automatically start playback
            show_controls: Whether to show playback controls
            height: Component height in pixels
            theme: Visual theme ("light" or "dark")
            
        Returns:
            Dictionary with playback state and user interactions
        """
        
        # Theme colors
        if theme == "dark":
            bg_color = "#1a1a1a"
            text_color = "#ffffff"
            accent_color = "#0066cc"
        else:
            bg_color = "#ffffff"
            text_color = "#000000"
            accent_color = "#007bff"
        
        # Initialize session state for playback
        if 'voice_playback_state' not in st.session_state:
            st.session_state.voice_playback_state = {
                'is_playing': False,
                'current_time': 0,
                'duration': 0,
                'volume': 1.0,
                'playback_rate': 1.0,
                'loop': False
            }
        
        # HTML component with enhanced audio player
        voice_playback_html = f"""
        <div id="voice-playback-container" style="
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 10px 0;
        ">
            <!-- Audio Player Header -->
            <div class="player-header" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            ">
                <h3 style="margin: 0; font-size: 18px; color: {text_color};">
                    🔊 Voice Playback
                </h3>
                <div class="player-status" id="player-status" style="
                    background: {accent_color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 500;
                ">
                    Ready
                </div>
            </div>
            
            <!-- Main Audio Player -->
            <audio id="voice-audio-player" controls style="
                width: 100%;
                margin-bottom: 15px;
                border-radius: 8px;
            "></audio>
            
            <!-- Enhanced Controls -->
            <div class="enhanced-controls" style="
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 15px;
            ">
                <!-- Volume Control -->
                <div class="control-group">
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">
                        🔊 Volume: <span id="volume-value">100%</span>
                    </label>
                    <input type="range" id="volume-slider" min="0" max="1" step="0.1" value="1" style="
                        width: 100%;
                        height: 6px;
                        border-radius: 3px;
                        background: #ddd;
                        outline: none;
                    ">
                </div>
                
                <!-- Playback Rate Control -->
                <div class="control-group">
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">
                        ⚡ Speed: <span id="speed-value">1.0x</span>
                    </label>
                    <input type="range" id="speed-slider" min="0.5" max="2" step="0.1" value="1" style="
                        width: 100%;
                        height: 6px;
                        border-radius: 3px;
                        background: #ddd;
                        outline: none;
                    ">
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="action-buttons" style="
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-bottom: 15px;
            ">
                <button id="play-pause-btn" class="control-btn primary" style="
                    background: {accent_color};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                ">
                    ▶️ Play
                </button>
                
                <button id="stop-btn" class="control-btn secondary" style="
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                ">
                    ⏹️ Stop
                </button>
                
                <button id="loop-btn" class="control-btn secondary" style="
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                ">
                    🔁 Loop: OFF
                </button>
                
                <button id="download-btn" class="control-btn secondary" style="
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                ">
                    💾 Download
                </button>
            </div>
            
            <!-- Progress Bar -->
            <div class="progress-container" style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span id="current-time">0:00</span>
                    <span id="duration">0:00</span>
                </div>
                <div class="progress-bar" style="
                    width: 100%;
                    height: 8px;
                    background: #e9ecef;
                    border-radius: 4px;
                    position: relative;
                    cursor: pointer;
                ">
                    <div id="progress-fill" style="
                        width: 0%;
                        height: 100%;
                        background: {accent_color};
                        border-radius: 4px;
                        transition: width 0.1s ease;
                    "></div>
                </div>
            </div>
            
            <!-- Audio Info -->
            <div class="audio-info" id="audio-info" style="
                background: rgba(0, 0, 0, 0.05);
                padding: 10px;
                border-radius: 6px;
                font-size: 12px;
                display: none;
            ">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div><strong>Format:</strong> <span id="info-format">-</span></div>
                    <div><strong>Size:</strong> <span id="info-size">-</span></div>
                    <div><strong>Duration:</strong> <span id="info-duration">-</span></div>
                    <div><strong>Quality:</strong> <span id="info-quality">-</span></div>
                </div>
            </div>
            
            <!-- Error Message -->
            <div id="error-message" class="error-message" style="
                background: #f8d7da;
                color: #721c24;
                padding: 10px;
                border-radius: 6px;
                margin-top: 10px;
                display: none;
            "></div>
        </div>
        
        <style>
            .control-btn:hover {{
                opacity: 0.8;
                transform: translateY(-1px);
                transition: all 0.2s ease;
            }}
            
            .control-btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            
            input[type="range"]::-webkit-slider-thumb {{
                appearance: none;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: {accent_color};
                cursor: pointer;
            }}
            
            input[type="range"]::-moz-range-thumb {{
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: {accent_color};
                cursor: pointer;
                border: none;
            }}
            
            .progress-bar:hover #progress-fill {{
                opacity: 0.8;
            }}
        </style>
        
        <script>
            // Audio player state
            let audioPlayer = document.getElementById('voice-audio-player');
            let playPauseBtn = document.getElementById('play-pause-btn');
            let stopBtn = document.getElementById('stop-btn');
            let loopBtn = document.getElementById('loop-btn');
            let downloadBtn = document.getElementById('download-btn');
            let volumeSlider = document.getElementById('volume-slider');
            let speedSlider = document.getElementById('speed-slider');
            let progressFill = document.getElementById('progress-fill');
            let currentTimeEl = document.getElementById('current-time');
            let durationEl = document.getElementById('duration');
            let playerStatus = document.getElementById('player-status');
            let audioInfo = document.getElementById('audio-info');
            let errorMessage = document.getElementById('error-message');
            
            let isLooping = false;
            let currentAudioData = null;
            
            // Initialize with audio data if provided
            {f'initializeAudio({json.dumps(audio_data)});' if audio_data else ''}
            
            function initializeAudio(audioData) {{
                if (!audioData || !audioData.audio_base64) {{
                    showError('No audio data available');
                    return;
                }}
                
                try {{
                    currentAudioData = audioData;
                    
                    // Create audio blob from base64
                    const audioBytes = atob(audioData.audio_base64);
                    const audioArray = new Uint8Array(audioBytes.length);
                    for (let i = 0; i < audioBytes.length; i++) {{
                        audioArray[i] = audioBytes.charCodeAt(i);
                    }}
                    
                    const audioBlob = new Blob([audioArray], {{ type: audioData.mime_type || 'audio/mpeg' }});
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Set audio source
                    audioPlayer.src = audioUrl;
                    
                    // Update audio info
                    updateAudioInfo(audioData);
                    
                    // Auto-play if requested
                    if ({str(auto_play).lower()}) {{
                        audioPlayer.play();
                    }}
                    
                    updateStatus('Loaded');
                    
                }} catch (error) {{
                    showError('Failed to load audio: ' + error.message);
                }}
            }}
            
            function updateAudioInfo(audioData) {{
                document.getElementById('info-format').textContent = audioData.mime_type || 'Unknown';
                document.getElementById('info-size').textContent = formatFileSize(audioData.audio_size || 0);
                document.getElementById('info-duration').textContent = audioData.duration || 'Unknown';
                document.getElementById('info-quality').textContent = 'High';
                audioInfo.style.display = 'block';
            }}
            
            function formatFileSize(bytes) {{
                if (bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }}
            
            function formatTime(seconds) {{
                if (isNaN(seconds)) return '0:00';
                const minutes = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${{minutes}}:${{secs.toString().padStart(2, '0')}}`;
            }}
            
            function updateStatus(status) {{
                playerStatus.textContent = status;
                playerStatus.style.background = status === 'Playing' ? '#28a745' : 
                                              status === 'Error' ? '#dc3545' : '#6c757d';
            }}
            
            function showError(message) {{
                errorMessage.textContent = message;
                errorMessage.style.display = 'block';
                updateStatus('Error');
            }}
            
            // Audio event listeners
            audioPlayer.addEventListener('loadedmetadata', function() {{
                durationEl.textContent = formatTime(audioPlayer.duration);
            }});
            
            audioPlayer.addEventListener('timeupdate', function() {{
                currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
                const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
                progressFill.style.width = progress + '%';
            }});
            
            audioPlayer.addEventListener('play', function() {{
                playPauseBtn.innerHTML = '⏸️ Pause';
                updateStatus('Playing');
            }});
            
            audioPlayer.addEventListener('pause', function() {{
                playPauseBtn.innerHTML = '▶️ Play';
                updateStatus('Paused');
            }});
            
            audioPlayer.addEventListener('ended', function() {{
                if (isLooping) {{
                    audioPlayer.currentTime = 0;
                    audioPlayer.play();
                }} else {{
                    playPauseBtn.innerHTML = '▶️ Play';
                    updateStatus('Ended');
                }}
            }});
            
            audioPlayer.addEventListener('error', function() {{
                showError('Audio playback error: ' + audioPlayer.error.message);
            }});
            
            // Control event listeners
            playPauseBtn.addEventListener('click', function() {{
                if (audioPlayer.paused) {{
                    audioPlayer.play();
                }} else {{
                    audioPlayer.pause();
                }}
            }});
            
            stopBtn.addEventListener('click', function() {{
                audioPlayer.pause();
                audioPlayer.currentTime = 0;
                playPauseBtn.innerHTML = '▶️ Play';
                updateStatus('Stopped');
            }});
            
            loopBtn.addEventListener('click', function() {{
                isLooping = !isLooping;
                audioPlayer.loop = isLooping;
                loopBtn.innerHTML = `🔁 Loop: ${{isLooping ? 'ON' : 'OFF'}}`;
                loopBtn.style.background = isLooping ? '#28a745' : '#6c757d';
            }});
            
            downloadBtn.addEventListener('click', function() {{
                if (currentAudioData && currentAudioData.audio_base64) {{
                    const audioBytes = atob(currentAudioData.audio_base64);
                    const audioArray = new Uint8Array(audioBytes.length);
                    for (let i = 0; i < audioBytes.length; i++) {{
                        audioArray[i] = audioBytes.charCodeAt(i);
                    }}
                    
                    const audioBlob = new Blob([audioArray], {{ type: currentAudioData.mime_type || 'audio/mpeg' }});
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    const a = document.createElement('a');
                    a.href = audioUrl;
                    a.download = `voice_audio_${{new Date().toISOString().replace(/[:.]/g, '-')}}.${{currentAudioData.mime_type?.split('/')[1] || 'mp3'}}`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(audioUrl);
                }}
            }});
            
            volumeSlider.addEventListener('input', function() {{
                audioPlayer.volume = this.value;
                document.getElementById('volume-value').textContent = Math.round(this.value * 100) + '%';
            }});
            
            speedSlider.addEventListener('input', function() {{
                audioPlayer.playbackRate = this.value;
                document.getElementById('speed-value').textContent = this.value + 'x';
            }});
            
            // Progress bar click to seek
            document.querySelector('.progress-bar').addEventListener('click', function(e) {{
                if (audioPlayer.duration) {{
                    const rect = this.getBoundingClientRect();
                    const percent = (e.clientX - rect.left) / rect.width;
                    audioPlayer.currentTime = percent * audioPlayer.duration;
                }}
            }});
            
            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {{
                if (e.target.tagName.toLowerCase() === 'input') return;
                
                switch(e.key) {{
                    case ' ':
                        e.preventDefault();
                        if (audioPlayer.paused) {{
                            audioPlayer.play();
                        }} else {{
                            audioPlayer.pause();
                        }}
                        break;
                    case 'ArrowLeft':
                        e.preventDefault();
                        audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 5);
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 5);
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        audioPlayer.volume = Math.min(1, audioPlayer.volume + 0.1);
                        volumeSlider.value = audioPlayer.volume;
                        document.getElementById('volume-value').textContent = Math.round(audioPlayer.volume * 100) + '%';
                        break;
                    case 'ArrowDown':
                        e.preventDefault();
                        audioPlayer.volume = Math.max(0, audioPlayer.volume - 0.1);
                        volumeSlider.value = audioPlayer.volume;
                        document.getElementById('volume-value').textContent = Math.round(audioPlayer.volume * 100) + '%';
                        break;
                }}
            }});
            
            // Function to update audio data from external calls
            window.updateAudioData = function(audioData) {{
                initializeAudio(audioData);
            }};
        </script>
        """
        
        # Render the component
        components.html(voice_playback_html, height=height)
        
        # Return playback state
        return {
            'component_loaded': True,
            'audio_data': audio_data,
            'auto_play': auto_play,
            'theme': theme
        }
    
    def synthesize_and_play(
        self,
        text: str,
        voice: str = "alloy",
        auto_play: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synthesize speech and prepare for playback
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            auto_play: Whether to auto-play after synthesis
            **kwargs: Additional synthesis parameters
            
        Returns:
            Dictionary with synthesis result and audio data
        """
        
        if not text or not text.strip():
            return {
                'status': 'error',
                'error': 'Text is required for speech synthesis',
                'audio_data': None
            }
        
        with st.spinner("🎙️ Synthesizing speech..."):
            try:
                # Call TTS API
                response = requests.post(
                    f"{self.api_url}/voice/synthesize/base64",
                    json={
                        "text": text,
                        "voice": voice,
                        "use_cache": True,
                        **kwargs
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        audio_data = {
                            "audio_base64": result.get("audio_base64"),
                            "mime_type": result.get("mime_type", "audio/mpeg"),
                            "voice": result.get("voice", voice),
                            "text_length": result.get("text_length", len(text)),
                            "audio_size": result.get("audio_size", 0),
                            "text": text,
                            "duration": "Unknown"
                        }
                        
                        # Store in session state for playback
                        st.session_state.current_audio_data = audio_data
                        
                        # Add to playback history
                        self.playback_history.append({
                            "timestamp": time.time(),
                            "text": text,
                            "voice": voice,
                            "audio_data": audio_data
                        })
                        
                        st.success("✅ Speech synthesized successfully!")
                        return {
                            'status': 'success',
                            'audio_data': audio_data,
                            'text': text,
                            'voice': voice
                        }
                    else:
                        st.error(f"❌ Speech synthesis failed: {result.get('error', 'Unknown error')}")
                        return {
                            'status': 'error',
                            'error': result.get('error', 'Unknown error'),
                            'audio_data': None
                        }
                else:
                    st.error(f"❌ API request failed: {response.status_code}")
                    return {
                        'status': 'error',
                        'error': f"API request failed: {response.status_code}",
                        'audio_data': None
                    }
                    
            except requests.RequestException as e:
                st.error(f"❌ Network error during speech synthesis: {e}")
                return {
                    'status': 'error',
                    'error': f"Network error: {e}",
                    'audio_data': None
                }
            except Exception as e:
                st.error(f"❌ Unexpected error during speech synthesis: {e}")
                return {
                    'status': 'error',
                    'error': f"Unexpected error: {e}",
                    'audio_data': None
                }
    
    def render_playback_history(self) -> None:
        """Render playback history sidebar"""
        if not self.playback_history:
            st.info("No playback history yet")
            return
        
        st.subheader("📚 Playback History")
        
        for i, item in enumerate(reversed(self.playback_history[-5:])):  # Show last 5 items
            with st.expander(f"🎵 {item['text'][:50]}{'...' if len(item['text']) > 50 else ''}", expanded=False):
                st.write(f"**Voice:** {item['voice']}")
                st.write(f"**Time:** {time.strftime('%H:%M:%S', time.localtime(item['timestamp']))}")
                
                if st.button(f"▶️ Play Again", key=f"play_history_{i}"):
                    st.session_state.current_audio_data = item['audio_data']
                    st.rerun()
    
    def render_audio_analyzer(self, audio_data: Dict[str, Any]) -> None:
        """Render audio analysis information"""
        if not audio_data:
            return
        
        st.subheader("📊 Audio Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Format", audio_data.get('mime_type', 'Unknown'))
            st.metric("Voice", audio_data.get('voice', 'Unknown'))
            st.metric("Text Length", f"{audio_data.get('text_length', 0)} characters")
        
        with col2:
            size_mb = audio_data.get('audio_size', 0) / (1024 * 1024)
            st.metric("File Size", f"{size_mb:.2f} MB")
            st.metric("Quality", "High")
            st.metric("Sample Rate", "44.1 kHz")

def render_voice_playback_component(
    audio_data: Optional[Dict[str, Any]] = None,
    api_url: str = "http://127.0.0.1:8000",
    **kwargs
) -> VoicePlaybackComponent:
    """
    Main function to render voice playback component
    
    Args:
        audio_data: Audio data dictionary
        api_url: Backend API URL
        **kwargs: Additional parameters
        
    Returns:
        VoicePlaybackComponent instance
    """
    playback_component = VoicePlaybackComponent(api_url)
    
    # Get current audio data from session state if not provided
    if not audio_data and 'current_audio_data' in st.session_state:
        audio_data = st.session_state.current_audio_data
    
    # Render the playback component
    playback_component.render_voice_playback(audio_data=audio_data, **kwargs)
    
    return playback_component

# Example usage
def voice_playback_demo():
    """Demo function showing how to use the voice playback component"""
    st.title("🔊 Voice Playback Component Demo")
    
    # Initialize component
    playback_component = render_voice_playback_component()
    
    # Text input for synthesis
    st.subheader("🎙️ Text to Speech")
    text_input = st.text_area(
        "Enter text to synthesize:",
        value="Hello! This is a demonstration of the enhanced voice playback component.",
        height=100
    )
    
    # Voice selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_voice = st.selectbox(
            "Select Voice",
            options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            index=0
        )
    
    with col2:
        auto_play = st.checkbox("Auto-play after synthesis", value=True)
    
    with col3:
        show_controls = st.checkbox("Show enhanced controls", value=True)
    
    # Synthesize button
    if st.button("🎙️ Synthesize and Play", type="primary"):
        if text_input.strip():
            result = playback_component.synthesize_and_play(
                text=text_input,
                voice=selected_voice,
                auto_play=auto_play
            )
            
            if result['status'] == 'success':
                st.success("✅ Ready to play!")
                st.rerun()
        else:
            st.warning("⚠️ Please enter some text to synthesize")
    
    # Show playback history
    with st.sidebar:
        playback_component.render_playback_history()
    
    # Show audio analysis if available
    if 'current_audio_data' in st.session_state:
        playback_component.render_audio_analyzer(st.session_state.current_audio_data)

if __name__ == "__main__":
    voice_playback_demo()
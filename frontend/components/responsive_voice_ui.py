import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, Optional, List
import json

class ResponsiveVoiceUI:
    """Responsive and accessible voice UI components"""
    
    def __init__(self):
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1200
        }
        self.accessibility_features = {
            'high_contrast': False,
            'large_text': False,
            'reduced_motion': False,
            'screen_reader': False
        }
        
    def render_responsive_container(self, content_html: str, height: int = 400) -> None:
        """
        Render a responsive container that adapts to different screen sizes
        
        Args:
            content_html: HTML content to render
            height: Base height for the container
        """
        
        responsive_html = f"""
        <div id="responsive-voice-container" class="voice-container">
            <style>
            .voice-container {{
                width: 100%;
                max-width: 100%;
                margin: 0 auto;
                padding: 10px;
                box-sizing: border-box;
            }}
            
            /* Mobile styles */
            @media (max-width: {self.breakpoints['mobile']}px) {{
                .voice-container {{
                    padding: 5px;
                }}
                .voice-controls {{
                    flex-direction: column !important;
                    gap: 10px !important;
                }}
                .voice-button {{
                    width: 100% !important;
                    margin: 2px 0 !important;
                    font-size: 14px !important;
                    padding: 12px 8px !important;
                }}
                .voice-status {{
                    text-align: center !important;
                    font-size: 12px !important;
                }}
                .voice-waveform {{
                    height: 60px !important;
                }}
                .voice-settings {{
                    font-size: 14px !important;
                }}
            }}
            
            /* Tablet styles */
            @media (min-width: {self.breakpoints['mobile']}px) and (max-width: {self.breakpoints['tablet']}px) {{
                .voice-container {{
                    padding: 15px;
                }}
                .voice-controls {{
                    flex-wrap: wrap !important;
                }}
                .voice-button {{
                    flex: 1 1 calc(50% - 10px) !important;
                    margin: 5px !important;
                }}
                .voice-waveform {{
                    height: 80px !important;
                }}
            }}
            
            /* Desktop styles */
            @media (min-width: {self.breakpoints['tablet']}px) {{
                .voice-container {{
                    padding: 20px;
                }}
                .voice-controls {{
                    display: flex !important;
                    gap: 15px !important;
                }}
                .voice-button {{
                    flex: 1 !important;
                    min-width: 120px !important;
                }}
                .voice-waveform {{
                    height: 100px !important;
                }}
            }}
            
            /* Accessibility styles */
            .voice-button:focus {{
                outline: 3px solid #007bff !important;
                outline-offset: 2px !important;
            }}
            
            .voice-button:hover {{
                transform: translateY(-1px);
                transition: transform 0.2s ease;
            }}
            
            .high-contrast {{
                filter: contrast(1.5);
            }}
            
            .large-text {{
                font-size: 1.2em !important;
            }}
            
            .reduced-motion * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
            
            /* Screen reader only content */
            .sr-only {{
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }}
            </style>
            
            <div class="voice-content" role="main" aria-label="Voice Interface">
                {content_html}
            </div>
            
            <script>
            // Detect screen size and apply appropriate styles
            function updateResponsiveLayout() {{
                const container = document.getElementById('responsive-voice-container');
                const width = window.innerWidth;
                
                // Update ARIA labels based on screen size
                const buttons = container.querySelectorAll('.voice-button');
                buttons.forEach(button => {{
                    if (width <= {self.breakpoints['mobile']}) {{
                        button.setAttribute('aria-label', button.textContent + ' (Mobile view)');
                    }} else {{
                        button.setAttribute('aria-label', button.textContent);
                    }}
                }});
                
                // Adjust touch targets for mobile
                if (width <= {self.breakpoints['mobile']}) {{
                    buttons.forEach(button => {{
                        button.style.minHeight = '44px';
                        button.style.minWidth = '44px';
                    }});
                }}
            }}
            
            // Initialize and listen for resize
            document.addEventListener('DOMContentLoaded', updateResponsiveLayout);
            window.addEventListener('resize', updateResponsiveLayout);
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Tab') {{
                    document.body.classList.add('keyboard-navigation');
                }}
            }});
            
            document.addEventListener('mousedown', function() {{
                document.body.classList.remove('keyboard-navigation');
            }});
            
            // Check for reduced motion preference
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
                document.body.classList.add('reduced-motion');
            }}
            
            // Check for high contrast preference
            if (window.matchMedia('(prefers-contrast: high)').matches) {{
                document.body.classList.add('high-contrast');
            }}
            </script>
        </div>
        """
        
        components.html(responsive_html, height=height)
    
    def render_accessible_recorder(self, height: int = 300) -> None:
        """Render an accessible audio recorder"""
        
        recorder_html = """
        <div class="accessible-recorder" role="application" aria-label="Voice Recorder">
            <div class="recorder-header">
                <h2 id="recorder-title">Voice Recorder</h2>
                <div class="recorder-status" role="status" aria-live="polite" aria-atomic="true">
                    <span id="status-text">Ready to record</span>
                </div>
            </div>
            
            <div class="recorder-controls voice-controls" role="group" aria-label="Recording controls">
                <button id="record-btn" class="voice-button record-btn" 
                        aria-label="Start recording" 
                        aria-describedby="recorder-help">
                    <span class="button-icon" aria-hidden="true">🎙️</span>
                    <span class="button-text">Record</span>
                </button>
                
                <button id="stop-btn" class="voice-button stop-btn" 
                        aria-label="Stop recording" disabled>
                    <span class="button-icon" aria-hidden="true">⏹️</span>
                    <span class="button-text">Stop</span>
                </button>
                
                <button id="play-btn" class="voice-button play-btn" 
                        aria-label="Play recording" disabled>
                    <span class="button-icon" aria-hidden="true">▶️</span>
                    <span class="button-text">Play</span>
                </button>
                
                <button id="clear-btn" class="voice-button clear-btn" 
                        aria-label="Clear recording" disabled>
                    <span class="button-icon" aria-hidden="true">🗑️</span>
                    <span class="button-text">Clear</span>
                </button>
            </div>
            
            <div class="recorder-visual" role="img" aria-label="Audio waveform visualization">
                <canvas id="waveform" class="voice-waveform" aria-hidden="true"></canvas>
                <div class="fallback-visual sr-only">
                    Audio level indicator: <span id="audio-level-text">Silent</span>
                </div>
            </div>
            
            <div class="recorder-info">
                <div class="timer" role="timer" aria-label="Recording duration">
                    <span id="timer-display">00:00</span>
                </div>
                
                <div class="audio-info" aria-live="polite">
                    <span id="format-info">Format: WebM</span>
                    <span id="size-info">Size: 0 KB</span>
                </div>
            </div>
            
            <div id="recorder-help" class="help-text sr-only">
                Use the Record button to start recording audio from your microphone.
                Press Stop to finish recording, then Play to review your recording.
                Use Tab to navigate between controls.
            </div>
        </div>
        
        <style>
        .accessible-recorder {
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        }
        
        .recorder-header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .recorder-header h2 {
            margin: 0;
            color: #333;
        }
        
        .recorder-status {
            margin-top: 10px;
            font-weight: bold;
        }
        
        .voice-controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .voice-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            min-height: 44px;
            min-width: 44px;
        }
        
        .voice-button:disabled {
            background: #ccc;
            cursor: not-allowed;
            opacity: 0.6;
        }
        
        .voice-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .voice-button:focus {
            outline: 3px solid #007bff;
            outline-offset: 2px;
        }
        
        .record-btn {
            background: linear-gradient(135deg, #28a745 0%, #20a03a 100%);
        }
        
        .stop-btn {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        }
        
        .play-btn {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        }
        
        .clear-btn {
            background: linear-gradient(135deg, #6c757d 0%, #545b62 100%);
        }
        
        .recorder-visual {
            margin: 20px 0;
            text-align: center;
        }
        
        .voice-waveform {
            width: 100%;
            height: 100px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #f8f9fa;
        }
        
        .recorder-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }
        
        .timer {
            font-family: monospace;
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        
        .keyboard-navigation .voice-button:focus {{
            outline: 3px solid #007bff !important;
            outline-offset: 2px !important;
        }}
        
        /* High contrast mode */
        .high-contrast .voice-button {
            border: 2px solid #000;
        }
        
        .high-contrast .accessible-recorder {
            border: 3px solid #000;
        }
        </style>
        """
        
        self.render_responsive_container(recorder_html, height)
    
    def render_accessible_playback(self, audio_data: Optional[Dict[str, Any]] = None) -> None:
        """Render an accessible audio playback component"""
        
        playback_html = f"""
        <div class="accessible-playback" role="application" aria-label="Audio Player">
            <div class="playback-header">
                <h2 id="playback-title">Voice Playback</h2>
                <div class="playback-status" role="status" aria-live="polite" aria-atomic="true">
                    <span id="playback-status-text">No audio loaded</span>
                </div>
            </div>
            
            <div class="audio-player-container">
                <audio id="audio-player" controls 
                       aria-label="Audio playback controls"
                       aria-describedby="player-help">
                    Your browser does not support the audio element.
                </audio>
            </div>
            
            <div class="playback-controls voice-controls" role="group" aria-label="Playback controls">
                <button id="play-pause-btn" class="voice-button" 
                        aria-label="Play or pause audio" disabled>
                    <span class="button-icon" aria-hidden="true">▶️</span>
                    <span class="button-text">Play</span>
                </button>
                
                <button id="rewind-btn" class="voice-button" 
                        aria-label="Rewind 10 seconds" disabled>
                    <span class="button-icon" aria-hidden="true">⏪</span>
                    <span class="button-text">-10s</span>
                </button>
                
                <button id="forward-btn" class="voice-button" 
                        aria-label="Forward 10 seconds" disabled>
                    <span class="button-icon" aria-hidden="true">⏩</span>
                    <span class="button-text">+10s</span>
                </button>
                
                <button id="download-btn" class="voice-button" 
                        aria-label="Download audio file" disabled>
                    <span class="button-icon" aria-hidden="true">💾</span>
                    <span class="button-text">Download</span>
                </button>
            </div>
            
            <div class="playback-info">
                <div class="progress-container">
                    <label for="progress-slider" class="sr-only">Audio progress</label>
                    <input type="range" id="progress-slider" 
                           class="progress-slider" 
                           min="0" max="100" value="0"
                           aria-label="Audio progress slider">
                    <div class="time-display">
                        <span id="current-time">0:00</span> / <span id="total-time">0:00</span>
                    </div>
                </div>
                
                <div class="volume-control">
                    <label for="volume-slider" class="sr-only">Volume control</label>
                    <input type="range" id="volume-slider" 
                           class="volume-slider" 
                           min="0" max="100" value="100"
                           aria-label="Volume control">
                    <span id="volume-text" aria-live="polite">100%</span>
                </div>
            </div>
            
            <div class="audio-metadata" aria-live="polite">
                <div id="audio-format" class="metadata-item">Format: <span>-</span></div>
                <div id="audio-size" class="metadata-item">Size: <span>-</span></div>
                <div id="audio-duration" class="metadata-item">Duration: <span>-</span></div>
            </div>
            
            <div id="player-help" class="help-text sr-only">
                Use the Play button to start audio playback. 
                Use the progress slider to navigate through the audio.
                Use the volume slider to adjust the audio volume.
                Keyboard shortcuts: Space to play/pause, Arrow keys to seek.
            </div>
        </div>
        
        <style>
        .accessible-playback {{
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        }}
        
        .playback-header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .playback-header h2 {{
            margin: 0;
            color: #333;
        }}
        
        .audio-player-container {{
            margin: 20px 0;
            text-align: center;
        }}
        
        #audio-player {{
            width: 100%;
            max-width: 400px;
            height: 40px;
        }}
        
        .playback-info {{
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 20px;
            margin: 20px 0;
            align-items: center;
        }}
        
        .progress-container {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .progress-slider {{
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: #ddd;
            outline: none;
            cursor: pointer;
        }}
        
        .progress-slider::-webkit-slider-thumb {{
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #007bff;
            cursor: pointer;
        }}
        
        .time-display {{
            font-family: monospace;
            font-size: 14px;
            color: #666;
            text-align: center;
        }}
        
        .volume-control {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .volume-slider {{
            width: 80px;
            height: 6px;
            border-radius: 3px;
            background: #ddd;
            outline: none;
        }}
        
        .volume-slider::-webkit-slider-thumb {{
            appearance: none;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #007bff;
            cursor: pointer;
        }}
        
        #volume-text {{
            font-size: 12px;
            color: #666;
            min-width: 35px;
        }}
        
        .audio-metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }}
        
        .metadata-item {{
            padding: 5px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        
        /* Keyboard navigation focus styles */
        .keyboard-navigation .voice-button:focus,
        .keyboard-navigation .progress-slider:focus,
        .keyboard-navigation .volume-slider:focus {{
            outline: 3px solid #007bff !important;
            outline-offset: 2px !important;
        }}
        </style>
        
        <script>
        // Initialize audio player with accessibility features
        document.addEventListener('DOMContentLoaded', function() {{
            const audioPlayer = document.getElementById('audio-player');
            const playPauseBtn = document.getElementById('play-pause-btn');
            const progressSlider = document.getElementById('progress-slider');
            const volumeSlider = document.getElementById('volume-slider');
            const volumeText = document.getElementById('volume-text');
            const currentTimeEl = document.getElementById('current-time');
            const totalTimeEl = document.getElementById('total-time');
            const statusText = document.getElementById('playback-status-text');
            
            // Load audio data if provided
            {f'loadAudioData({json.dumps(audio_data)});' if audio_data else ''}
            
            function loadAudioData(audioData) {{
                if (audioData && audioData.audio_base64) {{
                    const audioBytes = atob(audioData.audio_base64);
                    const audioArray = new Uint8Array(audioBytes.length);
                    for (let i = 0; i < audioBytes.length; i++) {{
                        audioArray[i] = audioBytes.charCodeAt(i);
                    }}
                    
                    const audioBlob = new Blob([audioArray], {{ type: audioData.mime_type || 'audio/mpeg' }});
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    audioPlayer.src = audioUrl;
                    playPauseBtn.disabled = false;
                    
                    // Update metadata
                    document.querySelector('#audio-format span').textContent = audioData.mime_type || 'Unknown';
                    document.querySelector('#audio-size span').textContent = formatFileSize(audioData.audio_size || 0);
                    statusText.textContent = 'Audio loaded';
                    
                    // Announce to screen readers
                    announceToScreenReader('Audio file loaded and ready to play');
                }}
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
            
            function announceToScreenReader(message) {{
                const announcement = document.createElement('div');
                announcement.setAttribute('aria-live', 'polite');
                announcement.setAttribute('class', 'sr-only');
                announcement.textContent = message;
                document.body.appendChild(announcement);
                setTimeout(() => document.body.removeChild(announcement), 1000);
            }}
            
            // Audio event listeners
            audioPlayer.addEventListener('loadedmetadata', function() {{
                totalTimeEl.textContent = formatTime(audioPlayer.duration);
                progressSlider.max = audioPlayer.duration;
            }});
            
            audioPlayer.addEventListener('timeupdate', function() {{
                currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
                progressSlider.value = audioPlayer.currentTime;
            }});
            
            audioPlayer.addEventListener('play', function() {{
                playPauseBtn.querySelector('.button-text').textContent = 'Pause';
                playPauseBtn.querySelector('.button-icon').textContent = '⏸️';
                statusText.textContent = 'Playing';
                announceToScreenReader('Audio playing');
            }});
            
            audioPlayer.addEventListener('pause', function() {{
                playPauseBtn.querySelector('.button-text').textContent = 'Play';
                playPauseBtn.querySelector('.button-icon').textContent = '▶️';
                statusText.textContent = 'Paused';
                announceToScreenReader('Audio paused');
            }});
            
            audioPlayer.addEventListener('ended', function() {{
                playPauseBtn.querySelector('.button-text').textContent = 'Play';
                playPauseBtn.querySelector('.button-icon').textContent = '▶️';
                statusText.textContent = 'Ended';
                announceToScreenReader('Audio playback ended');
            }});
            
            // Control event listeners
            playPauseBtn.addEventListener('click', function() {{
                if (audioPlayer.paused) {{
                    audioPlayer.play();
                }} else {{
                    audioPlayer.pause();
                }}
            }});
            
            progressSlider.addEventListener('input', function() {{
                audioPlayer.currentTime = this.value;
            }});
            
            volumeSlider.addEventListener('input', function() {{
                audioPlayer.volume = this.value / 100;
                volumeText.textContent = this.value + '%';
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
                        audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 10);
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        audioPlayer.volume = Math.min(1, audioPlayer.volume + 0.1);
                        volumeSlider.value = audioPlayer.volume * 100;
                        volumeText.textContent = Math.round(audioPlayer.volume * 100) + '%';
                        break;
                    case 'ArrowDown':
                        e.preventDefault();
                        audioPlayer.volume = Math.max(0, audioPlayer.volume - 0.1);
                        volumeSlider.value = audioPlayer.volume * 100;
                        volumeText.textContent = Math.round(audioPlayer.volume * 100) + '%';
                        break;
                }}
            }});
        }});
        </script>
        """
        
        self.render_responsive_container(playback_html, height=400)
    
    def render_accessibility_panel(self) -> Dict[str, bool]:
        """Render accessibility settings panel"""
        
        st.markdown("### ♿ Accessibility Settings")
        
        # High contrast mode
        high_contrast = st.checkbox(
            "🔲 High Contrast Mode",
            value=self.accessibility_features['high_contrast'],
            help="Increase contrast for better visibility"
        )
        
        # Large text
        large_text = st.checkbox(
            "📝 Large Text",
            value=self.accessibility_features['large_text'],
            help="Increase text size for better readability"
        )
        
        # Reduced motion
        reduced_motion = st.checkbox(
            "🚫 Reduced Motion",
            value=self.accessibility_features['reduced_motion'],
            help="Reduce animations and transitions"
        )
        
        # Screen reader optimizations
        screen_reader = st.checkbox(
            "🔊 Screen Reader Optimizations",
            value=self.accessibility_features['screen_reader'],
            help="Optimize interface for screen readers"
        )
        
        # Update features
        self.accessibility_features = {
            'high_contrast': high_contrast,
            'large_text': large_text,
            'reduced_motion': reduced_motion,
            'screen_reader': screen_reader
        }
        
        # Apply accessibility CSS
        accessibility_css = ""
        if high_contrast:
            accessibility_css += "body { filter: contrast(1.5); }"
        if large_text:
            accessibility_css += "body { font-size: 1.2em; }"
        if reduced_motion:
            accessibility_css += "* { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }"
        
        if accessibility_css:
            st.markdown(f"<style>{accessibility_css}</style>", unsafe_allow_html=True)
        
        # Keyboard shortcuts guide
        with st.expander("⌨️ Keyboard Shortcuts"):
            st.markdown("""
            **Global Shortcuts:**
            - `Tab` - Navigate between controls
            - `Shift + Tab` - Navigate backwards
            - `Enter` - Activate button/link
            - `Space` - Play/pause audio, start/stop recording
            
            **Audio Player:**
            - `Arrow Left` - Rewind 10 seconds
            - `Arrow Right` - Forward 10 seconds
            - `Arrow Up` - Increase volume
            - `Arrow Down` - Decrease volume
            - `Home` - Go to beginning
            - `End` - Go to end
            
            **Voice Recorder:**
            - `R` - Start/stop recording
            - `P` - Play recording
            - `C` - Clear recording
            - `Escape` - Cancel operation
            """)
        
        return self.accessibility_features

def render_responsive_voice_interface():
    """Render a complete responsive voice interface"""
    
    ui = ResponsiveVoiceUI()
    
    st.markdown("## 📱 Responsive Voice Interface")
    
    # Accessibility panel
    accessibility_settings = ui.render_accessibility_panel()
    
    # Responsive recorder
    st.markdown("### 🎤 Accessible Voice Recorder")
    ui.render_accessible_recorder()
    
    # Responsive playback
    st.markdown("### 🔊 Accessible Voice Playback")
    ui.render_accessible_playback()
    
    # Device detection info
    st.markdown("### 📱 Device Information")
    
    # JavaScript for device detection
    device_detection_js = """
    <script>
    function detectDevice() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        const userAgent = navigator.userAgent;
        
        let deviceType = 'desktop';
        if (width <= 768) {
            deviceType = 'mobile';
        } else if (width <= 1024) {
            deviceType = 'tablet';
        }
        
        // Send info to Streamlit
        const deviceInfo = {
            type: deviceType,
            width: width,
            height: height,
            userAgent: userAgent,
            touchSupport: 'ontouchstart' in window,
            orientation: screen.orientation ? screen.orientation.type : 'unknown'
        };
        
        // Store in session storage for retrieval
        sessionStorage.setItem('deviceInfo', JSON.stringify(deviceInfo));
    }
    
    // Run on load
    detectDevice();
    window.addEventListener('resize', detectDevice);
    </script>
    """
    
    components.html(device_detection_js, height=0)
    
    # Display device info (simulated for demo)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Device Type", "Desktop")
    with col2:
        st.metric("Screen Width", "1920px")
    with col3:
        st.metric("Touch Support", "Yes")
    
    # Responsive testing tips
    st.markdown("### 🧪 Responsive Testing")
    st.info("""
    **Testing Tips:**
    - Resize your browser window to test different layouts
    - Use browser dev tools to simulate mobile devices
    - Test with keyboard navigation only
    - Enable screen reader to test accessibility
    - Try high contrast mode in your OS settings
    """)

if __name__ == "__main__":
    render_responsive_voice_interface()
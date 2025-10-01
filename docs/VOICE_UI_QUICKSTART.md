# Voice UI Components Quick Start Guide

This guide will help you get started with the Voice UI components quickly and easily.

## Prerequisites

- Python 3.8 or higher
- Streamlit installed (`pip install streamlit`)
- Backend voice service running on `http://localhost:8000`
- Modern web browser with microphone support

## Quick Installation

1. **Clone the Repository**
```bash
git clone <repository-url>
cd voice-rag-system
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Start Backend Service**
```bash
cd backend
python main.py
```

4. **Start Frontend**
```bash
cd frontend
streamlit run app.py
```

## Basic Usage

### 1. Simple Voice Recording

```python
import streamlit as st
from components.native_audio_recorder import native_audio_recorder

st.title("Voice Recording Demo")

# Add audio recorder
audio_data = native_audio_recorder(
    height=300,
    recording_color="#dc3545",
    background_color="#f8f9fa"
)

if audio_data:
    st.success("Audio recorded successfully!")
    st.json(audio_data)
```

### 2. Voice Playback

```python
import streamlit as st
from components.voice_playback import render_voice_playback_component

st.title("Voice Playback Demo")

# Render playback component
playback_component = render_voice_playback_component(
    api_url="http://localhost:8000"
)

# Text input for synthesis
text = st.text_input("Enter text to synthesize:")

if st.button("Speak") and text:
    result = playback_component.synthesize_and_play(text)
    if result['status'] == 'success':
        st.success("Speech synthesized!")
    else:
        st.error(f"Error: {result['error']}")
```

### 3. Voice Settings

```python
import streamlit as st
from components.voice_settings_panel import render_voice_settings_panel

st.title("Voice Settings Demo")

# Render settings panel
settings = render_voice_settings_panel(
    api_url="http://localhost:8000"
)

st.write("Current Settings:")
st.json(settings.__dict__)
```

## Complete Voice Interface

For a complete voice interface with all features integrated:

```python
import streamlit as st
from pages.voice_interface import main

if __name__ == "__main__":
    main()
```

Or run directly:
```bash
streamlit run pages/voice_interface.py
```

## Common Use Cases

### 1. Voice-Enabled Chat

```python
import streamlit as st
from components.native_audio_recorder import native_audio_recorder
from components.voice_playback import render_voice_playback_component

st.title("Voice Chat")

# Chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice input
audio_data = native_audio_recorder()

if audio_data:
    # Process voice input (transcription + RAG + TTS)
    with st.spinner("Processing..."):
        # Add your voice processing logic here
        response_text = "This is a sample response"
        
        # Add message to history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text
        })
        
        # Synthesize response
        playback_component = render_voice_playback_component()
        playback_component.synthesize_and_play(response_text)
    
    st.rerun()
```

### 2. Voice Form Filling

```python
import streamlit as st
from components.native_audio_recorder import native_audio_recorder

st.title("Voice Form")

# Form fields
name = st.text_input("Name:")
email = st.text_input("Email:")

# Voice input for additional info
st.subheader("Additional Information (Voice)")
audio_data = native_audio_recorder(height=200)

if audio_data and st.button("Process Voice Input"):
    # Transcribe and process
    transcribed_text = transcribe_audio(audio_data)
    st.text_area("Transcribed Text:", value=transcribed_text, height=100)
    
    if st.button("Submit Form"):
        # Process form with voice input
        st.success("Form submitted successfully!")
```

### 3. Voice Commands

```python
import streamlit as st
from components.native_audio_recorder import native_audio_recorder

st.title("Voice Commands")

st.markdown("""
Say commands like:
- "Show help"
- "Clear data"
- "Save file"
- "Open settings"
""")

audio_data = native_audio_recorder()

if audio_data:
    # Transcribe and detect commands
    transcribed_text = transcribe_audio(audio_data).lower()
    
    if "help" in transcribed_text:
        st.info("Help: Available commands are...")
    elif "clear" in transcribed_text:
        if st.button("Confirm Clear"):
            st.success("Data cleared!")
    elif "save" in transcribed_text:
        st.success("File saved!")
    else:
        st.warning(f"Unknown command: {transcribed_text}")
```

## Configuration

### Environment Variables

```bash
# API Configuration
export VOICE_API_URL="http://localhost:8000"
export VOICE_API_KEY="your-api-key"

# Feature Flags
export VOICE_DEBUG="true"
export VOICE_ENABLE_ENHANCED="true"
```

### Settings File

Create `voice_config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "default_voice": "alloy",
  "default_language": "en",
  "auto_transcribe": true,
  "auto_play_response": true,
  "recording_format": "webm",
  "playback_format": "mp3",
  "enable_caching": true,
  "theme": "light"
}
```

## Troubleshooting

### Microphone Not Working

1. **Check Browser Permissions**
   - Click the microphone icon in your browser
   - Allow microphone access for the site

2. **Use HTTPS**
   - Microphone access requires HTTPS in most browsers
   - For local development, use `http://localhost` which is exempt

3. **Check Other Applications**
   - Close other apps using the microphone
   - Restart browser if needed

### Audio Not Playing

1. **Check Browser Audio**
   - Ensure browser is not muted
   - Check system volume settings

2. **Try Different Format**
   - Change audio format in settings
   - MP3 has widest compatibility

3. **Check Network**
   - Ensure backend service is running
   - Check API connectivity

### Performance Issues

1. **Reduce Audio Quality**
   - Lower recording quality in settings
   - Use compressed formats (Opus)

2. **Enable Caching**
   - Turn on TTS caching
   - Clear cache if needed

## Next Steps

1. **Explore Features**: Browse through all available components
2. **Customize Settings**: Adjust voice settings to your preferences
3. **Integrate with Your App**: Add voice features to your application
4. **Run Tests**: Execute the test suite to verify functionality
5. **Read Documentation**: Check the full documentation for advanced features

## Examples Repository

For complete working examples, see the `examples/` directory:

- `basic_recording.py` - Simple audio recording
- `voice_chat.py` - Complete voice-enabled chat
- `voice_commands.py` - Voice command processing
- `custom_settings.py` - Custom configuration example

## Support

- **Documentation**: [VOICE_UI_COMPONENTS.md](VOICE_UI_COMPONENTS.md)
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact development team for support

---

*Happy coding with voice! 🎤*
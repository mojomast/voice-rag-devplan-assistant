# Voice UI Components Documentation

This document provides comprehensive documentation for the Voice UI components in the Voice RAG System. These components enable users to interact with the system using voice input and output, providing a seamless hands-free experience.

## Table of Contents

1. [Overview](#overview)
2. [Component Architecture](#component-architecture)
3. [Components](#components)
   - [Audio Recorder Component](#audio-recorder-component)
   - [Voice Playback Component](#voice-playback-component)
   - [Voice Settings Panel](#voice-settings-panel)
   - [Error Handler](#error-handler)
   - [Responsive UI](#responsive-ui)
4. [Integration Guide](#integration-guide)
5. [API Reference](#api-reference)
6. [Accessibility Features](#accessibility-features)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Overview

The Voice UI components provide a comprehensive voice interface for the Voice RAG System, enabling users to:

- Record audio using their device's microphone
- Transcribe speech to text using advanced STT (Speech-to-Text)
- Synthesize text to speech using natural TTS (Text-to-Speech)
- Configure voice settings and preferences
- Handle errors gracefully with user-friendly feedback
- Access the interface on various devices with responsive design

### Key Features

- **Native Audio Recording**: High-quality audio recording with real-time visualization
- **Enhanced Voice Playback**: Advanced audio controls with playback management
- **Comprehensive Settings**: Extensive configuration options for voice features
- **Error Handling**: Robust error handling with user-friendly messages
- **Responsive Design**: Works seamlessly across desktop, tablet, and mobile devices
- **Accessibility**: Full support for screen readers and keyboard navigation
- **Multi-language Support**: Support for multiple languages and voice options

## Component Architecture

The voice UI components are built with a modular architecture:

```
frontend/
├── components/
│   ├── native_audio_recorder.py    # Audio recording functionality
│   ├── voice_playback.py           # Audio playback and synthesis
│   ├── voice_settings_panel.py     # Settings and configuration
│   ├── voice_error_handler.py      # Error handling and user feedback
│   └── responsive_voice_ui.py      # Responsive and accessible design
├── pages/
│   ├── voice_interface.py          # Complete voice interface
│   └── voice_demo.py               # Demo and testing interface
└── utils/
    └── api_client.py               # API communication utilities
```

### Design Principles

1. **Modularity**: Each component is self-contained and can be used independently
2. **Accessibility**: Full WCAG compliance with screen reader support
3. **Responsiveness**: Adaptive layouts for different screen sizes
4. **Error Resilience**: Comprehensive error handling and recovery
5. **Performance**: Optimized for smooth user experience
6. **Extensibility**: Easy to extend with new features

## Components

### Audio Recorder Component

The Audio Recorder component provides high-quality audio recording capabilities with real-time visualization and enhanced features.

#### Features

- **Native Device Access**: Direct access to device microphone
- **Real-time Visualization**: Live audio waveform and level monitoring
- **Multiple Format Support**: WebM, MP4, WAV, OGG formats
- **Audio Enhancement**: Noise reduction and quality improvement
- **Keyboard Shortcuts**: Full keyboard navigation support
- **Permission Handling**: Graceful microphone permission management

#### Usage

```python
from components.native_audio_recorder import native_audio_recorder

# Basic usage
audio_data = native_audio_recorder(
    height=300,
    recording_color="#dc3545",
    background_color="#f8f9fa"
)

if audio_data:
    print(f"Recorded audio: {audio_data['duration']} seconds")
    print(f"File size: {audio_data['size']} bytes")
    print(f"Format: {audio_data['mime_type']}")
```

#### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `height` | int | 300 | Component height in pixels |
| `auto_start` | bool | False | Automatically start recording |
| `recording_color` | str | "#dc3545" | Recording indicator color |
| `background_color` | str | "#f8f9fa" | Background color |

#### Returned Data Structure

```python
{
    "audio_data": "base64_encoded_audio_data",
    "mime_type": "audio/webm",
    "size": 1024000,
    "duration": "00:15",
    "sequence_number": 0
}
```

### Voice Playback Component

The Voice Playback component provides advanced audio playback capabilities with enhanced controls and synthesis features.

#### Features

- **Enhanced Audio Controls**: Play, pause, stop, seek, volume, speed controls
- **TTS Integration**: Direct text-to-speech synthesis
- **Playback History**: Track and replay previous audio
- **Download Support**: Save audio files locally
- **Keyboard Navigation**: Full keyboard control support
- **Loop and Repeat**: Advanced playback options

#### Usage

```python
from components.voice_playback import render_voice_playback_component

# Render playback component
playback_component = render_voice_playback_component(
    api_url="http://localhost:8000",
    auto_play=True,
    show_controls=True,
    theme="light"
)

# Synthesize speech
result = playback_component.synthesize_and_play(
    text="Hello, world!",
    voice="alloy",
    auto_play=True
)
```

#### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_url` | str | "http://127.0.0.1:8000" | Backend API URL |
| `auto_play` | bool | False | Auto-play synthesized audio |
| `show_controls` | bool | True | Show enhanced controls |
| `theme` | str | "light" | Visual theme ("light" or "dark") |

### Voice Settings Panel

The Voice Settings Panel provides comprehensive configuration options for all voice features.

#### Features

- **TTS Settings**: Voice selection, speed, format, caching
- **STT Settings**: Language detection, noise reduction, enhancement
- **Recording Settings**: Format, quality, auto-processing
- **UI Settings**: Theme, layout, accessibility options
- **Advanced Settings**: API configuration, performance tuning
- **Import/Export**: Save and load settings profiles

#### Usage

```python
from components.voice_settings_panel import render_voice_settings_panel, VoiceSettings

# Render settings panel
settings = render_voice_settings_panel(
    api_url="http://localhost:8000"
)

# Access settings
print(f"TTS Voice: {settings.tts_voice}")
print(f"Speech Speed: {settings.tts_speed}")
print(f"Recording Format: {settings.recording_format}")
```

#### Settings Categories

1. **TTS Settings**
   - Voice selection (alloy, echo, fable, onyx, nova, shimmer)
   - Speech speed (0.25x - 4.0x)
   - Output format (MP3, Opus, AAC, FLAC)
   - Caching options

2. **STT Settings**
   - Language selection and auto-detection
   - Noise reduction and audio enhancement
   - Quality thresholds and processing options

3. **Recording Settings**
   - Audio format and quality
   - Auto-transcription and processing
   - Silence detection and chunk duration

4. **UI Settings**
   - Theme selection (light, dark, auto)
   - Display options and layout preferences
   - Keyboard shortcuts and accessibility

### Error Handler

The Error Handler provides comprehensive error management with user-friendly feedback and recovery options.

#### Features

- **Error Classification**: Categorize errors by type and severity
- **User-Friendly Messages**: Clear, actionable error messages
- **Retry Mechanisms**: Automatic retry with exponential backoff
- **Error History**: Track and analyze error patterns
- **Callback System**: Custom error handling callbacks

#### Usage

```python
from components.voice_error_handler import handle_voice_error, ErrorCategory, ErrorSeverity

try:
    # Voice operation that might fail
    result = voice_api_call()
except Exception as e:
    # Handle error with user feedback
    error = handle_voice_error(
        e,
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        context={"operation": "voice_synthesis"}
    )
```

#### Error Categories

- **Network**: Connection and timeout errors
- **Permission**: Microphone and camera access issues
- **Audio Format**: Unsupported or corrupted audio
- **API**: Backend service errors
- **Browser**: Compatibility and feature support
- **User Input**: Invalid or missing input
- **System**: General system errors

### Responsive UI

The Responsive UI component ensures the voice interface works seamlessly across all devices and screen sizes.

#### Features

- **Adaptive Layouts**: Mobile, tablet, and desktop layouts
- **Touch Optimization**: Large touch targets and gestures
- **Accessibility**: Full WCAG compliance
- **Keyboard Navigation**: Complete keyboard support
- **Screen Reader**: Optimized for assistive technologies

#### Usage

```python
from components.responsive_voice_ui import render_responsive_voice_interface

# Render responsive interface
render_responsive_voice_interface()
```

#### Breakpoints

- **Mobile**: ≤ 768px
- **Tablet**: 769px - 1024px
- **Desktop**: ≥ 1025px

## Integration Guide

### Basic Integration

1. **Import Components**
```python
from components.native_audio_recorder import native_audio_recorder
from components.voice_playback import render_voice_playback_component
from components.voice_settings_panel import render_voice_settings_panel
```

2. **Initialize Components**
```python
# Set up API URL
API_URL = "http://localhost:8000"

# Initialize components
playback_component = render_voice_playback_component(API_URL)
```

3. **Handle Audio Data**
```python
# Record audio
audio_data = native_audio_recorder()

if audio_data:
    # Transcribe or process audio
    result = transcribe_audio(audio_data)
    
    # Synthesize response
    playback_component.synthesize_and_play(result['text'])
```

### Advanced Integration

For more advanced use cases, see the complete voice interface in `pages/voice_interface.py`.

### Session Management

The voice components support session state management for persistent settings and history:

```python
# Store settings in session state
st.session_state.voice_settings = settings

# Store audio data for playback
st.session_state.current_audio_data = audio_data

# Store session history
st.session_state.voice_sessions = sessions
```

## API Reference

### Voice Playback Component

#### `VoicePlaybackComponent(api_url)`

Initialize the voice playback component.

**Parameters:**
- `api_url` (str): Backend API URL

**Methods:**

- `render_voice_playback(audio_data, auto_play, show_controls, height, theme)`
- `synthesize_and_play(text, voice, auto_play, **kwargs)`
- `render_playback_history()`
- `render_audio_analyzer(audio_data)`

### Voice Settings Panel

#### `VoiceSettingsPanel(api_url)`

Initialize the voice settings panel.

**Parameters:**
- `api_url` (str): Backend API URL

**Methods:**

- `render_settings_panel(settings)`
- `load_available_voices()`
- `load_voice_capabilities()`
- `export_settings(settings)`
- `import_settings(settings_json)`

### Error Handler

#### `handle_voice_error(error, category, severity, context, show_to_user)`

Handle an error with appropriate user feedback.

**Parameters:**
- `error` (Exception): The exception that occurred
- `category` (ErrorCategory): Error category
- `severity` (ErrorSeverity): Error severity level
- `context` (dict): Additional context information
- `show_to_user` (bool): Whether to display error to user

**Returns:**
- `VoiceError`: Structured error information

## Accessibility Features

The voice UI components are designed with full accessibility support:

### WCAG 2.1 Compliance

- **Level AA**: All components meet WCAG 2.1 Level AA standards
- **Keyboard Navigation**: Full keyboard control without mouse
- **Screen Reader Support**: Optimized for JAWS, NVDA, and VoiceOver
- **Color Contrast**: High contrast options available
- **Focus Management**: Clear focus indicators and logical tab order

### Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| `Space` | Start/Stop recording, Play/Pause audio |
| `Enter` | Play audio, Activate buttons |
| `Escape` | Stop recording, Clear audio |
| `Arrow Left/Right` | Seek audio (±10 seconds) |
| `Arrow Up/Down` | Adjust volume (±10%) |
| `Tab` | Navigate between controls |
| `Shift + Tab` | Navigate backwards |

### Screen Reader Support

- **ARIA Labels**: Comprehensive ARIA labeling for all controls
- **Live Regions**: Dynamic content announcements
- **Semantic HTML**: Proper heading structure and landmarks
- **Alternative Text**: Descriptive text for all visual elements

## Testing

### Running Tests

```bash
# Run all voice component tests
pytest tests/frontend/test_voice_components.py -v

# Run specific test categories
pytest tests/frontend/test_voice_components.py::TestVoicePlaybackComponent -v
pytest tests/frontend/test_voice_components.py::TestVoiceSettingsPanel -v

# Run with coverage
pytest tests/frontend/test_voice_components.py --cov=frontend/components --cov-report=html
```

### Test Categories

1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: Component interaction testing
3. **End-to-End Tests**: Complete workflow testing
4. **Performance Tests**: Load and timing tests
5. **Accessibility Tests**: Screen reader and keyboard testing

### Test Fixtures

The test suite includes comprehensive fixtures for:

- Mock API responses
- Sample audio data
- Streamlit mocking
- Session state simulation

## Troubleshooting

### Common Issues

#### Microphone Access Denied

**Problem**: Users see "Microphone access denied" error.

**Solution**:
1. Check browser permissions for microphone access
2. Ensure HTTPS connection (required for microphone access)
3. Try refreshing the page and granting permissions
4. Check if another application is using the microphone

#### Audio Not Playing

**Problem**: Synthesized audio doesn't play.

**Solution**:
1. Check browser audio permissions
2. Ensure audio format is supported
3. Check if browser is muted
4. Try different audio format (MP3, Opus, AAC)

#### API Connection Errors

**Problem**: Cannot connect to backend API.

**Solution**:
1. Verify API URL is correct
2. Check if backend service is running
3. Ensure network connectivity
4. Check for CORS issues

#### Recording Quality Issues

**Problem**: Poor audio quality in recordings.

**Solution**:
1. Check microphone hardware
2. Ensure quiet recording environment
3. Enable noise reduction in settings
4. Try different recording format

### Debug Mode

Enable debug mode for detailed logging:

```python
import os
os.environ["VOICE_DEBUG"] = "true"

# Or in settings
settings.debug_mode = True
```

### Performance Optimization

For optimal performance:

1. **Audio Caching**: Enable TTS caching to reduce API calls
2. **Format Selection**: Use efficient audio formats (Opus for compression)
3. **Chunk Processing**: Use appropriate chunk sizes for streaming
4. **Browser Compatibility**: Test on target browsers

### Browser Compatibility

| Browser | Version | Recording | Playback | Notes |
|---------|---------|-----------|----------|-------|
| Chrome | 90+ | ✅ | ✅ | Full support |
| Firefox | 88+ | ✅ | ✅ | Full support |
| Safari | 14+ | ✅ | ✅ | Limited format support |
| Edge | 90+ | ✅ | ✅ | Full support |

### Mobile Considerations

- **Touch Targets**: Minimum 44px touch targets
- **Orientation**: Support for portrait and landscape
- **Performance**: Optimize for mobile processors
- **Battery**: Consider power consumption

## Contributing

When contributing to voice UI components:

1. **Follow Code Style**: Use PEP 8 and project conventions
2. **Add Tests**: Include comprehensive test coverage
3. **Document Changes**: Update documentation for new features
4. **Test Accessibility**: Ensure WCAG compliance
5. **Performance Testing**: Verify performance impact

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests in watch mode
pytest tests/frontend/test_voice_components.py --watch

# Run linting
flake8 frontend/components/
black frontend/components/
```

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:

1. **Documentation**: Check this documentation first
2. **Issues**: Create GitHub issues for bugs and feature requests
3. **Discussions**: Use GitHub discussions for questions
4. **Email**: Contact the development team for urgent issues

---

*Last updated: October 2023*
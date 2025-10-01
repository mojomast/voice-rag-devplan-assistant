# Voice System Configuration and Setup Guide

## Overview

This document provides comprehensive information about the Voice RAG System's voice capabilities, configuration, and setup procedures.

## Voice System Features

### Core Capabilities

- **Text-to-Speech (TTS)**: Convert text to natural-sounding speech using OpenAI's TTS models
- **Speech-to-Text (STT)**: Transcribe audio files to text using OpenAI's Whisper models
- **Voice Processing Pipeline**: Complete end-to-end voice query processing
- **Base64 Audio Processing**: Handle audio data encoded in base64 format
- **Audio Validation**: Validate audio formats and file sizes
- **Advanced Audio Processing**: Noise reduction, audio enhancement, and quality analysis
- **Multi-format Support**: MP3, WAV, WebM, OGG, M4A, FLAC formats

### Available Voices

The system supports the following OpenAI TTS voices:

| Voice | Description |
|-------|-------------|
| alloy | Balanced, neutral voice |
| echo | Male voice with clarity |
| fable | Expressive, storytelling voice |
| onyx | Deep, authoritative voice |
| nova | Youthful, energetic voice |
| shimmer | Soft, pleasant voice |

## Configuration

### Environment Variables

Add the following voice-related environment variables to your `.env` file:

```bash
# Core Voice Settings
TTS_MODEL="tts-1"                    # OpenAI TTS model
TTS_VOICE="alloy"                    # Default voice for TTS
WHISPER_MODEL="whisper-1"            # OpenAI Whisper model for STT
ENABLE_WAKE_WORD=False               # Wake word detection (experimental)
WAKE_WORD="hey assistant"            # Custom wake word phrase

# Additional Voice Settings
TEMP_AUDIO_DIR="./temp_audio"        # Directory for temporary audio files
VOICE_LANGUAGE="en"                  # Default language for voice processing
TTS_SPEED="1.0"                      # Speech synthesis speed (0.25-4.0)
AUDIO_SAMPLE_RATE="16000"            # Audio sample rate for processing
MAX_AUDIO_DURATION="300"             # Maximum audio duration in seconds (5 minutes)
```

### Configuration Files

#### `backend/config.py`

The main configuration file contains all voice-related settings with proper defaults and validation:

```python
# Voice Settings
TTS_MODEL: str = os.getenv("TTS_MODEL", "tts-1")
TTS_VOICE: str = os.getenv("TTS_VOICE", "alloy")
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")
ENABLE_WAKE_WORD: bool = os.getenv("ENABLE_WAKE_WORD", "False").lower() == "true"
WAKE_WORD: str = os.getenv("WAKE_WORD", "hey assistant")

# Additional Voice Settings
TEMP_AUDIO_DIR: str = os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
VOICE_LANGUAGE: str = os.getenv("VOICE_LANGUAGE", "en")
TTS_SPEED: float = float(os.getenv("TTS_SPEED", "1.0"))
AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
MAX_AUDIO_DURATION: int = int(os.getenv("MAX_AUDIO_DURATION", "300"))
```

## Dependencies

### Required Dependencies

The voice system requires the following Python packages:

```bash
# Core voice dependencies
openai>=1.0.0
whisper
librosa
soundfile
noisereduce
scipy
mutagen
numpy
```

### Optional Dependencies

For advanced features:

```bash
# Speaker identification (optional)
pyannote.audio
torchaudio

# Wake word detection (optional)
openwakeword
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Install required dependencies
pip install openai whisper librosa soundfile noisereduce scipy mutagen numpy

# Install optional dependencies for advanced features
pip install pyannote.audio torchaudio openwakeword
```

### 2. Configure Environment

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit the `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY="your_openai_api_key_here"
```

3. Configure voice settings as needed (see Configuration section above)

### 3. Verify Setup

Run the voice system test to verify everything is working:

```bash
python test_voice_system.py
```

Expected output should show:
```
🎉 All voice system tests passed!
```

## Usage Examples

### Basic Text-to-Speech

```python
from backend.voice_service import VoiceService

# Initialize voice service
voice_service = VoiceService()

# Synthesize speech
result = voice_service.synthesize_speech(
    text="Hello, this is a test of the voice system.",
    voice="alloy"
)

if result["status"] == "success":
    print(f"Audio saved to: {result['audio_file']}")
```

### Basic Speech-to-Text

```python
# Transcribe audio file
result = voice_service.transcribe_audio("path/to/audio.wav")

if result["status"] == "success":
    print(f"Transcription: {result['text']}")
    print(f"Language: {result['language']}")
    print(f"Confidence: {result['confidence']}")
```

### Base64 Audio Processing

```python
import base64

# Convert audio to base64
with open("audio.wav", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode('utf-8')

# Transcribe base64 audio
result = voice_service.transcribe_base64_audio(
    audio_base64, 
    mime_type="audio/wav"
)
```

### Voice Pipeline

```python
# Complete voice processing pipeline
result = voice_service.process_voice_query("audio.wav")

if result["status"] == "success":
    print(f"Transcription: {result['transcription']}")
    print(f"Language: {result['language']}")
```

## Testing

### Running Tests

The voice system includes a comprehensive test suite:

```bash
# Run all voice system tests
python test_voice_system.py

# Run specific test categories
python -m pytest tests/unit/test_voice_service.py
```

### Test Coverage

The test suite covers:
- ✅ Voice dependencies availability
- ✅ Configuration loading and validation
- ✅ Voice service initialization
- ✅ Text-to-speech functionality
- ✅ Speech-to-text functionality
- ✅ Base64 audio processing
- ✅ Voice processing pipeline
- ✅ Audio format validation
- ✅ Error handling and fallbacks

## Modes of Operation

### Production Mode

When `OPENAI_API_KEY` is configured and valid:
- Full OpenAI API integration
- Real TTS and STT processing
- Cost tracking and monitoring
- Enhanced error handling

### Test Mode

When no API key is available:
- Synthetic audio generation for TTS
- Mock responses for STT
- Graceful fallbacks
- Development and testing support

## Advanced Features

### Audio Enhancement

```python
# Enhance audio quality
result = voice_service.enhance_audio_quality(
    "input_audio.wav",
    "enhanced_audio.wav"
)

if result["status"] == "success":
    print(f"Enhancements applied: {result['enhancements_applied']}")
```

### Audio Analysis

```python
# Analyze audio characteristics
analysis = voice_service.analyze_audio_characteristics("audio.wav")

if analysis["status"] == "success":
    print(f"Duration: {analysis['basic_info']['duration']}s")
    print(f"Sample rate: {analysis['basic_info']['sample_rate']}Hz")
    print(f"Quality metrics: {analysis['quality_metrics']}")
```

### Speaker Identification (Optional)

```python
# Transcribe with speaker identification
result = voice_service.transcribe_with_speaker_identification("audio.wav")

if result["status"] == "success":
    print(f"Number of speakers: {result['speaker_analysis']['num_speakers']}")
    print(f"Text: {result['text']}")
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Not Found**
   - Ensure `OPENAI_API_KEY` is set in your environment
   - Check that the key is valid and active

2. **Audio Format Not Supported**
   - Verify the audio file format is supported
   - Check file size (max 25MB for OpenAI API)

3. **Dependencies Missing**
   - Install all required dependencies
   - Check Python version compatibility

4. **Permission Errors**
   - Ensure write permissions for temp audio directory
   - Check file system permissions

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL="DEBUG"
```

### Performance Optimization

- Use appropriate audio sample rates (16kHz is usually sufficient)
- Limit audio duration to avoid excessive processing time
- Consider audio compression for large files
- Use caching for frequently processed audio

## Security Considerations

- Store API keys securely using environment variables
- Validate audio file uploads to prevent malicious files
- Implement rate limiting for voice API endpoints
- Clean up temporary audio files regularly
- Monitor API usage and costs

## Future Enhancements

Planned improvements to the voice system:

- Real-time streaming audio processing
- Additional voice models and languages
- Voice activity detection
- Custom voice training
- Enhanced noise reduction algorithms
- Voice biometrics and authentication

## Support

For issues or questions about the voice system:

1. Check the test results: `python test_voice_system.py`
2. Review the logs in the application log files
3. Verify configuration in `.env` file
4. Check dependency installation

## API Reference

### VoiceService Class

#### Methods

- `synthesize_speech(text, voice=None, output_file_path=None)` - Convert text to speech
- `transcribe_audio(audio_file_path, language=None)` - Transcribe audio to text
- `transcribe_base64_audio(audio_base64, mime_type, language=None)` - Process base64 audio
- `process_voice_query(audio_file_path)` - Complete voice processing pipeline
- `synthesize_speech_to_base64(text, voice=None)` - Get speech as base64
- `get_available_voices(include_descriptions=False)` - List available voices
- `validate_audio_format(file_path)` - Validate audio file format
- `get_audio_info(audio_file_path)` - Get audio file metadata
- `enhance_audio_quality(audio_file_path, output_path=None)` - Enhance audio quality
- `analyze_audio_characteristics(audio_file_path)` - Analyze audio properties

#### Configuration

All voice settings are configurable through environment variables or the `Settings` class in `backend/config.py`.

---

*Last updated: October 1, 2025*
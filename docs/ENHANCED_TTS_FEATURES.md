# Enhanced TTS (Text-to-Speech) Features

This document describes the enhanced TTS functionality implemented in the Voice RAG System, including caching, audio format validation, base64 encoding, voice selection, and comprehensive error handling.

## Overview

The enhanced TTS system provides:
- **Audio Format Validation**: Support for multiple audio formats with detailed validation
- **Base64 Encoding**: Web-compatible audio playback without file downloads
- **Intelligent Caching**: Performance optimization through smart caching mechanisms
- **Voice Selection UI**: Intuitive voice selection with preview capabilities
- **Enhanced Error Handling**: Specific error types with user-friendly messages
- **Configuration Options**: Flexible voice and audio settings

## Features

### 1. Audio Format Validation

#### Supported Formats
- **MP3**: Up to 25MB, `audio/mpeg`
- **WAV**: Up to 50MB, `audio/wav`
- **WebM**: Up to 25MB, `audio/webm`
- **OGG**: Up to 25MB, `audio/ogg`
- **M4A**: Up to 25MB, `audio/mp4`
- **FLAC**: Up to 100MB, `audio/flac`

#### Validation Features
- File existence and readability checks
- Format support validation
- File size limits enforcement
- Corruption detection
- Detailed error reporting with error types

#### API Usage
```python
# Validate audio file
result = voice_service.validate_audio_format_enhanced("audio.mp3")

if result["valid"]:
    print(f"Format: {result['format']}, Size: {result['size']} bytes")
else:
    print(f"Error: {result['error']} (Type: {result['error_type']})")
```

### 2. Base64 Encoding for Web Playback

#### Features
- Direct audio playback in web browsers
- Multiple output formats (MP3, Opus, AAC, FLAC)
- Metadata inclusion options
- Cache integration for performance

#### API Usage
```python
# Synthesize speech to base64
result = voice_service.synthesize_speech_to_base64(
    text="Hello, world!",
    voice="alloy",
    output_format="mp3",
    use_cache=True,
    include_metadata=True
)

if result["status"] == "success":
    audio_base64 = result["audio_base64"]
    mime_type = result["mime_type"]
    
    # Use in HTML audio element
    html = f'<audio src="data:{mime_type};base64,{audio_base64}" controls>'
```

### 3. Intelligent Caching System

#### Features
- LRU (Least Recently Used) cache eviction
- TTL (Time To Live) support (default: 7 days)
- Configurable cache size limits
- Persistent cache storage
- Cache statistics and monitoring

#### Cache Configuration
```python
# Environment variables
TTS_CACHE_DIR=./cache/tts
TTS_CACHE_MAX_SIZE=100
TTS_CACHE_TTL=604800  # 7 days in seconds
TTS_ENABLE_CACHING=True
```

#### Cache Management
```python
# Get cache statistics
stats = voice_service.get_cache_stats()
print(f"Cache entries: {stats['total_entries']}")
print(f"Cache size: {stats['cache_size_bytes']} bytes")

# Clear cache
voice_service.clear_cache()

# Cleanup expired entries
voice_service.cleanup_cache()
```

### 4. Voice Selection UI

#### Available Voices
- **alloy**: Balanced, neutral voice
- **echo**: Male voice with clarity
- **fable**: Expressive, storytelling voice
- **onyx**: Deep, authoritative voice
- **nova**: Youthful, energetic voice
- **shimmer**: Soft, pleasant voice

#### UI Features
- Voice preview functionality
- Format selection
- Speech speed adjustment
- Caching options
- Cache statistics display

#### Frontend Integration
```python
from components.voice_selector import render_voice_settings_panel

# Render voice settings panel
voice_settings = render_voice_settings_panel(api_url="http://127.0.0.1:8000")
```

### 5. Enhanced Error Handling

#### Error Types
- `TTSError`: Base exception for TTS errors
- `AudioFormatError`: Audio format validation errors
- `VoiceNotFoundError`: Voice selection errors
- `CacheError`: Cache operation errors

#### Error Response Format
```python
{
    "status": "error",
    "error": "Human-readable error message",
    "error_type": "specific_error_type",
    "available_voices": ["alloy", "echo", "fable", ...]  # For voice errors
}
```

### 6. Configuration Options

#### Voice Settings
```python
# Basic voice settings
TTS_MODEL=tts-1
TTS_VOICE=alloy
TTS_SPEED=1.0
TTS_MAX_TEXT_LENGTH=4096

# Cache settings
TTS_CACHE_DIR=./cache/tts
TTS_CACHE_MAX_SIZE=100
TTS_CACHE_TTL=604800
TTS_ENABLE_CACHING=True

# UI settings
VOICE_AUTO_PLAY=False
VOICE_SHOW_METADATA=True
VOICE_CACHE_STATS=True
```

## API Endpoints

### Voice Management
- `GET /voice/voices` - Get available voices
- `GET /voice/capabilities` - Get voice service capabilities
- `GET /voice/health` - Voice service health check

### Speech Synthesis
- `POST /voice/synthesize` - Synthesize speech to file
- `POST /voice/synthesize/base64` - Synthesize speech to base64

### Audio Processing
- `POST /voice/transcribe` - Transcribe audio file
- `POST /voice/transcribe/base64` - Transcribe base64 audio
- `POST /voice/validate-format` - Validate audio format

### Cache Management
- `GET /voice/cache/stats` - Get cache statistics
- `DELETE /voice/cache` - Clear cache
- `POST /voice/cache/cleanup` - Cleanup expired entries

## Usage Examples

### Basic Speech Synthesis
```python
import requests

# Synthesize speech
response = requests.post("http://127.0.0.1:8000/voice/synthesize", json={
    "text": "Hello, this is a test!",
    "voice": "alloy",
    "output_format": "mp3",
    "use_cache": True
})

if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Cached: {result.get('cached', False)}")
```

### Base64 Synthesis for Web
```python
# Synthesize to base64
response = requests.post("http://127.0.0.1:8000/voice/synthesize/base64", json={
    "text": "Hello, this is a web-compatible test!",
    "voice": "alloy",
    "output_format": "mp3",
    "use_cache": True,
    "include_metadata": True
})

if response.status_code == 200:
    result = response.json()
    audio_html = f'''
    <audio controls autoplay>
        <source src="data:{result['mime_type']};base64,{result['audio_base64']}" type="{result['mime_type']}">
    </audio>
    '''
    print(audio_html)
```

### Audio Format Validation
```python
# Upload and validate audio file
with open("test_audio.mp3", "rb") as f:
    files = {"file": ("test.mp3", f, "audio/mpeg")}
    response = requests.post("http://127.0.0.1:8000/voice/validate-format", files=files)

if response.status_code == 200:
    result = response.json()
    if result["valid"]:
        print(f"Valid format: {result['format']}")
    else:
        print(f"Invalid: {result['error']}")
```

## Performance Considerations

### Caching Benefits
- **Reduced API Calls**: Cached responses avoid repeated TTS synthesis
- **Faster Response Times**: Cache hits return immediately
- **Cost Savings**: Fewer API calls to TTS services
- **Offline Capability**: Cached audio works without internet

### Cache Optimization
- Monitor cache hit rates through `/voice/cache/stats`
- Adjust `TTS_CACHE_MAX_SIZE` based on available storage
- Set appropriate `TTS_CACHE_TTL` for your use case
- Regular cleanup prevents cache bloat

### Memory Management
- Cache entries are automatically cleaned up when expired
- LRU eviction prevents unlimited growth
- Cache size is configurable and monitored

## Troubleshooting

### Common Issues

#### Cache Not Working
```python
# Check cache status
response = requests.get("http://127.0.0.1:8000/voice/cache/stats")
print(response.json())

# Ensure cache directory exists and is writable
import os
cache_dir = "./cache/tts"
os.makedirs(cache_dir, exist_ok=True)
```

#### Audio Format Errors
```python
# Validate format before processing
validation_result = voice_service.validate_audio_format_enhanced(file_path)
if not validation_result["valid"]:
    print(f"Format error: {validation_result['error']}")
    print(f"Supported formats: {validation_result['supported_formats']}")
```

#### Voice Not Available
```python
# Check available voices
response = requests.get("http://127.0.0.1:8000/voice/voices")
voices = response.json()["voices"]
print(f"Available voices: {[v['name'] for v in voices]}")
```

### Debug Mode
Enable debug logging for detailed troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

### Unit Tests
Run the comprehensive test suite:
```bash
cd voice-rag-system
python -m pytest tests/unit/test_enhanced_voice_service.py -v
```

### Integration Tests
Test API endpoints:
```bash
python -m pytest tests/integration/test_voice_api.py -v
```

### Manual Testing
Use the frontend voice selector component to test:
- Voice selection and preview
- Audio format validation
- Cache management
- Base64 audio playback

## Migration Guide

### From Basic TTS
1. Update API calls to include new parameters:
   ```python
   # Old
   result = voice_service.synthesize_speech(text, voice)
   
   # New
   result = voice_service.synthesize_speech(
       text, voice, use_cache=True, output_format="mp3"
   )
   ```

2. Handle enhanced error responses:
   ```python
   if result["status"] == "error":
       error_type = result.get("error_type", "unknown")
       # Handle specific error types
   ```

3. Update frontend to use voice selector component:
   ```python
   from components.voice_selector import render_voice_settings_panel
   voice_settings = render_voice_settings_panel(api_url)
   ```

### Configuration Updates
Add these environment variables to your configuration:
```bash
TTS_CACHE_DIR=./cache/tts
TTS_CACHE_MAX_SIZE=100
TTS_CACHE_TTL=604800
TTS_ENABLE_CACHING=True
TTS_MAX_TEXT_LENGTH=4096
```

## Future Enhancements

### Planned Features
- **Voice Cloning**: Custom voice creation
- **Real-time Streaming**: Live audio synthesis
- **Multi-language Support**: Extended language capabilities
- **Voice Emotions**: Emotional tone control
- **Audio Effects**: Post-processing effects

### Performance Improvements
- **Compression**: Audio compression for cache storage
- **Distributed Caching**: Redis integration
- **Batch Processing**: Multiple text synthesis
- **Edge Caching**: CDN integration

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Run the test suite to verify functionality
4. Check logs for detailed error messages
5. Create an issue with reproduction steps

---

*Last updated: October 2024*
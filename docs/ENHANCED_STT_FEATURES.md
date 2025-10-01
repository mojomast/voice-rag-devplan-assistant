# Enhanced STT (Speech-to-Text) Features

This document describes the enhanced Speech-to-Text (STT) features implemented in the Voice RAG System.

## Overview

The enhanced STT implementation provides advanced audio processing capabilities including:
- Real-time streaming audio support
- Automatic language detection
- Audio quality enhancement
- Multi-format audio support
- Comprehensive error handling
- Configurable processing options

## Features

### 1. Streaming Audio Support

Real-time audio processing for live transcription applications.

#### Key Features:
- **Chunk-based processing**: Process audio in configurable chunks (default: 1024 bytes)
- **Buffer management**: Configurable buffer size for efficient memory usage
- **Session management**: Multiple concurrent streaming sessions
- **Timeout handling**: Automatic session cleanup after configurable duration

#### API Methods:
```python
# Start a streaming session
result = voice_service.start_streaming_session(session_id)

# Add audio chunks
result = voice_service.add_streaming_chunk(session_id, audio_data, is_final=False)

# Process streaming session
async for result in voice_service.process_streaming_session(session_id):
    print(result["text"])
```

#### Configuration:
```python
STT_STREAMING_CHUNK_SIZE = 1024
STT_STREAMING_BUFFER_SIZE = 8192
STT_STREAMING_MAX_DURATION = 300  # 5 minutes
STT_SILENCE_THRESHOLD = 0.5  # seconds
```

### 2. Language Detection

Automatic detection of spoken language with confidence scoring.

#### Key Features:
- **Automatic detection**: Identifies language without manual specification
- **Confidence scoring**: Provides confidence levels for detected languages
- **Consistency analysis**: Analyzes language consistency across segments
- **Multi-language support**: Supports 13+ languages

#### Supported Languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Dutch (nl)
- Polish (pl)
- Russian (ru)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)
- Arabic (ar)

#### API Methods:
```python
# Enhanced language detection
result = voice_service.detect_language_enhanced(audio_file_path)
print(f"Language: {result['language']}")
print(f"Confidence: {result['confidence']}")
```

#### Configuration:
```python
STT_ENABLE_LANGUAGE_DETECTION = True
STT_LANGUAGE_CONFIDENCE_THRESHOLD = 0.7
STT_SUPPORTED_LANGUAGES = "en,es,fr,de,it,pt,nl,pl,ru,ja,ko,zh,ar"
```

### 3. Audio Quality Enhancement

Advanced audio processing to improve transcription accuracy.

#### Key Features:
- **Noise reduction**: Reduces background noise using spectral processing
- **Normalization**: Optimizes audio levels for consistent processing
- **Spectral gating**: Removes low-energy noise components
- **Dynamic range compression**: Balances audio dynamics
- **Quality metrics**: Provides before/after quality analysis

#### Enhancement Pipeline:
1. **Format validation**: Verify audio format and integrity
2. **Noise reduction**: Apply stationary noise reduction
3. **Normalization**: Peak normalization to -1 dBFS
4. **Spectral gating**: Frequency-domain noise removal
5. **Dynamic processing**: Compression and filtering

#### API Methods:
```python
# Enhance audio quality
result = voice_service.enhance_audio_quality(audio_file_path)
print(f"Enhancements applied: {result['enhancements_applied']}")
print(f"Quality improvement: {result['quality_improvement']}")
```

#### Configuration:
```python
STT_ENABLE_NOISE_REDUCTION = True
STT_ENABLE_AUDIO_ENHANCEMENT = True
STT_NOISE_REDUCTION_STRENGTH = 0.8
STT_ENABLE_NORMALIZATION = True
STT_ENABLE_SPECTRAL_GATING = True
```

### 4. Multi-Format Audio Support

Comprehensive support for various audio formats.

#### Supported Formats:
- **MP3**: MPEG Audio Layer III (max: 25MB)
- **WAV**: Waveform Audio File Format (max: 50MB)
- **WebM**: Web Media format (max: 25MB)
- **OGG**: Ogg Vorbis format (max: 25MB)
- **M4A**: MPEG-4 Audio (max: 25MB)
- **FLAC**: Free Lossless Audio Codec (max: 100MB)

#### Format Handling:
- **Automatic detection**: Identify format from file extension
- **Validation**: Verify file integrity and size limits
- **Conversion**: Handle format-specific loading/saving
- **Optimization**: Format-specific processing optimizations

#### API Methods:
```python
# Validate audio format
result = voice_service.validate_audio_format_enhanced(audio_file_path)
print(f"Valid: {result['valid']}")
print(f"Format: {result['format']}")
print(f"Size: {result['size']} bytes")
```

### 5. Enhanced Error Handling

Comprehensive error handling with specific error types and user-friendly messages.

#### Error Types:
- **StreamingError**: Streaming audio processing failures
- **LanguageDetectionError**: Language detection failures
- **AudioEnhancementError**: Audio enhancement failures
- **TranscriptionError**: Transcription process failures
- **AudioProcessingError**: General audio processing failures
- **AudioFormatError**: Unsupported or invalid audio formats
- **AudioSizeError**: Audio file size violations

#### Error Response Format:
```python
{
    "status": "error",
    "error": "Human-readable error message",
    "error_type": "specific_error_type",
    "processing_time": 1.23,
    "additional_context": {}
}
```

### 6. Enhanced Transcription

Advanced transcription with comprehensive metadata and analysis.

#### Key Features:
- **Quality analysis**: Audio quality assessment before processing
- **Language detection**: Automatic language identification
- **Audio enhancement**: Optional audio preprocessing
- **Performance metrics**: Processing time and optimization info
- **Segment analysis**: Detailed transcription segments

#### API Methods:
```python
# Enhanced transcription
result = voice_service.transcribe_audio_enhanced(audio_file_path)
print(f"Text: {result['text']}")
print(f"Language: {result['language']}")
print(f"Confidence: {result['confidence']}")
print(f"Processing time: {result['processing_time']}")
print(f"Enhanced features: {result['enhanced_features']}")
```

## Configuration

### Environment Variables

All STT features can be configured using environment variables:

```bash
# Streaming settings
STT_STREAMING_CHUNK_SIZE=1024
STT_STREAMING_BUFFER_SIZE=8192
STT_STREAMING_MAX_DURATION=300
STT_SILENCE_THRESHOLD=0.5

# Language detection
STT_ENABLE_LANGUAGE_DETECTION=true
STT_LANGUAGE_CONFIDENCE_THRESHOLD=0.7
STT_SUPPORTED_LANGUAGES=en,es,fr,de,it,pt,nl,pl,ru,ja,ko,zh,ar

# Audio enhancement
STT_ENABLE_NOISE_REDUCTION=true
STT_ENABLE_AUDIO_ENHANCEMENT=true
STT_NOISE_REDUCTION_STRENGTH=0.8
STT_ENABLE_NORMALIZATION=true
STT_ENABLE_SPECTRAL_GATING=true

# Transcription settings
STT_TRANSCRIPTION_TEMPERATURE=0.2
STT_ENABLE_WORD_TIMESTAMPS=true
STT_ENABLE_SEGMENT_TIMESTAMPS=true
STT_MAX_AUDIO_LENGTH=600

# Quality settings
STT_MIN_AUDIO_QUALITY_THRESHOLD=0.3
STT_ENABLE_QUALITY_ANALYSIS=true
```

### Configuration Class

The `STTConfig` class provides programmatic configuration:

```python
from voice_service import STTConfig

config = STTConfig.from_settings()
print(f"Streaming chunk size: {config.streaming_chunk_size}")
print(f"Language detection enabled: {config.enable_language_detection}")
```

## Usage Examples

### Basic Enhanced Transcription

```python
from voice_service import VoiceService

# Initialize service
voice_service = VoiceService()

# Enhanced transcription with all features
result = voice_service.transcribe_audio_enhanced("audio.wav")

if result["status"] == "success":
    print(f"Transcription: {result['text']}")
    print(f"Language: {result['language']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Processing time: {result['processing_time']}s")
    
    # Check enhanced features used
    features = result["enhanced_features"]
    if features["audio_enhanced"]:
        print("Audio enhancement was applied")
    if features["language_auto_detected"]:
        print(f"Language auto-detected: {result['detected_language']}")
    if features["quality_analyzed"]:
        print("Audio quality was analyzed")
```

### Streaming Audio Processing

```python
import asyncio

async def process_streaming_audio():
    voice_service = VoiceService()
    
    # Start streaming session
    session_result = voice_service.start_streaming_session("session_123")
    
    if session_result["status"] == "success":
        print(f"Started session: {session_result['session_id']}")
        
        # Simulate adding audio chunks
        audio_chunks = get_audio_chunks()  # Your audio source
        
        for i, chunk in enumerate(audio_chunks):
            is_final = (i == len(audio_chunks) - 1)
            result = voice_service.add_streaming_chunk("session_123", chunk, is_final)
            
            if result["status"] == "error":
                print(f"Error adding chunk: {result['error']}")
                break
        
        # Process the streaming session
        async for transcription_result in voice_service.process_streaming_session("session_123"):
            if transcription_result["status"] == "success":
                print(f"Partial transcription: {transcription_result['text']}")
                if transcription_result.get("partial"):
                    print("Processing... (partial result)")
                else:
                    print("Final transcription complete")
            else:
                print(f"Error: {transcription_result['error']}")

# Run the streaming processor
asyncio.run(process_streaming_audio())
```

### Language Detection

```python
# Detect language of audio file
result = voice_service.detect_language_enhanced("audio.wav")

if result["status"] == "success":
    print(f"Detected language: {result['language']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Supported language: {result['supported_language']}")
    print(f"Processing time: {result['processing_time']:.2f}s")
    
    # Check language consistency
    consistency = result.get("language_consistency", {})
    print(f"Consistency score: {consistency.get('consistency_score', 0):.2f}")
else:
    print(f"Language detection failed: {result['error']}")
```

### Audio Quality Enhancement

```python
# Enhance audio quality
result = voice_service.enhance_audio_quality("input.wav", "output_enhanced.wav")

if result["status"] == "success":
    print(f"Enhanced audio saved to: {result['enhanced_file']}")
    print(f"Enhancements applied: {', '.join(result['enhancements_applied'])}")
    
    # Check quality improvement
    improvement = result["quality_improvement"]
    print(f"SNR improvement: {improvement.get('snr_improvement_db', 0):.1f} dB")
    print(f"Overall improvement: {improvement.get('overall_improvement', 0):.2f}")
    
    # Compare quality metrics
    original = result["original_quality"]
    enhanced = result["enhanced_quality"]
    print(f"Original SNR: {original.get('snr_estimate', 0):.1f} dB")
    print(f"Enhanced SNR: {enhanced.get('snr_estimate', 0):.1f} dB")
else:
    print(f"Audio enhancement failed: {result['error']}")
```

## Performance Considerations

### Memory Usage
- Streaming sessions use configurable buffer sizes
- Temporary files are automatically cleaned up
- Audio processing is optimized for memory efficiency

### Processing Time
- Audio enhancement adds processing overhead
- Language detection requires additional API calls
- Quality analysis provides metrics but increases processing time

### Quality vs. Speed Trade-offs
- Disable audio enhancement for faster processing
- Reduce chunk size for lower latency streaming
- Adjust quality thresholds for your use case

## Troubleshooting

### Common Issues

1. **Audio processing unavailable**
   - Install required dependencies: `pip install librosa soundfile noisereduce scipy`
   - Check system audio libraries

2. **Streaming session timeouts**
   - Increase `STT_STREAMING_MAX_DURATION`
   - Check network connectivity for real-time processing

3. **Language detection low confidence**
   - Ensure audio quality is sufficient
   - Check if language is in supported list
   - Adjust confidence threshold

4. **Audio enhancement not working**
   - Verify audio file format is supported
   - Check audio file integrity
   - Review enhancement settings

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

### Required Dependencies
- `librosa`: Audio analysis and processing
- `soundfile`: Audio file I/O
- `noisereduce`: Noise reduction algorithms
- `scipy`: Signal processing
- `numpy`: Numerical computing

### Optional Dependencies
- `mutagen`: Audio metadata extraction
- `pyannote.audio`: Speaker identification
- `openwakeword`: Wake word detection

### Installation

```bash
# Install core dependencies
pip install librosa soundfile noisereduce scipy numpy

# Install optional dependencies
pip install mutagen pyannote.audio openwakeword
```

## API Reference

### Core Classes

- `VoiceService`: Main service class for STT operations
- `STTConfig`: Configuration management
- `StreamingAudioChunk`: Streaming audio data container
- `TranscriptionResult`: Enhanced transcription result

### Error Classes

- `STTError`: Base STT error class
- `StreamingError`: Streaming-related errors
- `LanguageDetectionError`: Language detection errors
- `AudioEnhancementError`: Audio enhancement errors
- `TranscriptionError`: Transcription errors
- `AudioProcessingError`: General audio processing errors

### Key Methods

See individual method documentation in the code for detailed parameter and return value information.

## Future Enhancements

Planned improvements to the STT system:

1. **Real-time speaker diarization**: Identify and separate speakers
2. **Custom language models**: Support for domain-specific models
3. **Voice activity detection**: Automatic speech detection
4. **Audio format conversion**: On-the-fly format conversion
5. **Batch processing**: Process multiple files simultaneously
6. **Performance optimization**: GPU acceleration support
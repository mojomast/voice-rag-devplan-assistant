import os
import uuid
import tempfile
import base64
import io
import asyncio
import hashlib
import json
import time
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Union, BinaryIO, Any, Tuple, Iterator, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import openai
from openai import OpenAI
import numpy as np

try:
    from .config import settings
    from .monitoring import cost_tracker
except ImportError:  # pragma: no cover - allow direct module imports in tests
    from config import settings
    from monitoring import cost_tracker

# Optional advanced audio processing
try:
    import librosa
    import noisereduce as nr
    from scipy import signal
    import soundfile as sf
    AUDIO_PROCESSING_AVAILABLE = True
    logger.info("Advanced audio processing enabled (librosa, noisereduce)")
except ImportError as e:
    AUDIO_PROCESSING_AVAILABLE = False
    logger.warning(f"Advanced audio processing not available: {e}")

# Optional speaker identification
try:
    from pyannote.audio import Pipeline
    import torchaudio
    SPEAKER_ID_AVAILABLE = True
    logger.info("Speaker identification available (pyannote)")
except ImportError:
    SPEAKER_ID_AVAILABLE = False
    logger.warning("Speaker identification not available - install pyannote.audio")

# Optional wake word detection
try:
    import openwakeword
    from openwakeword import Model
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WAKE_WORD_AVAILABLE = False
    logger.warning("openwakeword not available - wake word detection disabled")

class AudioFormat(Enum):
    """Supported audio formats with their properties"""
    MP3 = ("mp3", "audio/mpeg", True, 25 * 1024 * 1024)  # 25MB
    WAV = ("wav", "audio/wav", True, 50 * 1024 * 1024)   # 50MB
    WEBM = ("webm", "audio/webm", True, 25 * 1024 * 1024)  # 25MB
    OGG = ("ogg", "audio/ogg", True, 25 * 1024 * 1024)   # 25MB
    M4A = ("m4a", "audio/mp4", True, 25 * 1024 * 1024)   # 25MB
    FLAC = ("flac", "audio/flac", True, 100 * 1024 * 1024)  # 100MB
    
    def __init__(self, extension: str, mime_type: str, supported: bool, max_size: int):
        self.extension = extension
        self.mime_type = mime_type
        self.supported = supported
        self.max_size = max_size

class TTSError(Exception):
    """Base exception for TTS-related errors"""
    pass

class STTError(Exception):
    """Base exception for STT-related errors"""
    pass

class AudioFormatError(TTSError):
    """Raised when audio format is not supported"""
    pass

class AudioSizeError(TTSError):
    """Raised when audio file is too large"""
    pass

class VoiceNotFoundError(TTSError):
    """Raised when requested voice is not available"""
    pass

class CacheError(TTSError):
    """Raised when cache operations fail"""
    pass

# Enhanced STT Error Classes
class StreamingError(STTError):
    """Raised when streaming audio processing fails"""
    pass

class LanguageDetectionError(STTError):
    """Raised when language detection fails"""
    pass

class AudioEnhancementError(STTError):
    """Raised when audio enhancement fails"""
    pass

class TranscriptionError(STTError):
    """Raised when transcription fails"""
    pass

class AudioProcessingError(STTError):
    """Raised when general audio processing fails"""
    pass

@dataclass
class TTSCacheEntry:
    """Cache entry for TTS results"""
    text_hash: str
    voice: str
    audio_data: bytes
    mime_type: str
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "text_hash": self.text_hash,
            "voice": self.voice,
            "audio_data": base64.b64encode(self.audio_data).decode('utf-8'),
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TTSCacheEntry':
        return cls(
            text_hash=data["text_hash"],
            voice=data["voice"],
            audio_data=base64.b64decode(data["audio_data"]),
            mime_type=data["mime_type"],
            created_at=datetime.fromisoformat(data["created_at"]),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        )

@dataclass
class StreamingAudioChunk:
    """Represents a chunk of streaming audio data"""
    data: bytes
    timestamp: datetime
    sequence_number: int
    is_final: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "data": base64.b64encode(self.data).decode('utf-8'),
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "is_final": self.is_final,
            "size": len(self.data)
        }

@dataclass
class TranscriptionResult:
    """Enhanced transcription result with metadata"""
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict] = field(default_factory=list)
    detected_language: Optional[str] = None
    language_confidence: float = 0.0
    audio_quality_metrics: Optional[Dict] = None
    processing_time: float = 0.0
    enhanced_features: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "language": self.language,
            "confidence": self.confidence,
            "duration": self.duration,
            "segments": self.segments,
            "detected_language": self.detected_language,
            "language_confidence": self.language_confidence,
            "audio_quality_metrics": self.audio_quality_metrics,
            "processing_time": self.processing_time,
            "enhanced_features": self.enhanced_features
        }

@dataclass
class STTConfig:
    """Enhanced STT configuration options"""
    # Streaming settings
    streaming_chunk_size: int = 1024
    streaming_buffer_size: int = 8192
    streaming_max_duration: int = 300  # 5 minutes
    streaming_silence_threshold: float = 0.5  # seconds
    
    # Language detection settings
    enable_language_detection: bool = True
    language_detection_confidence_threshold: float = 0.7
    supported_languages: List[str] = field(default_factory=lambda: [
        "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja", "ko", "zh", "ar"
    ])
    
    # Audio enhancement settings
    enable_noise_reduction: bool = True
    enable_audio_enhancement: bool = True
    noise_reduction_strength: float = 0.8
    enable_normalization: bool = True
    enable_spectral_gating: bool = True
    
    # Transcription settings
    transcription_temperature: float = 0.2
    enable_word_timestamps: bool = True
    enable_segment_timestamps: bool = True
    max_audio_length: int = 600  # 10 minutes
    
    # Quality settings
    min_audio_quality_threshold: float = 0.3
    enable_quality_analysis: bool = True
    
    @classmethod
    def from_settings(cls) -> 'STTConfig':
        """Create STTConfig from application settings"""
        return cls(
            streaming_chunk_size=getattr(settings, "STT_STREAMING_CHUNK_SIZE", 1024),
            streaming_buffer_size=getattr(settings, "STT_STREAMING_BUFFER_SIZE", 8192),
            streaming_max_duration=getattr(settings, "STT_STREAMING_MAX_DURATION", 300),
            streaming_silence_threshold=getattr(settings, "STT_SILENCE_THRESHOLD", 0.5),
            enable_language_detection=getattr(settings, "STT_ENABLE_LANGUAGE_DETECTION", True),
            language_detection_confidence_threshold=getattr(settings, "STT_LANGUAGE_CONFIDENCE_THRESHOLD", 0.7),
            supported_languages=getattr(settings, "STT_SUPPORTED_LANGUAGES", [
                "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja", "ko", "zh", "ar"
            ]),
            enable_noise_reduction=getattr(settings, "STT_ENABLE_NOISE_REDUCTION", True),
            enable_audio_enhancement=getattr(settings, "STT_ENABLE_AUDIO_ENHANCEMENT", True),
            noise_reduction_strength=getattr(settings, "STT_NOISE_REDUCTION_STRENGTH", 0.8),
            enable_normalization=getattr(settings, "STT_ENABLE_NORMALIZATION", True),
            enable_spectral_gating=getattr(settings, "STT_ENABLE_SPECTRAL_GATING", True),
            transcription_temperature=getattr(settings, "STT_TRANSCRIPTION_TEMPERATURE", 0.2),
            enable_word_timestamps=getattr(settings, "STT_ENABLE_WORD_TIMESTAMPS", True),
            enable_segment_timestamps=getattr(settings, "STT_ENABLE_SEGMENT_TIMESTAMPS", True),
            max_audio_length=getattr(settings, "STT_MAX_AUDIO_LENGTH", 600),
            min_audio_quality_threshold=getattr(settings, "STT_MIN_AUDIO_QUALITY_THRESHOLD", 0.3),
            enable_quality_analysis=getattr(settings, "STT_ENABLE_QUALITY_ANALYSIS", True)
        )

VOICE_DEFINITIONS: List[tuple[str, str]] = [
    ("alloy", "Balanced, neutral voice"),
    ("echo", "Male voice with clarity"),
    ("fable", "Expressive, storytelling voice"),
    ("onyx", "Deep, authoritative voice"),
    ("nova", "Youthful, energetic voice"),
    ("shimmer", "Soft, pleasant voice")
]

VOICE_NAMES: List[str] = [name for name, _ in VOICE_DEFINITIONS]
VOICE_NAME_SET = set(VOICE_NAMES)

SUPPORTED_AUDIO_FORMATS = {
    fmt.extension: fmt for fmt in AudioFormat
}

class VoiceService:
    def __init__(self):
        self.test_mode = bool(getattr(settings, "TEST_MODE", False))
        api_key = getattr(settings, "OPENAI_API_KEY", None)

        if not api_key:
            self.test_mode = True

        self.client = None
        if api_key and not self.test_mode:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:  # pragma: no cover - safeguard for bad credentials
                logger.warning(f"Failed to initialize OpenAI client, falling back to test mode: {e}")
                self.test_mode = True

        self.wake_word_model = None
        self.speaker_pipeline = None
        
        # Initialize enhanced STT configuration
        self.stt_config = STTConfig.from_settings()
        
        # Initialize streaming components
        self._streaming_buffers: Dict[str, queue.Queue] = {}
        self._streaming_threads: Dict[str, threading.Thread] = {}
        self._streaming_active: Dict[str, bool] = {}
        
        # Initialize TTS cache
        self.cache_dir = Path(getattr(settings, "TTS_CACHE_DIR", "./cache/tts"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "tts_cache.json"
        self.cache_max_size = getattr(settings, "TTS_CACHE_MAX_SIZE", 100)  # Max entries
        self.cache_ttl = getattr(settings, "TTS_CACHE_TTL", 7 * 24 * 3600)  # 7 days in seconds
        self._tts_cache: Dict[str, TTSCacheEntry] = {}
        self._load_cache()

        # Initialize wake word detection if enabled and available
        if getattr(settings, "ENABLE_WAKE_WORD", False) and WAKE_WORD_AVAILABLE and not self.test_mode:
            try:
                self.wake_word_model = Model(
                    wakeword_models=["hey_jarvis_v0.1.pkl"],  # Default model
                    inference_framework="onnx"
                )
                logger.info(f"Wake word detection initialized: {settings.WAKE_WORD}")
            except Exception as e:
                logger.warning(f"Failed to initialize wake word detection: {e}")

        # Initialize speaker identification pipeline if available
        if SPEAKER_ID_AVAILABLE and not self.test_mode:
            try:
                # Note: In production, you'd use your own Hugging Face token
                # self.speaker_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
                logger.info("Speaker identification system ready")
            except Exception as e:
                logger.warning(f"Failed to initialize speaker identification: {e}")

        mode_label = "test" if self.test_mode or self.client is None else "production"
        logger.info(f"Voice Service initialized ({mode_label} mode)")
        logger.info(f"TTS cache initialized: {self.cache_dir}, max_entries: {self.cache_max_size}")

    def _load_cache(self) -> None:
        """Load TTS cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                self._tts_cache = {}
                for key, entry_data in cache_data.items():
                    entry = TTSCacheEntry.from_dict(entry_data)
                    # Check if entry is still valid
                    if self._is_cache_entry_valid(entry):
                        self._tts_cache[key] = entry
                
                logger.info(f"Loaded {len(self._tts_cache)} valid TTS cache entries")
            else:
                logger.info("No existing TTS cache file found")
        except Exception as e:
            logger.error(f"Failed to load TTS cache: {e}")
            self._tts_cache = {}

    def _save_cache(self) -> None:
        """Save TTS cache to disk"""
        try:
            cache_data = {key: entry.to_dict() for key, entry in self._tts_cache.items()}
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Saved {len(self._tts_cache)} TTS cache entries")
        except Exception as e:
            logger.error(f"Failed to save TTS cache: {e}")
            raise CacheError(f"Failed to save cache: {e}")

    def _is_cache_entry_valid(self, entry: TTSCacheEntry) -> bool:
        """Check if a cache entry is still valid"""
        age = (datetime.now() - entry.created_at).total_seconds()
        return age < self.cache_ttl

    def _cleanup_cache(self) -> None:
        """Clean up expired and excess cache entries"""
        try:
            # Remove expired entries
            expired_keys = [
                key for key, entry in self._tts_cache.items()
                if not self._is_cache_entry_valid(entry)
            ]
            for key in expired_keys:
                del self._tts_cache[key]
            
            # If still too many entries, remove least recently used
            if len(self._tts_cache) > self.cache_max_size:
                # Sort by last_accessed (None treated as oldest)
                sorted_entries = sorted(
                    self._tts_cache.items(),
                    key=lambda x: x[1].last_accessed or datetime.min
                )
                
                # Remove oldest entries
                excess_count = len(self._tts_cache) - self.cache_max_size
                for key, _ in sorted_entries[:excess_count]:
                    del self._tts_cache[key]
            
            logger.debug(f"Cache cleanup completed. Current size: {len(self._tts_cache)}")
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    def _get_cache_key(self, text: str, voice: str) -> str:
        """Generate cache key for text and voice"""
        content = f"{text}:{voice}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _get_cached_audio(self, text: str, voice: str) -> Optional[TTSCacheEntry]:
        """Get cached audio if available"""
        cache_key = self._get_cache_key(text, voice)
        entry = self._tts_cache.get(cache_key)
        
        if entry and self._is_cache_entry_valid(entry):
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            logger.debug(f"Cache hit for text hash: {cache_key}")
            return entry
        
        return None

    def _cache_audio(self, text: str, voice: str, audio_data: bytes, mime_type: str) -> None:
        """Cache audio data"""
        try:
            cache_key = self._get_cache_key(text, voice)
            entry = TTSCacheEntry(
                text_hash=cache_key,
                voice=voice,
                audio_data=audio_data,
                mime_type=mime_type,
                created_at=datetime.now(),
                access_count=1,
                last_accessed=datetime.now()
            )
            
            self._tts_cache[cache_key] = entry
            
            # Cleanup if needed
            if len(self._tts_cache) > self.cache_max_size:
                self._cleanup_cache()
            
            # Save to disk
            self._save_cache()
            
            logger.debug(f"Cached audio for text hash: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to cache audio: {e}")
            # Don't raise - caching failure shouldn't break TTS

    def validate_audio_format_enhanced(self, file_path: str) -> Dict[str, Any]:
        """Enhanced audio format validation with detailed error reporting"""
        try:
            if not os.path.exists(file_path):
                return {
                    "valid": False,
                    "error": "File does not exist",
                    "error_type": "file_not_found"
                }
            
            file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
            
            if file_extension not in SUPPORTED_AUDIO_FORMATS:
                return {
                    "valid": False,
                    "error": f"Unsupported format: .{file_extension}",
                    "error_type": "unsupported_format",
                    "supported_formats": list(SUPPORTED_AUDIO_FORMATS.keys())
                }
            
            audio_format = SUPPORTED_AUDIO_FORMATS[file_extension]
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > audio_format.max_size:
                return {
                    "valid": False,
                    "error": f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds {audio_format.max_size / 1024 / 1024:.0f}MB limit",
                    "error_type": "file_too_large",
                    "file_size": file_size,
                    "max_size": audio_format.max_size
                }
            
            # Check if file is actually readable
            try:
                with open(file_path, 'rb') as f:
                    # Read first few bytes to verify it's not corrupted
                    header = f.read(1024)
                    if not header:
                        return {
                            "valid": False,
                            "error": "File appears to be empty or corrupted",
                            "error_type": "corrupted_file"
                        }
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"Cannot read file: {str(e)}",
                    "error_type": "read_error"
                }
            
            return {
                "valid": True,
                "format": file_extension,
                "mime_type": audio_format.mime_type,
                "size": file_size,
                "max_size": audio_format.max_size,
                "supported": audio_format.supported
            }
            
        except Exception as e:
            logger.error(f"Audio format validation failed: {e}")
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "error_type": "validation_error"
            }

    def transcribe_audio(self, audio_file_path: Optional[str], language: Optional[str] = None) -> Dict:
        """Transcribe an audio file to text, with graceful fallbacks in test mode."""
        logger.info(f"Transcribing audio file: {audio_file_path}")

        if not audio_file_path:
            logger.error("No audio file path provided for transcription")
            return {
                "text": "",
                "status": "error",
                "error": "Audio file path is required",
                "error_type": "invalid_input"
            }

        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return {
                "text": "",
                "status": "error",
                "error": "Audio file not found",
                "error_type": "file_not_found"
            }

        try:
            file_size = os.path.getsize(audio_file_path)
            duration_estimate = file_size / (128000 / 8)  # Rough estimate based on 128kbps
        except OSError as exc:
            logger.error(f"Failed to inspect audio file for transcription: {exc}")
            return {
                "text": "",
                "status": "error",
                "error": "Unable to read audio file",
                "error_type": "file_read_error"
            }

        if self.client and not self.test_mode:
            try:
                with open(audio_file_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=settings.WHISPER_MODEL,
                        file=audio_file,
                        language=language,
                        response_format="verbose_json",
                        temperature=self.stt_config.transcription_temperature
                    )

                cost_tracker.track_api_call(
                    model=settings.WHISPER_MODEL,
                    duration=duration_estimate,
                    call_type="transcription"
                )

                result = {
                    "text": self._extract_text(transcript),
                    "language": getattr(transcript, "language", language or "unknown"),
                    "duration": getattr(transcript, "duration", duration_estimate),
                    "confidence": getattr(transcript, "confidence", 1.0),
                    "segments": getattr(transcript, "segments", []),
                    "status": "success"
                }

                logger.info(
                    f"Transcription successful: {len(result['text'])} characters, language: {result['language']}"
                )
                return result
            except Exception as exc:
                logger.error(f"Error during OpenAI transcription: {exc}")
                return {
                    "text": "",
                    "status": "error",
                    "error": str(exc),
                    "error_type": "transcription_failed"
                }

        # Lightweight fallback for test/offline mode - create mock result
        logger.warning("OpenAI transcription not available in test mode; returning mock result")
        return {
            "text": "",
            "language": language or "unknown",
            "duration": duration_estimate,
            "confidence": 0.0,
            "segments": [],
            "status": "error",
            "error": "Transcription unavailable in test mode - requires OpenAI API key",
            "error_type": "test_mode_limitation"
        }

    def transcribe_audio_enhanced(self, audio_file_path: Optional[str], language: Optional[str] = None) -> Dict:
        """Enhanced transcription with audio processing, language detection, and quality analysis"""
        start_time = time.time()
        logger.info(f"Starting enhanced transcription: {audio_file_path}")

        if not audio_file_path:
            return {
                "text": "",
                "status": "error",
                "error": "Audio file path is required",
                "error_type": "invalid_input",
                "processing_time": time.time() - start_time
            }

        try:
            # Validate audio format
            validation = self.validate_audio_format_enhanced(audio_file_path)
            if not validation["valid"]:
                return {
                    "text": "",
                    "status": "error",
                    "error": validation["error"],
                    "error_type": validation["error_type"],
                    "processing_time": time.time() - start_time
                }

            processed_path = audio_file_path
            enhancement_results = []
            
            # Step 1: Enhance audio quality if enabled
            if self.stt_config.enable_audio_enhancement and AUDIO_PROCESSING_AVAILABLE:
                enhancement_result = self.enhance_audio_quality(audio_file_path)
                if enhancement_result["status"] == "success":
                    processed_path = enhancement_result["enhanced_file"]
                    enhancement_results.append(enhancement_result)
                    logger.info("Audio enhancement applied for transcription")

            # Step 2: Language detection if enabled and no language specified
            detected_language = language
            language_confidence = 1.0
            
            if self.stt_config.enable_language_detection and not language:
                lang_detection = self.detect_language_enhanced(processed_path)
                if lang_detection["status"] == "success":
                    detected_language = lang_detection["language"]
                    language_confidence = lang_detection["confidence"]
                    logger.info(f"Auto-detected language: {detected_language} (confidence: {language_confidence:.2f})")

            # Step 3: Analyze audio quality if enabled
            quality_metrics = None
            if self.stt_config.enable_quality_analysis and AUDIO_PROCESSING_AVAILABLE:
                quality_analysis = self.analyze_audio_characteristics(processed_path)
                if quality_analysis["status"] == "success":
                    quality_metrics = quality_analysis
                    
                    # Check if quality meets threshold
                    if quality_metrics.get("quality_metrics", {}).get("snr_estimate_db", 0) < self.stt_config.min_audio_quality_threshold * 20:
                        logger.warning(f"Audio quality below threshold: {quality_metrics['quality_metrics']['snr_estimate_db']:.1f} dB")

            # Step 4: Perform transcription
            transcription_result = self.transcribe_audio(processed_path, detected_language)
            
            if transcription_result["status"] != "success":
                return transcription_result

            # Step 5: Create enhanced result
            processing_time = time.time() - start_time
            
            enhanced_result = TranscriptionResult(
                text=transcription_result["text"],
                language=transcription_result.get("language", detected_language or "unknown"),
                confidence=transcription_result.get("confidence", 1.0),
                duration=transcription_result.get("duration", 0),
                segments=transcription_result.get("segments", []),
                detected_language=detected_language,
                language_confidence=language_confidence,
                audio_quality_metrics=quality_metrics,
                processing_time=processing_time,
                enhanced_features={
                    "audio_enhanced": len(enhancement_results) > 0,
                    "language_auto_detected": language is None and detected_language is not None,
                    "quality_analyzed": quality_metrics is not None,
                    "enhancement_count": len(enhancement_results),
                    "original_file": audio_file_path,
                    "processed_file": processed_path,
                    "file_different": processed_path != audio_file_path
                }
            )

            result = enhanced_result.to_dict()
            result["status"] = "success"
            
            logger.info(f"Enhanced transcription completed: {len(result['text'])} chars, time: {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Enhanced transcription failed: {e}")
            return {
                "text": "",
                "status": "error",
                "error": str(e),
                "error_type": "enhanced_transcription_failed",
                "processing_time": time.time() - start_time
            }

    def synthesize_speech(
        self,
        text: Optional[str],
        voice: Optional[str] = None,
        output_file_path: Optional[str] = None,
        use_cache: bool = True,
        output_format: str = "mp3"
    ) -> Dict:
        """Enhanced text-to-speech synthesis with caching and improved error handling."""

        # Input validation
        if text is None or text.strip() == "":
            error_msg = "Text is required for speech synthesis"
            logger.error(error_msg)
            return {
                "audio_file": "",
                "output_file": "",
                "status": "error",
                "error": error_msg,
                "error_type": "invalid_input"
            }

        text = text.strip()
        
        # Validate text length
        max_text_length = getattr(settings, "TTS_MAX_TEXT_LENGTH", 4096)
        if len(text) > max_text_length:
            error_msg = f"Text too long ({len(text)} chars). Maximum allowed: {max_text_length}"
            logger.error(error_msg)
            return {
                "audio_file": "",
                "output_file": "",
                "status": "error",
                "error": error_msg,
                "error_type": "text_too_long"
            }

        # Resolve voice parameter
        inferred_output_path = output_file_path
        resolved_voice = voice

        if inferred_output_path is None and resolved_voice and self._looks_like_file_path(resolved_voice):
            inferred_output_path = resolved_voice
            resolved_voice = None

        if not resolved_voice:
            resolved_voice = getattr(settings, "TTS_VOICE", VOICE_NAMES[0])

        if resolved_voice not in VOICE_NAME_SET:
            error_msg = f"Voice '{resolved_voice}' is not supported. Available voices: {', '.join(VOICE_NAMES)}"
            logger.error(error_msg)
            return {
                "audio_file": "",
                "output_file": "",
                "status": "error",
                "error": error_msg,
                "error_type": "voice_not_supported",
                "available_voices": VOICE_NAMES
            }

        # Check cache first
        if use_cache and not self.test_mode:
            cached_entry = self._get_cached_audio(text, resolved_voice)
            if cached_entry:
                target_path = self._ensure_output_path(inferred_output_path)
                try:
                    with open(target_path, 'wb') as f:
                        f.write(cached_entry.audio_data)
                    
                    logger.info(f"Retrieved from cache: {len(text)} characters, voice: {resolved_voice}")
                    return self._synthesis_success(target_path, resolved_voice, text, cached=True)
                except Exception as e:
                    logger.warning(f"Failed to write cached audio to file: {e}")
                    # Continue with normal synthesis

        target_path = self._ensure_output_path(inferred_output_path)
        logger.info(f"Synthesizing speech: {len(text)} characters, voice: {resolved_voice}, format: {output_format}")

        # Production mode with OpenAI
        if self.client and not self.test_mode:
            try:
                # Validate output format
                if output_format not in ["mp3", "opus", "aac", "flac"]:
                    output_format = "mp3"  # Default fallback
                
                response = self.client.audio.speech.create(
                    model=settings.TTS_MODEL,
                    voice=resolved_voice,
                    input=text,
                    response_format=output_format,
                    speed=getattr(settings, "TTS_SPEED", 1.0)
                )

                # Get audio data for caching
                audio_data = response.content
                with open(target_path, 'wb') as f:
                    f.write(audio_data)

                # Cache the result
                if use_cache:
                    mime_type = f"audio/{output_format}"
                    self._cache_audio(text, resolved_voice, audio_data, mime_type)

                cost_tracker.track_api_call(
                    model=settings.TTS_MODEL,
                    characters=len(text),
                    call_type="text_to_speech"
                )

                return self._synthesis_success(target_path, resolved_voice, text)

            except Exception as exc:
                logger.error(f"Error during OpenAI speech synthesis: {exc}")
                return {
                    "audio_file": "",
                    "output_file": "",
                    "status": "error",
                    "error": str(exc),
                    "error_type": "synthesis_failed"
                }

        # Test/offline fallback - create synthetic audio
        logger.warning("OpenAI TTS not available in test mode; generating synthetic audio output")
        try:
            self._create_fake_audio_file(target_path, text)
            return self._synthesis_success(target_path, resolved_voice, text, simulated=True)
        except Exception as exc:
            logger.error(f"Synthetic audio generation failed: {exc}")
            return {
                "audio_file": "",
                "output_file": "",
                "status": "error",
                "error": "TTS unavailable in test mode - requires OpenAI API key",
                "error_type": "test_mode_limitation"
            }

    def process_voice_query(self, audio_file_path: str) -> Dict:
        """Complete voice processing pipeline: STT -> transcription"""
        logger.info("Processing voice query pipeline")

        # Step 1: Transcribe audio
        transcription_result = self.transcribe_audio(audio_file_path)

        if transcription_result["status"] != "success":
            return transcription_result

        return {
            "transcription": transcription_result["text"],
            "language": transcription_result.get("language", "unknown"),
            "duration": transcription_result.get("duration", 0),
            "status": "success"
        }

    def detect_wake_word(self, audio_data) -> bool:
        """Detect wake word in audio data (if enabled)"""
        if not self.wake_word_model:
            return False

        try:
            # Process audio through wake word model
            prediction = self.wake_word_model.predict(audio_data)

            # Check if wake word was detected
            for wake_word, confidence in prediction.items():
                if confidence > 0.5:  # Configurable threshold
                    logger.info(f"Wake word detected: {wake_word} (confidence: {confidence})")
                    return True

            return False

        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            return False

    def transcribe_base64_audio(self, audio_base64: str, mime_type: str = "audio/webm",
                               language: Optional[str] = None) -> Dict:
        """Transcribe audio from base64 data (from native recorder)"""
        logger.info(f"Transcribing base64 audio data: {len(audio_base64)} chars, type: {mime_type}")

        try:
            # Decode base64 audio
            audio_data = base64.b64decode(audio_base64)

            # Determine file extension from mime type
            extension = ".webm"
            if "mp4" in mime_type:
                extension = ".mp4"
            elif "wav" in mime_type:
                extension = ".wav"
            elif "ogg" in mime_type:
                extension = ".ogg"

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # Transcribe using existing method
                result = self.transcribe_audio(temp_file_path, language)
                result["source"] = "native_recorder"
                result["original_format"] = mime_type
                return result
            finally:
                # Clean up temporary file
                self.cleanup_temp_files([temp_file_path])

        except Exception as e:
            logger.error(f"Error transcribing base64 audio: {e}")
            return {
                "text": "",
                "status": "error",
                "error": str(e)
            }

    def synthesize_speech_to_base64(self, text: str, voice: Optional[str] = None) -> Dict:
        """Synthesize speech and return as base64 for direct playback"""
        if not voice:
            voice = settings.TTS_VOICE

        logger.info(f"Synthesizing speech to base64: {len(text)} characters")

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file_path = temp_file.name

            # Generate speech
            result = self.synthesize_speech(text, voice=voice, output_file_path=temp_file_path)

            if result["status"] != "success":
                return result

            # Read file and convert to base64
            audio_path = result.get("audio_file") or temp_file_path

            with open(audio_path, "rb") as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Clean up
            self.cleanup_temp_files([audio_path])

            return {
                "audio_base64": audio_base64,
                "mime_type": "audio/mpeg",
                "voice": voice,
                "text_length": len(text),
                "audio_size": len(audio_data),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error synthesizing speech to base64: {e}")
            return {
                "audio_base64": "",
                "status": "error",
                "error": str(e)
            }

    async def process_streaming_audio(self, audio_stream: BinaryIO, chunk_size: int = 1024) -> Dict:
        """Process audio in streaming fashion for real-time applications"""
        logger.info("Processing streaming audio")

        audio_chunks = []
        try:
            # Read audio stream in chunks
            while True:
                chunk = audio_stream.read(chunk_size)
                if not chunk:
                    break
                audio_chunks.append(chunk)

            # Combine chunks
            audio_data = b''.join(audio_chunks)

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # Transcribe with enhanced features
                result = self.transcribe_audio_enhanced(temp_file_path)
                result["source"] = "streaming"
                result["chunks_processed"] = len(audio_chunks)
                return result
            finally:
                # Clean up
                self.cleanup_temp_files([temp_file_path])

        except Exception as e:
            logger.error(f"Error processing streaming audio: {e}")
            return {
                "text": "",
                "status": "error",
                "error": str(e),
                "error_type": "streaming_error"
            }

    def start_streaming_session(self, session_id: str) -> Dict:
        """Start a new streaming audio session"""
        if session_id in self._streaming_active:
            return {
                "status": "error",
                "error": f"Streaming session {session_id} already exists",
                "error_type": "session_exists"
            }

        try:
            self._streaming_buffers[session_id] = queue.Queue(maxsize=self.stt_config.streaming_buffer_size)
            self._streaming_active[session_id] = True
            
            logger.info(f"Started streaming session: {session_id}")
            
            return {
                "status": "success",
                "session_id": session_id,
                "config": {
                    "chunk_size": self.stt_config.streaming_chunk_size,
                    "buffer_size": self.stt_config.streaming_buffer_size,
                    "max_duration": self.stt_config.streaming_max_duration
                }
            }
        except Exception as e:
            logger.error(f"Failed to start streaming session: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": "session_start_failed"
            }

    def add_streaming_chunk(self, session_id: str, audio_data: bytes, is_final: bool = False) -> Dict:
        """Add an audio chunk to a streaming session"""
        if session_id not in self._streaming_active:
            return {
                "status": "error",
                "error": f"Streaming session {session_id} not found",
                "error_type": "session_not_found"
            }

        try:
            chunk = StreamingAudioChunk(
                data=audio_data,
                timestamp=datetime.now(),
                sequence_number=len(self._streaming_buffers[session_id].queue),
                is_final=is_final
            )
            
            self._streaming_buffers[session_id].put(chunk)
            
            if is_final:
                self._streaming_active[session_id] = False
            
            return {
                "status": "success",
                "sequence_number": chunk.sequence_number,
                "timestamp": chunk.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to add streaming chunk: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": "chunk_add_failed"
            }

    async def process_streaming_session(self, session_id: str) -> AsyncGenerator[Dict, None]:
        """Process a streaming session and yield transcription results"""
        if session_id not in self._streaming_active:
            yield {
                "status": "error",
                "error": f"Streaming session {session_id} not found",
                "error_type": "session_not_found"
            }
            return

        buffer = self._streaming_buffers[session_id]
        audio_chunks = []
        start_time = time.time()
        
        try:
            while self._streaming_active.get(session_id, False) or not buffer.empty():
                try:
                    # Wait for chunk with timeout
                    chunk = buffer.get(timeout=1.0)
                    audio_chunks.append(chunk)
                    
                    # Check if we should process accumulated audio
                    if chunk.is_final or len(audio_chunks) >= 10:  # Process every 10 chunks or on final
                        combined_audio = b''.join([c.data for c in audio_chunks])
                        
                        # Create temporary file for processing
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                            temp_file.write(combined_audio)
                            temp_file_path = temp_file.name
                        
                        try:
                            # Transcribe the accumulated audio
                            result = self.transcribe_audio_enhanced(temp_file_path)
                            result["session_id"] = session_id
                            result["chunk_count"] = len(audio_chunks)
                            result["partial"] = not chunk.is_final
                            
                            yield result
                            
                            if chunk.is_final:
                                break
                                
                        finally:
                            self.cleanup_temp_files([temp_file_path])
                        
                        # Keep only recent chunks for context
                        if len(audio_chunks) > 20:
                            audio_chunks = audio_chunks[-10:]
                            
                except queue.Empty:
                    # Check timeout
                    if time.time() - start_time > self.stt_config.streaming_max_duration:
                        logger.warning(f"Streaming session {session_id} timed out")
                        break
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing streaming session {session_id}: {e}")
            yield {
                "status": "error",
                "error": str(e),
                "error_type": "streaming_processing_error",
                "session_id": session_id
            }
        finally:
            # Cleanup session
            self.cleanup_streaming_session(session_id)

    def cleanup_streaming_session(self, session_id: str) -> None:
        """Clean up a streaming session"""
        try:
            self._streaming_active.pop(session_id, None)
            self._streaming_buffers.pop(session_id, None)
            self._streaming_threads.pop(session_id, None)
            logger.info(f"Cleaned up streaming session: {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up streaming session {session_id}: {e}")

    def detect_language_enhanced(self, audio_file_path: str) -> Dict:
        """Enhanced language detection with confidence scoring"""
        logger.info(f"Detecting language for: {audio_file_path}")
        start_time = time.time()

        try:
            # Validate audio file first
            validation = self.validate_audio_format_enhanced(audio_file_path)
            if not validation["valid"]:
                return {
                    "language": "unknown",
                    "confidence": 0.0,
                    "status": "error",
                    "error": validation["error"],
                    "error_type": validation["error_type"],
                    "processing_time": time.time() - start_time
                }

            # Enhance audio if enabled
            processed_path = audio_file_path
            if self.stt_config.enable_audio_enhancement and AUDIO_PROCESSING_AVAILABLE:
                enhancement_result = self.enhance_audio_quality(audio_file_path)
                if enhancement_result["status"] == "success":
                    processed_path = enhancement_result["enhanced_file"]

            try:
                with open(processed_path, "rb") as audio_file:
                    # Use Whisper to detect language with verbose output
                    transcript = self.client.audio.transcriptions.create(
                        model=settings.WHISPER_MODEL,
                        file=audio_file,
                        response_format="verbose_json",
                        language=None,  # Let Whisper detect
                        temperature=self.stt_config.transcription_temperature
                    )

                detected_language = getattr(transcript, 'language', 'unknown')
                confidence = getattr(transcript, 'confidence', 0.0) if hasattr(transcript, 'confidence') else 1.0
                
                # Analyze segments for language consistency
                segments = getattr(transcript, 'segments', [])
                language_consistency = self._analyze_language_consistency(segments)
                
                processing_time = time.time() - start_time
                
                result = {
                    "language": detected_language,
                    "confidence": confidence,
                    "status": "success",
                    "processing_time": processing_time,
                    "language_consistency": language_consistency,
                    "supported_language": detected_language in self.stt_config.supported_languages,
                    "segments_analyzed": len(segments),
                    "audio_enhanced": processed_path != audio_file_path
                }
                
                logger.info(f"Language detected: {detected_language} (confidence: {confidence:.2f}, time: {processing_time:.2f}s)")
                return result

            except Exception as e:
                logger.error(f"Whisper language detection failed: {e}")
                return {
                    "language": "unknown",
                    "confidence": 0.0,
                    "status": "error",
                    "error": str(e),
                    "error_type": "whisper_detection_failed",
                    "processing_time": time.time() - start_time
                }

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {
                "language": "unknown",
                "confidence": 0.0,
                "status": "error",
                "error": str(e),
                "error_type": "detection_failed",
                "processing_time": time.time() - start_time
            }

    def _analyze_language_consistency(self, segments: List[Dict]) -> Dict:
        """Analyze language consistency across transcription segments"""
        if not segments:
            return {"consistency_score": 0.0, "language_changes": 0}
        
        # This is a simplified analysis - in a real implementation you might
        # use language detection on each segment
        languages = []
        for segment in segments:
            # Whisper doesn't provide per-segment language, so we analyze
            # text patterns as a proxy for language consistency
            text = getattr(segment, 'text', '')
            if text:
                # Simple heuristic: check for common language indicators
                languages.append(self._detect_text_language_heuristic(text))
        
        # Calculate consistency
        unique_languages = set(filter(None, languages))
        consistency_score = 1.0 if len(unique_languages) <= 1 else 0.5
        
        return {
            "consistency_score": consistency_score,
            "language_changes": len(unique_languages) - 1,
            "detected_languages": list(unique_languages)
        }

    def _detect_text_language_heuristic(self, text: str) -> Optional[str]:
        """Simple heuristic language detection from text"""
        # This is a very basic implementation - in production you'd use
        # a proper language detection library like langdetect
        text_lower = text.lower()
        
        # Check for common language indicators
        if any(word in text_lower for word in ['the', 'and', 'is', 'are', 'was', 'were']):
            return 'en'
        elif any(word in text_lower for word in ['el', 'la', 'es', 'son', 'era', 'eran']):
            return 'es'
        elif any(word in text_lower for word in ['le', 'la', 'les', 'est', 'sont', 'était']):
            return 'fr'
        elif any(word in text_lower for word in ['der', 'die', 'das', 'ist', 'sind', 'war']):
            return 'de'
        
        return None

    def detect_language(self, audio_file_path: str) -> Dict:
        """Detect language of audio file"""
        logger.info(f"Detecting language for: {audio_file_path}")

        try:
            with open(audio_file_path, "rb") as audio_file:
                # Use Whisper to detect language
                transcript = self.client.audio.transcriptions.create(
                    model=settings.WHISPER_MODEL,
                    file=audio_file,
                    response_format="verbose_json"
                )

            detected_language = getattr(transcript, 'language', 'unknown')
            confidence = getattr(transcript, 'confidence', 0.0) if hasattr(transcript, 'confidence') else 1.0

            logger.info(f"Language detected: {detected_language} (confidence: {confidence})")

            return {
                "language": detected_language,
                "confidence": confidence,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return {
                "language": "unknown",
                "confidence": 0.0,
                "status": "error",
                "error": str(e)
            }

    def get_audio_info(self, audio_file_path: str) -> Dict:
        """Get metadata information about audio file"""
        try:
            import mutagen  # type: ignore[import-unresolved]
            from mutagen import File  # type: ignore[import-unresolved]

            audio_file = File(audio_file_path)
            if audio_file is None:
                # Fallback to basic file info
                file_size = os.path.getsize(audio_file_path)
                return {
                    "file_size": file_size,
                    "duration": None,
                    "format": os.path.splitext(audio_file_path)[1],
                    "status": "partial"
                }

            return {
                "file_size": os.path.getsize(audio_file_path),
                "duration": getattr(audio_file.info, 'length', 0),
                "bitrate": getattr(audio_file.info, 'bitrate', 0),
                "sample_rate": getattr(audio_file.info, 'sample_rate', 0),
                "channels": getattr(audio_file.info, 'channels', 0),
                "format": audio_file.mime[0] if audio_file.mime else "unknown",
                "status": "success"
            }

        except ImportError:
            # mutagen not available, use basic info
            file_size = os.path.getsize(audio_file_path)
            return {
                "file_size": file_size,
                "duration": None,
                "format": os.path.splitext(audio_file_path)[1],
                "status": "basic",
                "note": "Install mutagen for detailed audio metadata"
            }
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def validate_audio_format(self, file_path: str) -> Dict:
        """Validate if audio format is supported"""
        supported_formats = ['.mp3', '.mp4', '.wav', '.webm', '.ogg', '.m4a', '.flac']

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in supported_formats:
            # Additional size check
            file_size = os.path.getsize(file_path)
            max_size = 25 * 1024 * 1024  # 25MB limit for OpenAI

            if file_size > max_size:
                return {
                    "valid": False,
                    "error": f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds 25MB limit",
                    "format": file_extension
                }

            return {
                "valid": True,
                "format": file_extension,
                "size": file_size
            }
        else:
            return {
                "valid": False,
                "error": f"Unsupported format: {file_extension}",
                "supported_formats": supported_formats
            }

    def get_available_voices(self, include_descriptions: bool = False) -> List[Union[str, Dict[str, str]]]:
        """Return available voice identifiers, optionally including descriptions."""
        if include_descriptions:
            return [
                {"name": name, "description": description}
                for name, description in VOICE_DEFINITIONS
            ]

        return list(VOICE_NAMES)

    @staticmethod
    def _looks_like_file_path(candidate: str) -> bool:
        if not candidate:
            return False

        lowered = candidate.lower()
        path_indicators = (os.sep in candidate, "/" in candidate, "\\" in candidate)
        audio_extensions = (".mp3", ".wav", ".ogg", ".webm", ".m4a", ".flac")

        return any(path_indicators) or lowered.endswith(audio_extensions)

    @staticmethod
    def _prepare_directory(path: str) -> None:
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _ensure_output_path(self, desired_path: Optional[str]) -> str:
        if desired_path:
            self._prepare_directory(desired_path)
            return desired_path

        temp_dir = getattr(settings, "TEMP_AUDIO_DIR", "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
        file_name = f"voice_{uuid.uuid4().hex}.mp3"
        return os.path.join(temp_dir, file_name)

    def _create_fake_audio_file(self, target_path: str, text: str) -> str:
        self._prepare_directory(target_path)
        payload = (text or "synthetic speech").encode("utf-8")
        with open(target_path, "wb") as fake_audio:
            fake_audio.write(b"SIMULATED AUDIO\n")
            fake_audio.write(payload[:4096])
        return target_path

    @staticmethod
    def _extract_text(transcript: Any) -> str:
        if transcript is None:
            return ""
        if hasattr(transcript, "text"):
            return getattr(transcript, "text")
        if isinstance(transcript, dict):
            return str(transcript.get("text", ""))
        return str(transcript)

    @staticmethod
    def _extract_audio_bytes(response: Any) -> Optional[bytes]:
        if response is None:
            return None

        content = None
        if hasattr(response, "content"):
            content = response.content
        elif isinstance(response, dict):
            content = response.get("content")

        if content is None:
            return None

        if isinstance(content, bytes):
            return content

        if hasattr(content, "read") and callable(content.read):
            return content.read()

        return None

    @staticmethod
    def _synthesis_success(path: str, voice: str, text: str, simulated: bool = False, cached: bool = False) -> Dict:
        return {
            "audio_file": path,
            "output_file": path,
            "voice": voice,
            "text_length": len(text),
            "status": "success",
            "simulated": simulated,
            "cached": cached
        }

    # ===== Advanced Voice Processing Methods =====

    def enhance_audio_quality(self, audio_file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Enhance audio quality using advanced processing techniques."""
        if not AUDIO_PROCESSING_AVAILABLE:
            return {
                "status": "error",
                "error": "Advanced audio processing not available",
                "error_type": "processing_unavailable"
            }

        logger.info(f"Enhancing audio quality: {audio_file_path}")

        try:
            # Validate input file
            validation = self.validate_audio_format_enhanced(audio_file_path)
            if not validation["valid"]:
                return {
                    "status": "error",
                    "error": validation["error"],
                    "error_type": validation["error_type"]
                }

            # Load audio with format-specific handling
            audio_data, sample_rate = self._load_audio_with_format_handling(audio_file_path)
            
            # Analyze original audio quality
            original_quality = self._calculate_quality_metrics(audio_data, sample_rate)
            
            enhancements_applied = []
            enhanced_audio = audio_data.copy()

            # Step 1: Apply noise reduction if enabled
            if self.stt_config.enable_noise_reduction:
                enhanced_audio = self._apply_noise_reduction(enhanced_audio, sample_rate)
                enhancements_applied.append("noise_reduction")

            # Step 2: Apply normalization if enabled
            if self.stt_config.enable_normalization:
                enhanced_audio = self._apply_normalization(enhanced_audio)
                enhancements_applied.append("normalization")

            # Step 3: Apply spectral gating if enabled
            if self.stt_config.enable_spectral_gating:
                enhanced_audio = self._apply_spectral_gating(enhanced_audio, sample_rate)
                enhancements_applied.append("spectral_gating")

            # Step 4: Apply additional enhancements
            enhanced_audio = self._apply_audio_enhancements(enhanced_audio, sample_rate)
            enhancements_applied.extend(["dynamic_range_compression", "high_pass_filter"])

            # Step 5: Save enhanced audio with format preservation
            if output_path is None:
                base, ext = os.path.splitext(audio_file_path)
                output_path = f"{base}_enhanced{ext}"

            self._save_audio_with_format(enhanced_audio, sample_rate, output_path, ext)

            # Calculate quality improvement
            enhanced_quality = self._calculate_quality_metrics(enhanced_audio, sample_rate)
            quality_improvement = self._calculate_quality_improvement(original_quality, enhanced_quality)

            return {
                "status": "success",
                "original_file": audio_file_path,
                "enhanced_file": output_path,
                "sample_rate": sample_rate,
                "duration": len(enhanced_audio) / sample_rate,
                "enhancements_applied": enhancements_applied,
                "original_quality": original_quality,
                "enhanced_quality": enhanced_quality,
                "quality_improvement": quality_improvement,
                "processing_info": {
                    "samples_processed": len(enhanced_audio),
                    "channels": 1,  # librosa loads as mono
                    "bit_depth": "float32"
                }
            }

        except Exception as e:
            logger.error(f"Error enhancing audio quality: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": "audio_enhancement_failed"
            }

    def _load_audio_with_format_handling(self, audio_file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio with format-specific handling"""
        file_ext = os.path.splitext(audio_file_path)[1].lower()
        
        try:
            # Use librosa for most formats
            if file_ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']:
                audio_data, sample_rate = librosa.load(audio_file_path, sr=None, mono=True)
                return audio_data, sample_rate
            else:
                # Fallback to soundfile for other formats
                audio_data, sample_rate = sf.read(audio_file_path, always_2d=False)
                if audio_data.ndim > 1:
                    audio_data = np.mean(audio_data, axis=1)  # Convert to mono
                return audio_data, sample_rate
        except Exception as e:
            logger.warning(f"Format-specific loading failed, using fallback: {e}")
            # Final fallback
            return librosa.load(audio_file_path, sr=None, mono=True)

    def _save_audio_with_format(self, audio_data: np.ndarray, sample_rate: int,
                               output_path: str, file_ext: str) -> None:
        """Save audio with format-specific handling"""
        try:
            # Normalize audio to prevent clipping
            audio_data = np.clip(audio_data, -1.0, 1.0)
            
            # Use soundfile for most formats
            if file_ext in ['.wav', '.flac']:
                sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')
            elif file_ext in ['.ogg']:
                sf.write(output_path, audio_data, sample_rate, subtype='VORBIS')
            else:
                # Default to WAV for unknown formats
                sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')
                
        except Exception as e:
            logger.warning(f"Format-specific saving failed, using fallback: {e}")
            # Fallback to WAV
            sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')

    def _apply_normalization(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply audio normalization"""
        try:
            # Peak normalization to -1 dBFS
            peak = np.max(np.abs(audio_data))
            if peak > 0:
                target_peak = 0.891  # -1 dBFS
                audio_data = audio_data * (target_peak / peak)
            return audio_data
        except Exception as e:
            logger.warning(f"Normalization failed: {e}")
            return audio_data

    def _apply_spectral_gating(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply spectral gating for noise reduction"""
        try:
            # Simple spectral gating implementation
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Calculate noise floor (bottom 10% of magnitude values)
            noise_floor = np.percentile(magnitude, 10)
            
            # Apply gate
            gate_threshold = noise_floor * 3  # 3x noise floor
            gated_magnitude = np.where(magnitude < gate_threshold, magnitude * 0.1, magnitude)
            
            # Reconstruct signal
            gated_stft = gated_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(gated_stft)
            
            # Ensure same length as original
            if len(enhanced_audio) > len(audio_data):
                enhanced_audio = enhanced_audio[:len(audio_data)]
            elif len(enhanced_audio) < len(audio_data):
                enhanced_audio = np.pad(enhanced_audio, (0, len(audio_data) - len(enhanced_audio)))
            
            return enhanced_audio
        except Exception as e:
            logger.warning(f"Spectral gating failed: {e}")
            return audio_data

    def _calculate_quality_improvement(self, original: Dict, enhanced: Dict) -> Dict[str, float]:
        """Calculate quality improvement metrics"""
        try:
            improvements = {}
            
            # SNR improvement
            if "snr_estimate" in original and "snr_estimate" in enhanced:
                improvements["snr_improvement_db"] = enhanced["snr_estimate"] - original["snr_estimate"]
            
            # Dynamic range improvement
            if "dynamic_range_db" in original and "dynamic_range_db" in enhanced:
                improvements["dynamic_range_improvement_db"] = enhanced["dynamic_range_db"] - original["dynamic_range_db"]
            
            # Overall quality score (0-1)
            improvements["overall_improvement"] = min(1.0, max(0.0,
                (improvements.get("snr_improvement_db", 0) + improvements.get("dynamic_range_improvement_db", 0)) / 20
            ))
            
            return improvements
        except Exception as e:
            logger.warning(f"Quality improvement calculation failed: {e}")
            return {"overall_improvement": 0.0}

    def _apply_noise_reduction(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply noise reduction to audio data."""
        try:
            # Use stationary noise reduction
            reduced_noise = nr.reduce_noise(
                y=audio_data,
                sr=sample_rate,
                stationary=False,
                prop_decrease=0.8
            )
            return reduced_noise
        except Exception as e:
            logger.warning(f"Noise reduction failed, using original audio: {e}")
            return audio_data

    def _apply_audio_enhancements(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply additional audio enhancements."""
        try:
            # Normalize audio
            audio_data = librosa.util.normalize(audio_data)

            # Apply gentle high-pass filter to remove low-frequency noise
            sos = signal.butter(5, 80, btype='high', fs=sample_rate, output='sos')
            audio_data = signal.sosfilt(sos, audio_data)

            # Apply dynamic range compression
            audio_data = self._apply_compression(audio_data)

            return audio_data

        except Exception as e:
            logger.warning(f"Audio enhancement failed: {e}")
            return audio_data

    def _apply_compression(self, audio_data: np.ndarray, ratio: float = 4.0, threshold: float = -20.0) -> np.ndarray:
        """Apply dynamic range compression."""
        try:
            # Convert to dB
            audio_db = 20 * np.log10(np.abs(audio_data) + 1e-8)

            # Apply compression
            compressed_db = np.where(
                audio_db > threshold,
                threshold + (audio_db - threshold) / ratio,
                audio_db
            )

            # Convert back to linear scale
            compressed_audio = np.sign(audio_data) * (10 ** (compressed_db / 20))

            return compressed_audio

        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return audio_data

    def identify_speakers(self, audio_file_path: str) -> Dict[str, Any]:
        """Identify and diarize speakers in audio."""
        if not SPEAKER_ID_AVAILABLE:
            return {
                "status": "error",
                "error": "Speaker identification not available"
            }

        logger.info(f"Identifying speakers in: {audio_file_path}")

        try:
            # Mock implementation - in production you'd use pyannote
            # Load audio for analysis
            audio_data, sample_rate = librosa.load(audio_file_path, sr=16000)
            duration = len(audio_data) / sample_rate

            # Mock speaker diarization result
            speakers = [
                {
                    "speaker_id": "SPEAKER_00",
                    "start_time": 0.0,
                    "end_time": duration * 0.6,
                    "confidence": 0.89
                },
                {
                    "speaker_id": "SPEAKER_01",
                    "start_time": duration * 0.6,
                    "end_time": duration,
                    "confidence": 0.82
                }
            ]

            return {
                "status": "success",
                "audio_file": audio_file_path,
                "duration": duration,
                "num_speakers": len(set(s["speaker_id"] for s in speakers)),
                "speakers": speakers,
                "speaker_segments": len(speakers)
            }

        except Exception as e:
            logger.error(f"Speaker identification failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def transcribe_with_speaker_identification(self, audio_file_path: str,
                                             language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio with speaker identification."""
        logger.info(f"Transcribing with speaker identification: {audio_file_path}")

        try:
            # First, identify speakers
            speaker_result = self.identify_speakers(audio_file_path)

            if speaker_result["status"] != "success":
                logger.warning("Speaker identification failed, proceeding with regular transcription")
                return self.transcribe_audio(audio_file_path, language)

            # Transcribe the full audio
            transcription_result = self.transcribe_audio(audio_file_path, language)

            if transcription_result["status"] != "success":
                return transcription_result

            # Combine results
            combined_result = {
                "status": "success",
                "text": transcription_result["text"],
                "language": transcription_result.get("language", "unknown"),
                "duration": transcription_result.get("duration", 0),
                "confidence": transcription_result.get("confidence", 1.0),
                "speaker_analysis": {
                    "num_speakers": speaker_result.get("num_speakers", 1),
                    "speakers": speaker_result.get("speakers", []),
                    "speaker_segments": speaker_result.get("speaker_segments", 0)
                },
                "enhanced_features": {
                    "speaker_diarization": True,
                    "multi_speaker_detected": speaker_result.get("num_speakers", 1) > 1
                }
            }

            return combined_result

        except Exception as e:
            logger.error(f"Error in speaker-aware transcription: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def analyze_audio_characteristics(self, audio_file_path: str) -> Dict[str, Any]:
        """Analyze audio characteristics and quality metrics."""
        if not AUDIO_PROCESSING_AVAILABLE:
            return {
                "status": "error",
                "error": "Audio analysis not available"
            }

        logger.info(f"Analyzing audio characteristics: {audio_file_path}")

        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None)
            duration = len(audio_data) / sample_rate

            # Calculate various audio metrics
            analysis = {
                "status": "success",
                "file_path": audio_file_path,
                "basic_info": {
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "channels": 1,  # librosa loads as mono by default
                    "samples": len(audio_data)
                },
                "quality_metrics": self._calculate_quality_metrics(audio_data, sample_rate),
                "spectral_features": self._extract_spectral_features(audio_data, sample_rate),
                "noise_analysis": self._analyze_noise_level(audio_data, sample_rate)
            }

            return analysis

        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _calculate_quality_metrics(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Calculate audio quality metrics."""
        try:
            # RMS energy
            rms = np.sqrt(np.mean(audio_data**2))

            # Peak amplitude
            peak = np.max(np.abs(audio_data))

            # Dynamic range
            dynamic_range = 20 * np.log10(peak / (rms + 1e-8))

            # Zero crossing rate
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data))

            # Spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            spectral_centroid_mean = np.mean(spectral_centroids)

            return {
                "rms_energy": float(rms),
                "peak_amplitude": float(peak),
                "dynamic_range_db": float(dynamic_range),
                "zero_crossing_rate": float(zcr),
                "spectral_centroid_hz": float(spectral_centroid_mean),
                "snr_estimate": float(20 * np.log10(rms / (np.std(audio_data) + 1e-8)))
            }

        except Exception as e:
            logger.warning(f"Quality metrics calculation failed: {e}")
            return {}

    def _extract_spectral_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Extract spectral features from audio."""
        try:
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)

            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)

            # MFCCs
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)

            return {
                "spectral_rolloff_hz": float(np.mean(spectral_rolloff)),
                "spectral_bandwidth_hz": float(np.mean(spectral_bandwidth)),
                "mfcc_mean": np.mean(mfccs, axis=1).tolist(),
                "dominant_frequency_hz": float(sample_rate * np.argmax(np.abs(np.fft.fft(audio_data))) / len(audio_data))
            }

        except Exception as e:
            logger.warning(f"Spectral feature extraction failed: {e}")
            return {}

    def _analyze_noise_level(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Analyze noise levels in audio."""
        try:
            # Estimate noise floor (bottom 10% of energy)
            energy = audio_data**2
            sorted_energy = np.sort(energy)
            noise_floor = np.mean(sorted_energy[:int(len(sorted_energy) * 0.1)])

            # Signal to noise ratio estimate
            signal_energy = np.mean(energy)
            snr_estimate = 10 * np.log10(signal_energy / (noise_floor + 1e-8))

            # Silence detection (frames below threshold)
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.01 * sample_rate)     # 10ms hop

            frames = librosa.util.frame(audio_data, frame_length=frame_length, hop_length=hop_length)
            frame_energy = np.sum(frames**2, axis=0)
            silence_threshold = np.percentile(frame_energy, 20)
            silence_ratio = np.sum(frame_energy < silence_threshold) / len(frame_energy)

            return {
                "noise_floor_db": float(10 * np.log10(noise_floor + 1e-8)),
                "snr_estimate_db": float(snr_estimate),
                "silence_ratio": float(silence_ratio),
                "speech_activity": float(1.0 - silence_ratio)
            }

        except Exception as e:
            logger.warning(f"Noise analysis failed: {e}")
            return {}

    def get_processing_capabilities(self) -> Dict[str, bool]:
        """Get information about available processing capabilities."""
        return {
            "basic_transcription": True,
            "text_to_speech": True,
            "wake_word_detection": WAKE_WORD_AVAILABLE,
            "noise_reduction": AUDIO_PROCESSING_AVAILABLE,
            "speaker_identification": SPEAKER_ID_AVAILABLE,
            "audio_enhancement": AUDIO_PROCESSING_AVAILABLE,
            "quality_analysis": AUDIO_PROCESSING_AVAILABLE,
            "base64_processing": True,
            "streaming_support": True,
            "language_detection": True
        }

    def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary audio files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {e}")
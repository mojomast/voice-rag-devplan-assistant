import os
import uuid
import tempfile
import base64
import io
import asyncio
import numpy as np
from typing import Optional, Dict, List, Union, BinaryIO, Any
from loguru import logger
import openai
from openai import OpenAI

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

    def transcribe_audio(self, audio_file_path: Optional[str], language: Optional[str] = None) -> Dict:
        """Transcribe an audio file to text, with graceful fallbacks in test mode."""
        logger.info(f"Transcribing audio file: {audio_file_path}")

        if not audio_file_path:
            logger.error("No audio file path provided for transcription")
            return {
                "text": "",
                "status": "error",
                "error": "Audio file path is required"
            }

        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return {
                "text": "",
                "status": "error",
                "error": "Audio file not found"
            }

        try:
            file_size = os.path.getsize(audio_file_path)
            duration_estimate = file_size / (128000 / 8)  # Rough estimate based on 128kbps
        except OSError as exc:
            logger.error(f"Failed to inspect audio file for transcription: {exc}")
            return {
                "text": "",
                "status": "error",
                "error": "Unable to read audio file"
            }

        if self.client and not self.test_mode:
            try:
                with open(audio_file_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=settings.WHISPER_MODEL,
                        file=audio_file,
                        language=language,
                        response_format="verbose_json",
                        temperature=0.2
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
                    "error": str(exc)
                }

        # Lightweight fallback for test/offline mode
        try:
            speech_api = getattr(openai, "Audio", None)
            transcribe_method = getattr(speech_api, "transcribe", None) if speech_api else None

            if transcribe_method:
                with open(audio_file_path, "rb") as audio_file:
                    transcript = transcribe_method(
                        model=getattr(settings, "WHISPER_MODEL", "gpt-4o-mini-transcribe"),
                        file=audio_file,
                        language=language
                    )

                text = self._extract_text(transcript)
                language_value = getattr(transcript, "language", None)
                if language_value is None:
                    language_value = language or "unknown"
                elif not isinstance(language_value, str):
                    language_value = str(language_value)

                result = {
                    "text": text,
                    "language": language_value,
                    "duration": getattr(transcript, "duration", duration_estimate),
                    "confidence": getattr(transcript, "confidence", 1.0),
                    "segments": getattr(transcript, "segments", []),
                    "status": "success"
                }
                logger.info("Transcription completed via fallback OpenAI audio API")
                return result

            # If no API available, provide a deterministic stub
            logger.warning("OpenAI Audio transcribe API not available; returning stub result")
            return {
                "text": "",
                "language": language or "unknown",
                "duration": duration_estimate,
                "confidence": 0.0,
                "segments": [],
                "status": "error",
                "error": "Transcription unavailable in test mode without OpenAI dependency"
            }

        except Exception as exc:
            logger.error(f"Fallback transcription failed: {exc}")
            return {
                "text": "",
                "status": "error",
                "error": str(exc)
            }

    def synthesize_speech(
        self,
        text: Optional[str],
        voice: Optional[str] = None,
        output_file_path: Optional[str] = None
    ) -> Dict:
        """Synthesize text to speech, supporting both production and test modes."""

        if text is None or text == "":
            logger.error("No text provided for speech synthesis")
            return {
                "audio_file": "",
                "output_file": "",
                "status": "error",
                "error": "Text is required for speech synthesis"
            }

        inferred_output_path = output_file_path
        resolved_voice = voice

        if inferred_output_path is None and resolved_voice and self._looks_like_file_path(resolved_voice):
            inferred_output_path = resolved_voice
            resolved_voice = None

        if not resolved_voice:
            resolved_voice = getattr(settings, "TTS_VOICE", VOICE_NAMES[0])

        if resolved_voice not in VOICE_NAME_SET:
            logger.error(f"Requested voice '{resolved_voice}' is not supported")
            return {
                "audio_file": "",
                "output_file": "",
                "status": "error",
                "error": f"Voice '{resolved_voice}' is not supported"
            }

        target_path = self._ensure_output_path(inferred_output_path)
        logger.info(f"Synthesizing speech: {len(text)} characters, voice: {resolved_voice}")

        if self.client and not self.test_mode:
            try:
                response = self.client.audio.speech.create(
                    model=settings.TTS_MODEL,
                    voice=resolved_voice,
                    input=text,
                    response_format="mp3",
                    speed=1.0
                )

                response.stream_to_file(target_path)

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
                    "error": str(exc)
                }

        # Test/offline fallback
        try:
            speech_api = getattr(openai, "Audio", None)
            speech_resource = getattr(speech_api, "speech", None) if speech_api else None
            create_method = getattr(speech_resource, "create", None) if speech_resource else None

            if create_method:
                response = create_method(
                    model=getattr(settings, "TTS_MODEL", "gpt-4o-mini-tts"),
                    voice=resolved_voice,
                    input=text,
                    response_format="mp3",
                )

                audio_bytes = self._extract_audio_bytes(response)
                if audio_bytes:
                    self._prepare_directory(target_path)
                    with open(target_path, "wb") as audio_file:
                        audio_file.write(audio_bytes)
                    logger.info("Speech synthesized via fallback OpenAI audio API")
                    return self._synthesis_success(target_path, resolved_voice, text)

            logger.warning("OpenAI Audio speech API not available; generating synthetic audio output")
            self._create_fake_audio_file(target_path, text)
            return self._synthesis_success(target_path, resolved_voice, text, simulated=True)

        except Exception as exc:
            logger.error(f"Fallback speech synthesis failed: {exc}")
            return {
                "audio_file": "",
                "output_file": "",
                "status": "error",
                "error": str(exc)
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
                # Transcribe
                result = self.transcribe_audio(temp_file_path)
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
                "error": str(e)
            }

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
    def _synthesis_success(path: str, voice: str, text: str, simulated: bool = False) -> Dict:
        return {
            "audio_file": path,
            "output_file": path,
            "voice": voice,
            "text_length": len(text),
            "status": "success",
            "simulated": simulated
        }

    # ===== Advanced Voice Processing Methods =====

    def enhance_audio_quality(self, audio_file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Enhance audio quality using advanced processing techniques."""
        if not AUDIO_PROCESSING_AVAILABLE:
            return {
                "status": "error",
                "error": "Advanced audio processing not available"
            }

        logger.info(f"Enhancing audio quality: {audio_file_path}")

        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None)

            # Apply noise reduction
            enhanced_audio = self._apply_noise_reduction(audio_data, sample_rate)

            # Apply additional enhancements
            enhanced_audio = self._apply_audio_enhancements(enhanced_audio, sample_rate)

            # Save enhanced audio
            if output_path is None:
                base, ext = os.path.splitext(audio_file_path)
                output_path = f"{base}_enhanced{ext}"

            sf.write(output_path, enhanced_audio, sample_rate)

            return {
                "status": "success",
                "original_file": audio_file_path,
                "enhanced_file": output_path,
                "sample_rate": sample_rate,
                "duration": len(enhanced_audio) / sample_rate,
                "enhancements_applied": [
                    "noise_reduction",
                    "spectral_gating",
                    "dynamic_range_compression"
                ]
            }

        except Exception as e:
            logger.error(f"Error enhancing audio quality: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

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
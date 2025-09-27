import os
import tempfile
from typing import Optional, Dict, List
from loguru import logger
from openai import OpenAI
from .config import settings

# Optional wake word detection
try:
    import openwakeword
    from openwakeword import Model
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WAKE_WORD_AVAILABLE = False
    logger.warning("openwakeword not available - wake word detection disabled")

class VoiceService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.wake_word_model = None

        # Initialize wake word detection if enabled and available
        if settings.ENABLE_WAKE_WORD and WAKE_WORD_AVAILABLE:
            try:
                self.wake_word_model = Model(
                    wakeword_models=["hey_jarvis_v0.1.pkl"],  # Default model
                    inference_framework="onnx"
                )
                logger.info(f"Wake word detection initialized: {settings.WAKE_WORD}")
            except Exception as e:
                logger.warning(f"Failed to initialize wake word detection: {e}")

        logger.info("Voice Service initialized")

    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> Dict:
        """Transcribes an audio file to text using the OpenAI Whisper model."""
        logger.info(f"Transcribing audio file: {audio_file_path}")

        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=settings.WHISPER_MODEL,
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )

            result = {
                "text": transcript.text,
                "language": transcript.language if hasattr(transcript, 'language') else 'unknown',
                "duration": transcript.duration if hasattr(transcript, 'duration') else 0,
                "status": "success"
            }

            logger.info(f"Transcription successful: {len(result['text'])} characters")
            return result

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {
                "text": "",
                "status": "error",
                "error": str(e)
            }

    def synthesize_speech(self, text: str, output_file_path: str, voice: Optional[str] = None) -> Dict:
        """Synthesizes text into speech using the OpenAI TTS model."""
        if not voice:
            voice = settings.TTS_VOICE

        logger.info(f"Synthesizing speech: {len(text)} characters, voice: {voice}")

        try:
            response = self.client.audio.speech.create(
                model=settings.TTS_MODEL,
                voice=voice,
                input=text,
                response_format="mp3"
            )

            response.stream_to_file(output_file_path)

            result = {
                "output_file": output_file_path,
                "voice": voice,
                "text_length": len(text),
                "status": "success"
            }

            logger.info(f"Speech synthesis successful: {output_file_path}")
            return result

        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}")
            return {
                "output_file": "",
                "status": "error",
                "error": str(e)
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

    def get_available_voices(self) -> List[str]:
        """Get list of available TTS voices"""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary audio files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {e}")
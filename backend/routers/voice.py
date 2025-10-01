from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any
import tempfile
import os
import json
from loguru import logger

from ..voice_service import VoiceService, TTSError, AudioFormatError, CacheError
from ..config import settings

router = APIRouter(prefix="/voice", tags=["voice"])

# Initialize voice service
voice_service = VoiceService()

@router.get("/voices")
async def get_available_voices():
    """Get list of available TTS voices"""
    try:
        voices = voice_service.get_available_voices(include_descriptions=True)
        return {
            "voices": voices,
            "total_count": len(voices),
            "default_voice": settings.TTS_VOICE
        }
    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize")
async def synthesize_speech(
    text: str,
    voice: Optional[str] = None,
    output_format: str = "mp3",
    use_cache: bool = True,
    speech_speed: Optional[float] = None
):
    """Synthesize text to speech"""
    try:
        # Override speed if provided
        if speech_speed is not None:
            original_speed = getattr(settings, 'TTS_SPEED', 1.0)
            settings.TTS_SPEED = speech_speed
        
        result = voice_service.synthesize_speech(
            text=text,
            voice=voice,
            output_format=output_format,
            use_cache=use_cache
        )
        
        # Restore original speed
        if speech_speed is not None:
            settings.TTS_SPEED = original_speed
        
        return result
        
    except TTSError as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in speech synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize/base64")
async def synthesize_speech_base64(
    text: str,
    voice: Optional[str] = None,
    output_format: str = "mp3",
    use_cache: bool = True,
    include_metadata: bool = True,
    speech_speed: Optional[float] = None
):
    """Synthesize text to speech and return base64 encoded audio"""
    try:
        # Override speed if provided
        if speech_speed is not None:
            original_speed = getattr(settings, 'TTS_SPEED', 1.0)
            settings.TTS_SPEED = speech_speed
        
        result = voice_service.synthesize_speech_to_base64(
            text=text,
            voice=voice,
            output_format=output_format,
            use_cache=use_cache,
            include_metadata=include_metadata
        )
        
        # Restore original speed
        if speech_speed is not None:
            settings.TTS_SPEED = original_speed
        
        return result
        
    except TTSError as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in base64 speech synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None
):
    """Transcribe audio file to text"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Validate audio format first
            validation_result = voice_service.validate_audio_format_enhanced(tmp_file_path)
            if not validation_result["valid"]:
                os.unlink(tmp_file_path)
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": validation_result["error"],
                        "error_type": validation_result["error_type"]
                    }
                )
            
            # Transcribe audio
            result = voice_service.transcribe_audio(tmp_file_path, language)
            
            # Add validation info to result
            result["file_info"] = {
                "filename": file.filename,
                "format": validation_result.get("format"),
                "size": validation_result.get("size"),
                "mime_type": validation_result.get("mime_type")
            }
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe/base64")
async def transcribe_base64_audio(
    audio_base64: str,
    mime_type: str = "audio/webm",
    language: Optional[str] = None
):
    """Transcribe base64 encoded audio to text"""
    try:
        result = voice_service.transcribe_base64_audio(audio_base64, mime_type, language)
        return result
        
    except Exception as e:
        logger.error(f"Error transcribing base64 audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-format")
async def validate_audio_format(file: UploadFile = File(...)):
    """Validate audio file format and properties"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            result = voice_service.validate_audio_format_enhanced(tmp_file_path)
            
            # Add file info
            result["filename"] = file.filename
            result["content_type"] = file.content_type
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        logger.error(f"Error validating audio format: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_cache_stats():
    """Get TTS cache statistics"""
    try:
        cache_stats = {
            "total_entries": len(voice_service._tts_cache),
            "cache_size_bytes": sum(
                len(entry.audio_data) for entry in voice_service._tts_cache.values()
            ),
            "expired_entries": len([
                entry for entry in voice_service._tts_cache.values()
                if not voice_service._is_cache_entry_valid(entry)
            ]),
            "hit_rate": 0.0,  # Would need to track hits/misses over time
            "entries": {}
        }
        
        # Add detailed entry information (limited to prevent large responses)
        for i, (key, entry) in enumerate(voice_service._tts_cache.items()):
            if i >= 10:  # Limit to first 10 entries
                break
            cache_stats["entries"][key] = {
                "voice": entry.voice,
                "text_length": len(entry.audio_data),
                "created_at": entry.created_at.isoformat(),
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
                "mime_type": entry.mime_type
            }
        
        return cache_stats
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache")
async def clear_cache():
    """Clear TTS cache"""
    try:
        voice_service._tts_cache.clear()
        voice_service._save_cache()
        
        return {
            "message": "Cache cleared successfully",
            "timestamp": voice_service._get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/cleanup")
async def cleanup_cache(background_tasks: BackgroundTasks):
    """Clean up expired cache entries"""
    try:
        background_tasks.add_task(voice_service._cleanup_cache)
        
        return {
            "message": "Cache cleanup initiated",
            "timestamp": voice_service._get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error initiating cache cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_voice_capabilities():
    """Get voice service capabilities and configuration"""
    try:
        capabilities = voice_service.get_processing_capabilities()
        
        # Add configuration info
        config_info = {
            "tts_model": settings.TTS_MODEL,
            "whisper_model": settings.WHISPER_MODEL,
            "default_voice": settings.TTS_VOICE,
            "cache_enabled": settings.TTS_ENABLE_CACHING,
            "cache_max_size": settings.TTS_CACHE_MAX_SIZE,
            "cache_ttl": settings.TTS_CACHE_TTL,
            "max_text_length": settings.TTS_MAX_TEXT_LENGTH,
            "default_format": settings.TTS_DEFAULT_FORMAT,
            "supported_formats": ["mp3", "opus", "aac", "flac"],
            "test_mode": voice_service.test_mode
        }
        
        return {
            "capabilities": capabilities,
            "configuration": config_info,
            "available_voices": voice_service.get_available_voices(include_descriptions=True)
        }
        
    except Exception as e:
        logger.error(f"Error getting voice capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def voice_health_check():
    """Health check for voice service"""
    try:
        health_status = {
            "status": "healthy",
            "test_mode": voice_service.test_mode,
            "cache_status": "active" if voice_service._tts_cache else "empty",
            "supported_formats": list(voice_service.SUPPORTED_AUDIO_FORMATS.keys()),
            "available_voices_count": len(voice_service.get_available_voices())
        }
        
        # Check OpenAI client
        if voice_service.client:
            health_status["openai_client"] = "connected"
        else:
            health_status["openai_client"] = "disconnected"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in voice health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Helper method to add to VoiceService class
def _get_current_timestamp(self) -> str:
    """Get current timestamp as ISO string"""
    from datetime import datetime
    return datetime.now().isoformat()

# Add the method to VoiceService
VoiceService._get_current_timestamp = _get_current_timestamp
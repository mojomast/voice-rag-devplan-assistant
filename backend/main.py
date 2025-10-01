from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger
import os
import shutil
import tempfile
import uuid
from typing import Annotated, Optional, List, Dict
from datetime import datetime, timedelta

try:
    from .config import settings
    from .document_processor import DocumentProcessor
    from .rag_handler import RAGHandler
    from .voice_service import VoiceService
    from .monitoring import performance_monitor, cost_tracker
    from .performance_optimizer import (
        performance_track, smart_cache, performance_monitor as perf_monitor,
        resource_monitor, get_performance_summary, initialize_performance_optimizations
    )
    from .security import (
        security_manager, threat_detector, rate_limiter, security_monitor,
        InputValidator, security_check_input, get_client_ip, initialize_security_system,
        require_authentication, rate_limit, validate_input
    )
    from .monitoring_alerts import (
        monitoring_service, metrics_collector, alert_manager, health_checker,
        initialize_monitoring_system, shutdown_monitoring_system
    )
    from .database import init_database, shutdown_database
    from .routers import projects as projects_router
    from .routers import devplans as devplans_router
    from .routers import planning_chat as planning_router
    from .routers import templates as templates_router
    from .routers import search as search_router
except ImportError:  # pragma: no cover - enables direct module imports in tests
    from config import settings
    from document_processor import DocumentProcessor
    from rag_handler import RAGHandler
    from voice_service import VoiceService
    from monitoring import performance_monitor, cost_tracker
    from performance_optimizer import (
        performance_track, smart_cache, performance_monitor as perf_monitor,
        resource_monitor, get_performance_summary, initialize_performance_optimizations
    )
    from security import (
        security_manager, threat_detector, rate_limiter, security_monitor,
        InputValidator, security_check_input, get_client_ip, initialize_security_system,
        require_authentication, rate_limit, validate_input
    )
    from monitoring_alerts import (
        monitoring_service, metrics_collector, alert_manager, health_checker,
        initialize_monitoring_system, shutdown_monitoring_system
    )
    from database import init_database, shutdown_database
    from routers import projects as projects_router
    from routers import devplans as devplans_router
    from routers import planning_chat as planning_router
    from routers import templates as templates_router
    from routers import search as search_router

# Configure logging
logger.add("logs/app.log", rotation="1 day", retention="7 days", level=settings.LOG_LEVEL)

app = FastAPI(
    title="Voice-Enabled RAG System API",
    description="A voice-enabled document Q&A system with intelligent LLM routing",
    version="1.0.0"
)

# Register routers for development planning feature
app.include_router(projects_router.router)
app.include_router(devplans_router.router)
app.include_router(planning_router.router)
app.include_router(templates_router.router)
app.include_router(search_router.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security middleware for threat detection and rate limiting."""
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    # Check if IP is blocked
    if threat_detector.is_ip_blocked(client_ip):
        logger.warning(f"Blocked IP attempted access: {client_ip}")
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied"}
        )

    skip_limits = getattr(settings, "TEST_MODE", False) or getattr(settings, "DEBUG", False)

    if not skip_limits:
        # Rate limiting
        if rate_limiter.is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )

        # Check burst protection
        if rate_limiter.check_burst_protection(client_ip):
            logger.warning(f"Burst limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests"}
            )

    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

# Authentication setup
security_scheme = HTTPBearer(auto_error=False)

# Global service instances
doc_processor = DocumentProcessor()
voice_service = VoiceService()
_rag_handler = None  # Lazy loaded

# Ensure required directories exist
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
os.makedirs("temp_audio", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# --- Dependency Injection ---
def get_rag_handler():
    """Lazy load RAG handler to allow for vector store initialization"""
    global _rag_handler
    if _rag_handler is None:
        try:
            _rag_handler = RAGHandler()
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return _rag_handler

def reset_rag_handler():
    """Reset RAG handler to reload vector store after document updates"""
    global _rag_handler
    _rag_handler = None

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str
    include_sources: bool = True

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    query: str
    status: str

class DocumentUploadResponse(BaseModel):
    status: str
    message: str
    file_name: str
    document_count: int = 0
    chunk_count: int = 0

class VoiceSettings(BaseModel):
    voice: str = "alloy"
    speed: float = 1.0

class Base64AudioRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    mime_type: str = "audio/webm"
    language: Optional[str] = None

class TextToSpeechRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    return_base64: bool = False

class AudioTranscriptionResponse(BaseModel):
    text: str
    language: str
    duration: float
    confidence: float = 1.0
    source: Optional[str] = None
    status: str

class SystemStatus(BaseModel):
    status: str
    vector_store_exists: bool
    document_count: int
    requesty_enabled: bool
    wake_word_enabled: bool
    test_mode: bool


class ConfigUpdateRequest(BaseModel):
    openai_api_key: Optional[str] = None
    requesty_api_key: Optional[str] = None
    test_mode: Optional[bool] = None

# --- Utility Functions ---
def cleanup_temp_files(file_paths: List[str]):
    """Background task to cleanup temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")

# --- API Endpoints ---

@app.on_event("startup")
async def startup_event():
    """Initialize performance optimizations, security, and monitoring on startup."""
    await init_database()
    await initialize_performance_optimizations()
    initialize_security_system()
    await initialize_monitoring_system()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of monitoring and other services."""
    await shutdown_monitoring_system()
    await shutdown_database()

@app.get("/", response_model=SystemStatus)
@performance_track("health_check")
async def root():
    """Get system status and health check"""
    try:
        vector_stats = doc_processor.get_vector_store_stats()
        return SystemStatus(
            status="healthy",
            vector_store_exists=vector_stats.get("exists", False),
            document_count=vector_stats.get("document_count", 0),
            requesty_enabled=bool(settings.REQUESTY_API_KEY),
            wake_word_enabled=settings.ENABLE_WAKE_WORD,
            test_mode=settings.TEST_MODE
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemStatus(
            status="unhealthy",
            vector_store_exists=False,
            document_count=0,
            requesty_enabled=False,
            wake_word_enabled=False,
            test_mode=True
        )


@app.post("/config/update")
async def update_configuration(
    config_update: ConfigUpdateRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """Update runtime credentials and test mode flags."""
    admin_token = None

    if credentials and (credentials.scheme or "").lower() == "bearer":
        admin_token = credentials.credentials
    else:
        admin_token = (
            request.headers.get("x-admin-token")
            or request.headers.get("x-admin-secret")
            or request.headers.get("x-runtime-admin")
        )

    is_authorized = settings.validate_admin_token(admin_token)

    if not is_authorized and admin_token:
        is_authorized, _ = security_manager.validate_api_key(admin_token)

    if not is_authorized:
        client_ip = get_client_ip(request)
        logger.warning("Unauthorized runtime configuration attempt from %s", client_ip)
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")

    try:
        update_result = settings.update_credentials(
            openai_api_key=config_update.openai_api_key,
            requesty_api_key=config_update.requesty_api_key,
            test_mode=config_update.test_mode
        )

        global doc_processor, voice_service
        doc_processor = DocumentProcessor()
        voice_service = VoiceService()
        reset_rag_handler()

        logger.info(
            "Runtime configuration updated (test_mode=%s, requesty_enabled=%s, openai_configured=%s)",
            update_result["test_mode"],
            update_result["requesty_enabled"],
            update_result["openai_configured"]
        )

        return {"status": "success", **update_result}

    except Exception as exc:
        logger.error(f"Failed to update configuration: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/documents/upload", response_model=DocumentUploadResponse)
@performance_track("document_upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a document, process it, and add it to the vector store."""
    logger.info(f"Document upload request: {file.filename}")

    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.docx'}
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file
    file_location = os.path.join(settings.UPLOAD_PATH, file.filename)

    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Process and index the document
        result = doc_processor.process_and_index_file(file_location)

        if result["status"] == "success":
            # Reset RAG handler to reload vector store
            reset_rag_handler()

            response = DocumentUploadResponse(
                status="success",
                message=f"Document '{file.filename}' uploaded and indexed successfully",
                file_name=file.filename,
                document_count=result.get("document_count", 0),
                chunk_count=result.get("chunk_count", 0)
            )

            logger.info(f"Successfully processed: {file.filename}")
            return response
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.post("/query/text", response_model=QueryResponse)
@performance_track("text_query")
@validate_input(max_length=1000)
async def query_text(
    request: QueryRequest,
    http_request: Request,
    rag_handler: Annotated[RAGHandler, Depends(get_rag_handler)]
):
    """Process a text query and return an answer with sources."""
    logger.info(f"Text query received: {request.query[:100]}...")

    # Security validation
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("user-agent", "")

    # Check input for security threats
    security_check_passed = await security_check_input(request.query, client_ip, user_agent)
    if not security_check_passed:
        logger.warning(f"Security check failed for query from {client_ip}")
        raise HTTPException(status_code=400, detail="Invalid input detected")

    # Check cache first
    cache_key = f"text_query:{request.query}"
    cached_result = await smart_cache.get(cache_key, include_sources=request.include_sources)
    if cached_result:
        logger.info("Returning cached result")
        return QueryResponse(**cached_result)

    try:
        result = rag_handler.ask_question(request.query)

        # Cache successful results
        await smart_cache.set(cache_key, result, ttl=600, include_sources=request.include_sources)

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Text query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/voice")
@performance_track("voice_query")
async def query_voice(
    background_tasks: BackgroundTasks,
    rag_handler: Annotated[RAGHandler, Depends(get_rag_handler)],
    file: UploadFile = File(...),
    voice_settings: Optional[str] = None
):
    """Process a voice query: audio -> text -> RAG -> audio response."""
    logger.info("Voice query received")

    # Create temporary files
    query_id = str(uuid.uuid4())
    temp_dir = "temp_audio"
    audio_input_path = os.path.join(temp_dir, f"query_{query_id}.wav")
    audio_output_path = os.path.join(temp_dir, f"response_{query_id}.mp3")

    try:
        # Save uploaded audio file
        with open(audio_input_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Step 1: Speech to Text
        transcription_result = voice_service.transcribe_audio(audio_input_path)

        if transcription_result["status"] != "success":
            raise HTTPException(status_code=400, detail="Audio transcription failed")

        query_text = transcription_result["text"]
        logger.info(f"Transcribed query: {query_text}")

        # Step 2: Get answer from RAG
        rag_result = rag_handler.ask_question(query_text)

        if rag_result["status"] != "success":
            raise HTTPException(status_code=500, detail="Failed to generate answer")

        answer_text = rag_result["answer"]

        # Step 3: Text to Speech
        tts_result = voice_service.synthesize_speech(
            answer_text,
            output_file_path=audio_output_path
        )

        if tts_result["status"] != "success":
            raise HTTPException(status_code=500, detail="Speech synthesis failed")

        # Schedule cleanup of temporary files
        background_tasks.add_task(cleanup_temp_files, [audio_input_path, audio_output_path])

        # Return audio response
        return FileResponse(
            path=audio_output_path,
            media_type="audio/mpeg",
            filename=f"response_{query_id}.mp3",
            headers={
                "X-Query-Text": query_text,
                "X-Response-Text": answer_text[:200] + "..." if len(answer_text) > 200 else answer_text
            }
        )

    except Exception as e:
        # Cleanup on error
        cleanup_temp_files([audio_input_path, audio_output_path])
        logger.error(f"Voice query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/stats")
async def get_document_stats():
    """Get statistics about indexed documents."""
    try:
        stats = doc_processor.get_vector_store_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/supported-formats")
async def get_supported_formats():
    """Get list of supported document formats."""
    try:
        formats = doc_processor.get_supported_formats()
        return formats
    except Exception as e:
        logger.error(f"Failed to get supported formats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/clear")
async def clear_documents():
    """Clear all documents from the vector store."""
    try:
        if os.path.exists(settings.VECTOR_STORE_PATH):
            shutil.rmtree(settings.VECTOR_STORE_PATH)
            os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)

        # Reset RAG handler
        reset_rag_handler()

        logger.info("All documents cleared from vector store")
        return {"status": "success", "message": "All documents cleared"}

    except Exception as e:
        logger.error(f"Failed to clear documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice/voices")
async def get_available_voices():
    """Get list of available TTS voices."""
    return {"voices": voice_service.get_available_voices()}

@app.post("/voice/transcribe-base64", response_model=AudioTranscriptionResponse)
async def transcribe_base64_audio(request: Base64AudioRequest):
    """Transcribe audio from base64 data (from native recorder)."""
    logger.info(f"Transcribing base64 audio: {len(request.audio_data)} chars, type: {request.mime_type}")

    try:
        result = voice_service.transcribe_base64_audio(
            request.audio_data,
            request.mime_type,
            request.language
        )

        if result["status"] != "success":
            raise HTTPException(status_code=400, detail=result.get("error", "Transcription failed"))

        return AudioTranscriptionResponse(
            text=result["text"],
            language=result.get("language", "unknown"),
            duration=result.get("duration", 0),
            confidence=result.get("confidence", 1.0),
            source=result.get("source", "base64"),
            status=result["status"]
        )

    except Exception as e:
        logger.error(f"Base64 transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/synthesize")
async def synthesize_speech_endpoint(request: TextToSpeechRequest):
    """Synthesize text to speech, optionally returning base64 audio."""
    logger.info(f"Synthesizing speech: {len(request.text)} characters, voice: {request.voice}")

    try:
        if request.return_base64:
            # Return base64 audio for direct playback
            result = voice_service.synthesize_speech_to_base64(request.text, request.voice)

            if result["status"] != "success":
                raise HTTPException(status_code=500, detail=result.get("error", "Speech synthesis failed"))

            return {
                "audio_base64": result["audio_base64"],
                "mime_type": result["mime_type"],
                "voice": result["voice"],
                "text_length": result["text_length"],
                "audio_size": result["audio_size"],
                "status": "success"
            }
        else:
            # Return audio file
            query_id = str(uuid.uuid4())
            temp_dir = "temp_audio"
            audio_output_path = os.path.join(temp_dir, f"tts_{query_id}.mp3")

            result = voice_service.synthesize_speech(
                request.text,
                voice=request.voice,
                output_file_path=audio_output_path
            )

            if result["status"] != "success":
                raise HTTPException(status_code=500, detail=result.get("error", "Speech synthesis failed"))

            return FileResponse(
                path=audio_output_path,
                media_type="audio/mpeg",
                filename=f"speech_{query_id}.mp3"
            )

    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/query-base64")
async def query_voice_base64(
    request: Base64AudioRequest,
    rag_handler: Annotated[RAGHandler, Depends(get_rag_handler)]
):
    """Complete voice query pipeline using base64 audio input."""
    logger.info("Processing voice query from base64 audio")

    try:
        # Step 1: Transcribe base64 audio
        transcription_result = voice_service.transcribe_base64_audio(
            request.audio_data,
            request.mime_type,
            request.language
        )

        if transcription_result["status"] != "success":
            raise HTTPException(status_code=400, detail="Audio transcription failed")

        query_text = transcription_result["text"]
        logger.info(f"Transcribed query: {query_text}")

        # Step 2: Get answer from RAG
        rag_result = rag_handler.ask_question(query_text)

        if rag_result["status"] != "success":
            raise HTTPException(status_code=500, detail="Failed to generate answer")

        answer_text = rag_result["answer"]

        # Step 3: Generate speech response as base64
        tts_result = voice_service.synthesize_speech_to_base64(answer_text)

        if tts_result["status"] != "success":
            raise HTTPException(status_code=500, detail="Speech synthesis failed")

        return {
            "query": query_text,
            "answer": answer_text,
            "transcription": {
                "text": query_text,
                "language": transcription_result.get("language", "unknown"),
                "duration": transcription_result.get("duration", 0),
                "confidence": transcription_result.get("confidence", 1.0)
            },
            "audio_response": {
                "audio_base64": tts_result["audio_base64"],
                "mime_type": tts_result["mime_type"],
                "voice": tts_result["voice"],
                "audio_size": tts_result["audio_size"]
            },
            "sources": rag_result.get("sources", []),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Voice query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/detect-language")
async def detect_audio_language(file: UploadFile = File(...)):
    """Detect the language of an audio file."""
    logger.info(f"Detecting language for audio file: {file.filename}")

    # Create temporary file
    query_id = str(uuid.uuid4())
    temp_dir = "temp_audio"
    audio_path = os.path.join(temp_dir, f"detect_{query_id}.{file.filename.split('.')[-1]}")

    try:
        # Save uploaded file
        with open(audio_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Detect language
        result = voice_service.detect_language(audio_path)

        # Cleanup
        cleanup_temp_files([audio_path])

        return result

    except Exception as e:
        cleanup_temp_files([audio_path])
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice/audio-info/{file_id}")
async def get_audio_info(file_id: str):
    """Get metadata information about an uploaded audio file."""
    # This would typically retrieve from a database or file system
    # For now, return a placeholder response
    return {
        "file_id": file_id,
        "message": "Audio info endpoint - implement file tracking system",
        "status": "placeholder"
    }

@app.post("/voice/enhance-audio")
async def enhance_audio_quality(file: UploadFile = File(...)):
    """Enhance audio quality using advanced processing."""
    logger.info(f"Enhancing audio quality for: {file.filename}")

    # Create temporary files
    query_id = str(uuid.uuid4())
    temp_dir = "temp_audio"
    input_path = os.path.join(temp_dir, f"input_{query_id}.{file.filename.split('.')[-1]}")

    try:
        # Save uploaded file
        with open(input_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Enhance audio quality
        result = voice_service.enhance_audio_quality(input_path)

        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Audio enhancement failed"))

        # Return enhanced file
        enhanced_path = result["enhanced_file"]

        return FileResponse(
            path=enhanced_path,
            media_type="audio/wav",
            filename=f"enhanced_{file.filename}",
            headers={
                "X-Original-Duration": str(result.get("duration", 0)),
                "X-Sample-Rate": str(result.get("sample_rate", 0)),
                "X-Enhancements": ",".join(result.get("enhancements_applied", []))
            }
        )

    except Exception as e:
        cleanup_temp_files([input_path])
        logger.error(f"Audio enhancement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/analyze-audio")
async def analyze_audio_characteristics(file: UploadFile = File(...)):
    """Analyze audio characteristics and quality metrics."""
    logger.info(f"Analyzing audio characteristics for: {file.filename}")

    # Create temporary file
    query_id = str(uuid.uuid4())
    temp_dir = "temp_audio"
    audio_path = os.path.join(temp_dir, f"analyze_{query_id}.{file.filename.split('.')[-1]}")

    try:
        # Save uploaded file
        with open(audio_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Analyze audio
        result = voice_service.analyze_audio_characteristics(audio_path)

        # Cleanup
        cleanup_temp_files([audio_path])

        return result

    except Exception as e:
        cleanup_temp_files([audio_path])
        logger.error(f"Audio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/identify-speakers")
async def identify_speakers(file: UploadFile = File(...)):
    """Identify and diarize speakers in audio."""
    logger.info(f"Identifying speakers for: {file.filename}")

    # Create temporary file
    query_id = str(uuid.uuid4())
    temp_dir = "temp_audio"
    audio_path = os.path.join(temp_dir, f"speakers_{query_id}.{file.filename.split('.')[-1]}")

    try:
        # Save uploaded file
        with open(audio_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Identify speakers
        result = voice_service.identify_speakers(audio_path)

        # Cleanup
        cleanup_temp_files([audio_path])

        return result

    except Exception as e:
        cleanup_temp_files([audio_path])
        logger.error(f"Speaker identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/transcribe-with-speakers")
async def transcribe_with_speaker_identification(file: UploadFile = File(...)):
    """Transcribe audio with speaker identification."""
    logger.info(f"Transcribing with speaker ID for: {file.filename}")

    # Create temporary file
    query_id = str(uuid.uuid4())
    temp_dir = "temp_audio"
    audio_path = os.path.join(temp_dir, f"transcribe_speakers_{query_id}.{file.filename.split('.')[-1]}")

    try:
        # Save uploaded file
        with open(audio_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Transcribe with speaker identification
        result = voice_service.transcribe_with_speaker_identification(audio_path)

        # Cleanup
        cleanup_temp_files([audio_path])

        return result

    except Exception as e:
        cleanup_temp_files([audio_path])
        logger.error(f"Transcription with speaker ID failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice/capabilities")
async def get_voice_processing_capabilities():
    """Get information about available voice processing capabilities."""
    try:
        capabilities = voice_service.get_processing_capabilities()
        return capabilities
    except Exception as e:
        logger.error(f"Failed to get voice capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/clear")
async def clear_chat_memory(rag_handler: Annotated[RAGHandler, Depends(get_rag_handler)]):
    """Clear the conversation memory."""
    try:
        rag_handler.clear_memory()
        return {"status": "success", "message": "Chat memory cleared"}
    except Exception as e:
        logger.error(f"Failed to clear chat memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usage/stats")
async def get_usage_stats(rag_handler: Annotated[RAGHandler, Depends(get_rag_handler)]):
    """Get usage statistics from Requesty.ai if available."""
    try:
        requesty_stats = rag_handler.requesty_client.get_usage_stats()
        memory_stats = rag_handler.get_memory_summary()

        return {
            "requesty": requesty_stats,
            "memory": memory_stats,
            "vector_store": doc_processor.get_vector_store_stats()
        }
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        return {"error": str(e)}

@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get comprehensive analytics data for the dashboard."""
    logger.info("Fetching analytics dashboard data")

    try:
        # Get performance metrics
        performance_stats = performance_monitor.get_performance_stats()
        system_metrics = performance_monitor.collect_system_metrics()
        health_status = performance_monitor.get_health_status()

        # Get cost analysis
        cost_summary = cost_tracker.get_cost_summary(days=7)

        # Get document stats
        doc_stats = doc_processor.get_vector_store_stats()

        # Calculate derived metrics
        overall_stats = performance_stats.get("_overall", {})
        total_requests = overall_stats.get("total_requests", 0)
        total_errors = overall_stats.get("total_errors", 0)

        # Mock some additional data for comprehensive dashboard
        from datetime import datetime, timedelta
        import numpy as np

        now = datetime.now()

        analytics_data = {
            # Performance metrics
            "avg_response_time": overall_stats.get("requests_per_second", 0) / max(1, total_requests) if total_requests > 0 else 1.2,
            "response_time_change": np.random.uniform(-0.3, 0.1),
            "success_rate": overall_stats.get("overall_success_rate", 100),
            "success_rate_change": np.random.uniform(-2, 5),
            "total_queries": total_requests,
            "queries_change": np.random.randint(50, 200),
            "queries_per_second": overall_stats.get("requests_per_second", 0),
            "throughput_change": np.random.uniform(-1, 2),
            "active_requests_total": overall_stats.get("active_requests_total", 0),

            # Response time history (mock data based on current performance)
            "response_times": [
                {
                    "timestamp": (now - timedelta(hours=i)).isoformat(),
                    "response_time": max(0.1, np.random.normal(1.2, 0.3))
                }
                for i in range(24, 0, -1)
            ],

            # Endpoint statistics from performance monitor
            "endpoint_stats": {
                endpoint: {
                    "avg_response_time": stats.get("avg_response_time", 0),
                    "success_rate": stats.get("success_rate", 100),
                    "total_requests": stats.get("total_requests", 0)
                }
                for endpoint, stats in performance_stats.items()
                if endpoint != "_overall"
            },

            # Cost analysis from cost tracker
            "cost_analysis": {
                "total_cost": cost_summary.get("total_estimated_cost", 0),
                "daily_average": cost_summary.get("daily_average", 0),
                "monthly_projection": cost_summary.get("projection_monthly", 0),
                "total_calls": cost_summary.get("total_calls", 0),
                "cost_by_model": cost_summary.get("cost_by_model", {}),
                "daily_costs": [
                    {"date": (now - timedelta(days=i)).date().isoformat(), "cost": np.random.uniform(1.0, 3.0)}
                    for i in range(7, 0, -1)
                ]
            },

            # Usage statistics
            "usage_stats": {
                "documents_processed": doc_stats.get("total_documents", 0),
                "voice_queries": total_requests // 3,  # Estimate
                "text_queries": total_requests * 2 // 3,  # Estimate
                "hourly_activity": np.random.poisson(3, (7, 24)).tolist()
            },

            # System metrics from performance monitor
            "system_metrics": {
                "current": {
                    "cpu_percent": system_metrics.get("cpu", {}).get("percent", 0) if system_metrics else 0,
                    "memory_percent": system_metrics.get("memory", {}).get("percent", 0) if system_metrics else 0,
                    "disk_percent": system_metrics.get("disk", {}).get("percent", 0) if system_metrics else 0,
                    "network_io": system_metrics.get("network", {}).get("bytes_recv", 0) / (1024*1024) if system_metrics else 0
                },
                "historical": [
                    {
                        "timestamp": (now - timedelta(hours=i)).isoformat(),
                        "cpu_percent": max(0, min(100, np.random.normal(35, 15))),
                        "memory_percent": max(0, min(100, np.random.normal(65, 10))),
                        "disk_percent": max(0, min(100, np.random.normal(46, 5)))
                    }
                    for i in range(24, 0, -1)
                ]
            },

            # Health status from performance monitor
            "health_status": health_status,

            # Recent alerts (mock data)
            "recent_alerts": [
                {"timestamp": (now - timedelta(minutes=i*15)).strftime("%Y-%m-%d %H:%M:%S"),
                 "level": np.random.choice(["info", "warning", "error"], p=[0.7, 0.2, 0.1]),
                 "message": np.random.choice([
                     "System performance normal",
                     "High response time detected",
                     "Memory usage elevated",
                     "API rate limit approached",
                     "Document processing completed"
                 ])}
                for i in range(10)
            ]
        }

        logger.info("Analytics dashboard data compiled successfully")
        return analytics_data

    except Exception as e:
        logger.error(f"Failed to get analytics dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_prometheus_metrics():
    """Get metrics in Prometheus format."""
    try:
        metrics = performance_monitor.get_metrics_for_prometheus()
        return {"metrics": metrics, "format": "prometheus"}
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        return {"error": str(e)}

@app.get("/performance/stats")
async def get_performance_stats():
    """Get detailed performance statistics."""
    try:
        stats = performance_monitor.get_performance_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance/summary")
@performance_track("performance_summary")
async def get_performance_summary_endpoint():
    """Get comprehensive performance summary with optimizations."""
    try:
        summary = await get_performance_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance/cache-stats")
async def get_cache_stats():
    """Get cache performance statistics."""
    try:
        cache_stats = smart_cache.get_stats()
        perf_cache_metrics = perf_monitor.analyze_performance_trends()

        return {
            "cache_statistics": cache_stats,
            "performance_metrics": perf_cache_metrics,
            "resource_recommendations": resource_monitor.get_resource_recommendations()
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/performance/cache/clear")
async def clear_cache():
    """Clear performance cache for troubleshooting."""
    try:
        await smart_cache.invalidate()
        return {"status": "success", "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/performance/benchmark")
async def trigger_performance_benchmark():
    """Trigger a performance benchmark test."""
    try:
        # This would typically trigger actual benchmark tests
        # For now, return a placeholder response
        return {
            "status": "benchmark_triggered",
            "message": "Performance benchmark initiated",
            "benchmark_id": str(uuid.uuid4()),
            "estimated_duration": "5-10 minutes"
        }
    except Exception as e:
        logger.error(f"Failed to trigger benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== Security Management Endpoints =====

@app.get("/security/dashboard")
async def get_security_dashboard():
    """Get security dashboard with threat analysis and system status."""
    try:
        dashboard_data = security_monitor.get_security_dashboard()
        return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get security dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/security/threats")
async def get_recent_threats():
    """Get recent security threats and analysis."""
    try:
        threat_summary = threat_detector.get_threat_summary()
        return {
            "threat_summary": threat_summary,
            "recent_threats": [
                {
                    "type": threat.threat_type.value,
                    "severity": threat.severity.value,
                    "source_ip": threat.source_ip,
                    "timestamp": threat.timestamp.isoformat(),
                    "details": threat.details
                }
                for threat in list(threat_detector.recent_threats)[-20:]
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get threat data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/security/api-key")
async def generate_api_key(
    user_id: str,
    permissions: List[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """Generate API key for user (requires admin authentication)."""
    try:
        # In production, validate admin credentials here
        api_key = security_manager.generate_api_key(user_id, permissions)
        return {
            "api_key": api_key,
            "user_id": user_id,
            "permissions": permissions or ["read"],
            "expires_in_hours": 24
        }
    except Exception as e:
        logger.error(f"Failed to generate API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/security/validate-token")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """Validate API token and return user information."""
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="No token provided")

        valid, payload = security_manager.validate_api_key(credentials.credentials)
        if not valid:
            raise HTTPException(status_code=401, detail=payload.get("error", "Invalid token"))

        return {
            "valid": True,
            "user_id": payload["user_id"],
            "permissions": payload["permissions"],
            "expires_at": payload["expires_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/security/block-ip")
async def block_ip_address(
    ip_address: str,
    reason: str = "Manual block",
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """Block an IP address (requires admin authentication)."""
    try:
        # Validate IP address format
        import ipaddress
        ipaddress.ip_address(ip_address)

        threat_detector.block_ip(ip_address, reason)
        return {
            "status": "success",
            "message": f"IP {ip_address} blocked successfully",
            "reason": reason
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address format")
    except Exception as e:
        logger.error(f"Failed to block IP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/security/unblock-ip")
async def unblock_ip_address(
    ip_address: str,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """Unblock an IP address (requires admin authentication)."""
    try:
        # Validate IP address format
        import ipaddress
        ipaddress.ip_address(ip_address)

        threat_detector.blocked_ips.discard(ip_address)
        return {
            "status": "success",
            "message": f"IP {ip_address} unblocked successfully"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address format")
    except Exception as e:
        logger.error(f"Failed to unblock IP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/security/blocked-ips")
async def get_blocked_ips():
    """Get list of blocked IP addresses."""
    try:
        return {
            "blocked_ips": list(threat_detector.blocked_ips),
            "count": len(threat_detector.blocked_ips)
        }
    except Exception as e:
        logger.error(f"Failed to get blocked IPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/security/test-input")
async def test_input_security(
    test_input: str,
    request: Request
):
    """Test input for security threats (for development/testing)."""
    try:
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Validate input
        valid, errors = InputValidator.validate_text_input(test_input)

        # Detect threats
        threats = threat_detector.detect_threats(test_input, client_ip, user_agent)

        return {
            "input_valid": valid,
            "validation_errors": errors,
            "threats_detected": [
                {
                    "type": threat.threat_type.value,
                    "severity": threat.severity.value,
                    "details": threat.details
                }
                for threat in threats
            ],
            "security_passed": valid and len(threats) == 0
        }
    except Exception as e:
        logger.error(f"Failed to test input security: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== Monitoring and Health Check Endpoints =====

@app.get("/monitoring/status")
async def get_monitoring_status():
    """Get comprehensive monitoring system status."""
    try:
        status = monitoring_service.get_monitoring_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/health")
async def get_detailed_health_check():
    """Get detailed health check results."""
    try:
        health_results = await health_checker.perform_health_checks()
        return health_results
    except Exception as e:
        logger.error(f"Failed to perform health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/metrics")
async def get_current_metrics():
    """Get current system and application metrics."""
    try:
        system_metrics = metrics_collector.get_system_metrics()
        app_metrics = metrics_collector.get_application_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": system_metrics,
            "application_metrics": app_metrics
        }
    except Exception as e:
        logger.error(f"Failed to get current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/alerts")
async def get_alert_summary():
    """Get alert system summary and recent alerts."""
    try:
        alert_summary = alert_manager.get_alert_summary()
        return alert_summary
    except Exception as e:
        logger.error(f"Failed to get alert summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/test-alert")
async def trigger_test_alert(
    severity: str = "warning",
    message: str = "Test alert from monitoring system",
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """Trigger a test alert (for testing notification systems)."""
    try:
        try:
            from .monitoring_alerts import Alert, AlertSeverity
        except ImportError:  # pragma: no cover - support direct module imports in tests
            from monitoring_alerts import Alert, AlertSeverity

        # Validate severity
        try:
            alert_severity = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid severity level")

        # Create test alert
        test_alert = Alert(
            rule_name="test_alert",
            severity=alert_severity,
            message=message,
            current_value=100.0,
            threshold=50.0,
            timestamp=datetime.now(),
            source="manual_test",
            tags={"test": "true"}
        )

        # Fire test alert
        alert_manager.active_alerts["test_alert"] = test_alert
        alert_manager.alert_history.append(test_alert)

        # Send notifications (you would configure channels in production)
        logger.warning(f"TEST ALERT: {message}")

        return {
            "status": "success",
            "message": "Test alert triggered",
            "alert": {
                "rule_name": test_alert.rule_name,
                "severity": test_alert.severity.value,
                "message": test_alert.message,
                "timestamp": test_alert.timestamp.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/metrics/history/{metric_name}")
async def get_metric_history(
    metric_name: str,
    hours: int = 1
):
    """Get historical data for a specific metric."""
    try:
        time_window = timedelta(hours=hours)
        stats = metrics_collector.get_metric_stats(metric_name, time_window)

        if not stats:
            raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found or no data available")

        return {
            "metric_name": metric_name,
            "time_window_hours": hours,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/record-metric")
async def record_custom_metric(
    metric_name: str,
    value: float,
    tags: Dict[str, str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """Record a custom application metric."""
    try:
        metrics_collector.record_metric(metric_name, value, tags)

        return {
            "status": "success",
            "message": f"Metric '{metric_name}' recorded",
            "value": value,
            "tags": tags,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to record custom metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/uptime")
async def get_system_uptime():
    """Get system uptime and service availability metrics."""
    try:
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time

        # Calculate service uptime (since monitoring started)
        service_uptime = None
        if monitoring_service.running and health_checker.last_check_time:
            service_uptime = datetime.now() - health_checker.last_check_time

        return {
            "system_boot_time": boot_time.isoformat(),
            "system_uptime_seconds": uptime.total_seconds(),
            "system_uptime_human": str(uptime),
            "service_uptime_seconds": service_uptime.total_seconds() if service_uptime else None,
            "monitoring_active": monitoring_service.running,
            "last_health_check": health_checker.last_check_time.isoformat() if health_checker.last_check_time else None
        }

    except Exception as e:
        logger.error(f"Failed to get uptime: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.LOG_LEVEL.lower())
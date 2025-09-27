from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import os
import shutil
import tempfile
import uuid
from typing import Annotated, Optional, List

from .config import settings
from .document_processor import DocumentProcessor
from .rag_handler import RAGHandler
from .voice_service import VoiceService

# Configure logging
logger.add("logs/app.log", rotation="1 day", retention="7 days", level=settings.LOG_LEVEL)

app = FastAPI(
    title="Voice-Enabled RAG System API",
    description="A voice-enabled document Q&A system with intelligent LLM routing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class SystemStatus(BaseModel):
    status: str
    vector_store_exists: bool
    document_count: int
    requesty_enabled: bool
    wake_word_enabled: bool

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

@app.get("/", response_model=SystemStatus)
async def root():
    """Get system status and health check"""
    try:
        vector_stats = doc_processor.get_vector_store_stats()
        return SystemStatus(
            status="healthy",
            vector_store_exists=vector_stats.get("exists", False),
            document_count=vector_stats.get("document_count", 0),
            requesty_enabled=bool(settings.REQUESTY_API_KEY),
            wake_word_enabled=settings.ENABLE_WAKE_WORD
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemStatus(
            status="unhealthy",
            vector_store_exists=False,
            document_count=0,
            requesty_enabled=False,
            wake_word_enabled=False
        )

@app.post("/documents/upload", response_model=DocumentUploadResponse)
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
async def query_text(
    request: QueryRequest,
    rag_handler: Annotated[RAGHandler, Depends(get_rag_handler)]
):
    """Process a text query and return an answer with sources."""
    logger.info(f"Text query received: {request.query[:100]}...")

    try:
        result = rag_handler.ask_question(request.query)
        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Text query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/voice")
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
        tts_result = voice_service.synthesize_speech(answer_text, audio_output_path)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.LOG_LEVEL.lower())
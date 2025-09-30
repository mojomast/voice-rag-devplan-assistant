# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Voice-Enabled RAG System** - An enterprise-grade voice-enabled document Q&A system with FastAPI backend. The system combines RAG (Retrieval-Augmented Generation) with voice processing, security features, and production monitoring.

## Key Commands

### Development

```powershell
# Start backend API server (development mode with hot reload)
uvicorn backend.main:app --reload

# Start backend on specific host/port
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Run with debug logging
$env:DEBUG="True"; $env:LOG_LEVEL="DEBUG"; uvicorn backend.main:app --reload
```

### Testing

```powershell
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests
pytest tests/unit/test_rag_handler.py  # Single test file

# Run with coverage report
pytest --cov=backend --cov-report=html

# Run specific test function
pytest tests/unit/test_rag_handler.py::test_ask_question_success
```

### Linting & Code Quality

```powershell
# No specific linting commands configured yet
# Consider adding: black, flake8, mypy, or ruff
```

## Architecture Overview

### Core Components

The backend is organized as a **FastAPI monolith** with distinct service modules:

1. **main.py** - FastAPI application with endpoints and middleware
   - Security middleware (threat detection, rate limiting)
   - HTTP authentication via JWT
   - CORS configuration
   - Lazy-loaded RAG handler for performance

2. **config.py** - Centralized configuration management
   - Environment-based settings with `.env` support
   - Automatic TEST_MODE detection when no API keys present
   - Runtime credential updates via admin token
   - Sentinel value normalization for API keys

3. **rag_handler.py** - RAG engine with conversation memory
   - Dual-mode operation: production vs TEST_MODE
   - FAISS vector store for semantic search
   - ConversationalRetrievalChain with LangChain
   - Automatic fallback to synthetic test data

4. **voice_service.py** - Voice processing (transcription & TTS)
   - OpenAI Whisper for transcription
   - OpenAI TTS for text-to-speech
   - Graceful degradation to test mode
   - Optional: wake word detection, speaker ID, audio enhancement

5. **document_processor.py** - Multi-format document ingestion
   - 15+ file formats: PDF, DOCX, images (OCR), CSV, XLSX, etc.
   - Automatic format detection and loader selection
   - Text chunking with RecursiveCharacterTextSplitter
   - FAISS vector store creation and persistence

6. **requesty_client.py** - LLM routing client
   - Intelligent LLM routing via Requesty.ai (cost optimization)
   - Automatic fallback to direct OpenAI API
   - Custom LangChain LLM wrapper (RequestyLLM)

7. **security.py** - Enterprise security framework
   - Threat detection (SQL injection, XSS, command injection, path traversal)
   - Rate limiting with burst protection
   - Input validation and sanitization
   - JWT authentication
   - IP blocking and threat tracking

8. **monitoring.py** - Performance monitoring
   - Request/response time tracking
   - Success/error rate metrics
   - System resource monitoring
   - Metric collection and analysis

9. **monitoring_alerts.py** - Production alerting system
   - Multi-channel alerts (Email, Slack, Discord, webhooks)
   - Configurable alert rules with thresholds
   - System health checks
   - Metric retention and history

10. **performance_optimizer.py** - Performance optimization
    - Intelligent caching with TTL and LRU eviction
    - Query optimization analysis
    - Resource monitoring and trend analysis
    - Performance tracking decorators

### Data Flow

```
User Request
    ↓
FastAPI Endpoint (main.py)
    ↓
Security Middleware → Rate Limiting → Threat Detection
    ↓
Endpoint Handler
    ↓
Service Layer (RAGHandler / VoiceService / DocumentProcessor)
    ↓
External APIs (OpenAI / Requesty.ai)
    ↓
Response with monitoring & cost tracking
```

### Key Architectural Patterns

**Dual-Mode Operation (TEST_MODE)**
- When `OPENAI_API_KEY` and `REQUESTY_API_KEY` are absent (or `TEST_MODE=true`), the system enters offline mode
- Uses `FakeEmbeddings` for vector operations
- Generates synthetic test vector store with AI primer content
- Returns deterministic mock responses for tests without network calls
- Allows full test suite execution and local development without API costs

**Lazy Loading**
- `RAGHandler` is instantiated on first request (not at startup) to allow vector store initialization
- `reset_rag_handler()` reloads the vector store after document uploads

**Dependency Injection**
- FastAPI dependency injection used for `get_rag_handler()`
- Ensures consistent service instances across endpoints

**Module Import Flexibility**
- Try/except pattern for relative vs absolute imports enables both package imports and direct module execution (useful for testing)

**Graceful Degradation**
- Voice service falls back to test mode if OpenAI client initialization fails
- RAG handler switches to TEST_MODE if vector store is unavailable
- Document processor uses FakeEmbeddings when OPENAI_API_KEY is missing

## Configuration

### Environment Variables

Critical settings (defined in `config.py`):

```bash
# API Keys (optional in TEST_MODE)
OPENAI_API_KEY=sk-...
REQUESTY_API_KEY=...

# Test Mode (auto-detected if no keys, or explicit)
TEST_MODE=false

# Storage Paths
VECTOR_STORE_PATH=./vector_store
UPLOAD_PATH=./uploads

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=text-embedding-3-small

# LLM Settings
LLM_MODEL=gpt-4o-mini
TEMPERATURE=0.7

# Voice Settings
TTS_MODEL=tts-1
TTS_VOICE=alloy
WHISPER_MODEL=whisper-1
ENABLE_WAKE_WORD=false
WAKE_WORD=hey assistant

# Application
DEBUG=True
LOG_LEVEL=INFO

# Runtime Admin (for credential updates)
RUNTIME_ADMIN_TOKEN=...
```

### Runtime Configuration Updates

Use `/config/update` endpoint to change credentials without restart (requires admin token).

## Testing Approach

### Test Structure

```
tests/
├── unit/              # Unit tests with mocked dependencies
├── integration/       # Integration tests with real services
└── e2e/              # End-to-end browser tests
```

### Test Mode Features

- **Synthetic Vector Store**: Auto-generated FAISS index with test documents
- **Deterministic Responses**: No external API calls, consistent test results
- **FakeEmbeddings**: LangChain's FakeEmbeddings for offline vector operations
- **Mock Voice Services**: Transcription and TTS return predictable mock data

### Running Offline Tests

```powershell
# All tests work offline (no API keys required)
pytest tests/unit/

# Clear test vector store to regenerate
Remove-Item -Recurse -Force vector_store/
```

## Common Development Tasks

### Adding a New Endpoint

1. Define Pydantic models in `main.py` (request/response schemas)
2. Add endpoint handler with appropriate decorators:
   - `@performance_track()` for monitoring
   - `@rate_limit()` for rate limiting
   - `@validate_input()` for security
3. Use dependency injection for services (`get_rag_handler()`)
4. Add appropriate error handling and logging

### Adding Document Format Support

1. Update `document_processor.py`:
   - Add extension to `_is_supported_extension()`
   - Add loader case in `load_document()`
   - Import appropriate LangChain document loader
2. Test with sample file in TEST_MODE
3. Update `ALLOWED_FILE_TYPES` in `security.py`

### Adding Security Rules

1. Update threat patterns in `security.py`:
   - Add pattern to `ThreatDetector._load_threat_patterns()`
   - Define severity in `_get_threat_severity()`
2. Test with sample malicious input in unit tests

### Modifying Vector Store

1. Update `CHUNK_SIZE` or `CHUNK_OVERLAP` in config
2. Delete existing vector store: `Remove-Item -Recurse -Force vector_store/`
3. Re-upload and index documents via `/documents/upload`
4. System will regenerate with new chunking parameters

## Important Implementation Details

### Security Middleware Flow

All requests pass through `security_middleware` in this order:
1. IP blocking check (reject if blocked)
2. Rate limiting (429 if exceeded)
3. Burst protection (429 if burst limit hit)
4. Request processing
5. Security headers added to response

Rate limiting is **bypassed** when `TEST_MODE=True` or `DEBUG=True`.

### Conversation Memory

- `RAGHandler` uses `ConversationBufferMemory` to maintain chat context
- Memory is per-instance (not persisted across restarts)
- Clear memory via `/chat/clear` endpoint
- In TEST_MODE, memory is a simple list (`_conversation_history`)

### Cost Tracking

- `monitoring.py` includes `cost_tracker` for API usage
- Tracks token usage, API calls, and estimated costs
- Access metrics via `/usage/stats` endpoint
- Requesty.ai routing can save up to 80% on LLM costs

### Document Upload Process

1. File uploaded via multipart form data
2. Saved to `UPLOAD_PATH` with unique filename
3. `DocumentProcessor.load_document()` loads with appropriate loader
4. Documents split into chunks
5. Chunks embedded and stored in FAISS
6. Vector store saved to disk
7. `reset_rag_handler()` forces reload on next query

### Error Handling Strategy

- HTTP exceptions raised with appropriate status codes (400, 404, 500)
- Errors logged with `loguru` logger
- Graceful degradation to TEST_MODE when services unavailable
- User-facing error messages sanitized (no stack traces in production)

## Dependencies

Key dependencies from `requirements.txt`:
- **langchain** + **langchain-openai** + **langchain-community**: RAG framework
- **faiss-cpu**: Vector similarity search
- **openai**: API client for GPT, Whisper, TTS
- **fastapi** + **uvicorn**: Web framework and ASGI server
- **pypdf**, **python-docx**, **docx2txt**: Document loaders
- **loguru**: Advanced logging
- **PyJWT**, **bcrypt**: Security and authentication
- **pytest** + **pytest-asyncio** + **httpx**: Testing framework

Optional dependencies (feature flags in code):
- **pytesseract**, **pillow**, **opencv-python**: OCR support
- **pymupdf**: Advanced PDF processing
- **librosa**, **noisereduce**: Audio enhancement
- **pyannote.audio**: Speaker identification
- **openwakeword**: Wake word detection
- **beautifulsoup4**: HTML parsing
- **redis**: Distributed caching

## Troubleshooting

### Vector Store Not Found

**Error**: `FileNotFoundError: Vector store not found at ./vector_store`

**Solution**: Upload at least one document via `/documents/upload` to initialize the vector store, or set `TEST_MODE=true` for synthetic store.

### API Key Errors

**Error**: OpenAI API errors or authentication failures

**Solution**: 
1. Check `OPENAI_API_KEY` in `.env`
2. Verify key is not a sentinel value (e.g., "test-key", "placeholder")
3. System auto-enters TEST_MODE if keys are missing/invalid

### Rate Limiting in Development

**Error**: 429 Too Many Requests during testing

**Solution**: Set `TEST_MODE=true` or `DEBUG=true` to bypass rate limiting.

### Memory Issues with Large Documents

**Symptom**: High memory usage, slow performance

**Solution**:
1. Reduce `CHUNK_SIZE` (e.g., from 1000 to 500)
2. Process large documents in batches
3. Clear vector store and re-index
4. Enable caching in `performance_optimizer.py`

### Port Already in Use

**Error**: `[Errno 10048] Only one usage of each socket address`

**Solution**: Kill existing uvicorn process or change port:
```powershell
uvicorn backend.main:app --port 8001
```

## Production Considerations

- **Logging**: Logs rotate daily, retained 7 days (configured in `main.py`)
- **CORS**: Currently allows all origins (`["*"]`) - restrict in production
- **Admin Token**: Set strong `RUNTIME_ADMIN_TOKEN` for credential updates
- **Rate Limits**: Adjust `RATE_LIMIT_REQUESTS_PER_MINUTE` based on load
- **Vector Store Backup**: Regularly backup `./vector_store` directory
- **Monitoring**: Enable production monitoring with email/Slack alerts
- **Security Headers**: Automatically added by middleware (CSP, HSTS, etc.)

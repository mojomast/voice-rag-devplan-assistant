# API Requirements Analysis Report

## Overview
This report analyzes the actual API calls made in the voice-rag-system codebase and identifies the required API keys, credentials, and environment variables for real API testing.

## External APIs Identified

### 1. OpenAI API
**Primary Usage**: Voice processing and text generation
- **Base URL**: `https://api.openai.com/v1`
- **Authentication**: Bearer token (API key)
- **Required API Key**: `OPENAI_API_KEY`

#### API Endpoints Used:
1. **Audio Transcription (Whisper)**
   - Endpoint: `POST /audio/transcriptions`
   - Model: `whisper-1`
   - Purpose: Convert speech to text
   - Parameters: file, language, response_format, temperature

2. **Text-to-Speech (TTS)**
   - Endpoint: `POST /audio/speech`
   - Model: `tts-1`
   - Purpose: Convert text to speech
   - Parameters: model, voice, input, response_format, speed

3. **Chat Completions**
   - Endpoint: `POST /chat/completions`
   - Models: `gpt-4o-mini`, `gpt-3.5-turbo`
   - Purpose: Generate text responses
   - Parameters: model, messages, temperature, max_tokens

4. **Embeddings**
   - Endpoint: `POST /embeddings`
   - Model: `text-embedding-3-small`
   - Purpose: Generate text embeddings for vector search
   - Parameters: model, input

### 2. Requesty.ai API
**Primary Usage**: Cost-optimized LLM routing and embeddings
- **Base URL**: `https://router.requesty.ai/v1`
- **Authentication**: Bearer token (API key)
- **Required API Keys**: `REQUESTY_API_KEY` (legacy) or `ROUTER_API_KEY` (preferred)

#### API Endpoints Used:
1. **Router Chat Completions**
   - Endpoint: `POST /chat/completions`
   - Models: `zai/glm-4.5`, `openai/gpt-4o-mini`
   - Purpose: LLM routing for cost optimization
   - Parameters: model, messages, temperature, max_tokens

2. **Router Embeddings**
   - Endpoint: `POST /embeddings`
   - Model: `requesty/embedding-001`
   - Purpose: Generate embeddings via Requesty
   - Parameters: model, input

3. **Usage Statistics**
   - Endpoint: `GET /usage`
   - Purpose: Monitor API usage and costs
   - Authentication: Bearer token

## Environment Variables Required

### Core API Keys
```bash
# OpenAI API Configuration
OPENAI_API_KEY="sk-..."                    # Required for OpenAI services

# Requesty.ai API Configuration
REQUESTY_API_KEY="..."                     # Legacy Requesty key
ROUTER_API_KEY="..."                       # Preferred Requesty Router key
```

### Model Configuration
```bash
# LLM Models
LLM_MODEL="gpt-4o-mini"                   # Default OpenAI model
REQUESTY_PLANNING_MODEL="zai/glm-4.5"     # Requesty planning model
EMBEDDING_MODEL="text-embedding-3-small"   # OpenAI embeddings
REQUESTY_EMBEDDING_MODEL="requesty/embedding-001"  # Requesty embeddings

# Voice Models
TTS_MODEL="tts-1"                         # OpenAI TTS model
WHISPER_MODEL="whisper-1"                  # OpenAI transcription model
TTS_VOICE="alloy"                         # Default voice
```

### Voice Configuration
```bash
# Voice Settings
VOICE_LANGUAGE="en"                       # Default language
TTS_SPEED="1.0"                           # Speech speed
AUDIO_SAMPLE_RATE="16000"                 # Audio sample rate
MAX_AUDIO_DURATION="300"                  # Max audio duration (seconds)

# Enhanced Voice Features
STT_ENABLE_LANGUAGE_DETECTION="True"      # Auto-detect languages
STT_ENABLE_NOISE_REDUCTION="True"         # Audio enhancement
STT_ENABLE_AUDIO_ENHANCEMENT="True"       # Audio processing
```

### File Paths and Storage
```bash
# Storage Paths
VECTOR_STORE_PATH="./vector_store"         # Vector database location
DEVPLAN_VECTOR_STORE_PATH="./vector_store/devplans"
PROJECT_VECTOR_STORE_PATH="./vector_store/projects"
UPLOAD_PATH="./uploads"                   # Document upload directory
TEMP_AUDIO_DIR="./temp_audio"              # Temporary audio files
TTS_CACHE_DIR="./cache/tts"               # TTS cache directory
```

### Application Settings
```bash
# Application Configuration
DEBUG="True"                               # Debug mode
LOG_LEVEL="INFO"                           # Logging level
TEST_MODE="false"                          # Test mode flag
REQUIRE_ADMIN_TOKEN="True"                 # Security setting
DATABASE_URL="sqlite+aiosqlite:///./data/devplanning.db"  # Database
```

## API Key Validation and Security

### Key Validation Patterns
The system includes sophisticated validation for API keys:

#### OpenAI Key Validation
```python
SENTINEL_OPENAI_KEYS = {
    "", "none", "null", "placeholder",
    "your_openai_api_key_here",
    "sk-your-actual-openai-key-here",
    "test-key"
}
```

#### Requesty Key Validation
```python
SENTINEL_REQUESTY_KEYS = {
    "", "none", "null", "placeholder"
}
```

### Security Features
1. **Automatic Test Mode**: System falls back to test mode when valid keys are not provided
2. **Key Normalization**: Strips whitespace and validates against known placeholders
3. **Admin Token Protection**: Runtime updates require admin token validation
4. **Environment Variable Security**: Keys are loaded from environment, not hardcoded

## API Usage Patterns

### Voice Processing Pipeline
1. **Audio Input** → **Transcription** (Whisper API)
2. **Text Processing** → **LLM Response** (Chat Completions)
3. **Response Text** → **Speech Synthesis** (TTS API)

### Document Processing Pipeline
1. **Document Upload** → **Text Extraction**
2. **Text Chunking** → **Embedding Generation** (Embeddings API)
3. **Vector Storage** → **Similarity Search**
4. **Query + Context** → **LLM Response** (Chat Completions)

### Planning System Pipeline
1. **User Input** → **Context Building**
2. **Planning Request** → **LLM Generation** (Requesty Router)
3. **Plan Storage** → **Vector Indexing**
4. **Plan Retrieval** → **Similarity Search**

## Cost Considerations

### OpenAI API Costs
- **Whisper**: $0.006/minute (transcription)
- **TTS**: $15/1M characters (speech synthesis)
- **GPT-4o-mini**: $0.15/1M input tokens, $0.6/1M output tokens
- **Embeddings**: $0.02/1M tokens

### Requesty.ai Benefits
- **Cost Optimization**: Routes to most cost-effective models
- **Model Flexibility**: Access to multiple LLM providers
- **Usage Tracking**: Built-in usage statistics and monitoring

## Rate Limits and Quotas

### OpenAI Rate Limits
- **GPT-4o-mini**: 150 requests/minute, 40,000 tokens/minute
- **Whisper**: 50 requests/minute
- **TTS**: 50 requests/minute
- **Embeddings**: 3,000 requests/minute

### Requesty.ai Rate Limits
- **Router**: Configurable based on plan
- **Embeddings**: Typically higher limits than direct OpenAI

## Testing Requirements

### Minimum Viable API Configuration
For basic real API testing, you need:
```bash
OPENAI_API_KEY="sk-..."                    # Required for voice features
ROUTER_API_KEY="..."                       # Required for LLM features
```

### Optional Enhancements
```bash
REQUESTY_API_KEY="..."                     # Additional Requesty features
```

### Test Mode Configuration
When API keys are not available:
```bash
TEST_MODE="true"                           # Enables mock responses
OPENAI_API_KEY=""                          # Empty to trigger test mode
ROUTER_API_KEY=""                          # Empty to trigger test mode
```

## Error Handling and Fallbacks

### Graceful Degradation
1. **Missing OpenAI Key**: Falls back to test mode for voice features
2. **Missing Requesty Key**: Falls back to OpenAI direct API
3. **Both Missing**: Full test mode with deterministic responses
4. **API Failures**: Automatic retry with exponential backoff
5. **Rate Limits**: Queued requests with delay

### Error Categories
- **Authentication Errors** (401): Invalid API keys
- **Rate Limit Errors** (429): Too many requests
- **Model Errors** (400): Invalid model parameters
- **Network Errors**: Connection issues
- **Timeout Errors**: Request timeouts

## Monitoring and Usage Tracking

### Built-in Monitoring
1. **Cost Tracking**: Monitors API call costs
2. **Usage Statistics**: Tracks token usage and request counts
3. **Performance Metrics**: Response times and success rates
4. **Error Logging**: Detailed error reporting

### Requesty Usage API
```python
# Get usage statistics
usage_stats = requesty_client.get_usage_stats()
# Returns: request counts, costs, model usage breakdown
```

## Recommendations for Real API Testing

### 1. API Key Setup Priority
1. **High Priority**: OpenAI API key (essential for voice features)
2. **High Priority**: Requesty Router key (cost optimization)
3. **Medium Priority**: Requesty Legacy key (additional features)

### 2. Test Data Requirements
- **Audio Files**: Various formats (mp3, wav, webm) for STT testing
- **Text Samples**: Different lengths and languages for TTS testing
- **Documents**: PDF, TXT files for RAG testing
- **Test Queries**: Varied complexity for LLM testing

### 3. Cost Control Measures
- **Set Usage Limits**: Monitor API usage during testing
- **Use Cheaper Models**: Prefer gpt-4o-mini over gpt-4 for testing
- **Cache Responses**: Implement caching for repeated tests
- **Batch Requests**: Combine multiple operations where possible

### 4. Security Best Practices
- **Environment Variables**: Never commit API keys to version control
- **Key Rotation**: Regularly rotate API keys
- **Access Controls**: Limit API key permissions
- **Monitoring**: Track unusual usage patterns

## Next Steps for Implementation

1. **Create API Key Management System**
2. **Implement Real API Test Framework**
3. **Set Up Usage Monitoring**
4. **Create Cost Control Mechanisms**
5. **Implement Error Handling and Retries**
6. **Create Test Data Sets**
7. **Set Up CI/CD Integration**
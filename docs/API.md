# 🔌 API Documentation

Complete reference for the Voice-Enabled RAG System REST API.

## Base URL
```
http://localhost:8000
```

> ℹ️ Looking for semantic plan/project search? See `docs/API_SEARCH.md` for the full Phase 4 search endpoint reference and examples.

## Authentication
Currently, no authentication is required for local development. For production deployments, implement appropriate authentication mechanisms.

## Content Types
- **Request**: `application/json` for JSON payloads, `multipart/form-data` for file uploads
- **Response**: `application/json` for most endpoints, `audio/mpeg` for voice responses

---

## 📊 System Endpoints

### GET / - Health Check
Returns system status and configuration.

**Request:**
```bash
curl -X GET "http://localhost:8000/"
```

**Response:**
```json
{
  "status": "healthy",
  "vector_store_exists": true,
  "document_count": 15,
  "requesty_enabled": true,
  "wake_word_enabled": false
}
```

**Response Fields:**
- `status`: "healthy" or "unhealthy"
- `vector_store_exists`: Whether documents have been indexed
- `document_count`: Number of document chunks in vector store
- `requesty_enabled`: Whether Requesty.ai is configured
- `wake_word_enabled`: Whether wake word detection is enabled

---

## 📄 Document Management Endpoints

### POST /documents/upload - Upload Document
Upload and process a document for indexing.

**Request:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"
```

**Parameters:**
- `file`: Document file (PDF, TXT, DOCX)

**Response:**
```json
{
  "status": "success",
  "message": "Document 'document.pdf' uploaded and indexed successfully",
  "file_name": "document.pdf",
  "document_count": 10,
  "chunk_count": 45
}
```

**Error Response:**
```json
{
  "status": "error",
  "detail": "Unsupported file type: .xyz. Allowed: .pdf, .txt, .docx"
}
```

### GET /documents/stats - Document Statistics
Get statistics about indexed documents.

**Request:**
```bash
curl -X GET "http://localhost:8000/documents/stats"
```

**Response:**
```json
{
  "exists": true,
  "document_count": 127,
  "index_size": 2048576
}
```

### DELETE /documents/clear - Clear All Documents
Remove all documents from the vector store.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/documents/clear"
```

**Response:**
```json
{
  "status": "success",
  "message": "All documents cleared"
}
```

---

## 💬 Query Endpoints

### POST /query/text - Text Query
Submit a text question and get an answer with sources.

**Request:**
```bash
curl -X POST "http://localhost:8000/query/text" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main topics discussed in the documents?",
    "include_sources": true
  }'
```

**Request Body:**
```json
{
  "query": "Your question here",
  "include_sources": true
}
```

**Response:**
```json
{
  "answer": "Based on the documents, the main topics include...",
  "sources": [
    {
      "source": "document.pdf",
      "page": "3",
      "content_preview": "This section discusses the primary concepts..."
    }
  ],
  "query": "What are the main topics discussed in the documents?",
  "status": "success"
}
```

**Error Response:**
```json
{
  "answer": "I apologize, but I encountered an error processing your question: Vector store not found",
  "sources": [],
  "query": "Your question",
  "status": "error",
  "error": "Vector store not found at ./vector_store. Please upload and index documents first."
}
```

### POST /query/voice - Voice Query
Submit an audio file and get an audio response.

**Request:**
```bash
curl -X POST "http://localhost:8000/query/voice" \
  -F "file=@question.wav"
```

**Parameters:**
- `file`: Audio file (WAV, MP3, M4A, OGG)
- `voice_settings`: Optional JSON string with voice preferences

**Response:**
- **Content-Type**: `audio/mpeg`
- **Headers**:
  - `X-Query-Text`: Transcribed question text
  - `X-Response-Text`: First 200 characters of the answer
- **Body**: MP3 audio file of the response

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/query/voice" \
  -F "file=@question.wav" \
  -o response.mp3 \
  -D headers.txt
```

---

## 🎙️ Voice Endpoints

### GET /voice/voices - Available Voices
Get list of available text-to-speech voices.

**Request:**
```bash
curl -X GET "http://localhost:8000/voice/voices"
```

**Response:**
```json
{
  "voices": [
    "alloy",
    "echo",
    "fable",
    "onyx",
    "nova",
    "shimmer"
  ]
}
```

---

## 💭 Chat Management Endpoints

### POST /chat/clear - Clear Chat Memory
Clear the conversation history and memory.

**Request:**
```bash
curl -X POST "http://localhost:8000/chat/clear"
```

**Response:**
```json
{
  "status": "success",
  "message": "Chat memory cleared"
}
```

---

## 📈 Usage Statistics Endpoints

### GET /usage/stats - Usage Statistics
Get detailed usage statistics and cost information.

**Request:**
```bash
curl -X GET "http://localhost:8000/usage/stats"
```

**Response:**
```json
{
  "requesty": {
    "total_requests": 150,
    "cost_saved": "$12.50",
    "optimization_rate": "78%"
  },
  "memory": {
    "message_count": 24,
    "memory_buffer": "Recent conversation context..."
  },
  "vector_store": {
    "exists": true,
    "document_count": 127,
    "index_size": 2048576
  }
}
```

---

## 🔧 Error Codes

| HTTP Code | Description | Common Causes |
|-----------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid file format, malformed JSON |
| 404 | Not Found | Vector store not found, endpoint doesn't exist |
| 500 | Internal Server Error | API key issues, processing errors |

## 🔍 Error Response Format

All error responses follow this format:
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

---

## 📝 Request Examples

### Python Examples

#### Upload Document
```python
import requests

with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/documents/upload',
        files={'file': f}
    )

print(response.json())
```

#### Text Query
```python
import requests

response = requests.post(
    'http://localhost:8000/query/text',
    json={
        'query': 'What is the main conclusion?',
        'include_sources': True
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
for i, source in enumerate(result['sources'], 1):
    print(f"Source {i}: {source['source']} (Page {source['page']})")
```

#### Voice Query
```python
import requests

with open('question.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/query/voice',
        files={'file': f}
    )

# Save the audio response
with open('answer.mp3', 'wb') as f:
    f.write(response.content)

# Get transcribed text from headers
query_text = response.headers.get('X-Query-Text')
answer_text = response.headers.get('X-Response-Text')
print(f"Question: {query_text}")
print(f"Answer: {answer_text}")
```

### JavaScript Examples

#### Upload Document
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/documents/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Text Query
```javascript
fetch('http://localhost:8000/query/text', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        query: 'What is the main topic?',
        include_sources: true
    })
})
.then(response => response.json())
.then(data => {
    console.log('Answer:', data.answer);
    console.log('Sources:', data.sources);
});
```

### cURL Examples

#### System Status
```bash
curl -X GET "http://localhost:8000/" | jq
```

#### Upload and Query Workflow
```bash
# 1. Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"

# 2. Ask question
curl -X POST "http://localhost:8000/query/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}' | jq

# 3. Get statistics
curl -X GET "http://localhost:8000/usage/stats" | jq
```

---

## 🚀 Advanced Usage

### Batch Document Processing
```python
import requests
import os

def upload_documents(directory):
    for filename in os.listdir(directory):
        if filename.endswith(('.pdf', '.txt', '.docx')):
            filepath = os.path.join(directory, filename)

            with open(filepath, 'rb') as f:
                response = requests.post(
                    'http://localhost:8000/documents/upload',
                    files={'file': f}
                )

            print(f"Uploaded {filename}: {response.json()['status']}")

upload_documents('./documents/')
```

### Conversation with Memory
```python
import requests

def chat_with_memory(questions):
    for question in questions:
        response = requests.post(
            'http://localhost:8000/query/text',
            json={'query': question}
        )

        result = response.json()
        print(f"Q: {question}")
        print(f"A: {result['answer']}\n")

# Questions will have conversational context
questions = [
    "What is the main topic of the documents?",
    "Can you elaborate on that?",
    "What are the key conclusions?"
]

chat_with_memory(questions)
```

### Monitoring API Usage
```python
import requests
import time

def monitor_usage():
    while True:
        response = requests.get('http://localhost:8000/usage/stats')
        stats = response.json()

        print(f"Memory: {stats['memory']['message_count']} messages")
        print(f"Documents: {stats['vector_store']['document_count']}")

        if 'requesty' in stats and 'cost_saved' in stats['requesty']:
            print(f"Cost saved: {stats['requesty']['cost_saved']}")

        time.sleep(60)  # Check every minute

monitor_usage()
```

---

## 🔧 Rate Limiting & Performance

### Recommended Limits
- **Document Upload**: 1 request per 10 seconds
- **Text Queries**: 10 requests per minute
- **Voice Queries**: 2 requests per minute
- **File Size**: Maximum 50MB per document

### Performance Tips
1. **Batch uploads** during off-peak hours
2. **Cache responses** for repeated queries
3. **Use appropriate chunk sizes** for your document types
4. **Monitor API costs** regularly
5. **Clear conversation memory** periodically

### Concurrent Requests
The API supports multiple concurrent requests, but be mindful of:
- OpenAI API rate limits
- System memory usage
- Vector store access patterns

---

## 🐛 Debugging

### Enable Debug Mode
```bash
# Set environment variables
export DEBUG=True
export LOG_LEVEL=DEBUG

# Restart the API
uvicorn backend.main:app --reload --log-level debug
```

### Common Debug Scenarios

#### Check API Connectivity
```bash
curl -X GET "http://localhost:8000/" -v
```

#### Test Document Processing
```bash
# Upload a small test file
echo "This is a test document." > test.txt
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@test.txt" -v
```

#### Validate Configuration
```bash
curl -X GET "http://localhost:8000/" | jq '.requesty_enabled'
```

---

## 📚 OpenAPI Documentation

The API provides interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

These endpoints provide:
- Interactive API testing
- Complete request/response schemas
- Authentication requirements
- Example payloads
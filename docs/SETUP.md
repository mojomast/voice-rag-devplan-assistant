# 🛠️ Setup Guide

This guide will walk you through setting up the Voice-Enabled RAG System from scratch.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB free space

### Required API Keys
- **OpenAI API Key**: Required for LLM, embeddings, and voice services
  - Get it from: https://platform.openai.com/api-keys
  - Ensure you have credits available
- **Requesty.ai API Key**: Optional, for cost optimization
  - Get it from: https://requesty.ai (if available)

## 🚀 Installation Steps

### Step 1: Clone the Repository
```bash
# Clone the repository
git clone <repository-url>
cd voice-rag-system

# Verify the project structure
ls -la
```

Expected structure:
```
voice-rag-system/
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── document_processor.py
│   ├── main.py
│   ├── rag_handler.py
│   ├── requesty_client.py
│   └── voice_service.py
├── frontend/
│   └── app.py
├── .env.template
├── .gitignore
├── README.md
├── requirements.txt
└── [other directories]
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Verify activation (should show venv in prompt)
which python  # Should point to venv directory
```

### Step 3: Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(langchain|fastapi|streamlit|openai)"
```

### Step 4: Configure Environment Variables
```bash
# Copy the template
cp .env.template .env

# Edit the .env file with your API keys
# On Windows:
notepad .env
# On macOS:
open .env
# On Linux:
nano .env
```

**Required configuration in `.env`:**
```env
# REQUIRED: Your OpenAI API key
OPENAI_API_KEY="sk-your-actual-openai-key-here"

# OPTIONAL: For cost optimization
REQUESTY_API_KEY="your_requesty_key_here"

# File paths (defaults should work)
VECTOR_STORE_PATH="./vector_store"
UPLOAD_PATH="./uploads"

# Application settings
DEBUG=True
LOG_LEVEL="INFO"

# Voice settings
ENABLE_WAKE_WORD=False
WAKE_WORD="hey assistant"
```

### Step 5: Create Required Directories
```bash
# Create necessary directories
mkdir -p vector_store uploads temp_audio logs

# Verify directory structure
ls -la
```

### Step 6: Test Configuration
```bash
# Test that configuration loads correctly
python -c "
from backend.config import settings
print('✅ Configuration loaded successfully')
print(f'OpenAI API Key: {settings.OPENAI_API_KEY[:10]}...')
print(f'Vector Store Path: {settings.VECTOR_STORE_PATH}')
print(f'Upload Path: {settings.UPLOAD_PATH}')
"
```

## 🚦 Running the System

### Method 1: Manual Startup (Recommended for Development)

**Terminal 1 - Backend API:**
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start FastAPI backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

**Terminal 2 - Frontend:**
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Streamlit frontend
streamlit run frontend/app.py --server.port 8501

# You should see:
# You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
```

### Method 2: Background Services
```bash
# Start backend in background
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &

# Start frontend in background
nohup streamlit run frontend/app.py --server.port 8501 > logs/frontend.log 2>&1 &

# Check if services are running
curl http://localhost:8000/
curl http://localhost:8501/
```

## ✅ Verification Steps

### 1. Check API Health
```bash
# Test API health endpoint
curl http://localhost:8000/

# Expected response:
# {
#   "status": "healthy",
#   "vector_store_exists": false,
#   "document_count": 0,
#   "requesty_enabled": true/false,
#   "wake_word_enabled": false
# }
```

### 2. Access Web Interface
1. Open browser to http://localhost:8501
2. You should see the Voice RAG Q&A interface
3. System status should show "✅ System Online"

### 3. Test Document Upload
1. Prepare a test document (PDF, TXT, or DOCX)
2. Use the sidebar upload feature
3. Verify the document processes successfully

### 4. Test Text Query
1. After uploading a document, ask a question
2. Verify you get a response with sources

## 🔧 Configuration Options

### Performance Tuning
```env
# Adjust chunk size for different document types
CHUNK_SIZE=1000          # Default: 1000, Range: 500-2000
CHUNK_OVERLAP=200        # Default: 200, Range: 50-500

# LLM settings
LLM_MODEL="gpt-4o-mini"  # or "gpt-3.5-turbo", "gpt-4"
TEMPERATURE=0.7          # Range: 0.0-1.0

# Embedding model
EMBEDDING_MODEL="text-embedding-3-small"  # or "text-embedding-ada-002"
```

### Voice Settings
```env
# Text-to-Speech
TTS_MODEL="tts-1"        # or "tts-1-hd"
TTS_VOICE="alloy"        # alloy, echo, fable, onyx, nova, shimmer

# Speech-to-Text
WHISPER_MODEL="whisper-1"

# Wake word (optional)
ENABLE_WAKE_WORD=False
WAKE_WORD="hey assistant"
```

## 🐛 Common Setup Issues

### Issue: ModuleNotFoundError
**Problem**: Missing Python dependencies
**Solution**:
```bash
pip install -r requirements.txt
# Or for specific missing module:
pip install <module_name>
```

### Issue: OpenAI API Error
**Problem**: Invalid or missing API key
**Solution**:
- Verify your API key in the .env file
- Check your OpenAI account has credits
- Ensure the key has correct permissions

### Issue: Port Already in Use
**Problem**: Port 8000 or 8501 is occupied
**Solution**:
```bash
# Kill processes using the ports
lsof -ti:8000 | xargs kill -9
lsof -ti:8501 | xargs kill -9

# Or use different ports
uvicorn backend.main:app --port 8001
streamlit run frontend/app.py --server.port 8502
```

### Issue: Permission Errors
**Problem**: Cannot create directories or files
**Solution**:
```bash
# Ensure you have write permissions
chmod -R 755 voice-rag-system/
# Or run with appropriate permissions
```

### Issue: Vector Store Errors
**Problem**: FAISS installation or usage issues
**Solution**:
```bash
# Reinstall FAISS
pip uninstall faiss-cpu
pip install faiss-cpu

# Or try the GPU version if you have CUDA
pip install faiss-gpu
```

## 🎯 Next Steps

Once setup is complete:

1. **Upload Documents**: Start by uploading a few test documents
2. **Test Queries**: Ask questions to verify the RAG system works
3. **Try Voice Features**: Upload audio files and test voice queries
4. **Monitor Performance**: Check the usage stats in the sidebar
5. **Customize Settings**: Adjust configuration based on your needs

## 🔒 Security Recommendations

- **Never commit** your `.env` file to version control
- **Rotate API keys** regularly
- **Use environment-specific** configurations for production
- **Enable logging** to monitor API usage and costs
- **Set up rate limiting** for production deployments

## 📞 Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting section](README.md#troubleshooting) in the main README
2. Look at the logs in the `logs/` directory
3. Test individual components using the debug commands
4. Create an issue with detailed error messages and system information
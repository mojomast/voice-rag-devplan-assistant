# 🎤 Voice-Enabled RAG System

A **production-ready**, enterprise-grade voice-enabled document Q&A system that combines advanced AI capabilities with robust infrastructure. Features intelligent document processing, multi-modal interactions, comprehensive security, and enterprise-scale deployment capabilities.

## 🌟 Key Features

### 🎯 Core Capabilities
- **📄 Multi-Format Document Processing**: PDF, DOCX, TXT, images (with OCR), CSV, XLSX, PPTX, HTML
- **🧠 Advanced RAG Engine**: Context-aware Q&A with intelligent LLM routing via Requesty.ai
- **🎤 Professional Voice Processing**: Real-time transcription, TTS, noise reduction, speaker identification
- **💬 Conversational Interface**: Context-aware chat with conversation memory and source citations
- **📱 Progressive Web App**: Mobile-optimized with offline capabilities

### 🏢 Enterprise Features
- **🔒 Enterprise Security**: Threat detection, rate limiting, input validation, encryption
- **📊 Production Monitoring**: Real-time metrics, alerting (Email/Slack/Discord), health checks
- **⚡ Performance Optimization**: Intelligent caching, query optimization, auto-scaling
- **🐳 Cloud-Native Deployment**: Docker, Kubernetes, AWS/Terraform infrastructure
- **🧪 Comprehensive Testing**: Unit, integration, E2E, security, and performance testing

### 🚀 Advanced Capabilities
- **💰 Cost Optimization**: Up to 80% cost savings with intelligent LLM routing
- **🔊 Native Audio Recording**: Browser-based recording with real-time visualization
- **👁️ Multi-Modal Processing**: OCR for images and scanned documents
- **📈 Analytics Dashboard**: Usage analytics, cost tracking, performance insights
- **🛡️ Security Framework**: Advanced threat detection and incident response

### 🧭 Development Planning Assistant (Phase 2 Expansion)
- **LLM Planning Agent**: Requesty-powered `PlanningAgent` orchestrates context-aware planning conversations.
- **Structured Plan Generation**: `DevPlanGenerator` produces markdown devplans with version history via `DevPlanStore`.
- **Context Manager**: `PlanningContextManager` blends project metadata, recent conversations, and RAG summaries.
- **FastAPI Planning Chat**: `/planning/chat` now routes through the live agent, persisting generated plans automatically.
- **Test-Mode Safe**: Deterministic fallbacks enable offline development when Requesty/OpenAI keys are absent.

## 📋 System Requirements

### Minimum Requirements
- **CPU**: 2 cores, 2.4GHz
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: 100Mbps
- **OS**: Ubuntu 20.04+ / Windows 10+ / macOS 10.15+

### Production Requirements
- **CPU**: 8+ cores, 3.2GHz
- **RAM**: 16GB+
- **Storage**: 100GB+ NVMe SSD
- **Network**: 1Gbps+
- **Load Balancer**: NGINX/HAProxy
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API Key *(optional when running in offline/test mode)*
- Requesty.ai API Key (optional, for cost optimization)
- Docker & Docker Compose (for production deployment)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd voice-rag-system

# Copy and configure environment
cp .env.template .env
# Edit .env with your API keys (or set TEST_MODE=true for offline usage)
```

### 2. Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

### 3. Run the System

#### Development Mode
```bash
# Start backend API
uvicorn backend.main:app --reload

# In a new terminal, start frontend
streamlit run frontend/app.py

# API available at: http://localhost:8000
# Web interface at: http://localhost:8501
# API docs at: http://localhost:8000/docs
# Planning chat endpoint: http://localhost:8000/planning/chat
```

#### Production Mode (Docker)
```bash
# Start all services
docker-compose up -d

# With monitoring stack
docker-compose --profile monitoring up -d

# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Offline Test Mode & Synthetic Vector Store
- When no `OPENAI_API_KEY`/`REQUESTY_API_KEY` is detected (or `TEST_MODE=true`), the backend automatically enters **TEST_MODE**.
- A small synthetic FAISS vector store is generated on startup at `./vector_store`, seeded with AI primer content for deterministic answers.
- Voice transcription/synthesis fall back to deterministic mock responses so tests and demos work without external services.
- Clear and regenerate the test index by deleting `./vector_store/index.faiss` and restarting the backend or rerunning the tests.
- Swap API credentials or toggle test mode live from the Streamlit sidebar (`Credentials & Mode`) without restarting services.

### Enabling the Planning Agent
- Configure Requesty Router credentials in `.env` (`ROUTER_API_KEY`) to access `requesty/glm-4.5` and `requesty/embedding-001`.
- Optional overrides: `REQUESTY_PLANNING_MODEL`, `REQUESTY_EMBEDDING_MODEL`, `PLANNING_TEMPERATURE`, `PLANNING_MAX_TOKENS`.
- In TEST_MODE, the agent returns deterministic JSON payloads so downstream tests remain reliable.

## 🧪 Testing & Quality Assurance

### Comprehensive Testing Suite
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/              # Unit tests
pytest tests/integration/       # Integration tests
pytest tests/security/          # Security tests
npm test                        # E2E tests with Playwright

# Run with coverage
pytest --cov=backend --cov-report=html

# Security testing
python tests/security_scan.py

# Performance regression testing
python tests/performance_regression.py
```

#### Offline-Friendly Test Run
The full unit suite can be executed without API keys thanks to TEST_MODE fallbacks and the synthetic vector store:

```powershell
C:/Users/kyle/projects/noteagent/.venv/Scripts/python.exe -m pytest tests/unit
```

Pass/fail outcomes are deterministic and do not require network access.

#### Planning Agent Smoke Tests
```powershell
C:/Users/kyle/projects/noteagent/.venv/Scripts/python.exe -m pytest tests/unit/test_requesty_client.py tests/unit/test_planning_agent.py -q
```
Validates Requesty client routing and the planning agent orchestration without calling external APIs.

### Load & Performance Testing
```bash
# Run performance benchmarks
python tests/benchmark_performance.py

# Load testing with Locust
locust -f tests/load_test.py --host=http://localhost:8000

# Stress testing
python tests/stress_test.py --duration 300 --concurrent-users 50

# End-to-end browser testing
npx playwright test
```

## 🏢 Enterprise Deployment

### Quick Deployment Options

#### 1. Docker Compose (Recommended for Development)
```bash
# Start all services
docker-compose up -d

# With monitoring stack
docker-compose --profile monitoring up -d

# Production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 2. AWS Production Deployment
```bash
# Deploy infrastructure with Terraform
cd terraform
terraform init
terraform apply -var-file=production.tfvars

# Deploy application
./deploy/aws-deploy.sh production
```

#### 3. Kubernetes Deployment
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
helm install voice-rag ./helm-chart
```

### Monitoring & Observability

#### Built-in Monitoring Dashboard
- **System Health**: http://localhost:8000/monitoring/health
- **Performance Metrics**: http://localhost:8000/monitoring/metrics
- **Security Dashboard**: http://localhost:8000/security/dashboard
- **Analytics**: http://localhost:8501/analytics_dashboard

#### Production Monitoring
```bash
# View comprehensive system status
curl http://localhost:8000/monitoring/status

# Get performance summary
curl http://localhost:8000/performance/summary

# Check security threats
curl http://localhost:8000/security/threats

# System uptime and availability
curl http://localhost:8000/monitoring/uptime
```

#### Alert Configuration
```bash
# Configure email alerts
export SMTP_SERVER=smtp.gmail.com
export ALERT_EMAIL_TO=admin@yourcompany.com

# Configure Slack alerts
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Test alerting system
curl -X POST http://localhost:8000/monitoring/test-alert
```

## 🔒 Security Features

### Enterprise Security Framework
- **Threat Detection**: Real-time detection of SQL injection, XSS, and other attacks
- **Rate Limiting**: Configurable rate limits per endpoint and user
- **Input Validation**: Comprehensive input sanitization and validation
- **Authentication**: JWT-based authentication with role-based access control
- **Encryption**: Data encryption at rest and in transit
- **Audit Logging**: Comprehensive security event logging

### Security Configuration
```bash
# Enable security features
export ENABLE_SECURITY_MONITORING=true
export ENABLE_RATE_LIMITING=true
export ENABLE_THREAT_DETECTION=true

# Configure security thresholds
export RATE_LIMIT_REQUESTS_PER_MINUTE=60
export MAX_FILE_SIZE_MB=50
export PASSWORD_MIN_LENGTH=12
```

## 🚀 Advanced Features

### Multi-Modal Document Processing
- **OCR Support**: Extract text from images and scanned documents
- **Format Support**: 15+ document formats including images, Office docs, PDFs
- **Intelligent Processing**: Automatic format detection and optimization
- **Metadata Extraction**: Preserve document structure and metadata

### Voice Processing Capabilities
- **Real-time Transcription**: Speech-to-text with high accuracy
- **Text-to-Speech**: Natural voice synthesis with multiple voice options
- **Audio Enhancement**: Noise reduction and audio quality improvement
- **Speaker Identification**: Multi-speaker recognition and separation
- **Voice Activity Detection**: Automatic speech detection

### Performance Optimization
- **Intelligent Caching**: Multi-level caching with TTL and LRU eviction
- **Query Optimization**: Database query optimization and indexing
- **Async Processing**: Non-blocking operations for better throughput
- **Resource Monitoring**: Real-time resource usage tracking
- **Auto-scaling**: Automatic scaling based on load

## 📚 Documentation

### 📖 Complete Documentation Suite
- **[📋 Project Status](./PROJECT_STATUS.md)**: Overall project completion and capabilities
- **[🧭 Development Planning Roadmap](./dev-planning-roadmap.md)**: Phase-by-phase plan for the planning assistant expansion
- **[⚙️ Dev Planning Setup](./docs/DEVPLANNING_SETUP.md)**: Environment variables, Requesty configuration, and testing guidance
- **[👤 User Guide](./docs/USER_GUIDE.md)**: Comprehensive end-user documentation
- **[🔧 Administrator Guide](./docs/ADMIN_GUIDE.md)**: Complete system administration guide
- **[🏗️ API Documentation](http://localhost:8000/docs)**: Interactive API documentation
- **[📊 Architecture Overview](./docs/ARCHITECTURE.md)**: System architecture and design

### 🎯 Quick Reference
- **Getting Started**: See User Guide Quick Start section
- **Production Deployment**: See Administrator Guide deployment section
- **API Reference**: Available at `/docs` endpoint when running
- **Troubleshooting**: See both User and Admin guides
- **Security Configuration**: See Administrator Guide security section

## 🎉 Project Completion Status

**✅ Production system is live, 🚧 Development Planning Assistant expansion is in progress.**

### Development Phases (Historical)
- ✅ **Core Platform Phases 1-3**: Delivered production-grade voice-enabled RAG system
- 🚧 **Planning Assistant Phase 2**: Requesty-powered planning agent, context manager, and plan generation
- ⏳ **Planning Assistant Phases 3-5**: Frontend experience, persistent memory upgrades, and voice workflows

### Key Achievements
- **31 Major Features**: All planned features successfully implemented
- **Enterprise Security**: Comprehensive threat detection and security framework
- **Production Monitoring**: Real-time metrics, alerting, and health checks
- **Advanced AI**: Multi-modal processing with OCR and voice capabilities
- **Cloud Infrastructure**: Complete AWS deployment with Terraform
- **Comprehensive Testing**: Unit, integration, E2E, and security testing
- **Complete Documentation**: User and administrator guides

## 🏢 Enterprise Features

### Production-Ready Capabilities
- **Auto-scaling Infrastructure**: Scales based on demand
- **Multi-Environment Support**: Development, staging, production
- **Disaster Recovery**: Automated backups and recovery procedures
- **Compliance Ready**: Security auditing and access controls
- **Cost Optimization**: Up to 80% savings with intelligent routing
- **24/7 Monitoring**: Real-time alerts and health monitoring

### Integration Capabilities
- **API-First Design**: RESTful APIs for all functionality
- **Webhook Support**: Real-time event notifications
- **SSO Ready**: Extensible authentication framework
- **Multi-tenancy**: Support for multiple organizations
- **Custom Branding**: White-label deployment options

## 🔧 Configuration & Customization

### Environment Configuration
```env
# Core API Keys
OPENAI_API_KEY=your_openai_key
REQUESTY_API_KEY=your_requesty_key  # Optional for cost optimization

# System Configuration
ENVIRONMENT=production  # development, staging, production
DEBUG=false
LOG_LEVEL=INFO

# Performance Settings
CACHE_ENABLED=true
CACHE_TTL=3600
MAX_CONCURRENT_REQUESTS=100

# Security Settings
ENABLE_RATE_LIMITING=true
ENABLE_THREAT_DETECTION=true
JWT_EXPIRATION_HOURS=24

# Monitoring Settings
ENABLE_MONITORING=true
ALERT_EMAIL_TO=admin@yourcompany.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### Advanced Configuration
```python
# Custom configuration for enterprise deployment
PRODUCTION_CONFIG = {
    "database": {
        "pool_size": 20,
        "max_overflow": 30
    },
    "cache": {
        "max_size": 10000,
        "ttl": 7200
    },
    "security": {
        "rate_limit": "100/minute",
        "max_file_size": "100MB"
    },
    "monitoring": {
        "collection_interval": 30,
        "retention_days": 90
    }
}
```
    environment:
      - CUSTOM_SETTING=value
    volumes:
      - ./custom-config:/app/config
```

## 🔌 API Reference

### Core Endpoints
- `GET /` - System health check and status
- `GET /health` - Detailed health information
- `GET /metrics` - Prometheus metrics
- `POST /documents/upload` - Upload and index documents
- `POST /query/text` - Text-based Q&A
- `POST /query/voice` - Voice-based Q&A
- `GET /documents/stats` - Document statistics
- `DELETE /documents/clear` - Clear all documents
- `POST /chat/clear` - Clear conversation memory
- `GET /usage/stats` - Usage and cost analytics
- `GET /voice/voices` - Available TTS voices

### Monitoring Endpoints
- `GET /analytics/dashboard` - Analytics data
- `GET /performance/stats` - Performance statistics
- `POST /performance/benchmark` - Trigger benchmarks

### Example Usage
```python
import requests

# Upload a document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/documents/upload',
        files={'file': f}
    )

# Ask a question
response = requests.post(
    'http://localhost:8000/query/text',
    json={'query': 'What is the main topic of the document?'}
)

# Get performance stats
response = requests.get('http://localhost:8000/performance/stats')
```

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │    Services     │
│   Frontend      │◄──►│    Backend      │◄──►│                 │
│                 │    │                 │    │ • Document Proc │
│ • Chat UI       │    │ • REST API      │    │ • RAG Handler   │
│ • File Upload   │    │ • Voice API     │    │ • Voice Service │
│ • Voice UI      │    │ • Health Checks │    │ • Monitoring    │
│ • PWA Features  │    │ • Metrics       │    │ • Cost Tracking │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Infrastructure                           │
│                                                                 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │    Redis    │ │ PostgreSQL  │ │   Nginx     │ │ Monitoring  │ │
│ │   Cache     │ │  Metadata   │ │Load Balancer│ │   Stack     │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                    Data Layer                               │ │
│ │ • FAISS Vector Store  • File Storage  • Conversation Mem   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Development

### Project Structure
```
voice-rag-system/
├── backend/                 # FastAPI backend
│   ├── monitoring/         # Monitoring and metrics
│   ├── main.py            # API server
│   ├── config.py          # Configuration
│   └── ...
├── frontend/               # Streamlit frontend
│   ├── components/        # UI components
│   ├── static/           # PWA assets
│   └── app.py            # Main app
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   ├── benchmark_performance.py
│   └── load_test.py
├── docker/               # Docker configuration
├── monitoring/           # Monitoring configuration
└── docs/                # Documentation
```

### Running Tests
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Performance benchmarks
python tests/benchmark_performance.py

# Load testing
python tests/load_test.py

# Test coverage
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

## 🚀 Deployment

### Docker Deployment
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With full monitoring stack
docker-compose --profile monitoring --profile logging up -d
```

### Environment-Specific Deployments
```bash
# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Production with secrets
echo "your_secret_key" | docker secret create openai_api_key -
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 Performance Optimization

### Monitoring Performance
- Monitor `/metrics` endpoint for Prometheus metrics
- Use Grafana dashboards for visualization
- Check `/health` for system status
- Review logs for performance bottlenecks

### Optimization Tips
- **Chunk Size**: Adjust based on document types (500-2000)
- **Retrieval Count**: Optimize similar chunks retrieved (2-6)
- **Caching**: Enable Redis for query caching
- **Load Balancing**: Use multiple backend replicas

## 🔒 Security

### Security Features
- Non-root Docker containers
- Input validation and sanitization
- API rate limiting
- CORS configuration
- Secret management
- Health check endpoints

### Production Security
```bash
# Use secrets for sensitive data
echo "your_api_key" | docker secret create openai_api_key -

# Enable HTTPS
cp ssl/cert.pem nginx/ssl/
cp ssl/key.pem nginx/ssl/

# Update security headers in Nginx
```

## 🛠️ Troubleshooting

### Common Issues

**Vector store not found**
```bash
# Check permissions
ls -la vector_store/
# Upload and index at least one document first
```

**Voice processing fails**
```bash
# Verify OpenAI API key has audio permissions
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/audio/speech
```

**High API costs**
```bash
# Check cost analytics
curl http://localhost:8000/usage/stats
# Enable Requesty.ai integration
export REQUESTY_API_KEY=your_key
```

**Performance issues**
```bash
# Run performance benchmark
python tests/benchmark_performance.py

# Check system metrics
curl http://localhost:8000/metrics
```

### Debug Mode
```bash
# Enable detailed logging
export DEBUG=True
export LOG_LEVEL=DEBUG

# Run with verbose output
uvicorn backend.main:app --reload --log-level debug
```

### Health Checks
```bash
# Check all service health
docker-compose ps

# Individual service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs redis
```

## 📊 Monitoring & Alerting

### Built-in Dashboards
- System performance metrics
- API response times
- Error rates and success rates
- Cost analytics and usage trends
- Resource utilization

### Custom Alerts
```yaml
# alerting.yml
alerts:
  - name: high_error_rate
    condition: error_rate > 5%
    duration: 5m
    action: notify
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new features
4. Run the test suite (`pytest`)
5. Run performance benchmarks
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines
- Write tests for all new features
- Follow existing code style
- Update documentation
- Run performance benchmarks for significant changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Create GitHub issue with reproduction steps
- **Documentation**: Check `/docs` endpoint for API details
- **Performance**: Use monitoring dashboard for diagnostics
- **Testing**: Run comprehensive test suite before deployment

---

**Built with**: LangChain • FAISS • OpenAI • Requesty.ai • FastAPI • Streamlit • Docker • Prometheus • Grafana
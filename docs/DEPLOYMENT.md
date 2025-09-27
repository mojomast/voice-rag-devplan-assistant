# 🚀 Deployment Guide

This guide covers various deployment scenarios for the Voice-Enabled RAG System.

## 📋 Deployment Overview

The system can be deployed in several ways:
- **Local Development**: Direct Python execution
- **Docker Local**: Containerized local deployment
- **Cloud Services**: AWS, Google Cloud, Azure
- **Self-hosted**: VPS or dedicated servers

---

## 🏠 Local Development Deployment

### Quick Start
```bash
# 1. Setup environment
cp .env.template .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run backend
uvicorn backend.main:app --reload

# 4. Run frontend (new terminal)
streamlit run frontend/app.py
```

### Development with Hot Reload
```bash
# Backend with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend with auto-reload
streamlit run frontend/app.py --server.runOnSave true
```

---

## 🐳 Docker Deployment

### Docker Configuration Files

Create `docker/Dockerfile`:
```dockerfile
# Multi-stage build for optimized production image
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ ./backend/
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /data/vector_store /data/uploads /app/logs && \
    chown -R appuser:appuser /data /app/logs

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app
ENV VECTOR_STORE_PATH="/data/vector_store"
ENV UPLOAD_PATH="/data/uploads"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/', timeout=10)"

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: voice_rag_backend
    ports:
      - "8000:8000"
    volumes:
      # Persistent data storage
      - ./data/vector_store:/data/vector_store
      - ./data/uploads:/data/uploads
      - ./logs:/app/logs
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/', timeout=10)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - voice-rag-network

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    container_name: voice_rag_frontend
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - voice-rag-network

  # Optional: Add nginx reverse proxy for production
  nginx:
    image: nginx:alpine
    container_name: voice_rag_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - voice-rag-network
    profiles:
      - production

networks:
  voice-rag-network:
    driver: bridge

volumes:
  vector_store_data:
  upload_data:
  log_data:
```

### Docker Commands

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

---

## ☁️ Cloud Deployment

### AWS Deployment Options

#### Option 1: AWS ECS (Recommended)

Create `ecs-task-definition.json`:
```json
{
  "family": "voice-rag-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "voice-rag-backend",
      "image": "YOUR_ECR_URI/voice-rag-system:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PYTHONPATH",
          "value": "/app"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/voice-rag-system",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Deployment commands:
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URI
docker build -t voice-rag-system .
docker tag voice-rag-system:latest YOUR_ECR_URI/voice-rag-system:latest
docker push YOUR_ECR_URI/voice-rag-system:latest

# Create ECS service
aws ecs create-service \
  --cluster your-cluster \
  --service-name voice-rag-service \
  --task-definition voice-rag-system \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### Option 2: AWS Lambda (Serverless)

Create `serverless.yml`:
```yaml
service: voice-rag-system

provider:
  name: aws
  runtime: python3.10
  region: us-east-1
  timeout: 30
  environment:
    OPENAI_API_KEY: ${env:OPENAI_API_KEY}
    REQUESTY_API_KEY: ${env:REQUESTY_API_KEY}

functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements
  - serverless-wsgi

custom:
  wsgi:
    app: backend.main.app
  pythonRequirements:
    dockerizePip: true
```

### Google Cloud Deployment

#### Cloud Run Deployment
```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/voice-rag-system

gcloud run deploy voice-rag-system \
  --image gcr.io/PROJECT_ID/voice-rag-system \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY \
  --allow-unauthenticated
```

#### Kubernetes Deployment
Create `k8s-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-rag-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: voice-rag-backend
  template:
    metadata:
      labels:
        app: voice-rag-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/PROJECT_ID/voice-rag-system:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: voice-rag-service
spec:
  selector:
    app: voice-rag-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Azure Deployment

#### Container Instances
```bash
# Create resource group
az group create --name voice-rag-rg --location eastus

# Create container instance
az container create \
  --resource-group voice-rag-rg \
  --name voice-rag-container \
  --image YOUR_REGISTRY/voice-rag-system:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables PYTHONPATH=/app \
  --secure-environment-variables OPENAI_API_KEY=$OPENAI_API_KEY
```

---

## 🔧 Production Configuration

### Environment Variables for Production
```env
# Production Environment Configuration

# API Keys (REQUIRED)
OPENAI_API_KEY=your_production_openai_key
REQUESTY_API_KEY=your_production_requesty_key

# Application Settings
DEBUG=False
LOG_LEVEL=INFO

# Performance Settings
CHUNK_SIZE=1500
CHUNK_OVERLAP=150
TEMPERATURE=0.7

# Security Settings
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Monitoring
ENABLE_METRICS=True

# File Paths (Container paths - do not change)
VECTOR_STORE_PATH=/data/vector_store
UPLOAD_PATH=/data/uploads
```

### Nginx Configuration
Create `nginx/nginx.conf`:
```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:8501;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # API routes
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Handle file uploads
        client_max_body_size 100M;
        proxy_read_timeout 300s;
    }

    # Frontend routes
    location / {
        proxy_pass http://frontend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Load Balancer Configuration
For high-traffic deployments, consider:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  load-balancer:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
```

---

## 📊 Monitoring & Logging

### Application Monitoring
```python
# Add to backend/main.py
from prometheus_client import Counter, Histogram, generate_latest
import time

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')

@app.middleware("http")
async def add_monitoring(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()

    REQUEST_LATENCY.observe(time.time() - start_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Log Aggregation
```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  logstash:
    image: logstash:7.14.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  elasticsearch:
    image: elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:7.14.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

---

## 🔒 Security Considerations

### Production Security Checklist
- [ ] **API Key Security**: Store in secrets manager, not environment variables
- [ ] **HTTPS/SSL**: Use valid certificates for all traffic
- [ ] **CORS Configuration**: Restrict origins to trusted domains
- [ ] **Rate Limiting**: Implement API rate limiting
- [ ] **File Upload Security**: Validate and scan uploaded files
- [ ] **Container Security**: Use non-root users, scan for vulnerabilities
- [ ] **Network Security**: Use private networks, security groups
- [ ] **Monitoring**: Set up alerts for suspicious activity
- [ ] **Backup Strategy**: Regular backups of vector store and configurations
- [ ] **Secrets Rotation**: Regular rotation of API keys and certificates

### Secrets Management

#### AWS Secrets Manager
```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name "voice-rag/openai-key" \
  --description "OpenAI API key for Voice RAG system" \
  --secret-string "$OPENAI_API_KEY"

# Use in ECS task definition
{
  "secrets": [
    {
      "name": "OPENAI_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:voice-rag/openai-key"
    }
  ]
}
```

#### Kubernetes Secrets
```bash
# Create secret
kubectl create secret generic api-keys \
  --from-literal=openai-key=$OPENAI_API_KEY \
  --from-literal=requesty-key=$REQUESTY_API_KEY

# Use in deployment
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: api-keys
      key: openai-key
```

---

## 🚀 Performance Optimization

### Resource Allocation
| Environment | CPU | Memory | Storage |
|-------------|-----|--------|---------|
| Development | 1 core | 2GB | 10GB |
| Staging | 2 cores | 4GB | 50GB |
| Production | 4+ cores | 8GB+ | 100GB+ |

### Scaling Strategies

#### Horizontal Scaling
```yaml
# Auto-scaling configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: voice-rag-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: voice-rag-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Vertical Scaling
Monitor and adjust based on usage:
```bash
# Monitor resource usage
docker stats voice-rag-backend

# Adjust resources in docker-compose
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

---

## 🔄 Backup and Recovery

### Data Backup Strategy
```bash
#!/bin/bash
# backup.sh - Backup script for Voice RAG system

BACKUP_DIR="/backups/voice-rag-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup vector store
cp -r /data/vector_store $BACKUP_DIR/

# Backup uploaded documents
cp -r /data/uploads $BACKUP_DIR/

# Backup configuration
cp .env $BACKUP_DIR/

# Create archive
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### Disaster Recovery
```bash
#!/bin/bash
# restore.sh - Restore script

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
docker-compose down

# Extract backup
tar -xzf $BACKUP_FILE

# Restore data
cp -r voice-rag-*/vector_store /data/
cp -r voice-rag-*/uploads /data/

# Restart services
docker-compose up -d

echo "Restore completed from $BACKUP_FILE"
```

---

## 📋 Deployment Checklist

### Pre-deployment
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Security scan completed

### Post-deployment
- [ ] Health checks passing
- [ ] Logs flowing correctly
- [ ] Metrics being collected
- [ ] API endpoints responding
- [ ] File uploads working
- [ ] Voice processing functional
- [ ] Performance within targets

### Maintenance
- [ ] Regular security updates
- [ ] API key rotation
- [ ] Performance monitoring
- [ ] Cost optimization
- [ ] Backup verification
- [ ] Documentation updates
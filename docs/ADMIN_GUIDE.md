# Voice RAG System - Administrator Guide

## Table of Contents
1. [Installation and Initial Setup](#installation-and-initial-setup)
2. [Configuration Management](#configuration-management)
3. [User Management](#user-management)
4. [System Monitoring](#system-monitoring)
5. [Security Administration](#security-administration)
6. [Performance Optimization](#performance-optimization)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Production Deployment](#production-deployment)

---

## Installation and Initial Setup

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores, 2.4GHz
- **RAM**: 4GB
- **Storage**: 50GB SSD
- **Network**: 100Mbps connection
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Docker

#### Recommended Requirements
- **CPU**: 4+ cores, 3.0GHz
- **RAM**: 8GB+
- **Storage**: 100GB+ SSD
- **Network**: 1Gbps connection
- **OS**: Ubuntu 22.04 LTS

#### Production Requirements
- **CPU**: 8+ cores, 3.2GHz
- **RAM**: 16GB+
- **Storage**: 500GB+ SSD (NVMe preferred)
- **Network**: 10Gbps connection
- **Load Balancer**: NGINX/HAProxy
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+

### Installation Steps

#### 1. Docker Installation (Recommended)

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### 2. System Setup

```bash
# Clone repository
git clone https://github.com/voice-rag-system/voice-rag-system.git
cd voice-rag-system

# Create required directories
sudo mkdir -p /var/log/voice-rag
sudo mkdir -p /var/lib/voice-rag/vector_store
sudo mkdir -p /var/lib/voice-rag/uploads
sudo chown -R $USER:$USER /var/lib/voice-rag

# Set up environment
cp .env.example .env
```

#### 3. Configuration

```bash
# Edit environment file
nano .env
```

Essential configuration variables:
```env
# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
REQUESTY_API_KEY=your-requesty-key  # Optional

# Security
JWT_SECRET_KEY=your-256-bit-secret-key
ENCRYPTION_PASSWORD=your-encryption-password

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/voicerag
REDIS_URL=redis://localhost:6379

# Storage
UPLOAD_PATH=/var/lib/voice-rag/uploads
VECTOR_STORE_PATH=/var/lib/voice-rag/vector_store

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO

# Security
ENABLE_RATE_LIMITING=true
ENABLE_SECURITY_HEADERS=true
```

#### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 5. Initial Verification

```bash
# Health check
curl http://localhost:8000/health

# Frontend access
curl http://localhost:8501

# API documentation
curl http://localhost:8000/docs
```

### SSL/TLS Setup

#### 1. Generate SSL Certificates

```bash
# Using Let's Encrypt (recommended)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Or using self-signed certificates (development only)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/voice-rag.key \
    -out /etc/ssl/certs/voice-rag.crt
```

#### 2. NGINX Configuration

```nginx
# /etc/nginx/sites-available/voice-rag
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/voice-rag.crt;
    ssl_certificate_key /etc/ssl/private/voice-rag.key;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Frontend
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Configuration Management

### Environment Variables

#### Core Configuration
```env
# Application
APP_NAME=Voice RAG System
APP_VERSION=1.0.0
ENVIRONMENT=production  # development, staging, production

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # text, json
LOG_RETENTION_DAYS=30

# Performance
WORKER_PROCESSES=4
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=300
```

#### Security Configuration
```env
# Authentication
JWT_SECRET_KEY=your-secret-key-min-256-bits
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10

# Input Validation
MAX_INPUT_LENGTH=10000
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=.pdf,.docx,.txt,.jpg,.png

# Encryption
ENABLE_DATA_ENCRYPTION=true
ENCRYPTION_ALGORITHM=AES256
```

#### Monitoring Configuration
```env
# Basic Monitoring
MONITORING_ENABLED=true
METRICS_COLLECTION_INTERVAL=30
METRICS_RETENTION_DAYS=90

# Alerting
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_TO=admin@yourdomain.com

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#voice-rag-alerts

# Thresholds
CPU_WARNING_THRESHOLD=70
CPU_CRITICAL_THRESHOLD=85
MEMORY_WARNING_THRESHOLD=80
MEMORY_CRITICAL_THRESHOLD=90
```

### Configuration Files

#### 1. Main Configuration (`config/settings.yaml`)
```yaml
app:
  name: "Voice RAG System"
  version: "1.0.0"
  debug: false

database:
  host: "localhost"
  port: 5432
  name: "voicerag"
  pool_size: 10
  max_overflow: 20

redis:
  host: "localhost"
  port: 6379
  db: 0
  max_connections: 20

vector_store:
  type: "chroma"
  persist_directory: "/var/lib/voice-rag/vector_store"
  collection_name: "documents"

ai_services:
  openai:
    model: "gpt-3.5-turbo"
    max_tokens: 1000
    temperature: 0.1

  requesty:
    enabled: true
    fallback_to_openai: true
```

#### 2. Security Configuration (`config/security.yaml`)
```yaml
security:
  authentication:
    required: true
    methods: ["jwt", "api_key"]

  rate_limiting:
    enabled: true
    default_limit: "60/minute"
    limits:
      upload: "10/minute"
      query: "30/minute"

  input_validation:
    enabled: true
    max_length: 10000
    sanitize_html: true

  file_upload:
    max_size_mb: 50
    allowed_types:
      - "pdf"
      - "docx"
      - "txt"
      - "jpg"
      - "png"
    scan_for_malware: true
```

### Configuration Management Commands

```bash
# Validate configuration
docker-compose exec backend python -m backend.config.validate

# Reload configuration (graceful)
docker-compose exec backend kill -USR1 1

# View current configuration
curl http://localhost:8000/admin/config

# Update configuration
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d @new_config.json
```

---

## User Management

### User Roles and Permissions

#### Role Definitions
```python
ROLES = {
    "admin": {
        "permissions": ["*"],  # All permissions
        "description": "System administrator"
    },
    "user": {
        "permissions": ["read", "write", "upload", "query"],
        "description": "Regular user"
    },
    "readonly": {
        "permissions": ["read"],
        "description": "Read-only access"
    },
    "api_user": {
        "permissions": ["api_access", "query"],
        "description": "API-only access"
    }
}
```

#### Permission Matrix
| Permission | Admin | User | ReadOnly | API User |
|------------|-------|------|----------|----------|
| Read Documents | ✓ | ✓ | ✓ | ✓ |
| Upload Documents | ✓ | ✓ | ✗ | ✗ |
| Delete Documents | ✓ | ✓ | ✗ | ✗ |
| Query System | ✓ | ✓ | ✓ | ✓ |
| Voice Features | ✓ | ✓ | ✓ | ✓ |
| Analytics Access | ✓ | ✗ | ✗ | ✗ |
| User Management | ✓ | ✗ | ✗ | ✗ |
| System Config | ✓ | ✗ | ✗ | ✗ |

### User Management Commands

#### Create Users
```bash
# Create admin user
curl -X POST http://localhost:8000/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@yourdomain.com",
    "password": "secure_password",
    "role": "admin"
  }'

# Create regular user
curl -X POST http://localhost:8000/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@yourdomain.com",
    "password": "user_password",
    "role": "user"
  }'
```

#### Manage Users
```bash
# List all users
curl http://localhost:8000/admin/users

# Get user details
curl http://localhost:8000/admin/users/{user_id}

# Update user
curl -X PUT http://localhost:8000/admin/users/{user_id} \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

# Disable user
curl -X POST http://localhost:8000/admin/users/{user_id}/disable

# Delete user
curl -X DELETE http://localhost:8000/admin/users/{user_id}
```

#### API Key Management
```bash
# Generate API key
curl -X POST http://localhost:8000/admin/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "permissions": ["read", "query"],
    "expires_in_days": 90
  }'

# List API keys
curl http://localhost:8000/admin/api-keys

# Revoke API key
curl -X DELETE http://localhost:8000/admin/api-keys/{key_id}
```

### Authentication Integration

#### LDAP Integration
```python
# config/ldap.py
LDAP_CONFIG = {
    "server": "ldap://your-ldap-server.com",
    "base_dn": "dc=yourdomain,dc=com",
    "user_dn": "ou=users,dc=yourdomain,dc=com",
    "bind_dn": "cn=admin,dc=yourdomain,dc=com",
    "bind_password": "admin_password",
    "user_filter": "(uid={username})",
    "attributes": ["uid", "mail", "cn", "memberOf"]
}
```

#### OAuth Integration
```python
# config/oauth.py
OAUTH_CONFIG = {
    "google": {
        "client_id": "your-google-client-id",
        "client_secret": "your-google-client-secret",
        "redirect_uri": "https://yourdomain.com/auth/google/callback"
    },
    "github": {
        "client_id": "your-github-client-id",
        "client_secret": "your-github-client-secret",
        "redirect_uri": "https://yourdomain.com/auth/github/callback"
    }
}
```

---

## System Monitoring

### Monitoring Dashboard

#### Access Monitoring
- **URL**: http://localhost:8000/monitoring/status
- **Authentication**: Admin access required
- **Refresh**: Real-time updates every 30 seconds

#### Key Metrics
1. **System Health**
   - CPU usage (%)
   - Memory usage (%)
   - Disk usage (%)
   - Network I/O

2. **Application Metrics**
   - Request rate (req/sec)
   - Response time (ms)
   - Error rate (%)
   - Active users

3. **Service Metrics**
   - Database connections
   - Cache hit rate (%)
   - Queue length
   - Background tasks

### Monitoring Commands

#### System Status
```bash
# Overall system health
curl http://localhost:8000/monitoring/health

# Detailed metrics
curl http://localhost:8000/monitoring/metrics

# Performance statistics
curl http://localhost:8000/performance/stats

# Cache statistics
curl http://localhost:8000/performance/cache-stats
```

#### Service Status
```bash
# Check all services
docker-compose ps

# Service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs redis

# Resource usage
docker stats
```

#### Database Monitoring
```bash
# Database health
docker-compose exec postgres pg_isready

# Connection count
docker-compose exec postgres psql -U voicerag -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
docker-compose exec postgres psql -U voicerag -c "SELECT pg_size_pretty(pg_database_size('voicerag'));"

# Slow queries
docker-compose exec postgres psql -U voicerag -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Alert Configuration

#### Email Alerts
```bash
# Configure SMTP
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=alerts@yourdomain.com
export SMTP_PASSWORD=your-app-password
export ALERT_EMAIL_TO=admin@yourdomain.com

# Test email alert
curl -X POST http://localhost:8000/monitoring/test-alert \
  -H "Content-Type: application/json" \
  -d '{"severity": "warning", "message": "Test alert"}'
```

#### Slack Alerts
```bash
# Configure Slack webhook
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
export SLACK_CHANNEL=#voice-rag-alerts

# Test Slack alert
curl -X POST http://localhost:8000/monitoring/test-alert \
  -H "Content-Type: application/json" \
  -d '{"severity": "error", "message": "Test Slack notification"}'
```

#### Custom Alert Rules
```python
# Custom alert configuration
CUSTOM_ALERTS = [
    {
        "name": "high_query_volume",
        "condition": "query_rate > 100",
        "severity": "warning",
        "channels": ["email", "slack"]
    },
    {
        "name": "low_disk_space",
        "condition": "disk_usage > 90",
        "severity": "critical",
        "channels": ["email", "slack", "sms"]
    }
]
```

### Log Management

#### Log Configuration
```python
# logging.conf
[loggers]
keys=root,app,security,performance

[handlers]
keys=console,file,syslog

[formatters]
keys=standard,json

[logger_root]
level=INFO
handlers=console,file

[handler_file]
class=handlers.RotatingFileHandler
level=INFO
formatter=json
args=('/var/log/voice-rag/app.log', 'a', 10485760, 5)
```

#### Log Analysis
```bash
# View recent logs
tail -f /var/log/voice-rag/app.log

# Search for errors
grep -i error /var/log/voice-rag/app.log

# Analyze performance logs
awk '/response_time/ {sum+=$NF; count++} END {print "Avg response time:", sum/count}' /var/log/voice-rag/app.log

# Security event logs
grep -i "security\|threat\|blocked" /var/log/voice-rag/app.log
```

---

## Security Administration

### Security Monitoring

#### Security Dashboard
Access: http://localhost:8000/security/dashboard

Key security metrics:
- Active threats detected
- Blocked IP addresses
- Failed authentication attempts
- Rate limit violations
- Security rule violations

#### Security Commands
```bash
# Security status
curl http://localhost:8000/security/dashboard

# Recent threats
curl http://localhost:8000/security/threats

# Blocked IPs
curl http://localhost:8000/security/blocked-ips

# Test input security
curl -X POST http://localhost:8000/security/test-input \
  -H "Content-Type: application/json" \
  -d '{"test_input": "SELECT * FROM users;"}'
```

### Access Control

#### IP Whitelisting
```bash
# Add allowed IP
curl -X POST http://localhost:8000/admin/ip-whitelist \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100", "description": "Office network"}'

# Block IP address
curl -X POST http://localhost:8000/security/block-ip \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.200", "reason": "Suspicious activity"}'
```

#### Rate Limiting Configuration
```python
# Rate limiting rules
RATE_LIMITS = {
    "global": "1000/hour",
    "per_ip": "60/minute",
    "upload": "10/minute",
    "query": "30/minute",
    "voice": "20/minute"
}
```

### Security Hardening

#### File System Security
```bash
# Set proper permissions
sudo chown -R voicerag:voicerag /var/lib/voice-rag
sudo chmod 750 /var/lib/voice-rag
sudo chmod 640 /var/lib/voice-rag/config/*

# Secure log files
sudo chmod 640 /var/log/voice-rag/*
sudo chown voicerag:adm /var/log/voice-rag/*
```

#### Network Security
```bash
# Firewall configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Fail2ban configuration
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

#### Database Security
```sql
-- Create dedicated database user
CREATE USER voicerag WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE voicerag TO voicerag;
GRANT USAGE ON SCHEMA public TO voicerag;
GRANT CREATE ON SCHEMA public TO voicerag;

-- Revoke unnecessary permissions
REVOKE ALL ON SCHEMA public FROM public;
```

### Security Auditing

#### Audit Log Analysis
```bash
# Security events
grep -E "(login|auth|security|threat)" /var/log/voice-rag/security.log

# Failed authentication attempts
grep "authentication failed" /var/log/voice-rag/security.log | tail -20

# Blocked requests
grep "blocked" /var/log/voice-rag/security.log | wc -l

# Suspicious activity patterns
awk '/threat_detected/ {print $1, $2, $NF}' /var/log/voice-rag/security.log
```

#### Security Reports
```bash
# Generate daily security report
curl http://localhost:8000/admin/security-report?period=daily

# Weekly security summary
curl http://localhost:8000/admin/security-report?period=weekly

# Export security events
curl http://localhost:8000/admin/security-events?export=csv > security_events.csv
```

---

## Performance Optimization

### Performance Monitoring

#### Key Performance Indicators
1. **Response Time**: Target <2 seconds for queries
2. **Throughput**: Target >50 requests/second
3. **Error Rate**: Target <1%
4. **Resource Usage**: Target <80% CPU/Memory

#### Performance Commands
```bash
# Current performance metrics
curl http://localhost:8000/performance/summary

# Performance history
curl http://localhost:8000/monitoring/metrics/history/response_time?hours=24

# Cache performance
curl http://localhost:8000/performance/cache-stats

# Database performance
curl http://localhost:8000/performance/database-stats
```

### Optimization Strategies

#### 1. Database Optimization
```sql
-- Index optimization
CREATE INDEX CONCURRENTLY idx_documents_created_at ON documents(created_at);
CREATE INDEX CONCURRENTLY idx_queries_timestamp ON queries(timestamp);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Query optimization
ANALYZE documents;
VACUUM ANALYZE documents;

-- Connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

#### 2. Application Optimization
```python
# Cache configuration
CACHE_CONFIG = {
    "enabled": True,
    "max_size": 1000,
    "ttl": 3600,
    "redis_enabled": True
}

# Async processing
ASYNC_CONFIG = {
    "max_workers": 10,
    "queue_size": 100,
    "timeout": 300
}
```

#### 3. Infrastructure Optimization
```bash
# Increase file limits
echo "voicerag soft nofile 65536" >> /etc/security/limits.conf
echo "voicerag hard nofile 65536" >> /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.rmem_max = 16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" >> /etc/sysctl.conf
sysctl -p
```

### Load Testing

#### Performance Testing Scripts
```bash
# Install testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000

# Stress test specific endpoints
ab -n 1000 -c 10 http://localhost:8000/health
siege -c 20 -t 60s http://localhost:8000/
```

#### Load Test Configuration
```python
# tests/load_test.py
from locust import HttpUser, task, between

class VoiceRAGUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def query_text(self):
        self.client.post("/query/text", json={
            "query": "What is the main topic?",
            "include_sources": True
        })

    @task(1)
    def upload_document(self):
        with open("test_document.pdf", "rb") as f:
            self.client.post("/documents/upload", files={"file": f})

    @task(2)
    def health_check(self):
        self.client.get("/health")
```

---

## Backup and Recovery

### Backup Strategy

#### 1. Database Backup
```bash
# Daily database backup
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/voice-rag"
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker-compose exec postgres pg_dump -U voicerag voicerag > $BACKUP_DIR/db_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_$DATE.sql

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

#### 2. Vector Store Backup
```bash
# Backup vector store
rsync -av /var/lib/voice-rag/vector_store/ $BACKUP_DIR/vector_store_$DATE/

# Tar and compress
tar -czf $BACKUP_DIR/vector_store_$DATE.tar.gz -C $BACKUP_DIR vector_store_$DATE/
rm -rf $BACKUP_DIR/vector_store_$DATE/
```

#### 3. Configuration Backup
```bash
# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /var/lib/voice-rag/config/ \
    /etc/nginx/sites-available/voice-rag \
    .env
```

#### 4. Automated Backup Script
```bash
# /usr/local/bin/voice-rag-backup.sh
#!/bin/bash
set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/voice-rag"
RETENTION_DAYS=30
S3_BUCKET="your-backup-bucket"  # Optional

echo "Starting Voice RAG backup - $DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Backing up database..."
docker-compose exec -T postgres pg_dump -U voicerag voicerag | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Vector store backup
echo "Backing up vector store..."
tar -czf $BACKUP_DIR/vector_store_$DATE.tar.gz -C /var/lib/voice-rag vector_store/

# Configuration backup
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    -C /var/lib/voice-rag config/ \
    -C /etc/nginx/sites-available voice-rag \
    -C /path/to/project .env

# Upload to S3 (optional)
if [ ! -z "$S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://$S3_BUCKET/backups/
    aws s3 cp $BACKUP_DIR/vector_store_$DATE.tar.gz s3://$S3_BUCKET/backups/
    aws s3 cp $BACKUP_DIR/config_$DATE.tar.gz s3://$S3_BUCKET/backups/
fi

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully"
```

#### 5. Schedule Backups
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /usr/local/bin/voice-rag-backup.sh >> /var/log/voice-rag/backup.log 2>&1

# Weekly full backup at Sunday 1 AM
0 1 * * 0 /usr/local/bin/voice-rag-full-backup.sh >> /var/log/voice-rag/backup.log 2>&1
```

### Recovery Procedures

#### 1. Database Recovery
```bash
# Stop services
docker-compose stop backend frontend

# Restore database
gunzip -c /var/backups/voice-rag/db_20240101_020000.sql.gz | \
    docker-compose exec -T postgres psql -U voicerag voicerag

# Restart services
docker-compose up -d
```

#### 2. Vector Store Recovery
```bash
# Stop services
docker-compose stop

# Restore vector store
rm -rf /var/lib/voice-rag/vector_store/*
tar -xzf /var/backups/voice-rag/vector_store_20240101_020000.tar.gz \
    -C /var/lib/voice-rag/

# Fix permissions
chown -R voicerag:voicerag /var/lib/voice-rag/vector_store

# Restart services
docker-compose up -d
```

#### 3. Full System Recovery
```bash
# Full disaster recovery script
#!/bin/bash
BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20240101_020000"
    exit 1
fi

echo "Starting full system recovery for $BACKUP_DATE"

# Stop all services
docker-compose down

# Restore database
echo "Restoring database..."
gunzip -c /var/backups/voice-rag/db_$BACKUP_DATE.sql.gz | \
    docker-compose exec -T postgres psql -U voicerag voicerag

# Restore vector store
echo "Restoring vector store..."
rm -rf /var/lib/voice-rag/vector_store/*
tar -xzf /var/backups/voice-rag/vector_store_$BACKUP_DATE.tar.gz \
    -C /var/lib/voice-rag/

# Restore configuration
echo "Restoring configuration..."
tar -xzf /var/backups/voice-rag/config_$BACKUP_DATE.tar.gz \
    -C /

# Fix permissions
chown -R voicerag:voicerag /var/lib/voice-rag/

# Start services
docker-compose up -d

# Verify recovery
sleep 30
curl http://localhost:8000/health

echo "Recovery completed"
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check Docker status
sudo systemctl status docker

# Check container logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Check port conflicts
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8501

# Restart services
docker-compose down
docker-compose up -d
```

#### 2. Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready

# Check connection from backend
docker-compose exec backend python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://voicerag:password@postgres:5432/voicerag')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Reset database password
docker-compose exec postgres psql -U postgres -c "
ALTER USER voicerag PASSWORD 'new_password';
"
```

#### 3. High Memory Usage
```bash
# Check memory usage
free -h
docker stats

# Analyze memory consumption
docker-compose exec backend python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
print(f'Available memory: {psutil.virtual_memory().available / 1024**3:.2f} GB')
"

# Reduce memory usage
# Edit docker-compose.yml to limit memory
services:
  backend:
    mem_limit: 2g
  frontend:
    mem_limit: 1g
```

#### 4. Slow Performance
```bash
# Check system resources
top
htop
iotop

# Analyze slow queries
docker-compose exec postgres psql -U voicerag -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"

# Check cache hit ratio
curl http://localhost:8000/performance/cache-stats

# Clear cache if needed
curl -X POST http://localhost:8000/performance/cache/clear
```

#### 5. SSL/TLS Issues
```bash
# Check certificate validity
openssl x509 -in /etc/ssl/certs/voice-rag.crt -text -noout

# Test SSL connection
openssl s_client -connect yourdomain.com:443

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
sudo certbot renew
```

### Diagnostic Commands

#### System Diagnostics
```bash
# Comprehensive system check
curl http://localhost:8000/admin/diagnostics

# Check all services
docker-compose ps
docker-compose top

# Resource usage
docker system df
docker system prune -f

# Network connectivity
ping google.com
nslookup yourdomain.com
```

#### Application Diagnostics
```bash
# Application health
curl http://localhost:8000/health

# Performance metrics
curl http://localhost:8000/performance/summary

# Error logs
docker-compose logs backend | grep -i error
docker-compose logs frontend | grep -i error

# Security status
curl http://localhost:8000/security/dashboard
```

### Emergency Procedures

#### 1. Service Recovery
```bash
# Emergency restart
docker-compose down
sleep 10
docker-compose up -d

# Force container rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 2. Database Recovery
```bash
# Emergency database recovery
docker-compose stop backend frontend
docker-compose exec postgres pg_ctl restart
docker-compose start backend frontend
```

#### 3. Rollback Deployment
```bash
# Rollback to previous version
git checkout previous-stable-tag
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
```bash
#!/bin/bash
# daily-maintenance.sh

echo "Starting daily maintenance - $(date)"

# Check service health
curl -f http://localhost:8000/health || echo "Health check failed"

# Check disk space
df -h | awk '$5 > 80 {print "High disk usage:", $0}'

# Rotate logs
docker-compose exec backend logrotate /etc/logrotate.conf

# Update system metrics
curl http://localhost:8000/admin/update-metrics

echo "Daily maintenance completed"
```

#### Weekly Tasks
```bash
#!/bin/bash
# weekly-maintenance.sh

echo "Starting weekly maintenance - $(date)"

# Database maintenance
docker-compose exec postgres psql -U voicerag -c "VACUUM ANALYZE;"

# Clean old logs
find /var/log/voice-rag -name "*.log.*" -mtime +7 -delete

# Security scan
curl http://localhost:8000/admin/security-scan

# Performance analysis
curl http://localhost:8000/admin/performance-report > /tmp/performance-report.json

# Update documentation
curl http://localhost:8000/admin/update-docs

echo "Weekly maintenance completed"
```

#### Monthly Tasks
```bash
#!/bin/bash
# monthly-maintenance.sh

echo "Starting monthly maintenance - $(date)"

# Full system backup
/usr/local/bin/voice-rag-backup.sh

# Security audit
curl http://localhost:8000/admin/security-audit

# Performance optimization
curl -X POST http://localhost:8000/admin/optimize-performance

# Update SSL certificates
sudo certbot renew

# System updates
sudo apt update && sudo apt upgrade -y

# Docker cleanup
docker system prune -f
docker volume prune -f

echo "Monthly maintenance completed"
```

### Maintenance Schedule

```bash
# Add to crontab
crontab -e

# Daily maintenance at 3 AM
0 3 * * * /usr/local/bin/daily-maintenance.sh >> /var/log/voice-rag/maintenance.log 2>&1

# Weekly maintenance on Sunday at 4 AM
0 4 * * 0 /usr/local/bin/weekly-maintenance.sh >> /var/log/voice-rag/maintenance.log 2>&1

# Monthly maintenance on 1st day at 5 AM
0 5 1 * * /usr/local/bin/monthly-maintenance.sh >> /var/log/voice-rag/maintenance.log 2>&1
```

### Update Procedures

#### Application Updates
```bash
# Backup before update
/usr/local/bin/voice-rag-backup.sh

# Pull latest changes
git pull origin main

# Stop services
docker-compose down

# Build new images
docker-compose build

# Run database migrations
docker-compose run --rm backend python -m backend.db.migrate

# Start services
docker-compose up -d

# Verify update
sleep 30
curl http://localhost:8000/health
```

#### System Updates
```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Update Docker
sudo apt install docker-ce docker-ce-cli containerd.io

# Update Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Restart services
docker-compose down
docker-compose up -d
```

---

## Production Deployment

### Infrastructure Requirements

#### Minimum Production Setup
- **Load Balancer**: NGINX/HAProxy
- **Application Servers**: 2+ instances
- **Database**: PostgreSQL 14+ (managed service recommended)
- **Cache**: Redis 6+ (managed service recommended)
- **Storage**: S3 or compatible object storage
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or cloud logging

#### Recommended Architecture
```
Internet
    ↓
Load Balancer (NGINX)
    ↓
Application Servers (2+)
    ↓
Database Cluster (PostgreSQL)
    ↓
Cache Cluster (Redis)
    ↓
Object Storage (S3)
```

### Deployment Checklist

#### Pre-Deployment
- [ ] Infrastructure provisioned
- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Database migrations tested
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Load testing completed
- [ ] Security audit performed

#### Deployment Steps
1. **Infrastructure Setup**
   ```bash
   # Using Terraform (see terraform/ directory)
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

2. **Application Deployment**
   ```bash
   # Deploy to production
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Database Setup**
   ```bash
   # Run migrations
   docker-compose exec backend python -m backend.db.migrate

   # Create initial admin user
   docker-compose exec backend python -m backend.admin.create_user \
       --username admin \
       --email admin@yourdomain.com \
       --role admin
   ```

4. **Verification**
   ```bash
   # Health checks
   curl https://yourdomain.com/health
   curl https://yourdomain.com/api/health

   # Load testing
   locust -f tests/load_test.py --host=https://yourdomain.com
   ```

#### Post-Deployment
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] SSL certificates valid
- [ ] Performance metrics baseline established
- [ ] Backup schedule active
- [ ] Documentation updated
- [ ] Team training completed

### Production Configuration

#### Environment Variables
```env
# Production environment
ENVIRONMENT=production
DEBUG=false

# Security
ALLOWED_HOSTS=yourdomain.com
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true

# Database (managed service)
DATABASE_URL=postgresql://user:pass@prod-db.amazonaws.com:5432/voicerag

# Cache (managed service)
REDIS_URL=redis://prod-redis.amazonaws.com:6379

# Storage
AWS_STORAGE_BUCKET_NAME=voice-rag-prod
AWS_S3_REGION_NAME=us-west-2

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
NEWRELIC_LICENSE_KEY=your-newrelic-key

# Scaling
WORKER_PROCESSES=8
MAX_CONCURRENT_REQUESTS=200
```

#### Load Balancer Configuration
```nginx
# /etc/nginx/sites-available/voice-rag-prod
upstream voice_rag_backend {
    least_conn;
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
}

upstream voice_rag_frontend {
    least_conn;
    server 10.0.1.10:8501 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8501 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://voice_rag_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API
    location /api/ {
        proxy_pass http://voice_rag_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://voice_rag_backend/health;
        access_log off;
    }
}
```

This comprehensive administrator guide provides all the necessary information for setting up, configuring, monitoring, and maintaining a production Voice RAG System deployment. Regular review and updates of these procedures will ensure optimal system operation and security.
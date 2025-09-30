# Multi-stage build for optimized production image
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /data/vector_store /data/uploads /app/logs /app/temp_audio && \
    chown -R appuser:appuser /data /app/logs /app/temp_audio

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app \
    VECTOR_STORE_PATH="/data/vector_store" \
    UPLOAD_PATH="/data/uploads" \
    TEMP_AUDIO_PATH="/app/temp_audio" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Start command with proper signal handling
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
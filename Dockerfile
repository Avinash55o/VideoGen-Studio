# ============================================================
# VideoGen Studio — Local AI Video Generation Server
# 3-stage build: Frontend → Python deps → Runtime
# ============================================================

# === Stage 1: Build frontend ===
# You can use your preferred Node version
FROM node:20-slim AS frontend

WORKDIR /build

COPY package.json package-lock.json ./
COPY app/ ./app/
COPY web/ ./web/
RUN npm ci
RUN cd web && npm run build



# === Stage 2: Build Python dependencies ===
FROM python:3.12-slim AS backend-builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
RUN pip install --no-cache-dir --prefix=/install --no-deps chatterbox-tts
RUN pip install --no-cache-dir --prefix=/install --no-deps hume-tada
RUN pip install --no-cache-dir --prefix=/install \
    git+https://github.com/QwenLM/Qwen3-TTS.git


# === Stage 3: Runtime ===
FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r videogen && \
    useradd -r -g videogen -m -s /bin/bash videogen

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=backend-builder /install /usr/local

# Copy backend application code
COPY --chown=videogen:videogen backend/ /app/backend/

# Copy built frontend from frontend stage
COPY --from=frontend --chown=videogen:videogen /build/web/dist /app/frontend/

# Create data directories owned by non-root user
RUN mkdir -p /app/data/projects /app/data/renders /app/data/voice-profiles /app/data/cache \
    && chown -R videogen:videogen /app/data

# Switch to non-root user
USER videogen

# Expose the API port
EXPOSE 17493

# Health check — auto-restart if the server hangs
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:17493/health || exit 1

# Start the FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "17493"]

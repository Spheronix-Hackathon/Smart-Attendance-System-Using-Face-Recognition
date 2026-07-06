# =============================================================================
# Smart Attendance System Using Face Recognition (SASUFR)
# Production Dockerfile for Render
# =============================================================================

FROM python:3.11.11-slim

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PORT=10000

WORKDIR /app

# -----------------------------------------------------------------------------
# Linux dependencies
# -----------------------------------------------------------------------------

RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    pkg-config \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libjpeg62-turbo-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Upgrade pip
# -----------------------------------------------------------------------------

RUN python -m pip install --upgrade pip setuptools wheel

# -----------------------------------------------------------------------------
# Copy requirements first
# -----------------------------------------------------------------------------

COPY backend/requirements.txt .

# -----------------------------------------------------------------------------
# Install dlib binary FIRST
# -----------------------------------------------------------------------------

RUN pip install dlib-bin==19.24.6

# -----------------------------------------------------------------------------
# Install official face recognition models
# -----------------------------------------------------------------------------

RUN pip install --no-cache-dir \
    git+https://github.com/ageitgey/face_recognition_models.git

# -----------------------------------------------------------------------------
# Install face_recognition WITHOUT dependencies
# -----------------------------------------------------------------------------

RUN pip install --no-deps face-recognition==1.3.0

# -----------------------------------------------------------------------------
# Remove packages already installed
# -----------------------------------------------------------------------------

RUN grep -vE "^(dlib-bin|face-recognition|face_recognition_models)" requirements.txt > requirements-render.txt

# -----------------------------------------------------------------------------
# Install remaining packages
# -----------------------------------------------------------------------------

RUN pip install -r requirements-render.txt

# -----------------------------------------------------------------------------
# Copy application
# -----------------------------------------------------------------------------

COPY backend /app/backend
COPY frontend /app/frontend

WORKDIR /app/backend

# -----------------------------------------------------------------------------
# Render Port
# -----------------------------------------------------------------------------

EXPOSE 10000

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------

HEALTHCHECK CMD curl --fail http://localhost:10000/health || exit 1

# -----------------------------------------------------------------------------
# Start Server
# -----------------------------------------------------------------------------

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "300", "--graceful-timeout", "120"]
# =============================================================================
# Smart Attendance System Using Face Recognition (SASUFR)
# Production Dockerfile for Render
# =============================================================================

FROM python:3.11.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# -----------------------------------------------------------------------------
# Install Linux system dependencies
# -----------------------------------------------------------------------------

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    git \
    curl \
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
# Copy requirements first (Docker cache)
# -----------------------------------------------------------------------------

COPY backend/requirements.txt .

# -----------------------------------------------------------------------------
# Upgrade pip
# -----------------------------------------------------------------------------

RUN python -m pip install --upgrade pip setuptools wheel

# -----------------------------------------------------------------------------
# Install dlib binary FIRST
# -----------------------------------------------------------------------------

RUN pip install dlib-bin==19.24.6

# -----------------------------------------------------------------------------
# Install face recognition models
# -----------------------------------------------------------------------------

RUN pip install face_recognition_models==0.3.0

# -----------------------------------------------------------------------------
# Install face-recognition WITHOUT dependencies
# (prevents pip from compiling dlib)
# -----------------------------------------------------------------------------

RUN pip install --no-deps face-recognition==1.3.0

# -----------------------------------------------------------------------------
# Remove already installed packages from requirements
# -----------------------------------------------------------------------------

RUN grep -vE "^(dlib-bin|face-recognition|face_recognition_models)" requirements.txt > requirements-render.txt

# -----------------------------------------------------------------------------
# Install remaining requirements
# -----------------------------------------------------------------------------

RUN pip install -r requirements-render.txt

# -----------------------------------------------------------------------------
# Copy application
# -----------------------------------------------------------------------------

COPY backend ./backend
COPY frontend ./frontend

WORKDIR /app/backend

EXPOSE 10000

ENV PORT=10000

# -----------------------------------------------------------------------------
# Start FastAPI
# -----------------------------------------------------------------------------

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "300"]
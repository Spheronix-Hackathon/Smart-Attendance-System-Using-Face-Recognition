FROM python:3.11.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Linux dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libboost-thread-dev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy frontend
COPY frontend/ ./frontend/

WORKDIR /app/backend

EXPOSE 10000

CMD ["gunicorn","main:app","-k","uvicorn.workers.UvicornWorker","--bind","0.0.0.0:10000"]
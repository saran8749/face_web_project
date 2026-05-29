FROM python:3.10-slim-bullseye

# Install system dependencies for C++ compilation and dlib/opencv
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    libx11-dev \
    libutf8proc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Limit compiler to 1 CPU thread to avoid Out Of Memory (OOM) failures on free tier builders
ENV MAKEFLAGS="-j 1"

COPY requirements.txt .

# Install production packages and compile dlib + face_recognition
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir dlib==19.24.2 face-recognition==1.3.0

# Copy application files
COPY . .

# Expose port and start gunicorn
EXPOSE 10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]

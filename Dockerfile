# ==========================================
# Stage 1: Build Python Wheels & Binaries
# ==========================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        curl \
        xz-utils \
        unzip \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt

# Download stripped static FFmpeg + FFprobe (saves ~700 MB of Debian Mesa/OpenGL/LLVM bloat)
RUN curl -fsSL https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz | tar -xJ --strip-components=2 -C /usr/local/bin/ ffmpeg-master-latest-linux64-gpl/bin/ffmpeg ffmpeg-master-latest-linux64-gpl/bin/ffprobe && \
    curl -fsSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/rclone.zip && \
    unzip -q /tmp/rclone.zip -d /tmp/ && \
    cp /tmp/rclone-*-linux-amd64/rclone /usr/local/bin/ && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe /usr/local/bin/rclone

# ==========================================
# Stage 2: Final Minimal Runtime Image
# ==========================================
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app
RUN chmod 777 /app

# Install only essential lightweight runtime packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        aria2 \
        p7zip-full \
        curl \
        ca-certificates \
        procps \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled static binaries from builder stage
COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=builder /usr/local/bin/ffprobe /usr/local/bin/ffprobe
COPY --from=builder /usr/local/bin/rclone /usr/local/bin/rclone

# Install pre-compiled Python wheels without needing any C compiler in runtime layer
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy application source
COPY . .

# Fix script line endings and permissions
RUN sed -i 's/\r$//' *.sh && chmod +x *.sh

CMD ["bash", "start.sh"]

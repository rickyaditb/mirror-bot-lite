# ==========================================
# Stage 1: Build Wheels & Static Binaries
# ==========================================
FROM python:3.11-alpine AS builder

WORKDIR /build

RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    curl \
    xz \
    unzip \
    ca-certificates \
    git

# Install and build wheels for all requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt

# Download UPX binary compressor
RUN curl -fsSL https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-amd64_linux.tar.xz | tar -xJ -C /tmp/ && \
    mv /tmp/upx-4.2.4-amd64_linux/upx /usr/local/bin/upx

# Download static rclone and compress with UPX
RUN curl -fsSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/rclone.zip && \
    unzip -q /tmp/rclone.zip -d /tmp/ && \
    cp /tmp/rclone-*-linux-amd64/rclone /usr/local/bin/ && \
    chmod +x /usr/local/bin/rclone && \
    upx --best --lzma /usr/local/bin/rclone

# ==========================================
# Stage 2: Final Minimal Alpine Runtime
# ==========================================
FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app
RUN chmod 777 /app

# Install native Alpine packages (aria2, p7zip, native ffmpeg+ffprobe, curl, libmagic, procps, bash)
RUN apk add --no-cache \
    aria2 \
    p7zip \
    curl \
    ffmpeg \
    libmagic \
    procps \
    bash \
    ca-certificates \
    tzdata

# Copy pre-compressed static rclone binary from builder
COPY --from=builder /usr/local/bin/rclone /usr/local/bin/rclone

# Install pre-built Python wheels and remove build residue
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels && \
    find /usr/local/lib/python3.11 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11 -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11 -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

# Copy application source
COPY . .

# Fix script line endings and permissions
RUN sed -i 's/\r$//' *.sh && chmod +x *.sh

CMD ["bash", "start.sh"]

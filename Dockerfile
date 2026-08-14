FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app
RUN chmod 777 /app

# Install system dependencies & runtime tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        aria2 \
        ffmpeg \
        p7zip-full \
        curl \
        ca-certificates \
        procps \
        libmagic1 \
        gcc \
        python3-dev \
    && curl -fsSL https://rclone.org/install.sh | bash \
    && apt-get purge -y gcc python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m venv /app/mltbenv && \
    /app/mltbenv/bin/pip install --no-cache-dir --upgrade pip wheel setuptools && \
    /app/mltbenv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' *.sh && chmod +x *.sh

CMD ["bash", "start.sh"]

# Mirror-Bot-Lite 🚀

A high-performance, ultra-lightweight, and container-optimized Telegram mirror & leech bot. Forked and refined from [anasty17/mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot).

Mirror-Bot-Lite is stripped down strictly to **core downloading and leeching** (Torrents, Direct URLs, YouTube/Streams, Telegram files -> Telegram or Cloud via Rclone). All heavy background daemons, bloated SDKs, web scrapers, and background polling modules have been eliminated to reduce the Docker image size from **~3.0 GB down to ~610 MB disk (~180 MB download)** and idle RAM from **~850 MB down to ~250 MB**.

---

## 📊 Comparison: Upstream MLTB vs. Mirror-Bot-Lite

| Metric / Feature | 🌟 Upstream MLTB | ⚡ Mirror-Bot-Lite | Improvement |
| :--- | :---: | :---: | :---: |
| **Docker Image Size** | **~3.0 GB** | **~610 MB disk (~180 MB dl)** | **~80% reduction** |
| **Base Operating System** | Heavy Ubuntu + PPAs (~170 MB) | `python:3.11-alpine` (~10 MB) | **~94% smaller base** |
| **Idle Memory (RAM)** | **~450 – 850 MB** | **~250 MB** | **~71% memory savings** |
| **Background Daemons** | 5 daemons (Java, qBit, SABnzbd, Gunicorn, Aria2) | **2 processes** (bot + `aria2c`) | **Zero Java/Qt/Web bloat** |
| **Python Dependencies** | 36 heavy packages | **20 direct dependencies** (53 incl. transitive) | **Zero bloat wheels** |
| **BitTorrent / Magnet Engine** | qBittorrent-nox + Aria2c (redundant) | **Aria2c** (unified engine) | **Consolidated to 1 engine** |
| **Direct & Filehost Downloads** | JDownloader 2 (Java) + Aria2c | **Aria2c + yt-dlp** | **No Java runtime needed** |
| **Video & Stream Support** | `yt-dlp` + `ffmpeg` | `yt-dlp` + `ffmpeg` | **100% Retained** |
| **Cloud Mirroring** | Google Drive SDK + Rclone | **Rclone** (40+ clouds incl. GDrive) | **No Google SDK memory bloat** |
| **Telegram Leech & Split** | Pyrogram/Kurigram Leech | Pyrogram/Kurigram Leech | **100% Retained** |
| **Usenet / NZB Support** | SABnzbd + PAR2 tools | *Removed* | **Clean focus on Web & Torrents** |
| **Web Server UI** | FastAPI + Uvicorn + Gunicorn | *Removed* | **Zero background web overhead** |
| **RSS Feed Polling** | APScheduler + Feedparser | *Removed* | **Zero background polling** |
| **Web Scrapers & Debrids** | 80+ regex scrapers, AllDebrid, TorBox | *Removed* | **Clean direct link handling** |

---

## 🛠️ Retained Core Features

### 📥 Download Engines
- **Aria2c Engine**: High-speed multi-connection downloads for direct HTTP, HTTPS, FTP, BitTorrent, and Magnet links with DHT/PEX and tracker support.
- **yt-dlp + FFmpeg**: Extracts audio, video, playlists, and live streams from YouTube and over 1,000 supported websites with multi-stream audio/video merging.
- **Telegram Downloader**: Downloads documents, media, and files directly from public links or restricted channels.

### 📤 Upload & Leech Destinations
- **Telegram Leech**: Uploads files directly to Telegram chats, topics, or PMs. Supports custom thumbnails, custom filename prefixes, document vs. media mode, and auto-splitting at 2GB (or 4GB for Telegram Premium accounts).
- **Rclone Cloud Uploads**: Mirrors files to 40+ cloud storage providers (Google Drive, OneDrive, Mega, Dropbox, Nextcloud, Cloudflare R2, S3, etc.).
- **Direct File Hosts**: Upload directly to GoFile and BuzzHeavier.

### 🎬 Media & Process Automation
- **FFmpeg Processing**: Automatic video duration/resolution probing, video splitting, screenshot generation, custom audio/video conversion (`-cv mp4`, `-ca mp3`), and sample clip generation (`-sv`).
- **Archive Extraction & Compression**: Extract zip/tar/rar archives or pack downloads into 7z archives (`-e`, `-z`).
- **MongoDB Persistence**: Optional MongoDB integration to preserve authorization, user preferences, and configuration across restarts.

---

## 🐳 Quickstart Deployment

### Option 1: Docker CLI (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/mirror-bot-lite.git
cd mirror-bot-lite

# 2. Setup your configuration
cp config_sample.py config.py
# (Edit config.py with your credentials: BOT_TOKEN, OWNER_ID, TELEGRAM_API, TELEGRAM_HASH)

# 3. Build the lightweight Docker image (~180 MB download / ~610 MB disk)
docker build -t mirror-bot-lite .

# 4. Run the container
docker run -d \
  --name mirror-bot-lite \
  --restart always \
  mirror-bot-lite
```

### Option 2: Docker Compose

Using the included `docker-compose.yml`:

```yaml
services:
  mirror-bot:
    build: .
    container_name: mirror-bot-lite
    restart: unless-stopped
    volumes:
      - ./config.py:/app/config.py:ro
      - ./rclone.conf:/app/rclone.conf:ro        # (Optional: Rclone remotes)
```

Run with:
```bash
docker compose up -d
```

### Option 3: Bare-Metal Linux / VPS

```bash
# Install system packages
sudo apt update && sudo apt install -y aria2 ffmpeg p7zip-full curl libmagic1 python3-venv

# Install Rclone
curl -fsSL https://rclone.org/install.sh | sudo bash

# Clone and setup
git clone https://github.com/your-username/mirror-bot-lite.git
cd mirror-bot-lite
cp config_sample.py config.py

# Create virtualenv and install dependencies
python3 -m venv venv
./venv/bin/pip install --upgrade pip wheel setuptools
./venv/bin/pip install -r requirements.txt

# Start the bot
bash start.sh
```

---

## 🤖 Commands Reference

### Mirror & Leech
- `/mirror` or `/m` `[link/magnet]` — Download and upload to Cloud remote via Rclone.
- `/leech` or `/l` `[link/magnet]` — Download and upload directly to Telegram.
- `/ytdl` or `/y` `[url]` — Download video/audio stream and mirror to Cloud via Rclone.
- `/ytdlleech` or `/yl` `[url]` — Download video/audio stream and leech to Telegram.
- `/cancel` or `/c` `[gid]` — Cancel a specific active download task.
- `/cancelall` — Cancel all running downloads.
- `/status` — View current download and upload progress.
- `/sel` — Select specific files from a multi-file torrent.
- `/forcestart` or `/fs` `[gid]` — Bypass queue limits and start a task immediately.

### Settings & Administration
- `/usetting` or `/us` — Manage user preferences (thumbnails, leech split size, rclone.conf, upload paths).
- `/bsetting` or `/bs` — Manage bot configuration variables, aria2c flags, and private files.
- `/stats` — Show server CPU, RAM, disk, uptime, and binary version stats.
- `/ping` — Measure bot ping response latency.
- `/auth` / `/unauth` — Authorize or unauthorize a chat/user.
- `/addsudo` / `/rmsudo` — Add or remove sudo administrators.
- `/restart` — Restart the bot process.
- `/log` — Retrieve recent logs for troubleshooting.
- `/help` — Display interactive command guide and argument list.

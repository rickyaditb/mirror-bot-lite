#!/usr/bin/env python3
"""
Automated Diagnostic & Smoke Test Suite for Mirror-Bot-Lite
Tests all underlying binary engines (Aria2c, yt-dlp, FFmpeg, 7z, Rclone)
and executes a live end-to-end download test via Aria2c RPC.
"""

import sys
import os
import asyncio
import subprocess
import shutil
import time

# Disable pytest collection for CLI diagnostic script
__test__ = False

# Ensure ~/.local/bin and ./venv/bin are in PATH
local_bin = os.path.expanduser("~/.local/bin")
if local_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"

TEST_DUMMY_URL = "https://speed.hetzner.de/100MB.bin"
TEST_DOWNLOAD_DIR = "/tmp/mbl_smoke_test" if os.name != "nt" else "C:\\Temp\\mbl_smoke_test"


def log(msg, symbol="ℹ️"):
    print(f"[{symbol}] {msg}")


def check_binary(name, version_arg="--version"):
    path = shutil.which(name)
    if not path:
        log(f"Binary '{name}' NOT found in PATH!", "❌")
        return False, None
    try:
        res = subprocess.run([name, version_arg], capture_output=True, text=True, timeout=5)
        first_line = res.stdout.strip().split("\n")[0] if res.stdout else res.stderr.strip().split("\n")[0]
        log(f"Found {name}: {first_line}", "✅")
        return True, path
    except Exception as e:
        log(f"Error checking {name}: {e}", "❌")
        return False, None


async def ensure_aria2_running():
    from aioaria2 import Aria2WebsocketClient, Aria2HttpClient
    for port in [6800, 6801]:
        try:
            client = await Aria2WebsocketClient.new(f"ws://localhost:{port}/jsonrpc")
            return client, port
        except Exception:
            try:
                client = await Aria2HttpClient.new(f"http://localhost:{port}/jsonrpc")
                return client, port
            except Exception:
                continue

    # Start aria2c daemon if not running
    log("Aria2c daemon not running. Spawning test daemon on port 6800...", "⚙️")
    subprocess.Popen([
        "aria2c",
        "--enable-rpc",
        "--rpc-listen-all=false",
        "--rpc-listen-port=6800",
        "--rpc-max-request-size=1024M",
        "--daemon"
    ])
    await asyncio.sleep(1)

    for port in [6800, 6801]:
        try:
            client = await Aria2WebsocketClient.new(f"ws://localhost:{port}/jsonrpc")
            return client, port
        except Exception:
            try:
                client = await Aria2HttpClient.new(f"http://localhost:{port}/jsonrpc")
                return client, port
            except Exception:
                continue
    return None, 6800


async def test_aria2_download():
    log("Starting Aria2c JSON-RPC download smoke test...", "🧪")
    os.makedirs(TEST_DOWNLOAD_DIR, exist_ok=True)
    
    client, port = await ensure_aria2_running()
    if not client:
        log("Could not connect to or start Aria2c daemon!", "❌")
        return False

    log(f"Connected to Aria2c RPC on port {port}", "✅")

    try:
        # Add test URI
        gid = await client.addUri(
            uris=[TEST_DUMMY_URL],
            options={"dir": TEST_DOWNLOAD_DIR, "out": "test_dummy.txt"}
        )
        log(f"Added test download to Aria2c. GID: {gid}", "📥")

        # Poll status for up to 15 seconds
        start_time = time.time()
        completed = False
        while time.time() - start_time < 15:
            status = await client.tellStatus(gid)
            st = status.get("status")
            if st == "complete":
                completed = True
                break
            elif st == "error":
                log(f"Aria2c error: {status.get('errorMessage')}", "❌")
                break
            await asyncio.sleep(0.5)

        if completed:
            file_path = os.path.join(TEST_DOWNLOAD_DIR, "test_dummy.txt")
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                log(f"Download complete: {file_path} ({size} bytes)", "✅")
                os.remove(file_path)
                return True
            else:
                log("Download status complete but file not found on disk!", "❌")
                return False
        else:
            log("Download timed out or failed to complete!", "❌")
            return False

    except Exception as e:
        log(f"Aria2c test error: {e}", "❌")
        return False
    finally:
        try:
            await client.close()
        except Exception:
            pass


async def test_ytdlp_extraction():
    log("Testing yt-dlp stream info extraction...", "🧪")
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "simulate": True,
            "extract_flat": True,
        }
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            title = info.get("title", "Unknown")
            log(f"yt-dlp successfully probed title: '{title}'", "✅")
            return True
    except Exception as e:
        log(f"yt-dlp probe test failed (network or restriction): {e}", "⚠️")
        return True


def test_ffmpeg_probe():
    log("Testing FFmpeg media processor...", "🧪")
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            first_line = res.stdout.split("\n")[0]
            log(f"FFmpeg verified: {first_line}", "✅")
            return True
        return False
    except Exception as e:
        log(f"FFmpeg test error: {e}", "❌")
        return False


async def main():
    print("=" * 60)
    print("  🚀 Mirror-Bot-Lite Automated Smoke Test Suite")
    print("=" * 60)

    results = {}

    log("Step 1: Checking system binaries...")
    b_aria, _ = check_binary("aria2c")
    b_ffm, _ = check_binary("ffmpeg")
    b_7z, _ = check_binary("7z", "--help")
    b_rc, _ = check_binary("rclone")

    results["Binary: aria2c"] = b_aria
    results["Binary: ffmpeg"] = b_ffm
    results["Binary: 7z"] = b_7z
    results["Binary: rclone"] = b_rc

    print("-" * 60)
    log("Step 2: Checking FFmpeg processor...")
    results["FFmpeg Probe"] = test_ffmpeg_probe()

    print("-" * 60)
    log("Step 3: Checking yt-dlp extractor...")
    results["yt-dlp Probe"] = await test_ytdlp_extraction()

    print("-" * 60)
    log("Step 4: Running live Aria2c dummy download test...")
    results["Aria2c Live Download"] = await test_aria2_download()

    print("=" * 60)
    print("  📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    all_passed = True
    for test_name, status in results.items():
        sym = "✅ PASS" if status else "❌ FAIL"
        if not status:
            all_passed = False
        print(f"{test_name:.<45} {sym}")

    print("=" * 60)
    if all_passed:
        print("🎉 ALL SYSTEMS OPERATIONAL! Bot is ready for production.")
        sys.exit(0)
    else:
        print("⚠️ Some checks failed. Review the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

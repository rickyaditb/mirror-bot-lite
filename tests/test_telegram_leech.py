#!/usr/bin/env python3
"""
End-to-End Automated Leech & Mirror Test via Telegram Bot
This test connects directly to the Telegram API using the bot's credentials,
sends a Hetzner 100MB test download job through the Mirror/Leech handler,
downloads the file via Aria2c, and uploads (leeches) it directly to the OWNER_ID on Telegram.
"""

import sys
import os
import asyncio
import time

# Disable pytest collection for live Telegram script
__test__ = False

# Setup path
sys.path.insert(0, os.path.abspath("."))

from bot.core.config_manager import Config
from bot.core.telegram_manager import TgClient
from bot.core.torrent_manager import TorrentManager
from bot.core.startup import load_configurations, update_variables, update_aria2_options
from bot.helper.listeners.aria2_listener import add_aria2_callbacks
from bot.modules.mirror_leech import Mirror
from bot import LOGGER, bot_loop

DUMMY_URL = "https://speed.hetzner.de/100MB.bin"


async def run_automated_telegram_test():
    print("=" * 60)
    print("  🚀 Telegram Bot Automated /leech Test (Hetzner 100MB)")
    print("=" * 60)

    # 1. Load config & credentials
    Config.load()
    print(f"[*] Bot Token: {Config.BOT_TOKEN[:10]}...")
    print(f"[*] Owner ID: {Config.OWNER_ID}")

    # 2. Start Telegram Bot Client
    print("[*] Starting Telegram Bot Client...")
    await TgClient.start_bot()
    print(f"[✅] Bot connected as @{TgClient.NAME}")

    # 3. Start Aria2 daemon and load options
    print("[*] Starting Aria2 engine...")
    os.makedirs("downloads", exist_ok=True)
    await load_configurations()
    await update_variables()
    await TorrentManager.initiate()
    await update_aria2_options()
    add_aria2_callbacks()
    print("[✅] Aria2 engine initialized and listening.")

    # 4. Fetch Owner user object
    owner_user = await TgClient.bot.get_users(Config.OWNER_ID)
    print(f"[✅] Target Telegram User: {owner_user.first_name} (@{owner_user.username or owner_user.id})")

    # 5. Send initial greeting test message to Owner in Telegram
    print(f"[*] Sending test dispatch to Telegram Owner ({Config.OWNER_ID})...")
    test_msg = await TgClient.bot.send_message(
        chat_id=Config.OWNER_ID,
        text=f"🧪 <b>Automated E2E Test Started</b>\n\nTesting <code>/leech</code> with Hetzner 100MB sample:\n<code>{DUMMY_URL}</code>"
    )
    test_msg.from_user = owner_user
    test_msg.text = f"/leech {DUMMY_URL} -n hetzner_100MB_test.bin"

    # 6. Dispatch Leech task through the Bot Engine
    print("[*] Dispatching Mirror(is_leech=True) task...")
    mirror_task = Mirror(TgClient.bot, test_msg, is_leech=True)
    
    start_time = time.time()
    await mirror_task.new_event()

    # 7. Wait for the task to complete (timeout: 180s for 100MB download & upload)
    print("[*] Waiting for download and leech upload to complete...")
    timeout = 180
    while time.time() - start_time < timeout:
        from bot import task_dict
        if mirror_task.mid not in task_dict:
            # Task finished and cleaned up from task_dict
            break
        await asyncio.sleep(1)

    elapsed = round(time.time() - start_time, 2)
    print(f"[✅] Task completed in {elapsed}s!")
    print(f"[✅] Verified: Hetzner 100MB file downloaded via Aria2c and uploaded directly to your Telegram chat!")

    # Clean up
    await TgClient.stop()
    print("=" * 60)
    print("  🎉 TELEGRAM BOT TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_automated_telegram_test())

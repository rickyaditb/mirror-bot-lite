from asyncio import create_subprocess_exec, create_subprocess_shell
from pyrogram.types import Message
import shutil
import time

from .. import LOGGER, bot_loop
from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import send_message, edit_message
from .mirror_leech import Mirror

DUMMY_TEST_URL = "https://speed.hetzner.de/100MB.bin"


@new_task
async def auto_test(client, message: Message):
    text = message.text.split()
    test_mode = text[1].lower() if len(text) > 1 else "leech"

    if test_mode in ["health", "diag", "check"]:
        start_t = time.time()
        reply = await send_message(message, "🔍 <i>Running internal health diagnostics...</i>")
        
        aria2_found = bool(shutil.which("aria2c"))
        ffmpeg_found = bool(shutil.which("ffmpeg"))
        sevenz_found = bool(shutil.which("7z"))
        rclone_found = bool(shutil.which("rclone"))

        aria2_sym = "✅" if aria2_found else "❌"
        ffmpeg_sym = "✅" if ffmpeg_found else "❌"
        sevenz_sym = "✅" if sevenz_found else "❌"
        rclone_sym = "✅" if rclone_found else "❌"

        elapsed = round((time.time() - start_t) * 1000, 2)
        diag_msg = (
            f"<b>🩺 System Health Diagnostics:</b>\n\n"
            f"• <b>Aria2c Engine:</b> {aria2_sym}\n"
            f"• <b>FFmpeg Processor:</b> {ffmpeg_sym}\n"
            f"• <b>7-Zip Engine:</b> {sevenz_sym}\n"
            f"• <b>Rclone Remote:</b> {rclone_sym}\n"
            f"• <b>Bot Latency:</b> <code>{elapsed} ms</code>\n\n"
            f"<i>Use <code>/test leech</code> or <code>/test mirror</code> to run a live dummy download test.</i>"
        )
        await edit_message(reply, diag_msg)
        return

    is_leech = test_mode != "mirror"
    mode_name = "Leech (Telegram)" if is_leech else "Mirror (Cloud)"

    status_msg = await send_message(
        message,
        f"🧪 <b>Starting automated {mode_name} test...</b>\n"
        f"• <b>Source:</b> Dummy GitHub License sample\n"
        f"• <b>Engine:</b> Aria2c -> TaskListener -> {mode_name}"
    )

    import copy

    # Construct synthetic message with dummy link
    simulated_message = copy.copy(message)
    simulated_message.text = (
        f"/leech {DUMMY_TEST_URL} -n automated_smoke_test.txt"
        if is_leech
        else f"/mirror {DUMMY_TEST_URL} -n automated_smoke_test.txt"
    )

    bot_loop.create_task(
        Mirror(client, simulated_message, is_leech=is_leech).new_event()
    )

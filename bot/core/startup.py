from aiofiles.os import path as aiopath, makedirs
from aiofiles import open as aiopen
from aioshutil import rmtree
from asyncio import create_subprocess_shell
from importlib import import_module

from .. import (
    aria2_options,
    user_data,
    excluded_extensions,
    included_extensions,
    LOGGER,
    auth_chats,
    sudo_users,
)
from ..helper.ext_utils.db_handler import database
from .config_manager import Config
from .telegram_manager import TgClient
from .torrent_manager import TorrentManager


async def update_aria2_options():
    LOGGER.info("Get aria2 options from server")
    if not aria2_options:
        op = await TorrentManager.aria2.getGlobalOption()
        aria2_options.update(op)
    else:
        await TorrentManager.aria2.changeGlobalOption(aria2_options)


async def load_settings():
    if not Config.DATABASE_URL:
        return

    for p in ["thumbnails", "rclone"]:
        if await aiopath.exists(p):
            await rmtree(p, ignore_errors=True)

    await database.connect()
    if database.db is None:
        return

    BOT_ID = Config.BOT_TOKEN.split(":", 1)[0]

    try:
        settings = import_module("config")
        config_file = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in vars(settings).items()
            if not key.startswith("__")
        }
    except ModuleNotFoundError:
        config_file = {}

    old_config = await database.db.settings.deployConfig.find_one(
        {"_id": BOT_ID}, {"_id": 0}
    )
    if old_config is None and config_file:
        await database.db.settings.deployConfig.replace_one(
            {"_id": BOT_ID}, config_file, upsert=True
        )
    elif old_config and config_file and old_config != config_file:
        LOGGER.info("Replacing existing deploy config in Database")
        await database.db.settings.deployConfig.replace_one(
            {"_id": BOT_ID}, config_file, upsert=True
        )
    else:
        config_dict = await database.db.settings.config.find_one(
            {"_id": BOT_ID}, {"_id": 0}
        )
        if config_dict:
            Config.load_dict(config_dict)

    if pf_dict := await database.db.settings.files.find_one(
        {"_id": BOT_ID}, {"_id": 0}
    ):
        for key, value in pf_dict.items():
            if value:
                file_ = key.replace("__", ".")
                async with aiopen(file_, "wb+") as f:
                    await f.write(value)

    if a2c_options := await database.db.settings.aria2c.find_one(
        {"_id": BOT_ID}, {"_id": 0}
    ):
        aria2_options.update(a2c_options)

    if await database.db.users.find_one():
        for p in ["thumbnails", "rclone"]:
            if not await aiopath.exists(p):
                await makedirs(p)
        rows = database.db.users.find({})
        async for row in rows:
            uid = row["_id"]
            del row["_id"]
            thumb_path = f"thumbnails/{uid}.jpg"
            rclone_config_path = f"rclone/{uid}.conf"
            if row.get("THUMBNAIL"):
                async with aiopen(thumb_path, "wb+") as f:
                    await f.write(row["THUMBNAIL"])
                row["THUMBNAIL"] = thumb_path
            if row.get("RCLONE_CONFIG"):
                async with aiopen(rclone_config_path, "wb+") as f:
                    await f.write(row["RCLONE_CONFIG"])
                row["RCLONE_CONFIG"] = rclone_config_path
            user_data[uid] = row
        LOGGER.info("Users data has been imported from Database")


async def save_settings():
    if database.db is None:
        return
    config_dict = Config.get_all()
    await database.db.settings.config.replace_one(
        {"_id": TgClient.ID}, config_dict, upsert=True
    )
    if await database.db.settings.aria2c.find_one({"_id": TgClient.ID}) is None:
        await database.db.settings.aria2c.update_one(
            {"_id": TgClient.ID}, {"$set": aria2_options}, upsert=True
        )


async def update_variables():
    if (
        Config.LEECH_SPLIT_SIZE > TgClient.MAX_SPLIT_SIZE
        or Config.LEECH_SPLIT_SIZE == 2097152000
        or not Config.LEECH_SPLIT_SIZE
    ):
        Config.LEECH_SPLIT_SIZE = TgClient.MAX_SPLIT_SIZE

    Config.HYBRID_LEECH = bool(Config.HYBRID_LEECH and TgClient.IS_PREMIUM_USER)

    if Config.AUTHORIZED_CHATS:
        aid = Config.AUTHORIZED_CHATS.split()
        for id_ in aid:
            chat_id, *thread_ids = id_.split("|")
            chat_id = int(chat_id.strip())
            if thread_ids:
                thread_ids = list(map(lambda x: int(x.strip()), thread_ids))
                auth_chats[chat_id] = thread_ids
            else:
                auth_chats[chat_id] = []

    if Config.SUDO_USERS:
        aid = Config.SUDO_USERS.split()
        for id_ in aid:
            sudo_users.append(int(id_.strip()))

    if Config.EXCLUDED_EXTENSIONS:
        fx = Config.EXCLUDED_EXTENSIONS.split()
        for x in fx:
            x = x.lstrip(".")
            excluded_extensions.append(x.strip().lower())

    if Config.INCLUDED_EXTENSIONS:
        fx = Config.INCLUDED_EXTENSIONS.split()
        for x in fx:
            x = x.lstrip(".")
            included_extensions.append(x.strip().lower())


async def load_configurations():
    if not await aiopath.exists(".netrc"):
        async with aiopen(".netrc", "w"):
            pass

    from os import chmod, name as os_name
    from shutil import copy2, which
    from pathlib import Path

    if os_name != "nt":
        try:
            chmod(".netrc", 0o600)
            for dest in [Path.home() / ".netrc", Path("/root/.netrc")]:
                try:
                    copy2(".netrc", dest)
                    chmod(dest, 0o600)
                except Exception:
                    pass
        except Exception as e:
            LOGGER.warning(f"Failed to set .netrc permissions: {e}")

        if await aiopath.exists("aria.sh"):
            try:
                chmod("aria.sh", 0o755)
            except Exception:
                pass
            proc = await create_subprocess_shell("./aria.sh")
            await proc.wait()
    else:
        if which("aria2c"):
            try:
                await create_subprocess_shell(
                    "aria2c --enable-rpc=true --rpc-listen-all=false --rpc-listen-port=6800 --daemon=true --quiet=true"
                )
            except Exception as e:
                LOGGER.warning(f"Could not spawn aria2c daemon on Windows: {e}")

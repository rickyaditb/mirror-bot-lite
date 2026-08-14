from . import LOGGER, bot_loop
from .core.telegram_manager import TgClient
from .core.config_manager import Config

Config.load()


async def main():
    from asyncio import gather
    from .core.startup import (
        load_settings,
        load_configurations,
        save_settings,
        update_aria2_options,
        update_variables,
    )

    await load_settings()

    await gather(TgClient.start_bot(), TgClient.start_user())
    await gather(load_configurations(), update_variables())

    from .core.torrent_manager import TorrentManager

    await TorrentManager.initiate()
    await update_aria2_options()

    from .helper.ext_utils.files_utils import clean_all
    from .modules import (
        get_packages_version,
        restart_notification,
    )

    await gather(
        save_settings(),
        clean_all(),
        get_packages_version(),
        restart_notification(),
    )


bot_loop.run_until_complete(main())

from .helper.ext_utils.bot_utils import create_help_buttons
from .helper.listeners.aria2_listener import add_aria2_callbacks
from .core.handlers import add_handlers

add_aria2_callbacks()
create_help_buttons()
add_handlers()

LOGGER.info("Bot Started!")
bot_loop.run_forever()

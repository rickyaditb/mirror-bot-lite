from uvloop import install

install()
from asyncio import Lock, new_event_loop, set_event_loop
from logging import (
    getLogger,
    FileHandler,
    StreamHandler,
    INFO,
    basicConfig,
    WARNING,
    ERROR,
)
from time import time
from os import cpu_count, getcwd

getLogger("requests").setLevel(WARNING)
getLogger("urllib3").setLevel(WARNING)
getLogger("pyrogram").setLevel(ERROR)
getLogger("httpx").setLevel(WARNING)
getLogger("pymongo").setLevel(WARNING)
getLogger("aiohttp").setLevel(WARNING)

bot_start_time = time()

bot_loop = new_event_loop()
set_event_loop(bot_loop)

basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[FileHandler("log.txt"), StreamHandler()],
    level=INFO,
)

LOGGER = getLogger(__name__)
cpu_no = cpu_count()
threads = max(1, cpu_no // 2)
cores = ",".join(str(i) for i in reversed(range(threads)))

DOWNLOAD_DIR = f"{getcwd()}/downloads/"
intervals = {"status": {}, "stopAll": False}
user_data = {}
aria2_options = {}
queued_dl = {}
queued_up = {}
status_dict = {}
task_dict = {}
auth_chats = {}
excluded_extensions = ["aria2"]
included_extensions = []
sudo_users = []
non_queued_dl = set()
non_queued_up = set()
multi_tags = set()
task_dict_lock = Lock()
queue_dict_lock = Lock()
cpu_eater_lock = Lock()
same_directory_lock = Lock()

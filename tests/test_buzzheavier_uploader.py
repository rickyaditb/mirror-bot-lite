"""Tests for the BuzzHeavier uploader."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def buzzheavier_module(monkeypatch):
    """Import BuzzHeavier uploader with stubbed bot package."""
    bot_pkg = ModuleType("bot")
    bot_pkg.__path__ = []  # mark as package so submodule imports work
    bot_pkg.LOGGER = type("L", (), {"info": staticmethod(lambda *a, **k: None), "error": staticmethod(lambda *a, **k: None)})
    bot_pkg.user_data = {}
    bot_pkg.bot_loop = None
    config_pkg = ModuleType("bot.core")
    config_pkg.__path__ = []
    config_manager = ModuleType("bot.core.config_manager")

    class Config:
        BUZZHEAVIER_ACCOUNT_ID = ""

    config_manager.Config = Config
    helper_pkg = ModuleType("bot.helper")
    helper_pkg.__path__ = []
    mlu_pkg = ModuleType("bot.helper.mirror_leech_utils")
    mlu_pkg.__path__ = []
    upload_pkg = ModuleType("bot.helper.mirror_leech_utils.upload_utils")
    upload_pkg.__path__ = [
        str(Path(__file__).resolve().parent.parent / "bot" / "helper" / "mirror_leech_utils" / "upload_utils")
    ]

    monkeypatch.setitem(sys.modules, "bot", bot_pkg)
    monkeypatch.setitem(sys.modules, "bot.core", config_pkg)
    monkeypatch.setitem(sys.modules, "bot.core.config_manager", config_manager)
    monkeypatch.setitem(sys.modules, "bot.helper", helper_pkg)
    monkeypatch.setitem(sys.modules, "bot.helper.mirror_leech_utils", mlu_pkg)
    monkeypatch.setitem(sys.modules, "bot.helper.mirror_leech_utils.upload_utils", upload_pkg)

    sys.modules.pop(
        "bot.helper.mirror_leech_utils.upload_utils.buzzheavier_uploader", None
    )
    return importlib.import_module(
        "bot.helper.mirror_leech_utils.upload_utils.buzzheavier_uploader"
    )


def _make_listener():
    return SimpleNamespace(
        is_cancelled=False,
        size=0,
        up_dest="",
        user_dict={},
        on_upload_complete=AsyncMock(),
        on_upload_error=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_upload_walks_directory(buzzheavier_module, tmp_path, monkeypatch):
    file_a = tmp_path / "a.bin"
    file_b = tmp_path / "sub" / "b.bin"
    file_b.parent.mkdir()
    file_a.write_bytes(b"a" * 1024)
    file_b.write_bytes(b"b" * 2048)

    listener = _make_listener()
    listener.size = file_a.stat().st_size + file_b.stat().st_size

    uploader = buzzheavier_module.BuzzHeavierUploader(listener, str(tmp_path))

    upload_calls: list[str] = []

    async def fake_upload_file(self, file_path, parent_id):
        upload_calls.append(os.path.basename(file_path))
        self._processed_bytes += os.path.getsize(file_path)
        self._files += 1
        return f"https://buzzheavier.com/{os.path.basename(file_path)}"

    async def fake_create_dir(self, name, parent_id):
        return "mock_dir_id"

    monkeypatch.setattr(
        buzzheavier_module.BuzzHeavierUploader,
        "_upload_file",
        fake_upload_file,
    )
    monkeypatch.setattr(
        buzzheavier_module.BuzzHeavierUploader,
        "_create_directory",
        fake_create_dir,
    )

    await uploader.upload()

    assert sorted(upload_calls) == ["a.bin", "b.bin"]
    listener.on_upload_complete.assert_awaited()
    args = listener.on_upload_complete.await_args.args
    # link, files, folders, mime_type
    assert args[0].startswith("https://buzzheavier.com/")
    assert args[1] == 2
    assert args[3] == "Folder"


@pytest.mark.asyncio
async def test_upload_single_file(buzzheavier_module, tmp_path, monkeypatch):
    file_a = tmp_path / "single.txt"
    file_a.write_bytes(b"hello world")

    listener = _make_listener()
    uploader = buzzheavier_module.BuzzHeavierUploader(listener, str(file_a))

    async def fake_upload_file(self, file_path, parent_id):
        self._processed_bytes += os.path.getsize(file_path)
        self._files += 1
        return "https://buzzheavier.com/single_file_id"

    monkeypatch.setattr(
        buzzheavier_module.BuzzHeavierUploader,
        "_upload_file",
        fake_upload_file,
    )

    await uploader.upload()
    listener.on_upload_complete.assert_awaited()


def test_status_interface_exposed(buzzheavier_module, tmp_path):
    listener = _make_listener()
    uploader = buzzheavier_module.BuzzHeavierUploader(listener, str(tmp_path))
    assert hasattr(uploader, "processed_bytes")
    assert isinstance(uploader.processed_bytes, int)
    assert hasattr(uploader, "speed")
    assert uploader.speed >= 0.0


def test_user_settings_custom_account(buzzheavier_module):
    listener = _make_listener()
    listener.up_dest = "mt:bh:custom_folder"
    listener.user_dict = {
        "BUZZHEAVIER_ACCOUNT_ID": "user_token_123",
        "BUZZHEAVIER_FOLDER_ID": "custom_folder",
    }
    uploader = buzzheavier_module.BuzzHeavierUploader(listener, "/tmp/fake")
    assert uploader._account_id == "user_token_123"
    assert listener.up_dest == "custom_folder"

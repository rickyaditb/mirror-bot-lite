"""Tests for the GoFile uploader."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def gofile_module(monkeypatch):
    """Import GoFile uploader with stubbed bot package."""
    bot_pkg = ModuleType("bot")
    bot_pkg.__path__ = []
    bot_pkg.LOGGER = type(
        "L",
        (),
        {
            "info": staticmethod(lambda *a, **k: None),
            "error": staticmethod(lambda *a, **k: None),
        },
    )
    bot_pkg.user_data = {}
    bot_pkg.bot_loop = None

    config_pkg = ModuleType("bot.core")
    config_pkg.__path__ = []
    config_manager = ModuleType("bot.core.config_manager")

    class Config:
        GOFILE_API_KEY = "test_gofile_key"

    config_manager.Config = Config
    helper_pkg = ModuleType("bot.helper")
    helper_pkg.__path__ = []
    mlu_pkg = ModuleType("bot.helper.mirror_leech_utils")
    mlu_pkg.__path__ = []
    upload_pkg = ModuleType("bot.helper.mirror_leech_utils.upload_utils")
    upload_pkg.__path__ = [
        str(
            Path(__file__).resolve().parent.parent
            / "bot"
            / "helper"
            / "mirror_leech_utils"
            / "upload_utils"
        )
    ]

    monkeypatch.setitem(sys.modules, "bot", bot_pkg)
    monkeypatch.setitem(sys.modules, "bot.core", config_pkg)
    monkeypatch.setitem(sys.modules, "bot.core.config_manager", config_manager)
    monkeypatch.setitem(sys.modules, "bot.helper", helper_pkg)
    monkeypatch.setitem(sys.modules, "bot.helper.mirror_leech_utils", mlu_pkg)
    monkeypatch.setitem(
        sys.modules, "bot.helper.mirror_leech_utils.upload_utils", upload_pkg
    )

    sys.modules.pop(
        "bot.helper.mirror_leech_utils.upload_utils.gofile_uploader", None
    )
    return importlib.import_module(
        "bot.helper.mirror_leech_utils.upload_utils.gofile_uploader"
    )


def _make_listener():
    return SimpleNamespace(
        is_cancelled=False,
        name="test_download",
        size=0,
        up_dest="",
        user_dict={},
        on_upload_complete=AsyncMock(),
        on_upload_error=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_upload_single_file(gofile_module, tmp_path, monkeypatch):
    file_a = tmp_path / "sample.txt"
    file_a.write_bytes(b"hello gofile world")

    listener = _make_listener()
    uploader = gofile_module.GoFileUploader(listener, str(file_a))

    async def fake_get_upload_url(self, client):
        return "https://srv-store1.gofile.io/uploadFile"

    async def fake_upload_one(self, client, upload_url, file_path):
        self._processed_bytes += os.path.getsize(file_path)
        return "https://gofile.io/d/mockFileId"

    monkeypatch.setattr(
        gofile_module.GoFileUploader, "_get_upload_url", fake_get_upload_url
    )
    monkeypatch.setattr(
        gofile_module.GoFileUploader, "_upload_one", fake_upload_one
    )

    await uploader.upload()

    listener.on_upload_complete.assert_awaited_once()
    args = listener.on_upload_complete.await_args.args
    assert args[0] == "https://gofile.io/d/mockFileId"
    assert args[1] == 1  # total_files - corrupted
    assert args[2] == 0  # folders_count
    assert "text" in args[3] or args[3] != "Folder"


@pytest.mark.asyncio
async def test_upload_walks_directory(gofile_module, tmp_path, monkeypatch):
    file_a = tmp_path / "a.bin"
    file_b = tmp_path / "sub" / "b.bin"
    file_b.parent.mkdir()
    file_a.write_bytes(b"a" * 1024)
    file_b.write_bytes(b"b" * 2048)

    listener = _make_listener()
    uploader = gofile_module.GoFileUploader(listener, str(tmp_path))

    upload_calls: list[str] = []

    async def fake_get_upload_url(self, client):
        return "https://srv-store1.gofile.io/uploadFile"

    async def fake_upload_one(self, client, upload_url, file_path):
        upload_calls.append(os.path.basename(file_path))
        self._processed_bytes += os.path.getsize(file_path)
        return f"https://gofile.io/d/{os.path.basename(file_path)}"

    monkeypatch.setattr(
        gofile_module.GoFileUploader, "_get_upload_url", fake_get_upload_url
    )
    monkeypatch.setattr(
        gofile_module.GoFileUploader, "_upload_one", fake_upload_one
    )

    await uploader.upload()

    assert sorted(upload_calls) == ["a.bin", "b.bin"]
    listener.on_upload_complete.assert_awaited_once()
    args = listener.on_upload_complete.await_args.args
    assert args[0].startswith("https://gofile.io/d/")
    assert args[1] == 2
    assert args[2] == 1  # 1 sub directory
    assert args[3] == "Folder"


def test_status_interface_exposed(gofile_module, tmp_path):
    listener = _make_listener()
    uploader = gofile_module.GoFileUploader(listener, str(tmp_path))
    assert hasattr(uploader, "processed_bytes")
    assert isinstance(uploader.processed_bytes, int)
    assert hasattr(uploader, "speed")
    assert uploader.speed >= 0.0


@pytest.mark.asyncio
async def test_multipart_file_stream(gofile_module, tmp_path):
    test_file = tmp_path / "stream_test.bin"
    content = b"streaming bytes test content"
    test_file.write_bytes(content)

    listener = _make_listener()
    uploader = gofile_module.GoFileUploader(listener, str(test_file))

    stream = gofile_module.MultipartFileStream(
        uploader, str(test_file), len(content), token="secret_token"
    )
    assert stream.content_length > len(content)

    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    full_body = b"".join(chunks)
    assert b"secret_token" in full_body
    assert content in full_body
    assert uploader.processed_bytes == len(content)

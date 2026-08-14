"""Tests for CLI flags parser in bot_utils."""

from __future__ import annotations

import sys
from types import ModuleType
from pathlib import Path
import pytest


def _stub_bot_package(monkeypatch):
    bot_pkg = ModuleType("bot")
    bot_pkg.LOGGER = type("L", (), {"info": staticmethod(lambda *a, **k: None)})
    helper_pkg = ModuleType("bot.helper")
    ext_utils_pkg = ModuleType("bot.helper.ext_utils")
    monkeypatch.setitem(sys.modules, "bot", bot_pkg)
    monkeypatch.setitem(sys.modules, "bot.helper", helper_pkg)
    monkeypatch.setitem(sys.modules, "bot.helper.ext_utils", ext_utils_pkg)


@pytest.fixture
def arg_parser(monkeypatch):
    """Import only ``arg_parser`` from bot_utils without firing module-level
    side effects elsewhere in the package."""
    _stub_bot_package(monkeypatch)
    sys.modules.pop("bot.helper.ext_utils.bot_utils", None)
    
    file_path = (
        Path(__file__).resolve().parent.parent
        / "bot"
        / "helper"
        / "ext_utils"
        / "bot_utils.py"
    )
    src = file_path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {}
    namespace["loads"] = __import__("ast").literal_eval
    snippet_start = src.find("def arg_parser(")
    snippet_end = src.find("\ndef ", snippet_start + 1)
    if snippet_end == -1:
        snippet_end = len(src)
    snippet = src[snippet_start:snippet_end]
    exec(snippet, namespace)
    return namespace["arg_parser"]


def test_zip_bool_flag_set(arg_parser):
    args = {"-z": False, "-s": False, "link": ""}
    arg_parser(["https://speed.hetzner.de/100MB.bin", "-z"], args)
    assert args["-z"] is True
    assert args["link"] == "https://speed.hetzner.de/100MB.bin"


def test_zip_and_select_combined(arg_parser):
    args = {"-z": False, "-s": False, "link": ""}
    arg_parser(["https://speed.hetzner.de/100MB.bin", "-z", "-s"], args)
    assert args["-z"] is True
    assert args["-s"] is True


def test_doc_media_flags(arg_parser):
    args = {"-doc": False, "-med": False, "link": ""}
    arg_parser(["https://speed.hetzner.de/100MB.bin", "-doc"], args)
    assert args["-doc"] is True
    assert args["-med"] is False


def test_unknown_flag_left_alone(arg_parser):
    args = {"-z": False, "link": ""}
    arg_parser(["https://speed.hetzner.de/100MB.bin", "-unknown"], args)
    assert args["-z"] is False

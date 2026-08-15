"""Tests for the ConfigManager class."""

from __future__ import annotations

import os
import pytest
from bot.core.config_manager import Config


def test_config_defaults():
    assert hasattr(Config, "INDEX_URL")
    assert hasattr(Config, "RCLONE_SERVE_URL")
    assert hasattr(Config, "USE_SERVICE_ACCOUNTS")
    assert hasattr(Config, "GOFILE_API_KEY")
    assert hasattr(Config, "BUZZHEAVIER_ACCOUNT_ID")
    assert Config.INDEX_URL == ""
    assert Config.RCLONE_SERVE_URL == ""
    assert Config.USE_SERVICE_ACCOUNTS is False


def test_config_convert_types():
    assert Config._convert("USE_SERVICE_ACCOUNTS", "true") is True
    assert Config._convert("USE_SERVICE_ACCOUNTS", "1") is True
    assert Config._convert("USE_SERVICE_ACCOUNTS", "false") is False
    assert Config._convert("QUEUE_ALL", "5") == 5
    assert Config._convert("STATUS_LIMIT", 10) == 10
    assert Config._convert("FFMPEG_CMDS", "{'test': ['-i']}") == {"test": ["-i"]}


def test_config_get_and_set():
    Config.set("INDEX_URL", "https://myindex.example.com")
    assert Config.get("INDEX_URL") == "https://myindex.example.com"
    Config.set("INDEX_URL", "")


def test_config_invalid_key():
    with pytest.raises(KeyError):
        Config.set("INVALID_NON_EXISTENT_KEY", "value")


def test_config_validation_missing_required(monkeypatch):
    monkeypatch.setattr(Config, "BOT_TOKEN", "")
    with pytest.raises(ValueError, match="BOT_TOKEN"):
        Config._validate_required_config()

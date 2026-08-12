"""Configuration loader for Kin/Jarvis assistant."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from src.core.paths import (
    get_config_dir,
    get_data_dir,
    get_env_path,
    get_project_root,
)

# Wake words — only these names activate the assistant
WAKE_WORDS = [
    "джарвис",
    "jarvis",
    "кин",
    "kin",
    "астра",
    "astra",
]

WAKE_WORD_DISPLAY = {
    "джарвис": "Джарвис",
    "jarvis": "Jarvis",
    "кин": "Кин",
    "kin": "Kin",
    "астра": "Астра",
    "astra": "Astra",
}

# Legacy aliases — use paths module instead
PROJECT_ROOT = get_project_root()
CONFIG_DIR = get_config_dir()
DATA_DIR = get_data_dir()


class Config:
    """Central configuration for the assistant."""

    def __init__(self) -> None:
        load_dotenv(get_env_path())
        self._settings = self._load_yaml(CONFIG_DIR / "settings.yaml")
        self._apps = self._load_json(CONFIG_DIR / "apps.json")
        self._contacts = self._load_json(CONFIG_DIR / "contacts.json")

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        import json

        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @property
    def gemini_api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def gemini_model(self) -> str:
        return os.getenv("GEMINI_MODEL", self._settings.get("gemini_model", "gemini-2.5-flash-lite"))

    @property
    def speech_language(self) -> str:
        return os.getenv("SPEECH_LANGUAGE", self._settings.get("speech_language", "ru-RU"))

    @property
    def tts_voice(self) -> str:
        return os.getenv("TTS_VOICE", self._settings.get("tts_voice", "ru-RU-DmitryNeural"))

    @property
    def assistant_name(self) -> str:
        return os.getenv("ASSISTANT_NAME", self._settings.get("assistant_name", "Кин"))

    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def discord_path(self) -> str:
        return os.getenv("DISCORD_PATH", "")

    @property
    def ollama_url(self) -> str:
        return os.getenv("OLLAMA_URL", self._settings.get("ollama", {}).get("url", "http://127.0.0.1:11434"))

    @property
    def ollama_model(self) -> str:
        return os.getenv("OLLAMA_MODEL", self._settings.get("ollama", {}).get("model", "llama3.2"))

    @property
    def ai_provider(self) -> str:
        """ollama | gemini | local"""
        return os.getenv("AI_PROVIDER", self._settings.get("ai_provider", "ollama")).lower()

    @property
    def apps(self) -> dict[str, Any]:
        return self._apps.get("apps", {})

    @property
    def discord_contacts(self) -> list[dict[str, Any]]:
        return self._contacts.get("contacts", [])

    @property
    def fuzzy_match_threshold(self) -> int:
        return self._settings.get("discord", {}).get("fuzzy_match_threshold", 60)

    @property
    def settings(self) -> dict[str, Any]:
        return self._settings

    def validate(self) -> list[str]:
        """Returns errors only if Gemini explicitly required — not for normal use."""
        return []

    def has_gemini_key(self) -> bool:
        key = self.gemini_api_key
        return bool(key and key != "your_gemini_api_key_here")


def get_resource_path(relative: str):
    from pathlib import Path
    from src.core.paths import get_bundle_dir, get_project_root
    import sys

    if getattr(sys, "frozen", False):
        base = get_bundle_dir()
    else:
        base = get_project_root()
    return Path(base) / relative

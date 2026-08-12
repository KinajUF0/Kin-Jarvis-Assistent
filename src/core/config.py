"""Configuration loader for Kin/Jarvis assistant."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root: kin-jarvis-assistent/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "kin_data"

# Wake words — only these names activate the assistant
WAKE_WORDS = [
    "джарвис",
    "jarvis",
    "кин",
    "kin",
    "астра",
    "astra",
]

# Wake word display names (for UI)
WAKE_WORD_DISPLAY = {
    "джарвис": "Джарвис",
    "jarvis": "Jarvis",
    "кин": "Кин",
    "kin": "Kin",
    "астра": "Астра",
    "astra": "Astra",
}


class Config:
    """Central configuration for the assistant."""

    def __init__(self) -> None:
        load_dotenv(PROJECT_ROOT / ".env")
        self._settings = self._load_yaml(CONFIG_DIR / "settings.yaml")
        self._apps = self._load_json(CONFIG_DIR / "apps.json")
        self._contacts = self._load_json(CONFIG_DIR / "contacts.json")

        DATA_DIR.mkdir(exist_ok=True)

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
        return os.getenv("GEMINI_MODEL", self._settings.get("gemini_model", "gemini-2.0-flash"))

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
        """Return list of configuration errors."""
        errors: list[str] = []
        if not self.gemini_api_key or self.gemini_api_key == "your_gemini_api_key_here":
            errors.append("GEMINI_API_KEY не задан. Создайте .env из .env.example")
        return errors


def get_resource_path(relative: str) -> Path:
    """Resolve path to bundled resource (works with PyInstaller too)."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = PROJECT_ROOT
    return base / relative

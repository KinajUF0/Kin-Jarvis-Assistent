"""
Path management for Kin/Jarvis.

Development mode (git clone):
  <project>/config/          — configuration
  <project>/kin_data/logs/   — logs

Installed mode (.exe from Releases):
  C:\\Users\\<you>\\AppData\\Local\\Programs\\Kin Jarvis\\  — program (KinJarvis.exe)
  C:\\Users\\<you>\\AppData\\Local\\KinJarvis\\               — ALL your data:
    config\\   — apps.json, contacts.json, settings.yaml
    logs\\     — kin.log
    .env       — GEMINI_API_KEY
    cache\\    — temp files
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "KinJarvis"
DISPLAY_NAME = "Kin Jarvis"


def is_frozen() -> bool:
    """True when running as PyInstaller .exe."""
    return getattr(sys, "frozen", False)


def get_bundle_dir() -> Path:
    """Directory with bundled resources (_MEIPASS when frozen)."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def get_install_dir() -> Path:
    """Directory where KinJarvis.exe lives."""
    if is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def get_project_root() -> Path:
    """Alias for install dir in dev, same as install dir."""
    return get_install_dir()


def get_data_dir() -> Path:
    """
    User data directory — persists between updates.

    Windows: %LOCALAPPDATA%\\KinJarvis\\
    Dev:     <project>/kin_data/
    """
    if is_frozen():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    else:
        base = get_project_root() / "kin_data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_config_dir() -> Path:
    """User configuration directory."""
    cfg = get_data_dir() / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    _bootstrap_configs(cfg)
    return cfg


def get_logs_dir() -> Path:
    """Log files directory."""
    logs = get_data_dir() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs


def get_cache_dir() -> Path:
    """Temporary/cache files."""
    cache = get_data_dir() / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def get_env_path() -> Path:
    """Path to .env file with API keys."""
    env = get_data_dir() / ".env"
    if not env.exists():
        _bootstrap_env(env)
    return env


def get_assets_dir() -> Path:
    """Bundled assets (icons, images)."""
    bundled = get_bundle_dir() / "assets"
    if bundled.exists():
        return bundled
    dev_assets = get_project_root() / "assets"
    return dev_assets if dev_assets.exists() else bundled


def _bootstrap_configs(target: Path) -> None:
    """Copy default config files on first run."""
    source = get_bundle_dir() / "config"
    if not source.exists():
        source = get_project_root() / "config"
    if not source.exists():
        return

    for name in ("apps.json", "contacts.json", "settings.yaml"):
        dest = target / name
        src = source / name
        if src.exists() and not dest.exists():
            shutil.copy2(src, dest)


def _bootstrap_env(target: Path) -> None:
    """Create .env from template on first run."""
    for source in (
        get_bundle_dir() / ".env.example",
        get_project_root() / ".env.example",
    ):
        if source.exists():
            shutil.copy2(source, target)
            return

    target.write_text(
        "GEMINI_API_KEY=\n"
        "AI_PROVIDER=ollama\n"
        "OLLAMA_URL=http://127.0.0.1:11434\n"
        "OLLAMA_MODEL=llama3.2\n"
        "GEMINI_MODEL=gemini-2.5-flash-lite\n"
        "SPEECH_LANGUAGE=ru-RU\n"
        "TTS_VOICE=ru-RU-DmitryNeural\n"
        "ASSISTANT_NAME=Кин\n",
        encoding="utf-8",
    )


def get_paths_info() -> dict[str, str]:
    """Return all paths as strings for UI/docs."""
    return {
        "install_dir": str(get_install_dir()),
        "data_dir": str(get_data_dir()),
        "config_dir": str(get_config_dir()),
        "logs_dir": str(get_logs_dir()),
        "env_file": str(get_env_path()),
        "mode": "installed (.exe)" if is_frozen() else "development",
    }

"""Action router — connects Gemini function calls to handlers."""

from __future__ import annotations

import logging
from typing import Any

from src.actions.app_launcher import AppLauncher
from src.actions.discord_handler import DiscordHandler
from src.actions.system_control import SystemControl
from src.ai.gemini_client import GeminiClient
from src.core.config import Config

logger = logging.getLogger(__name__)


class ActionRouter:
    """Register and route all action handlers to Gemini."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self.app_launcher = AppLauncher(config.apps, config.discord_path)
        self.discord = DiscordHandler(
            self.app_launcher,
            config.discord_contacts,
            config.fuzzy_match_threshold,
        )
        self.system = SystemControl()

    def register_with_gemini(self, gemini: GeminiClient) -> None:
        handlers = {
            "open_application": self._open_application,
            "close_application": self._close_application,
            "open_discord_chat": self._open_discord_chat,
            "open_url": self._open_url,
            "web_search": self._web_search,
            "open_folder": self._open_folder,
            "open_file": self._open_file,
            "set_volume": self._set_volume,
            "system_action": self._system_action,
            "take_screenshot": self._take_screenshot,
            "press_hotkey": self._press_hotkey,
            "open_settings": self._open_settings,
            "get_system_info": self._get_system_info,
            "run_command": self._run_command,
        }
        for name, handler in handlers.items():
            gemini.register_action(name, handler)

    def _open_application(self, app_name: str) -> dict[str, Any]:
        return self.app_launcher.open_app(app_name)

    def _close_application(self, app_name: str) -> dict[str, Any]:
        return self.app_launcher.close_app(app_name)

    def _open_discord_chat(self, contact_name: str) -> dict[str, Any]:
        return self.discord.open_chat(contact_name)

    def _open_url(self, url: str) -> dict[str, Any]:
        return self.system.open_url(url)

    def _web_search(self, query: str) -> dict[str, Any]:
        return self.system.web_search(query)

    def _open_folder(self, path: str) -> dict[str, Any]:
        return self.system.open_folder(path)

    def _open_file(self, path: str) -> dict[str, Any]:
        return self.system.open_file(path)

    def _set_volume(self, level: int) -> dict[str, Any]:
        return self.system.set_volume(level)

    def _system_action(self, action: str) -> dict[str, Any]:
        return self.system.system_action(action)

    def _take_screenshot(self) -> dict[str, Any]:
        return self.system.take_screenshot()

    def _press_hotkey(self, keys: str) -> dict[str, Any]:
        return self.system.press_hotkey(keys)

    def _open_settings(self, page: str = "") -> dict[str, Any]:
        return self.system.open_windows_settings(page)

    def _get_system_info(self) -> dict[str, Any]:
        return self.system.get_system_info()

    def _run_command(self, command: str) -> dict[str, Any]:
        return self.system.run_command(command)

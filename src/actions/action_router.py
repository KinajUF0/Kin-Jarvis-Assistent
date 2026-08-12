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
        """Register all action handlers with Gemini client."""
        gemini.register_action("open_application", self._open_application)
        gemini.register_action("open_discord_chat", self._open_discord_chat)
        gemini.register_action("set_volume", self._set_volume)
        gemini.register_action("system_action", self._system_action)
        gemini.register_action("web_search", self._web_search)

    def _open_application(self, app_name: str) -> dict[str, Any]:
        return self.app_launcher.open_app(app_name)

    def _open_discord_chat(self, contact_name: str) -> dict[str, Any]:
        return self.discord.open_chat(contact_name)

    def _set_volume(self, level: int) -> dict[str, Any]:
        return self.system.set_volume(level)

    def _system_action(self, action: str) -> dict[str, Any]:
        return self.system.system_action(action)

    def _web_search(self, query: str) -> dict[str, Any]:
        return self.system.web_search(query)

    def execute_direct(self, action: str, **kwargs: Any) -> dict[str, Any]:
        """Execute action directly without Gemini (for UI buttons)."""
        handlers = {
            "open_application": self._open_application,
            "open_discord_chat": self._open_discord_chat,
            "set_volume": self._set_volume,
            "system_action": self._system_action,
            "web_search": self._web_search,
        }
        handler = handlers.get(action)
        if handler:
            return handler(**kwargs)
        return {"success": False, "message": f"Unknown action: {action}"}

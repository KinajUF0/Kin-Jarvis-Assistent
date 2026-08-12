"""Discord automation — open app and navigate to contacts via fuzzy matching."""

from __future__ import annotations

import logging
import platform
import time
from typing import Any

from rapidfuzz import fuzz, process

from src.actions.app_launcher import AppLauncher

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class DiscordHandler:
    """Handle Discord-specific commands with fuzzy contact matching."""

    def __init__(
        self,
        app_launcher: AppLauncher,
        contacts: list[dict[str, Any]],
        fuzzy_threshold: int = 60,
    ) -> None:
        self._launcher = app_launcher
        self._contacts = contacts
        self._threshold = fuzzy_threshold

    def find_contact(self, query: str) -> dict[str, Any] | None:
        """
        Find Discord contact by fuzzy matching.

        Matches against: aliases, display_name, username, search_terms.
        Example: "сэм" -> "[S_E_X_Y] Quinsames"
        """
        if not query or not self._contacts:
            return None

        query_lower = query.lower().strip()
        candidates: list[tuple[str, dict[str, Any]]] = []

        for contact in self._contacts:
            # Build searchable strings for this contact
            search_strings = []

            if contact.get("display_name"):
                search_strings.append(contact["display_name"])
            if contact.get("username"):
                search_strings.append(contact["username"])
            if contact.get("aliases"):
                search_strings.extend(contact["aliases"])
            if contact.get("search_terms"):
                search_strings.extend(contact["search_terms"])

            for s in search_strings:
                candidates.append((s.lower(), contact))

        if not candidates:
            return None

        # Use rapidfuzz for best match
        choices = [c[0] for c in candidates]
        result = process.extractOne(
            query_lower,
            choices,
            scorer=fuzz.WRatio,
            score_cutoff=self._threshold,
        )

        if not result:
            result = process.extractOne(
                query_lower,
                choices,
                scorer=fuzz.partial_ratio,
                score_cutoff=self._threshold,
            )

        if result:
            matched_string, score, index = result
            contact = candidates[index][1]
            logger.info(
                "Fuzzy match: '%s' -> '%s' (score=%d, contact=%s)",
                query,
                matched_string,
                score,
                contact.get("display_name"),
            )
            return {**contact, "_match_score": score, "_matched_term": matched_string}

        return None

    def open_chat(self, contact_name: str) -> dict[str, Any]:
        """Open Discord and navigate to a contact's DM."""
        # Step 1: Launch/focus Discord
        launch_result = self._launcher.open_app("discord")
        if not launch_result.get("success"):
            return launch_result

        time.sleep(1.5)

        # Step 2: Fuzzy find contact
        contact = self.find_contact(contact_name)
        if not contact:
            return {
                "success": False,
                "message": (
                    f"Контакт «{contact_name}» не найден. "
                    f"Добавьте его в config/contacts.json с алиасами."
                ),
            }

        # Step 3: Navigate using Quick Switcher (Ctrl+K)
        search_query = contact.get("quick_switcher_query") or contact.get("username") or contact.get("display_name", "")

        nav_success = self._navigate_to_contact(search_query)
        display = contact.get("display_name", contact_name)

        if nav_success:
            return {
                "success": True,
                "message": f"Открываю чат с {display} в Discord.",
                "contact": display,
                "match_score": contact.get("_match_score"),
            }

        return {
            "success": False,
            "message": (
                f"Discord открыт, но не удалось автоматически найти {display}. "
                f"Попробуйте вручную: Ctrl+K → «{search_query}»"
            ),
            "contact": display,
        }

    def _navigate_to_contact(self, search_query: str) -> bool:
        """Use keyboard automation to open Quick Switcher and search."""
        if not IS_WINDOWS:
            logger.warning("Discord navigation automation is optimized for Windows")
            return self._navigate_pyautogui(search_query)

        return self._navigate_pyautogui(search_query)

    def _navigate_pyautogui(self, search_query: str) -> bool:
        """Navigate Discord using pyautogui keyboard shortcuts."""
        try:
            import pyautogui

            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1

            time.sleep(0.5)

            # Ctrl+K — Quick Switcher in Discord
            pyautogui.hotkey("ctrl", "k")
            time.sleep(0.4)

            # Clear any existing text and type search query
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.1)
            pyautogui.typewrite(search_query, interval=0.03) if search_query.isascii() else pyautogui.write(search_query)
            time.sleep(0.8)

            # Press Enter to open first result
            pyautogui.press("enter")
            time.sleep(0.3)

            logger.info("Discord navigation: searched for '%s'", search_query)
            return True

        except Exception as exc:
            logger.error("Discord navigation failed: %s", exc)
            return False

    def list_contacts(self) -> list[dict[str, str]]:
        """Return list of configured contacts for UI display."""
        return [
            {
                "display_name": c.get("display_name", ""),
                "username": c.get("username", ""),
                "aliases": ", ".join(c.get("aliases", [])),
            }
            for c in self._contacts
        ]

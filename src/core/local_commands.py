"""Local command parser — NO internet, NO Gemini needed."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class LocalCommand:
    action: str
    params: dict[str, Any]
    response_hint: str = ""


# Small talk — no AI
_SMALL_TALK: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"как\s+дела", re.I), "Отлично, сэр. Готов к командам."),
    (re.compile(r"как\s+ты", re.I), "Работаю на полную. Чем помочь?"),
    (re.compile(r"привет|здаров|hello|hi\b", re.I), "Привет! Слушаю вас."),
    (re.compile(r"спасибо|благодар", re.I), "Всегда пожалуйста, сэр."),
    (re.compile(r"кто\s+ты|what are you", re.I), "Я Кин — ваш персональный ассистент."),
]

# Apps: pattern -> app key
_APP_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"discord|дискорд|дискорде", re.I), "discord"),
    (re.compile(r"браузер|browser|интернет", re.I), "browser"),
    (re.compile(r"\bedge\b|эдж|microsoft edge", re.I), "edge"),
    (re.compile(r"chrome|хром|гугл", re.I), "chrome"),
    (re.compile(r"firefox|файрфокс", re.I), "firefox"),
    (re.compile(r"steam|стим", re.I), "steam"),
    (re.compile(r"spotify|спотифай", re.I), "spotify"),
    (re.compile(r"telegram|телеграм|телега", re.I), "telegram"),
    (re.compile(r"vscode|visual studio code|код\b", re.I), "vscode"),
    (re.compile(r"блокнот|notepad", re.I), "notepad"),
    (re.compile(r"проводник|explorer|файлы", re.I), "explorer"),
    (re.compile(r"калькулятор|calculator|calc", re.I), "calculator"),
]

# Discord chat: "открой в discord чат с X" / "найди в discord X"
_DISCORD_CHAT = re.compile(
    r"(?:discord|дискорд).*?(?:чат|chat|напиши|найди|открой).*?(?:с|with)\s+(.+)|"
    r"(?:открой|open|найди).*?(?:discord|дискорд).*?(?:с|with)\s+(.+)",
    re.I,
)

_VOLUME = re.compile(r"громкость\s+(\d+)|volume\s+(\d+)|(?:установи|set)\s+(\d+)\s*%?", re.I)

_URL = re.compile(r"(?:открой\s+)?(?:сайт|url|site)\s+(.+)|(?:открой)\s+(https?://\S+|\S+\.\S+)", re.I)

_SEARCH = re.compile(r"(?:найди|search|поиск|загугли|google)\s+(.+)", re.I)

_FOLDER = re.compile(
    r"открой\s+папку\s+(.+)|open\s+folder\s+(.+)|"
    r"(загрузки|downloads|рабочий\s+стол|desktop|документы|documents|config|logs)",
    re.I,
)


def parse_local_command(command: str) -> LocalCommand | None:
    """
    Parse command locally. Returns None if needs AI (complex conversation).
    """
    cmd = command.strip()
    if not cmd:
        return None

    lower = cmd.lower()

    # Small talk
    for pattern, reply in _SMALL_TALK:
        if pattern.search(cmd):
            return LocalCommand("small_talk", {"text": reply}, reply)

    # Discord chat
    m = _DISCORD_CHAT.search(cmd)
    if m:
        contact = (m.group(1) or m.group(2) or "").strip().rstrip(".")
        if contact:
            return LocalCommand(
                "open_discord_chat",
                {"contact_name": contact},
                f"Открываю чат с {contact}",
            )

    # Open app: "открой X"
    if re.search(r"^(?:открой|open|запусти|launch|включи)\b", lower):
        for pattern, app_key in _APP_PATTERNS:
            if pattern.search(cmd):
                return LocalCommand(
                    "open_application",
                    {"app_name": app_key},
                    f"Открываю {app_key}",
                )
        # Generic: "открой Something"
        generic = re.sub(r"^(?:открой|open|запусти|launch|включи)\s+", "", cmd, flags=re.I).strip()
        if generic and len(generic) < 40:
            return LocalCommand(
                "open_application",
                {"app_name": generic},
                f"Запускаю {generic}",
            )

    # Close app
    m = re.search(r"(?:закрой|close|выключи\s+программу)\s+(.+)", cmd, re.I)
    if m:
        return LocalCommand("close_application", {"app_name": m.group(1).strip()}, "")

    # System actions
    if re.search(r"сверни|minimize|рабочий\s+стол|win\s*d|desktop", lower):
        return LocalCommand("system_action", {"action": "minimize_all"}, "Сворачиваю окна.")

    if re.search(r"блокир|lock", lower):
        return LocalCommand("system_action", {"action": "lock"}, "Блокирую экран.")

    if re.search(r"выключ|shutdown", lower) and "программу" not in lower:
        return LocalCommand("system_action", {"action": "shutdown"}, "Выключаю через 30 сек.")

    if re.search(r"перезагруз|restart|reboot", lower):
        return LocalCommand("system_action", {"action": "restart"}, "Перезагрузка через 30 сек.")

    if re.search(r"сон|sleep", lower):
        return LocalCommand("system_action", {"action": "sleep"}, "Режим сна.")

    # Volume
    m = _VOLUME.search(cmd)
    if m:
        level = int(next(g for g in m.groups() if g))
        return LocalCommand("set_volume", {"level": level}, f"Громкость {level}%.")

    # Screenshot
    if re.search(r"скрин|screenshot", lower):
        return LocalCommand("take_screenshot", {}, "Делаю скриншот.")

    # URL
    m = _URL.search(cmd)
    if m:
        url = (m.group(1) or "").strip()
        return LocalCommand("open_url", {"url": url}, f"Открываю {url}")

    # Search
    m = _SEARCH.search(cmd)
    if m:
        query = m.group(1).strip()
        return LocalCommand("web_search", {"query": query}, f"Ищу: {query}")

    # Folder
    m = _FOLDER.search(cmd)
    if m:
        path = next((g for g in m.groups() if g), None) or m.group(0)
        return LocalCommand("open_folder", {"path": path.strip()}, "")

    # Hotkeys
    if re.search(r"alt\s*tab", lower):
        return LocalCommand("press_hotkey", {"keys": "alt+tab"}, "")

    return None


def needs_ai(command: str) -> bool:
    """True if command likely needs AI (open-ended question)."""
    cmd = command.strip().lower()
    if parse_local_command(command):
        return False
    # Questions likely need AI
    if any(w in cmd for w in ("почему", "что такое", "объясни", "расскажи", "сколько", "когда", "где")):
        return True
    if cmd.endswith("?"):
        return True
    return False

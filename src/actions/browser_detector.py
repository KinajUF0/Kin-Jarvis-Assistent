"""Auto-detect user's default browser and installed browsers on Windows."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


@dataclass
class BrowserInfo:
    key: str
    display_name: str
    process_names: list[str]
    executable: str | None = None
    is_default: bool = False


# Known browsers with Windows install paths
BROWSER_CATALOG: dict[str, dict[str, Any]] = {
    "edge": {
        "display_name": "Microsoft Edge",
        "process_names": ["msedge"],
        "paths": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "msedge",
        ],
        "prog_ids": ["MSEdgeHTM", "MicrosoftEdge"],
    },
    "chrome": {
        "display_name": "Google Chrome",
        "process_names": ["chrome"],
        "paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "chrome",
        ],
        "prog_ids": ["ChromeHTML", "Chrome"],
    },
    "firefox": {
        "display_name": "Mozilla Firefox",
        "process_names": ["firefox"],
        "paths": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            "firefox",
        ],
        "prog_ids": ["FirefoxURL", "Firefox"],
    },
    "brave": {
        "display_name": "Brave",
        "process_names": ["brave"],
        "paths": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            "brave",
        ],
        "prog_ids": ["BraveHTML"],
    },
    "opera": {
        "display_name": "Opera",
        "process_names": ["opera"],
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\opera.exe"),
            r"C:\Program Files\Opera\opera.exe",
            "opera",
        ],
        "prog_ids": ["OperaStable"],
    },
    "yandex": {
        "display_name": "Yandex Browser",
        "process_names": ["browser"],
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Yandex\YandexBrowser\Application\browser.exe"),
            "browser",
        ],
        "prog_ids": ["YandexHTML"],
    },
}


def _find_executable(candidates: list[str]) -> str | None:
    for candidate in candidates:
        expanded = os.path.expandvars(candidate)
        if os.path.isfile(expanded):
            return expanded
        found = shutil.which(expanded)
        if found:
            return found
    return None


def _get_windows_default_prog_id() -> str | None:
    """Read default HTTPS handler ProgId from Windows registry."""
    if not IS_WINDOWS:
        return None
    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            return winreg.QueryValueEx(key, "ProgId")[0]
    except OSError:
        pass

    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"http\shell\open\command") as key:
            cmd = winreg.QueryValueEx(key, "")[0].lower()
            for browser_key, info in BROWSER_CATALOG.items():
                for proc in info["process_names"]:
                    if proc in cmd:
                        return info["prog_ids"][0]
    except OSError:
        pass

    return None


def _prog_id_to_browser(prog_id: str) -> str | None:
    prog_lower = prog_id.lower()
    for browser_key, info in BROWSER_CATALOG.items():
        for pid in info.get("prog_ids", []):
            if pid.lower() in prog_lower or prog_lower.startswith(pid.lower()):
                return browser_key
        for proc in info["process_names"]:
            if proc in prog_lower:
                return browser_key
    return None


def detect_installed_browsers() -> list[BrowserInfo]:
    """Find all installed browsers on the system."""
    found: list[BrowserInfo] = []
    default_key = get_default_browser_key()

    for key, info in BROWSER_CATALOG.items():
        exe = _find_executable(info["paths"])
        if exe:
            found.append(
                BrowserInfo(
                    key=key,
                    display_name=info["display_name"],
                    process_names=info["process_names"],
                    executable=exe,
                    is_default=(key == default_key),
                )
            )

    # Sort: default first, then alphabetically
    found.sort(key=lambda b: (not b.is_default, b.display_name))
    return found


def get_default_browser_key() -> str:
    """Return browser key for user's default browser. Falls back to edge then first found."""
    prog_id = _get_windows_default_prog_id()
    if prog_id:
        matched = _prog_id_to_browser(prog_id)
        if matched:
            logger.info("Default browser detected: %s (ProgId=%s)", matched, prog_id)
            return matched

    # Fallback: first installed browser, prefer Edge on Windows
    installed = detect_installed_browsers()
    if installed:
        return installed[0].key

    return "edge"


def get_default_browser() -> BrowserInfo:
    """Get full info for the default browser."""
    key = get_default_browser_key()
    installed = {b.key: b for b in detect_installed_browsers()}

    if key in installed:
        b = installed[key]
        b.is_default = True
        return b

    info = BROWSER_CATALOG.get(key, BROWSER_CATALOG["edge"])
    return BrowserInfo(
        key=key,
        display_name=info["display_name"],
        process_names=info["process_names"],
        executable=_find_executable(info["paths"]),
        is_default=True,
    )


def open_url(url: str, browser_key: str | None = None) -> dict[str, Any]:
    """Open URL in default or specified browser."""
    import webbrowser

    if browser_key and browser_key != "default":
        browser = next(
            (b for b in detect_installed_browsers() if b.key == browser_key),
            None,
        )
        if browser and browser.executable:
            subprocess.Popen([browser.executable, url])
            return {
                "success": True,
                "message": f"Открываю {url} в {browser.display_name}",
                "browser": browser.display_name,
            }

    # Use default browser via webbrowser module (respects OS default)
    if IS_WINDOWS:
        os.startfile(url)  # type: ignore[attr-defined]
    else:
        webbrowser.open(url)

    default = get_default_browser()
    return {
        "success": True,
        "message": f"Открываю {url} в {default.display_name}",
        "browser": default.display_name,
    }

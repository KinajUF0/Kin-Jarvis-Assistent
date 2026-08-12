"""Application launcher — opens or starts any program."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import time
from typing import Any

import psutil

from src.actions.browser_detector import get_default_browser, get_default_browser_key

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


def _is_process_running(process_names: list[str]) -> bool:
    names_lower = [n.lower() for n in process_names]
    for proc in psutil.process_iter(["name"]):
        try:
            pname = proc.info["name"]
            if pname and pname.lower().replace(".exe", "") in names_lower:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def _find_executable(candidates: list[str]) -> str | None:
    for candidate in candidates:
        expanded = os.path.expandvars(candidate)
        if os.path.isfile(expanded):
            return expanded
        found = shutil.which(expanded)
        if found:
            return found

    if IS_WINDOWS:
        local = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")

        for base in [local, program_files, program_files_x86]:
            if not base:
                continue
            for candidate in candidates:
                expanded = os.path.expandvars(candidate)
                full = os.path.join(base, expanded)
                if os.path.isfile(full):
                    return full
    return None


def _focus_window(process_names: list[str]) -> bool:
    if not IS_WINDOWS:
        return False
    try:
        import win32gui
        import win32con
        import win32process

        target_pids = set()
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower().replace(".exe", "") in [
                    n.lower() for n in process_names
                ]:
                    target_pids.add(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        def enum_callback(hwnd: int, _: Any) -> bool:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid in target_pids and win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return False
            return True

        win32gui.EnumWindows(enum_callback, None)
        return True
    except ImportError:
        return False
    except Exception as exc:
        logger.error("Window focus error: %s", exc)
        return False


def _search_start_menu(app_name: str) -> str | None:
    """Search Windows Start Menu for application .lnk or .exe."""
    if not IS_WINDOWS:
        return None

    search_dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]
    query = app_name.lower()

    for base in search_dirs:
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            for fname in files:
                if not fname.lower().endswith((".lnk", ".exe")):
                    continue
                name_lower = fname.lower().replace(".lnk", "").replace(".exe", "")
                if query in name_lower or name_lower in query:
                    return os.path.join(root, fname)
    return None


class AppLauncher:
    """Launch and focus applications."""

    def __init__(self, apps_config: dict[str, Any], custom_discord_path: str = "") -> None:
        self._apps = dict(apps_config)
        if custom_discord_path and "discord" in self._apps:
            self._apps["discord"]["paths"].insert(0, custom_discord_path)

    def open_app(self, app_name: str) -> dict[str, Any]:
        """Open or focus an application by name."""
        app_key = app_name.lower().strip()

        aliases = {
            "дискорд": "discord",
            "discord": "discord",
            "edge": "edge",
            "microsoft edge": "edge",
            "майкрософт эдж": "edge",
            "эдж": "edge",
            "chrome": "chrome",
            "хром": "chrome",
            "google chrome": "chrome",
            "firefox": "firefox",
            "файрфокс": "firefox",
            "brave": "brave",
            "брав": "brave",
            "opera": "opera",
            "опера": "opera",
            "yandex": "yandex",
            "яндекс": "yandex",
            "яндекс браузер": "yandex",
            "steam": "steam",
            "стим": "steam",
            "spotify": "spotify",
            "спотифай": "spotify",
            "telegram": "telegram",
            "телеграм": "telegram",
            "телега": "telegram",
            "vscode": "vscode",
            "code": "vscode",
            "visual studio code": "vscode",
            "notepad": "notepad",
            "блокнот": "notepad",
            "explorer": "explorer",
            "проводник": "explorer",
            "calculator": "calculator",
            "калькулятор": "calculator",
            "браузер": "browser",
            "browser": "browser",
            "интернет": "browser",
        }
        app_key = aliases.get(app_key, app_key)

        # "browser" = user's default browser (Edge, Chrome, etc.)
        if app_key == "browser":
            default = get_default_browser()
            app_key = default.key
            logger.info("Opening default browser: %s", default.display_name)

        app_info = self._apps.get(app_key)
        if not app_info:
            return self._try_launch_unknown(app_name, app_key)

        process_names = app_info.get("process_names", [app_key])
        display_name = app_info.get("display_name", app_key)

        if _is_process_running(process_names):
            _focus_window(process_names)
            return {
                "success": True,
                "message": f"{display_name} уже запущен — переключился на окно.",
                "app": app_key,
                "was_running": True,
            }

        paths = app_info.get("paths", [])
        executable = _find_executable(paths)

        if not executable:
            uri = app_info.get("uri")
            if uri:
                try:
                    if IS_WINDOWS:
                        os.startfile(uri)  # type: ignore[attr-defined]
                    else:
                        subprocess.Popen(["xdg-open", uri])
                    time.sleep(2)
                    return {
                        "success": True,
                        "message": f"{display_name} запускается...",
                        "app": app_key,
                    }
                except Exception as exc:
                    return {"success": False, "message": f"Не удалось запустить {display_name}: {exc}"}
            return {
                "success": False,
                "message": f"Не найден {display_name}. Проверьте config/apps.json или установите программу.",
            }

        try:
            subprocess.Popen([executable], shell=False)
            time.sleep(2)
            _focus_window(process_names)
            return {
                "success": True,
                "message": f"{display_name} успешно запущен.",
                "app": app_key,
            }
        except Exception as exc:
            return {"success": False, "message": f"Ошибка запуска {display_name}: {exc}"}

    def _try_launch_unknown(self, original_name: str, app_key: str) -> dict[str, Any]:
        """Try to launch any program by name via Start Menu or shell."""
        # Start Menu search
        shortcut = _search_start_menu(app_key)
        if shortcut:
            try:
                os.startfile(shortcut)  # type: ignore[attr-defined]
                return {
                    "success": True,
                    "message": f"Запускаю {original_name}...",
                    "app": app_key,
                }
            except Exception as exc:
                logger.error("Start menu launch failed: %s", exc)

        # Shell fallback
        if IS_WINDOWS:
            try:
                subprocess.Popen(f'start "" "{original_name}"', shell=True)
                return {
                    "success": True,
                    "message": f"Пробую запустить {original_name}...",
                    "app": app_key,
                }
            except Exception as exc:
                return {
                    "success": False,
                    "message": f"Программа «{original_name}» не найдена: {exc}",
                }

        return {
            "success": False,
            "message": f"Программа «{original_name}» не найдена. Добавьте в config/apps.json",
        }

    def close_app(self, app_name: str) -> dict[str, Any]:
        """Close/kill an application by name."""
        app_key = app_name.lower().strip()
        app_info = self._apps.get(app_key, {})
        process_names = app_info.get("process_names", [app_key])

        killed = 0
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                pname = proc.info["name"]
                if pname and pname.lower().replace(".exe", "") in [n.lower() for n in process_names]:
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            return {"success": True, "message": f"Закрыл {app_name} ({killed} процессов)."}
        return {"success": False, "message": f"{app_name} не запущен или не найден."}

    def get_default_browser_name(self) -> str:
        return get_default_browser().display_name

    def is_running(self, app_name: str) -> bool:
        app_info = self._apps.get(app_name.lower(), {})
        return _is_process_running(app_info.get("process_names", [app_name]))

"""Application launcher — opens or starts programs."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from typing import Any

import psutil

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


def _is_process_running(process_names: list[str]) -> bool:
    """Check if any process with given names is running."""
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
    """Find executable in PATH or common locations."""
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
        found = shutil.which(candidate)
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
                if os.path.isfile(os.path.join(base, candidate)):
                    return os.path.join(base, candidate)

    return None


def _focus_window(process_names: list[str]) -> bool:
    """Bring application window to foreground (Windows)."""
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
        logger.warning("pywin32 not available for window focus")
        return False
    except Exception as exc:
        logger.error("Window focus error: %s", exc)
        return False


class AppLauncher:
    """Launch and focus applications."""

    def __init__(self, apps_config: dict[str, Any], custom_discord_path: str = "") -> None:
        self._apps = apps_config
        if custom_discord_path and "discord" in self._apps:
            self._apps["discord"]["paths"].insert(0, custom_discord_path)

    def open_app(self, app_name: str) -> dict[str, Any]:
        """Open or focus an application by name."""
        app_key = app_name.lower().strip()
        # Aliases
        aliases = {
            "дискорд": "discord",
            "discord": "discord",
            "хром": "chrome",
            "google chrome": "chrome",
            "chrome": "chrome",
            "firefox": "firefox",
            "файрфокс": "firefox",
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
            "браузер": "chrome",
        }
        app_key = aliases.get(app_key, app_key)

        app_info = self._apps.get(app_key)
        if not app_info:
            return {
                "success": False,
                "message": f"Программа «{app_name}» не найдена в конфигурации. Добавьте её в config/apps.json",
            }

        process_names = app_info.get("process_names", [app_key])
        display_name = app_info.get("display_name", app_key)

        # Already running — focus window
        if _is_process_running(process_names):
            _focus_window(process_names)
            return {
                "success": True,
                "message": f"{display_name} уже запущен — переключился на окно.",
                "app": app_key,
                "was_running": True,
            }

        # Find and launch
        paths = app_info.get("paths", [])
        executable = _find_executable(paths)

        if not executable:
            # Try URI scheme
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
                        "was_running": False,
                    }
                except Exception as exc:
                    return {"success": False, "message": f"Не удалось запустить {display_name}: {exc}"}

            return {
                "success": False,
                "message": f"Не найден исполняемый файл для {display_name}. Проверьте config/apps.json",
            }

        try:
            if IS_WINDOWS:
                subprocess.Popen([executable], shell=False)
            else:
                subprocess.Popen([executable])
            time.sleep(2)
            _focus_window(process_names)
            return {
                "success": True,
                "message": f"{display_name} успешно запущен.",
                "app": app_key,
                "was_running": False,
            }
        except Exception as exc:
            logger.exception("Launch error for %s", app_key)
            return {"success": False, "message": f"Ошибка запуска {display_name}: {exc}"}

    def is_running(self, app_name: str) -> bool:
        app_info = self._apps.get(app_name.lower(), {})
        return _is_process_running(app_info.get("process_names", [app_name]))

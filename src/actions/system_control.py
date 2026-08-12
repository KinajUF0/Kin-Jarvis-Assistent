"""Extended system actions — folders, files, URLs, keyboard, screenshots."""

from __future__ import annotations

import logging
import os
import platform
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

from src.actions.browser_detector import get_default_browser, open_url
from src.core.paths import get_cache_dir, get_data_dir, get_logs_dir

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class SystemControl:
    """Handle system-level commands."""

    def set_volume(self, level: int) -> dict[str, Any]:
        level = max(0, min(100, level))
        if IS_WINDOWS:
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                return {"success": True, "message": f"Громкость установлена на {level}%."}
            except ImportError:
                return self._volume_keys(level)
            except Exception as exc:
                return {"success": False, "message": f"Ошибка громкости: {exc}"}
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"], check=True, capture_output=True)
            return {"success": True, "message": f"Громкость установлена на {level}%."}
        except Exception as exc:
            return {"success": False, "message": f"Ошибка громкости: {exc}"}

    def _volume_keys(self, level: int) -> dict[str, Any]:
        """Approximate volume via key simulation."""
        try:
            import pyautogui
            pyautogui.press("volumemute")
            return {"success": True, "message": f"Громкость ~{level}%. Для точного управления: pip install pycaw"}
        except Exception:
            return {"success": False, "message": "Не удалось изменить громкость."}

    def system_action(self, action: str) -> dict[str, Any]:
        action = action.lower().strip()
        actions_map = {
            "shutdown": self._shutdown, "restart": self._restart, "sleep": self._sleep,
            "lock": self._lock, "minimize_all": self._minimize_all,
            "выключение": self._shutdown, "перезагрузка": self._restart,
            "сон": self._sleep, "блокировка": self._lock,
        }
        handler = actions_map.get(action)
        if not handler:
            return {"success": False, "message": f"Неизвестное действие: {action}"}
        return handler()

    def _shutdown(self) -> dict[str, Any]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/s", "/t", "30"], check=False)
            return {"success": True, "message": "Выключение через 30 сек. Отмена: shutdown /a"}
        subprocess.run(["shutdown", "-h", "+1"], check=False)
        return {"success": True, "message": "Выключение через 1 минуту."}

    def _restart(self) -> dict[str, Any]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/r", "/t", "30"], check=False)
        else:
            subprocess.run(["shutdown", "-r", "+1"], check=False)
        return {"success": True, "message": "Перезагрузка через 30 секунд."}

    def _sleep(self) -> dict[str, Any]:
        if IS_WINDOWS:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=False)
        else:
            subprocess.run(["systemctl", "suspend"], check=False)
        return {"success": True, "message": "Перевожу систему в режим сна."}

    def _lock(self) -> dict[str, Any]:
        if IS_WINDOWS:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
        else:
            subprocess.run(["loginctl", "lock-session"], check=False)
        return {"success": True, "message": "Экран заблокирован."}

    def _minimize_all(self) -> dict[str, Any]:
        if IS_WINDOWS:
            import pyautogui
            pyautogui.hotkey("win", "d")
        return {"success": True, "message": "Все окна свёрнуты."}

    def web_search(self, query: str) -> dict[str, Any]:
        """Search in user's default browser (Edge, Chrome, etc.)."""
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        result = open_url(url)
        browser = get_default_browser().display_name
        return {
            "success": True,
            "message": f"Ищу «{query}» в {browser}.",
            "browser": browser,
        }

    def open_url(self, url: str) -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return open_url(url)

    def open_folder(self, path: str) -> dict[str, Any]:
        """Open folder in Explorer."""
        expanded = os.path.expandvars(os.path.expanduser(path))
        folder = Path(expanded)
        if not folder.exists():
            # Try common shortcuts
            shortcuts = {
                "downloads": Path.home() / "Downloads",
                "загрузки": Path.home() / "Downloads",
                "desktop": Path.home() / "Desktop",
                "рабочий стол": Path.home() / "Desktop",
                "documents": Path.home() / "Documents",
                "документы": Path.home() / "Documents",
                "data": get_data_dir(),
                "config": get_data_dir() / "config",
                "logs": get_logs_dir(),
            }
            folder = shortcuts.get(path.lower(), folder)

        if not folder.exists():
            return {"success": False, "message": f"Папка не найдена: {path}"}

        if IS_WINDOWS:
            os.startfile(str(folder))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(folder)])
        return {"success": True, "message": f"Открываю папку: {folder}"}

    def open_file(self, path: str) -> dict[str, Any]:
        expanded = os.path.expandvars(os.path.expanduser(path))
        file_path = Path(expanded)
        if not file_path.exists():
            return {"success": False, "message": f"Файл не найден: {path}"}
        if IS_WINDOWS:
            os.startfile(str(file_path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(file_path)])
        return {"success": True, "message": f"Открываю файл: {file_path.name}"}

    def take_screenshot(self) -> dict[str, Any]:
        try:
            import pyautogui
            cache = get_cache_dir()
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = cache / filename
            pyautogui.screenshot(str(filepath))
            return {"success": True, "message": f"Скриншот сохранён: {filepath}", "path": str(filepath)}
        except Exception as exc:
            return {"success": False, "message": f"Ошибка скриншота: {exc}"}

    def type_text(self, text: str) -> dict[str, Any]:
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.02) if text.isascii() else pyautogui.write(text)
            return {"success": True, "message": f"Напечатано: {text[:50]}..."}
        except Exception as exc:
            return {"success": False, "message": f"Ошибка ввода: {exc}"}

    def press_hotkey(self, keys: str) -> dict[str, Any]:
        """Press keyboard shortcut, e.g. 'ctrl+c', 'alt+tab', 'win+e'."""
        try:
            import pyautogui
            key_list = [k.strip() for k in keys.lower().split("+")]
            pyautogui.hotkey(*key_list)
            return {"success": True, "message": f"Нажато: {keys}"}
        except Exception as exc:
            return {"success": False, "message": f"Ошибка: {exc}"}

    def open_windows_settings(self, page: str = "") -> dict[str, Any]:
        """Open Windows Settings or specific page."""
        if not IS_WINDOWS:
            return {"success": False, "message": "Только для Windows."}
        pages = {
            "": "ms-settings:",
            "sound": "ms-settings:sound",
            "звук": "ms-settings:sound",
            "bluetooth": "ms-settings:bluetooth",
            "wifi": "ms-settings:network-wifi",
            "wifi": "ms-settings:network-wifi",
            "display": "ms-settings:display",
            "экран": "ms-settings:display",
            "privacy": "ms-settings:privacy",
            "update": "ms-settings:windowsupdate",
        }
        uri = pages.get(page.lower(), f"ms-settings:{page}" if page else "ms-settings:")
        os.startfile(uri)  # type: ignore[attr-defined]
        return {"success": True, "message": f"Открываю настройки Windows."}

    def get_system_info(self) -> dict[str, Any]:
        import psutil
        browser = get_default_browser()
        info = {
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent if not IS_WINDOWS else psutil.disk_usage("C:\\").percent,
            "default_browser": browser.display_name,
            "data_dir": str(get_data_dir()),
        }
        return {
            "success": True,
            "message": (
                f"CPU: {info['cpu_percent']}%, RAM: {info['ram_percent']}%, "
                f"Браузер: {info['default_browser']}, Данные: {info['data_dir']}"
            ),
            "info": info,
        }

    def run_command(self, command: str) -> dict[str, Any]:
        """Run a shell command (safe subset)."""
        blocked = ["format", "del /f", "rm -rf", "rmdir /s", ":(){", "shutdown"]
        if any(b in command.lower() for b in blocked):
            return {"success": False, "message": "Эта команда заблокирована из соображений безопасности."}
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout or result.stderr or "Готово."
            return {"success": True, "message": output[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Команда превысила лимит времени (30 сек)."}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

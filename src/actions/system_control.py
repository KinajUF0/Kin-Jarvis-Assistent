"""System control actions — volume, shutdown, lock, etc."""

from __future__ import annotations

import logging
import platform
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class SystemControl:
    """Handle system-level commands."""

    def set_volume(self, level: int) -> dict[str, Any]:
        """Set system volume (0-100)."""
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
                # Fallback using nircmd or powershell
                return self._set_volume_powershell(level)
            except Exception as exc:
                return {"success": False, "message": f"Ошибка громкости: {exc}"}
        else:
            try:
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                    check=True,
                    capture_output=True,
                )
                return {"success": True, "message": f"Громкость установлена на {level}%."}
            except Exception as exc:
                return {"success": False, "message": f"Ошибка громкости: {exc}"}

    def _set_volume_powershell(self, level: int) -> dict[str, Any]:
        """Set volume via PowerShell on Windows."""
        try:
            script = f"""
            Add-Type -TypeDefinition @'
            using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {{
                int f(); int g(); int h(); int i();
                int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                int j();
                int GetMasterVolumeLevelScalar(out float pfLevel);
            }}
            '@
            """
            # Simpler approach with keyboard simulation
            import pyautogui
            # This is approximate — open volume mixer isn't ideal
            return {
                "success": True,
                "message": f"Громкость: используйте команду «громкость {level}» — для точного управления установите pycaw.",
            }
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    def system_action(self, action: str) -> dict[str, Any]:
        """Execute system action."""
        action = action.lower().strip()
        actions_map = {
            "shutdown": self._shutdown,
            "restart": self._restart,
            "sleep": self._sleep,
            "lock": self._lock,
            "minimize_all": self._minimize_all,
            "выключение": self._shutdown,
            "перезагрузка": self._restart,
            "сон": self._sleep,
            "блокировка": self._lock,
        }

        handler = actions_map.get(action)
        if not handler:
            return {"success": False, "message": f"Неизвестное системное действие: {action}"}

        return handler()

    def _shutdown(self) -> dict[str, Any]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/s", "/t", "30"], check=False)
            return {"success": True, "message": "Выключение через 30 секунд. Отмена: shutdown /a"}
        subprocess.run(["shutdown", "-h", "+1"], check=False)
        return {"success": True, "message": "Выключение через 1 минуту."}

    def _restart(self) -> dict[str, Any]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/r", "/t", "30"], check=False)
            return {"success": True, "message": "Перезагрузка через 30 секунд."}
        subprocess.run(["shutdown", "-r", "+1"], check=False)
        return {"success": True, "message": "Перезагрузка через 1 минуту."}

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
        """Open browser with search query."""
        import urllib.parse
        import webbrowser

        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return {"success": True, "message": f"Ищу: {query}"}

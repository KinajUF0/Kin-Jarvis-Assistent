"""Speech recognition — microphones only, silent on noise."""

from __future__ import annotations

import logging
import re
import threading
from typing import Callable

import speech_recognition as sr

logger = logging.getLogger(__name__)

# Skip virtual / loopback devices
_SKIP_NAME = re.compile(
    r"stereo mix|loopback|output|speaker|колонк|динамик|line out|"
    r"mapped|virtual cable|what u hear|primary sound driver",
    re.I,
)


def _fix_name(name: str) -> str:
    """Fix Windows mojibake in device names."""
    if not name:
        return "Микрофон"
    for enc in ("utf-8", "cp1251"):
        try:
            fixed = name.encode("cp1252", errors="ignore").decode(enc)
            if fixed and len(fixed) >= 2:
                # Prefer result with readable Cyrillic or ASCII
                if not re.search(r"[\u0420-\u044f]{2}.*[\u0420-\u044f]{2}", name):
                    return fixed.strip()
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return name.strip()


def list_microphones() -> list[tuple[int, str]]:
    """Return INPUT devices only — real microphones, not speakers."""
    result: list[tuple[int, str]] = []
    seen: set[str] = set()

    try:
        import pyaudio

        pa = pyaudio.PyAudio()
        try:
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if int(info.get("maxInputChannels", 0)) < 1:
                    continue
                raw = str(info.get("name", ""))
                name = _fix_name(raw)
                if _SKIP_NAME.search(name):
                    continue
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)
                result.append((i, name))
        finally:
            pa.terminate()
    except Exception as exc:
        logger.warning("PyAudio device list failed: %s, fallback to speech_recognition", exc)
        try:
            for i, name in enumerate(sr.Microphone.list_microphone_names()):
                name = _fix_name(name or "")
                if _SKIP_NAME.search(name):
                    continue
                result.append((i, name))
        except Exception as exc2:
            logger.error("Cannot list microphones: %s", exc2)

    return result[:15]  # max 15 — no 40 devices


class SpeechListener:
    """Speech recognition with selectable microphone."""

    def __init__(
        self,
        language: str = "ru-RU",
        device_index: int | None = None,
        on_text: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self.language = language
        self.device_index = device_index
        self.on_text = on_text
        self.on_error = on_error
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = 400
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.9
        self._microphone: sr.Microphone | None = None
        self._listening = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def set_device(self, device_index: int | None) -> None:
        self.device_index = device_index
        self._microphone = None

    def _init_microphone(self) -> bool:
        try:
            self._microphone = sr.Microphone(device_index=self.device_index)
            with self._microphone as source:
                logger.info("Calibrating mic device=%s", self.device_index)
                self._recognizer.adjust_for_ambient_noise(source, duration=0.6)
            return True
        except Exception as exc:
            logger.error("Microphone init failed: %s", exc)
            if self.on_error:
                self.on_error(f"Микрофон недоступен: {exc}")
            return False

    def listen_once(
        self,
        timeout: float = 5,
        phrase_limit: float = 12,
        silent: bool = False,
    ) -> str | None:
        if not self._microphone and not self._init_microphone():
            return None

        try:
            with self._microphone as source:  # type: ignore[union-attr]
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            text = self._recognizer.recognize_google(audio, language=self.language)
            logger.info("Recognized: %s", text)
            return text
        except sr.WaitTimeoutError:
            return None  # silence — normal
        except sr.UnknownValueError:
            if not silent:
                logger.debug("Speech not understood (noise?)")
            return None
        except sr.RequestError as exc:
            logger.error("Speech API error: %s", exc)
            if not silent and self.on_error:
                self.on_error(f"Нужен интернет для распознавания речи.")
            return None
        except Exception as exc:
            logger.error("Listen error: %s", exc)
            if not silent and self.on_error:
                self.on_error(f"Ошибка микрофона: {exc}")
            return None

    def _listen_loop(self) -> None:
        """Background loop — completely silent on noise, no wake word check here."""
        while not self._stop_event.is_set():
            text = self.listen_once(timeout=3, phrase_limit=12, silent=True)
            if text and self.on_text:
                self.on_text(text)

    def start_continuous(self) -> bool:
        if self._listening:
            return True
        if not self._init_microphone():
            return False
        self._stop_event.clear()
        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def stop_continuous(self) -> None:
        self._stop_event.set()
        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    @property
    def is_listening(self) -> bool:
        return self._listening

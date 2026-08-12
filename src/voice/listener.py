"""Speech recognition with microphone selection."""

from __future__ import annotations

import logging
import threading
from typing import Callable

import speech_recognition as sr

logger = logging.getLogger(__name__)


def list_microphones() -> list[tuple[int, str]]:
    """Return list of (index, name) for available microphones."""
    try:
        names = sr.Microphone.list_microphone_names()
        return [(i, name or f"Микрофон {i}") for i, name in enumerate(names)]
    except Exception as exc:
        logger.error("Cannot list microphones: %s", exc)
        return []


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
        self._recognizer.energy_threshold = 300
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.8
        self._microphone: sr.Microphone | None = None
        self._listening = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def set_device(self, device_index: int | None) -> None:
        """Switch microphone device."""
        self.device_index = device_index
        self._microphone = None

    def _init_microphone(self) -> bool:
        try:
            self._microphone = sr.Microphone(device_index=self.device_index)
            with self._microphone as source:
                logger.info("Calibrating microphone (device=%s)...", self.device_index)
                self._recognizer.adjust_for_ambient_noise(source, duration=0.8)
            return True
        except Exception as exc:
            logger.error("Microphone init failed: %s", exc)
            if self.on_error:
                self.on_error(f"Микрофон недоступен: {exc}")
            return False

    def listen_once(self, timeout: float = 5, phrase_limit: float = 12) -> str | None:
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
            if self.on_error:
                self.on_error("Не услышал речь. Проверьте микрофон.")
            return None
        except sr.UnknownValueError:
            if self.on_error:
                self.on_error("Не разобрал речь. Попробуйте ещё раз.")
            return None
        except sr.RequestError as exc:
            logger.error("Speech recognition error: %s", exc)
            if self.on_error:
                self.on_error(f"Ошибка распознавания (нужен интернет): {exc}")
            return None
        except Exception as exc:
            logger.error("Listen error: %s", exc)
            if self.on_error:
                self.on_error(f"Ошибка микрофона: {exc}")
            return None

    def _listen_loop(self) -> None:
        while not self._stop_event.is_set():
            text = self.listen_once(timeout=4, phrase_limit=15)
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
        logger.info("Continuous listening started")
        return True

    def stop_continuous(self) -> None:
        self._stop_event.set()
        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("Continuous listening stopped")

    @property
    def is_listening(self) -> bool:
        return self._listening

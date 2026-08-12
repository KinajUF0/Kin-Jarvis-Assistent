"""Speech recognition module."""

from __future__ import annotations

import logging
import threading
from typing import Callable

import speech_recognition as sr

logger = logging.getLogger(__name__)


class SpeechListener:
    """Continuous speech recognition with callback support."""

    def __init__(
        self,
        language: str = "ru-RU",
        on_text: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self.language = language
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

    def _init_microphone(self) -> bool:
        try:
            self._microphone = sr.Microphone()
            with self._microphone as source:
                logger.info("Calibrating microphone...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
            return True
        except Exception as exc:
            logger.error("Microphone init failed: %s", exc)
            if self.on_error:
                self.on_error(f"Микрофон недоступен: {exc}")
            return False

    def listen_once(self, timeout: float = 5, phrase_limit: float = 10) -> str | None:
        """Listen for a single phrase and return transcribed text."""
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
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as exc:
            logger.error("Speech recognition error: %s", exc)
            if self.on_error:
                self.on_error(f"Ошибка распознавания: {exc}")
            return None
        except Exception as exc:
            logger.error("Listen error: %s", exc)
            return None

    def _listen_loop(self) -> None:
        """Background listening loop."""
        while not self._stop_event.is_set():
            text = self.listen_once(timeout=3, phrase_limit=15)
            if text and self.on_text:
                self.on_text(text)

    def start_continuous(self) -> bool:
        """Start continuous background listening."""
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
        """Stop background listening."""
        self._stop_event.set()
        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("Continuous listening stopped")

    @property
    def is_listening(self) -> bool:
        return self._listening

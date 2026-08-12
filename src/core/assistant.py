"""Main assistant orchestrator."""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Callable

from src.actions.action_router import ActionRouter
from src.ai.gemini_client import GeminiClient
from src.core.config import Config
from src.core.wake_word import (
    get_greeting_for_wake_word,
    is_wake_word_only,
    strip_wake_word,
)
from src.voice.listener import SpeechListener
from src.voice.speaker import SpeechSpeaker

logger = logging.getLogger(__name__)


class KinAssistant:
    """Central orchestrator for Kin/Jarvis AI assistant."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._validate_config()

        self.gemini = GeminiClient(
            api_key=self.config.gemini_api_key,
            model_name=self.config.gemini_model,
        )
        self.router = ActionRouter(self.config)
        self.router.register_with_gemini(self.gemini)

        self.listener = SpeechListener(
            language=self.config.speech_language,
            on_text=self._on_speech,
            on_error=self._on_error,
        )
        self.speaker = SpeechSpeaker(voice=self.config.tts_voice)

        self._active = False
        self._processing = False
        self._history: list[dict[str, Any]] = []

        # UI callbacks
        self.on_status_change: Callable[[str], None] | None = None
        self.on_message: Callable[[str, str, bool], None] | None = None  # role, text, success
        self.on_listening_change: Callable[[bool], None] | None = None

    def _validate_config(self) -> None:
        errors = self.config.validate()
        if errors:
            for err in errors:
                logger.warning("Config: %s", err)

    def _set_status(self, status: str) -> None:
        logger.info("Status: %s", status)
        if self.on_status_change:
            self.on_status_change(status)

    def _add_message(self, role: str, text: str, success: bool = True) -> None:
        entry = {
            "role": role,
            "text": text,
            "success": success,
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        self._history.append(entry)
        if self.on_message:
            self.on_message(role, text, success)

    def _on_error(self, error: str) -> None:
        logger.error(error)
        self._add_message("system", error, success=False)

    def _on_speech(self, text: str) -> None:
        """Handle incoming speech from continuous listener."""
        if not self._active:
            return
        self.process_text(text, source="voice")

    def process_text(self, text: str, source: str = "text") -> dict[str, Any] | None:
        """
        Process user input (voice or text).

        Returns response dict or None if wake word not detected.
        """
        if self._processing:
            return None

        wake = strip_wake_word(text)
        if not wake.detected:
            return None

        self._processing = True
        self._set_status("Обработка...")

        try:
            # User said only wake word
            if is_wake_word_only(text):
                greeting = get_greeting_for_wake_word(wake.wake_word)
                self._add_message("user", text)
                self._add_message("assistant", greeting)
                if source == "voice":
                    self.speaker.speak(greeting, blocking=False)
                return {"text": greeting, "action": None, "success": True}

            # Process command
            self._add_message("user", text)
            result = self.gemini.process(wake.command, wake.display_name)
            response_text = result.get("text", "")

            self._add_message(
                "assistant",
                response_text,
                success=result.get("success", True),
            )

            if source == "voice" and response_text:
                self.speaker.speak(response_text, blocking=False)

            return result

        finally:
            self._processing = False
            if self._active:
                self._set_status("Слушаю...")

    def start(self) -> bool:
        """Start the assistant (continuous listening)."""
        errors = self.config.validate()
        if errors:
            self._add_message("system", "\n".join(errors), success=False)
            return False

        self._active = True
        self._set_status("Слушаю...")
        if self.on_listening_change:
            self.on_listening_change(True)

        started = self.listener.start_continuous()
        if not started:
            self._active = False
            self._set_status("Микрофон недоступен")
            if self.on_listening_change:
                self.on_listening_change(False)
            return False

        greeting = f"{self.config.assistant_name} активирован. Обращайтесь: Джарвис, Кин, Jarvis, Астра или Astra."
        self._add_message("system", greeting)
        return True

    def stop(self) -> None:
        """Stop the assistant."""
        self._active = False
        self.listener.stop_continuous()
        self._set_status("Остановлен")
        if self.on_listening_change:
            self.on_listening_change(False)
        self._add_message("system", f"{self.config.assistant_name} деактивирован.")

    def send_text_command(self, text: str) -> dict[str, Any] | None:
        """Send text command from UI (must include wake word)."""
        return self.process_text(text, source="text")

    def send_direct_chat(self, message: str) -> str:
        """Direct chat with Gemini (no wake word required, for chat tab)."""
        self._add_message("user", message)
        response = self.gemini.chat_text_only(message)
        self._add_message("assistant", response)
        return response

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def is_processing(self) -> bool:
        return self._processing

"""Main assistant orchestrator — local commands first, AI optional."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Callable

from src.actions.action_router import ActionRouter
from src.ai.gemini_client import GeminiClient
from src.ai.ollama_client import OllamaClient
from src.core.config import Config
from src.core.local_commands import needs_ai, parse_local_command
from src.core.wake_word import (
    get_greeting_for_wake_word,
    is_wake_word_only,
    strip_wake_word,
)
from src.voice.listener import SpeechListener
from src.voice.speaker import SpeechSpeaker

logger = logging.getLogger(__name__)


class KinAssistant:
    """Central orchestrator — works WITHOUT Gemini for most commands."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.router = ActionRouter(self.config)

        self.gemini: GeminiClient | None = None
        self.ollama = OllamaClient(
            base_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        )
        self._init_gemini_if_key()

        self.listener = SpeechListener(
            language=self.config.speech_language,
            on_text=self._on_speech,
            on_error=self._on_error,
        )
        self.speaker = SpeechSpeaker(voice=self.config.tts_voice)

        self._active = False
        self._processing = False
        self._history: list[dict[str, Any]] = []

        self.on_status_change: Callable[[str], None] | None = None
        self.on_message: Callable[[str, str, bool], None] | None = None
        self.on_listening_change: Callable[[bool], None] | None = None

    def _init_gemini_if_key(self) -> None:
        key = self.config.gemini_api_key
        if key and key != "your_gemini_api_key_here":
            self.gemini = GeminiClient(api_key=key, model_name=self.config.gemini_model)
            self.router.register_with_gemini(self.gemini)

    def _on_error(self, error: str) -> None:
        """Only critical errors — not noise."""
        logger.warning("Listener: %s", error)
        self._add_message("system", error, success=False)

    def _on_speech(self, text: str) -> None:
        if not self._active:
            return
        # Only react if wake word present — ignore everything else silently
        if not strip_wake_word(text).detected:
            logger.debug("Ignored (no wake word): %s", text)
            return
        self.process_text(text, source="voice")

    def _execute_local(self, command: str) -> dict[str, Any] | None:
        local = parse_local_command(command)
        if not local:
            return None
        result = self.router.execute(local.action, **local.params)
        text = result.get("message") or local.response_hint or "Готово."
        return {"text": text, "action": local.action, "success": result.get("success", True)}

    def _execute_ai(self, command: str, wake_name: str) -> dict[str, Any]:
        # Try Ollama first if available (works in Russia, offline)
        if self.ollama.is_available():
            try:
                reply = self.ollama.chat(command)
                return {"text": reply, "action": "ollama", "success": True}
            except Exception as exc:
                logger.warning("Ollama failed: %s", exc)

        # Fallback Gemini
        if self.gemini:
            return self.gemini.process(command, wake_name)

        return {
            "text": (
                "Не понял команду.\n"
                "Примеры: «открой Discord», «сверни окна», «как дела».\n"
                "Для сложных вопросов: Gemini ключ или Ollama (ollama.com)."
            ),
            "action": None,
            "success": False,
        }

    def process_text(self, text: str, source: str = "text") -> dict[str, Any] | None:
        if self._processing:
            return None

        wake = strip_wake_word(text)
        if not wake.detected:
            return None

        self._processing = True
        self._set_status("Обработка...")

        try:
            if is_wake_word_only(text):
                greeting = get_greeting_for_wake_word(wake.wake_word)
                self._add_message("user", text)
                self._add_message("assistant", greeting)
                if source == "voice":
                    self.speaker.speak(greeting, blocking=False)
                return {"text": greeting, "action": None, "success": True}

            self._add_message("user", text)

            # 1. LOCAL — no internet, no Gemini
            result = self._execute_local(wake.command)
            if result is None and needs_ai(wake.command):
                # 2. AI only for open questions
                result = self._execute_ai(wake.command, wake.display_name)
            elif result is None:
                result = self._execute_ai(wake.command, wake.display_name)

            response_text = result.get("text", "")
            self._add_message("assistant", response_text, success=result.get("success", True))

            if source == "voice" and response_text:
                self.speaker.speak(response_text, blocking=False)

            return result

        finally:
            self._processing = False
            if self._active:
                self._set_status("Слушаю...")

    def start(self) -> bool:
        """Start — NO API key required for local commands."""
        self._active = True
        self._set_status("Слушаю...")
        if self.on_listening_change:
            self.on_listening_change(True)

        if not self.listener.start_continuous():
            self._active = False
            self._set_status("Микрофон недоступен")
            if self.on_listening_change:
                self.on_listening_change(False)
            return False

        hints = []
        if self.gemini:
            hints.append("Gemini")
        if self.ollama.is_available():
            hints.append("Ollama")
        ai_note = f" AI: {', '.join(hints)}." if hints else " Команды работают локально без AI."

        self._add_message(
            "system",
            f"Активирован. Обращайся: Кин, Джарvis, Астра.{ai_note}",
        )
        return True

    def stop(self) -> None:
        self._active = False
        self.listener.stop_continuous()
        self._set_status("Остановлен")
        if self.on_listening_change:
            self.on_listening_change(False)

    def send_text_command(self, text: str) -> dict[str, Any] | None:
        return self.process_text(text, source="text")

    def reload_api_key(self, api_key: str) -> None:
        if api_key and api_key != "your_gemini_api_key_here":
            self.gemini = GeminiClient(api_key=api_key, model_name=self.config.gemini_model)
            self.router.register_with_gemini(self.gemini)

    def _set_status(self, status: str) -> None:
        if self.on_status_change:
            self.on_status_change(status)

    def _add_message(self, role: str, text: str, success: bool = True) -> None:
        self._history.append({
            "role": role, "text": text, "success": success,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        if self.on_message:
            self.on_message(role, text, success)

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def is_processing(self) -> bool:
        return self._processing

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

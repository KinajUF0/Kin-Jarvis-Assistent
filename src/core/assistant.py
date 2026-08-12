"""Main assistant — local commands + Ollama AI."""

from __future__ import annotations

import logging
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
    """Kin assistant — local commands + Ollama (primary AI)."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.router = ActionRouter(self.config)

        self.ollama = OllamaClient(
            base_url=self.config.ollama_url,
            model=self.config.ollama_model,
        )
        self.gemini: GeminiClient | None = None
        if self.config.has_gemini_key() and self.config.ai_provider in ("gemini", "both"):
            self.gemini = GeminiClient(
                api_key=self.config.gemini_api_key,
                model_name=self.config.gemini_model,
            )
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

        self.on_status_change: Callable[[str], None] | None = None
        self.on_message: Callable[[str, str, bool], None] | None = None
        self.on_listening_change: Callable[[bool], None] | None = None

    def ollama_status(self) -> dict[str, Any]:
        return self.ollama.status()

    def _on_error(self, error: str) -> None:
        logger.warning("Listener: %s", error)
        self._add_message("system", error, success=False)

    def _on_speech(self, text: str) -> None:
        if not self._active:
            return
        if not strip_wake_word(text).detected:
            return
        self.process_text(text, source="voice")

    def _execute_local(self, command: str) -> dict[str, Any] | None:
        local = parse_local_command(command)
        if not local:
            return None
        result = self.router.execute(local.action, **local.params)
        text = result.get("message") or local.response_hint or "Готово."
        return {"text": text, "action": local.action, "success": result.get("success", True)}

    def _execute_ollama_action(self, parsed: dict[str, Any]) -> dict[str, Any]:
        action = parsed.get("action", "chat")
        if action == "chat":
            return {"text": parsed.get("text", "Слушаю."), "action": "chat", "success": True}
        params = parsed.get("params", {})
        result = self.router.execute(action, **params)
        text = result.get("message") or parsed.get("text", "Готово.")
        return {"text": text, "action": action, "success": result.get("success", True)}

    def _execute_ai(self, command: str, wake_name: str) -> dict[str, Any]:
        provider = self.config.ai_provider

        # Ollama first (default for Russia)
        if provider in ("ollama", "both") and self.ollama.is_available() and self.ollama.has_model():
            # Try parse as action
            parsed = self.ollama.parse_command(command)
            if parsed and parsed.get("action") and parsed["action"] != "chat":
                return self._execute_ollama_action(parsed)
            if parsed and parsed.get("action") == "chat":
                return {"text": parsed.get("text", ""), "action": "ollama", "success": True}
            # Plain chat
            try:
                reply = self.ollama.chat(command)
                return {"text": reply, "action": "ollama", "success": True}
            except Exception as exc:
                logger.warning("Ollama chat failed: %s", exc)

        # Gemini fallback
        if provider in ("gemini", "both") and self.gemini:
            return self.gemini.process(command, wake_name)

        # No AI
        st = self.ollama.status()
        if not st.get("running"):
            return {
                "text": (
                    "Ollama не запущен.\n"
                    "Запусти: scripts\\install_ollama.bat\n"
                    "Или скачай: ollama.com"
                ),
                "action": None,
                "success": False,
            }
        if not st.get("model_ready"):
            return {
                "text": (
                    f"Модель {self.config.ollama_model} не загружена.\n"
                    f"В терминале: ollama pull {self.config.ollama_model}"
                ),
                "action": None,
                "success": False,
            }

        return {
            "text": "Не понял. Примеры: «открой Discord», «сверни окна», «как дела?»",
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

            result = self._execute_local(wake.command)
            if result is None:
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

        ollama_msg = OllamaClient.format_status_ru(self.ollama.status())
        self._add_message(
            "system",
            f"Активирован. Обращайся: Кин, Джарvis, Астра.\n{ollama_msg}",
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

    def reload_ollama(self, url: str, model: str) -> None:
        self.ollama = OllamaClient(base_url=url, model=model)

    def reload_api_key(self, api_key: str) -> None:
        if api_key:
            self.gemini = GeminiClient(api_key=api_key, model_name=self.config.gemini_model)
            self.router.register_with_gemini(self.gemini)

    def pull_ollama_model(self) -> tuple[bool, str]:
        return self.ollama.pull_model()

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

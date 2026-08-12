"""Google Gemini AI client with function calling for actions."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Кин (Kin/Jarvis/Astra), персональный AI-ассистент пользователя Алексея.
Ты умный, вежливый, немного с юмором в стиле JARVIS из Iron Man.
Отвечай на том же языке, на котором говорит пользователь (русский или английский).

Твои возможности:
- Открывать программы (Discord, браузер, Steam, Spotify и др.)
- Открывать чаты в Discord по имени контакта (нечёткий поиск)
- Управлять системой (громкость, выключение, блокировка)
- Отвечать на любые вопросы и поддерживать беседу
- Искать информацию и давать советы

Когда пользователь просит открыть программу или чат — используй соответствующую функцию.
Когда просто спрашивает «как дела» или болтает — отвечай естественно, без вызова функций.
Будь кратким в голосовых ответах (1-3 предложения), подробнее в текстовых.
"""


# Function declarations for Gemini function calling
FUNCTIONS: list[FunctionDeclaration] = [
    FunctionDeclaration(
        name="open_application",
        description="Открыть или запустить программу/приложение на компьютере",
        parameters={
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Название программы: discord, chrome, firefox, steam, spotify, telegram, vscode, notepad, explorer, calculator",
                }
            },
            "required": ["app_name"],
        },
    ),
    FunctionDeclaration(
        name="open_discord_chat",
        description="Открыть Discord и найти чат/DM с конкретным человеком по имени или нику",
        parameters={
            "type": "object",
            "properties": {
                "contact_name": {
                    "type": "string",
                    "description": "Имя, ник или часть ника контакта в Discord (например: Сэм, Sam, Quinsames)",
                }
            },
            "required": ["contact_name"],
        },
    ),
    FunctionDeclaration(
        name="set_volume",
        description="Установить громкость системы",
        parameters={
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "description": "Уровень громкости от 0 до 100",
                }
            },
            "required": ["level"],
        },
    ),
    FunctionDeclaration(
        name="system_action",
        description="Выполнить системное действие",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Действие: shutdown, restart, sleep, lock, minimize_all",
                }
            },
            "required": ["action"],
        },
    ),
    FunctionDeclaration(
        name="web_search",
        description="Открыть браузер с поисковым запросом",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Поисковый запрос",
                }
            },
            "required": ["query"],
        },
    ),
]


class GeminiClient:
    """Gemini API wrapper with action routing via function calling."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash") -> None:
        genai.configure(api_key=api_key)
        self._model_name = model_name
        self._tool = Tool(function_declarations=FUNCTIONS)
        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            tools=[self._tool],
        )
        self._chat = self._model.start_chat(history=[])
        self._action_handlers: dict[str, Callable[..., dict[str, Any]]] = {}

    def register_action(self, name: str, handler: Callable[..., dict[str, Any]]) -> None:
        """Register a handler for a function call."""
        self._action_handlers[name] = handler

    def process(self, user_message: str, wake_word_name: str = "Кин") -> dict[str, Any]:
        """
        Process user message and return response dict.

        Returns:
            {
                "text": str,           # Response text to speak/display
                "action": str | None,  # Action that was executed
                "success": bool,
            }
        """
        try:
            prompt = f"[Пользователь обратился: {wake_word_name}] {user_message}"
            response = self._chat.send_message(prompt)

            # Check for function calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        action_name = fc.name
                        args = dict(fc.args) if fc.args else {}

                        logger.info("Function call: %s(%s)", action_name, args)

                        handler = self._action_handlers.get(action_name)
                        if handler:
                            result = handler(**args)
                        else:
                            result = {"success": False, "message": f"Неизвестное действие: {action_name}"}

                        # Send function result back to model for natural response
                        message = result.get("message", "Готово.")
                        try:
                            final = self._chat.send_message(
                                {
                                    "function_response": {
                                        "name": action_name,
                                        "response": result,
                                    }
                                }
                            )
                            text = final.text or message
                        except Exception:
                            text = message

                        return {
                            "text": text,
                            "action": action_name,
                            "success": result.get("success", True),
                            "details": result,
                        }

            text = response.text or "Извините, не смог обработать запрос."
            return {"text": text, "action": None, "success": True}

        except Exception as exc:
            logger.exception("Gemini error: %s", exc)
            return {
                "text": f"Произошла ошибка при обращении к AI: {exc}",
                "action": None,
                "success": False,
            }

    def reset_chat(self) -> None:
        """Reset conversation history."""
        self._chat = self._model.start_chat(history=[])

    def chat_text_only(self, message: str) -> str:
        """Simple text chat without function calling (for UI typing)."""
        try:
            response = self._chat.send_message(message)
            return response.text or ""
        except Exception as exc:
            return f"Ошибка: {exc}"

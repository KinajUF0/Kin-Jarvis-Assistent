"""Google Gemini AI client with function calling for actions."""

from __future__ import annotations

import logging
from typing import Any, Callable

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

from src.ai.gemini_utils import format_gemini_error

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Кин (Kin/Jarvis/Astra), персональный AI-ассистент пользователя Kinaj.
Ты умный, вежливый, немного с юмором в стиле JARVIS из Iron Man.
Отвечай на том же языке, на котором говорит пользователь (русский или английский).

Твои возможности (используй функции для выполнения):
- Открывать ЛЮБЫЕ программы (Discord, Steam, Spotify, блокнот, проводник и т.д.)
- Открывать браузер пользователя (авто-определение: Edge, Chrome, Firefox и др.)
- Открывать сайты и искать в интернете
- Открывать папки и файлы
- Discord: открывать чаты по имени (нечёткий поиск)
- Система: громкость, блокировка, выключение, скриншот, горячие клавиши
- Запуск команд в терминале
- Отвечать на любые вопросы

ВАЖНО:
- «браузер» / «browser» = браузер по умолчанию пользователя (НЕ предполагай Chrome!)
- Когда просят открыть программу — вызывай open_application
- Когда болтают — отвечай без функций
- Голосовые ответы: 1-3 предложения
"""


FUNCTIONS: list[FunctionDeclaration] = [
    FunctionDeclaration(
        name="open_application",
        description="Открыть/запустить любую программу. browser=браузер по умолчанию пользователя",
        parameters={
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "discord, browser, edge, chrome, firefox, steam, spotify, telegram, vscode, notepad, explorer, calculator или любое имя программы",
                }
            },
            "required": ["app_name"],
        },
    ),
    FunctionDeclaration(
        name="close_application",
        description="Закрыть программу",
        parameters={
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "Имя программы"}},
            "required": ["app_name"],
        },
    ),
    FunctionDeclaration(
        name="open_discord_chat",
        description="Открыть Discord и найти чат/DM с человеком по имени",
        parameters={
            "type": "object",
            "properties": {"contact_name": {"type": "string", "description": "Имя или ник контакта"}},
            "required": ["contact_name"],
        },
    ),
    FunctionDeclaration(
        name="open_url",
        description="Открыть сайт/URL в браузере пользователя",
        parameters={
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL сайта"}},
            "required": ["url"],
        },
    ),
    FunctionDeclaration(
        name="web_search",
        description="Поиск в Google через браузер пользователя",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Поисковый запрос"}},
            "required": ["query"],
        },
    ),
    FunctionDeclaration(
        name="open_folder",
        description="Открыть папку в проводнике",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Путь или: downloads, desktop, documents, data, config, logs",
                }
            },
            "required": ["path"],
        },
    ),
    FunctionDeclaration(
        name="open_file",
        description="Открыть файл",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Путь к файлу"}},
            "required": ["path"],
        },
    ),
    FunctionDeclaration(
        name="set_volume",
        description="Установить громкость 0-100",
        parameters={
            "type": "object",
            "properties": {"level": {"type": "integer", "description": "0-100"}},
            "required": ["level"],
        },
    ),
    FunctionDeclaration(
        name="system_action",
        description="Системное действие: shutdown, restart, sleep, lock, minimize_all",
        parameters={
            "type": "object",
            "properties": {"action": {"type": "string", "description": "Действие"}},
            "required": ["action"],
        },
    ),
    FunctionDeclaration(
        name="take_screenshot",
        description="Сделать скриншот экрана",
        parameters={"type": "object", "properties": {}, "required": []},
    ),
    FunctionDeclaration(
        name="press_hotkey",
        description="Нажать горячие клавиши",
        parameters={
            "type": "object",
            "properties": {"keys": {"type": "string", "description": "Например: ctrl+c, alt+tab, win+e"}},
            "required": ["keys"],
        },
    ),
    FunctionDeclaration(
        name="open_settings",
        description="Открыть настройки Windows",
        parameters={
            "type": "object",
            "properties": {"page": {"type": "string", "description": "sound, bluetooth, display, wifi или пусто"}},
            "required": [],
        },
    ),
    FunctionDeclaration(
        name="get_system_info",
        description="Информация о системе: CPU, RAM, браузер, папки",
        parameters={"type": "object", "properties": {}, "required": []},
    ),
    FunctionDeclaration(
        name="run_command",
        description="Выполнить команду в терминале/cmd",
        parameters={
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Команда"}},
            "required": ["command"],
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
        self._action_handlers[name] = handler

    def process(self, user_message: str, wake_word_name: str = "Кин") -> dict[str, Any]:
        try:
            prompt = f"[Пользователь обратился: {wake_word_name}] {user_message}"
            response = self._chat.send_message(prompt)

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        action_name = fc.name
                        args = dict(fc.args) if fc.args else {}

                        logger.info("Function call: %s(%s)", action_name, args)

                        handler = self._action_handlers.get(action_name)
                        result = handler(**args) if handler else {
                            "success": False, "message": f"Неизвестное действие: {action_name}"
                        }

                        message = result.get("message", "Готово.")
                        try:
                            final = self._chat.send_message({
                                "function_response": {"name": action_name, "response": result}
                            })
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
                "text": format_gemini_error(exc),
                "action": None,
                "success": False,
            }

    def reset_chat(self) -> None:
        self._chat = self._model.start_chat(history=[])

    def chat_text_only(self, message: str) -> str:
        try:
            response = self._chat.send_message(message)
            return response.text or ""
        except Exception as exc:
            return format_gemini_error(exc)

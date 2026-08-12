"""Ollama — основной локальный AI для Kin (работает в РФ, офлайн)."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

KIN_SYSTEM = """Ты — Кин (Kin/Jarvis), персональный AI-ассистент Kinaj.
Отвечай кратко на русском (1-3 предложения для голоса).
Ты умный, вежливый, в стиле JARVIS.
Если пользователь просит действие — скажи что делаешь, но не выдумывай что уже сделал."""

PARSE_SYSTEM = """Ты парсер команд ассистента Кин. Пользователь уже обратился по имени.
Верни ТОЛЬКО JSON (без markdown):
{"action":"chat","text":"ответ"} — для разговора/вопросов
{"action":"open_application","params":{"app_name":"discord"}} — открыть программу
{"action":"open_discord_chat","params":{"contact_name":"имя"}} — чат Discord
{"action":"system_action","params":{"action":"minimize_all"}} — свернуть окна (lock/shutdown/restart/sleep/minimize_all)
{"action":"set_volume","params":{"level":50}} — громкость 0-100
{"action":"web_search","params":{"query":"запрос"}} — поиск
{"action":"open_url","params":{"url":"site.com"}} — открыть сайт

app_name: discord, browser, edge, chrome, steam, spotify, telegram, notepad, explorer, calculator
"""


class OllamaClient:
    """Ollama HTTP API client."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "llama3.2") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._history: list[dict[str, str]] = []

    def _request(self, path: str, payload: dict | None = None, method: str = "GET", timeout: int = 120) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"} if data else {},
            method=method,
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def is_available(self) -> bool:
        try:
            self._request("/api/tags", timeout=3)
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            body = self._request("/api/tags", timeout=5)
            models = body.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
        except Exception as exc:
            logger.warning("Ollama list_models: %s", exc)
            return []

    def has_model(self) -> bool:
        models = self.list_models()
        if not models:
            return False
        # Exact or prefix match (llama3.2 vs llama3.2:latest)
        for m in models:
            if m == self.model or m.startswith(f"{self.model}:") or self.model.startswith(m.split(":")[0]):
                return True
        return False

    def status(self) -> dict[str, Any]:
        ok = self.is_available()
        models = self.list_models() if ok else []
        return {
            "running": ok,
            "model": self.model,
            "model_ready": self.has_model() if ok else False,
            "models": models,
            "url": self.base_url,
        }

    def chat(self, message: str, system: str = "") -> str:
        messages = [{"role": "system", "content": system or KIN_SYSTEM}]
        messages.extend(self._history[-6:])
        messages.append({"role": "user", "content": message})

        body = self._request("/api/chat", {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 256},
        })

        reply = body.get("message", {}).get("content", "").strip()
        if reply:
            self._history.append({"role": "user", "content": message})
            self._history.append({"role": "assistant", "content": reply})
        return reply or "Не смог ответить."

    def parse_command(self, command: str) -> dict[str, Any] | None:
        """Ask Ollama to parse command into action JSON."""
        try:
            body = self._request("/api/chat", {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": PARSE_SYSTEM},
                    {"role": "user", "content": command},
                ],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200},
            })
            raw = body.get("message", {}).get("content", "").strip()
            return self._extract_json(raw)
        except Exception as exc:
            logger.warning("Ollama parse failed: %s", exc)
            return None

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        text = text.strip()
        # Strip markdown code blocks
        if "```" in text:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if m:
                text = m.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
        return None

    def pull_model(self, model: str | None = None, on_progress: Any = None) -> tuple[bool, str]:
        """Download model (may take several minutes)."""
        target = model or self.model
        try:
            payload = {"name": target, "stream": False}
            req = urllib.request.Request(
                f"{self.base_url}/api/pull",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=600) as resp:
                resp.read()
            self.model = target
            return True, f"Модель {target} загружена."
        except urllib.error.URLError as exc:
            return False, f"Ollama не запущен. Установи с ollama.com и запусти Ollama."
        except Exception as exc:
            return False, f"Ошибка загрузки модели: {exc}"

    def reset_chat(self) -> None:
        self._history.clear()

    @staticmethod
    def format_status_ru(status: dict[str, Any]) -> str:
        if not status.get("running"):
            return "Ollama не запущен. Установи: ollama.com"
        if not status.get("model_ready"):
            models = status.get("models") or []
            if models:
                return f"Ollama работает. Модель «{status.get('model')}» не найдена. Доступны: {', '.join(models[:3])}"
            return f"Ollama работает. Скачай модель: ollama pull {status.get('model')}"
        return f"Ollama OK — модель {status.get('model')}"

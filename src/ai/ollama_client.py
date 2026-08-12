"""Optional Ollama local AI — works offline, no region limits."""

from __future__ import annotations

import logging
import urllib.request
import json

logger = logging.getLogger(__name__)


class OllamaClient:
    """Simple Ollama HTTP client."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "llama3.2") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def chat(self, message: str, system: str = "") -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or "Ты Кин, краткий русскоязычный ассистент."},
                {"role": "user", "content": message},
            ],
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
        return body.get("message", {}).get("content", "Нет ответа.")

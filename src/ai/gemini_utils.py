"""Gemini API helpers."""

from __future__ import annotations


def format_gemini_error(exc: Exception) -> str:
    """Convert Gemini API errors to readable Russian messages."""
    msg = str(exc)
    lower = msg.lower()

    if "api_key_invalid" in lower or "api key not valid" in lower:
        return (
            "Неверный Gemini API ключ.\n"
            "1. Получите ключ: aistudio.google.com/apikey\n"
            "2. Вставьте слева и нажмите «Сохранить ключ»"
        )
    if "quota" in lower or "rate" in lower:
        return "Превышен лимит запросов Gemini. Подождите немного."
    if "permission" in lower or "403" in msg:
        return "Нет доступа к Gemini API. Проверьте ключ и включите API в Google AI Studio."
    if "404" in msg and "model" in lower:
        return "Модель Gemini не найдена. Проверьте GEMINI_MODEL в .env"

    return f"Ошибка Gemini: {msg[:200]}"


def test_api_key(api_key: str, model: str = "gemini-2.0-flash") -> tuple[bool, str]:
    """Test if API key works. Returns (success, message)."""
    if not api_key or api_key == "your_gemini_api_key_here":
        return False, "Ключ не задан"

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(model)
        response = model_obj.generate_content("ping")
        if response.text:
            return True, "Ключ работает"
        return True, "Ключ принят"
    except Exception as exc:
        return False, format_gemini_error(exc)

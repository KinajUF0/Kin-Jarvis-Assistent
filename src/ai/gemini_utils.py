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
    if "quota" in lower or "rate" in lower or "429" in msg or "resource_exhausted" in lower:
        return (
            "Превышен лимит запросов Gemini (429).\n\n"
            "Возможные причины:\n"
            "• Free tier — ~10–15 запросов/мин, лимит в день\n"
            "• Россия не в списке поддерживаемых регионов — доступ нестабилен\n"
            "• Слишком много команд подряд\n\n"
            "Что делать:\n"
            "1. Подожди 1–2 минуты между командами\n"
            "2. Проверь лимиты: aistudio.google.com → твой проект → Rate limits\n"
            "3. Если из РФ — попробуй VPN (Финляндия, Германия, Казахстан)\n"
            "4. Смени модель в .env: GEMINI_MODEL=gemini-2.5-flash-lite"
        )
    if "permission" in lower or "403" in msg or "blocked" in lower or "region" in lower or "location" in lower:
        return (
            "Gemini API недоступен из твоего региона (403).\n"
            "Россия официально не поддерживается Google AI Studio.\n"
            "Варианты: VPN в EU/Казахстан, или другой AI-провайдер."
        )
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

"""Wake word detection — only responds to specific names."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.core.config import WAKE_WORDS, WAKE_WORD_DISPLAY


@dataclass
class WakeWordResult:
    """Result of wake word detection."""

    detected: bool
    wake_word: str = ""
    display_name: str = ""
    command: str = ""


# Patterns for each wake word (case-insensitive, supports mixed Cyrillic/Latin)
_WAKE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("джарвис", re.compile(r"\b(?:джарвис|jarvis|джарvis|дjarvis)\b", re.IGNORECASE)),
    ("jarvis", re.compile(r"\b(?:джарвис|jarvis|джарvis|дjarvis)\b", re.IGNORECASE)),
    ("кин", re.compile(r"\b(?:кин|kin)\b", re.IGNORECASE)),
    ("kin", re.compile(r"\b(?:кин|kin)\b", re.IGNORECASE)),
    ("астра", re.compile(r"\b(?:астра|astra)\b", re.IGNORECASE)),
    ("astra", re.compile(r"\b(?:астра|astra)\b", re.IGNORECASE)),
]


def strip_wake_word(text: str) -> WakeWordResult:
    """
    Check if text contains a valid wake word and extract the command.

    Only responds to: Джарvis, Jarvis, Кин, Kin, Астра, Astra.
    All other names are ignored.
    """
    if not text or not text.strip():
        return WakeWordResult(detected=False)

    normalized = text.strip()

    for wake_key, pattern in _WAKE_PATTERNS:
        match = pattern.search(normalized)
        if match:
            # Extract command after wake word
            command = normalized[match.end() :].strip()
            # Remove leading punctuation/commas
            command = re.sub(r"^[,.\-:!?\s]+", "", command).strip()

            return WakeWordResult(
                detected=True,
                wake_word=wake_key,
                display_name=WAKE_WORD_DISPLAY.get(wake_key, wake_key),
                command=command,
            )

    return WakeWordResult(detected=False)


def is_wake_word_only(text: str) -> bool:
    """Check if text is just a wake word with no command."""
    result = strip_wake_word(text)
    return result.detected and not result.command


def get_greeting_for_wake_word(wake_word: str) -> str:
    """Return a greeting when user only says the wake word."""
    name = WAKE_WORD_DISPLAY.get(wake_word, "сэр")
    greetings = {
        "джарвис": f"Да, сэр. Джарвис к вашим услугам.",
        "jarvis": "Yes, sir. Jarvis at your service.",
        "кин": f"Слушаю, сэр. Кин на связи.",
        "kin": "Listening, sir. Kin is online.",
        "астра": f"Астра активирована. Чем могу помочь?",
        "astra": "Astra activated. How can I help?",
    }
    return greetings.get(wake_word, f"Да, {name} слушает.")

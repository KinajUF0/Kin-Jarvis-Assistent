#!/usr/bin/env python3
"""Test local commands — no Gemini needed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.local_commands import parse_local_command
from src.core.wake_word import strip_wake_word

TESTS = [
    "Кин, открой Discord",
    "Кин, свернись на рабочий стол",
    "Джарvis, открой браузер",
    "Кин, как дела?",
    "Астра, открой в Discord чат с Сэмом",
    "Кин, установи громкость 50",
    "привет мир",  # no wake word
]

print("=== Wake words ===")
for t in TESTS:
    w = strip_wake_word(t)
    print(f"  {'OK' if w.detected else '--'} '{t}' -> '{w.command}'")

print("\n=== Local commands (no AI) ===")
for t in TESTS:
    w = strip_wake_word(t)
    if not w.detected:
        continue
    local = parse_local_command(w.command)
    if local:
        print(f"  OK '{t}' -> {local.action} {local.params}")
    else:
        print(f"  AI '{t}' -> needs AI")

print("\nDone.")

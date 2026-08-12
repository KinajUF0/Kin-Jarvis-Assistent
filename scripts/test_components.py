#!/usr/bin/env python3
"""Quick test script for Kin/Jarvis components without GUI."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import Config
from src.core.wake_word import strip_wake_word
from src.actions.discord_handler import DiscordHandler
from src.actions.app_launcher import AppLauncher


def test_wake_words() -> None:
    print("=== Wake Word Tests ===")
    tests = [
        "Кин, открой Discord",
        "Джарвис, как дела?",
        "Jarvis, open Chrome",
        "Астра, привет!",
        "Astra, what's up?",
        "Сiri, открой Discord",  # Should NOT match
        "Алиса, включи музыку",    # Should NOT match
        "Кин",
    ]
    for t in tests:
        result = strip_wake_word(t)
        status = "✅" if result.detected else "❌"
        print(f"  {status} '{t}' -> detected={result.detected}, command='{result.command}'")


def test_fuzzy_contacts() -> None:
    print("\n=== Discord Fuzzy Match Tests ===")
    config = Config()
    launcher = AppLauncher(config.apps)
    handler = DiscordHandler(launcher, config.discord_contacts, config.fuzzy_match_threshold)

    queries = ["сэм", "Sam", "quins", "sex y", "Kinaj", "алексей", "несуществующий"]
    for q in queries:
        contact = handler.find_contact(q)
        if contact:
            print(f"  ✅ '{q}' -> {contact.get('display_name')} ({contact.get('username')}) score={contact.get('_match_score')}")
        else:
            print(f"  ❌ '{q}' -> not found")


if __name__ == "__main__":
    test_wake_words()
    test_fuzzy_contacts()
    print("\n✅ Tests complete!")

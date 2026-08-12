#!/usr/bin/env python3
"""
Kin / Jarvis AI Assistant — Entry Point

Personal AI assistant with voice control, Gemini AI,
Discord integration, and application automation.

Usage:
    python -m src.main
    python src/main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.assistant import KinAssistant
from src.core.config import Config
from src.ui.app import KinApp


def setup_logging(level: str = "INFO") -> None:
    log_dir = PROJECT_ROOT / "kin_data"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "kin.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    config = Config()
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting Kin/Jarvis AI Assistant...")

    errors = config.validate()
    if errors:
        logger.warning("Configuration warnings:")
        for err in errors:
            logger.warning("  - %s", err)

    assistant = KinAssistant(config)
    app = KinApp(assistant)
    app.run()


if __name__ == "__main__":
    main()

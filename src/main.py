#!/usr/bin/env python3
"""Kin / Jarvis AI Assistant — Entry Point."""

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
from src.core.paths import get_logs_dir, is_frozen
from src.ui.app import KinApp


def setup_logging(level: str = "INFO") -> None:
    log_dir = get_logs_dir()
    log_file = log_dir / "kin.log"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def main() -> None:
    config = Config()
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    mode = "EXE" if is_frozen() else "DEV"
    logger.info("Starting Kin/Jarvis AI Assistant [%s]...", mode)

    assistant = KinAssistant(config)
    app = KinApp(assistant)
    app.run()


if __name__ == "__main__":
    main()

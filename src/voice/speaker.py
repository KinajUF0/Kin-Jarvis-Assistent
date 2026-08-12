"""Text-to-speech using Edge TTS."""

from __future__ import annotations

import asyncio
import logging
import tempfile
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class SpeechSpeaker:
    """Async text-to-speech with Edge TTS voices."""

    def __init__(self, voice: str = "ru-RU-DmitryNeural") -> None:
        self.voice = voice
        self._speaking = False
        self._lock = threading.Lock()

    async def _speak_async(self, text: str) -> None:
        import edge_tts

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(tmp_path)
            self._play_audio(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _play_audio(self, path: str) -> None:
        """Play audio file using pygame."""
        try:
            import pygame

            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()
        except Exception as exc:
            logger.error("Audio playback error: %s", exc)

    def speak(self, text: str, blocking: bool = True) -> None:
        """Speak text aloud."""
        if not text or not text.strip():
            return

        with self._lock:
            self._speaking = True

        def _run() -> None:
            try:
                asyncio.run(self._speak_async(text))
            except Exception as exc:
                logger.error("TTS error: %s", exc)
            finally:
                with self._lock:
                    self._speaking = False

        if blocking:
            _run()
        else:
            threading.Thread(target=_run, daemon=True).start()

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._speaking

    @staticmethod
    def list_voices(language: str = "ru") -> list[str]:
        """List available TTS voices for a language."""
        async def _get() -> list[str]:
            import edge_tts

            voices = await edge_tts.list_voices()
            return [v["ShortName"] for v in voices if language in v.get("Locale", "")]

        return asyncio.run(_get())

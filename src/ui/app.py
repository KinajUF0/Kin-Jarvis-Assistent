"""GUI for Kin/Jarvis assistant."""

from __future__ import annotations

import logging
import os
import threading
from typing import TYPE_CHECKING

import customtkinter as ctk

from src.core.config import WAKE_WORD_DISPLAY
from src.core.paths import get_assets_dir, get_env_path

if TYPE_CHECKING:
    from src.core.assistant import KinAssistant

logger = logging.getLogger(__name__)

COLORS = {
    "bg": "#0d1117",
    "panel": "#161b22",
    "card": "#21262d",
    "accent": "#58a6ff",
    "accent_hover": "#388bfd",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "green": "#3fb950",
    "red": "#f85149",
    "user": "#1f3a5f",
    "bot": "#21262d",
}


class KinApp(ctk.CTk):
    def __init__(self, assistant: KinAssistant) -> None:
        super().__init__()
        self.assistant = assistant
        self._setup_window()
        self._build_ui()
        self._bind_callbacks()
        self.after(400, self._check_api_key)

    def _setup_window(self) -> None:
        self.title("Kin Jarvis")
        self.geometry("960x640")
        self.minsize(800, 520)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=COLORS["bg"])

        ico = get_assets_dir() / "logo.ico"
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        side = ctk.CTkFrame(self, width=240, fg_color=COLORS["panel"], corner_radius=0)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        ctk.CTkLabel(
            side, text="KIN JARVIS",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            side, text="AI Assistant",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).pack(pady=(0, 20))

        # Status
        self._status_label = ctk.CTkLabel(
            side, text="Остановлен",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["muted"],
        )
        self._status_label.pack(pady=(0, 12))

        self._toggle_btn = ctk.CTkButton(
            side, text="Активировать", height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#ffffff", command=self._toggle,
        )
        self._toggle_btn.pack(fill="x", padx=16, pady=(0, 20))

        # Wake words
        ctk.CTkLabel(
            side, text="Обращайся:",
            font=ctk.CTkFont(size=11), text_color=COLORS["muted"],
        ).pack(anchor="w", padx=16)

        ctk.CTkLabel(
            side, text=", ".join(WAKE_WORD_DISPLAY.values()),
            font=ctk.CTkFont(size=11), text_color=COLORS["text"],
            wraplength=200, justify="left",
        ).pack(anchor="w", padx=16, pady=(2, 20))

        # API key
        ctk.CTkLabel(
            side, text="Gemini API Key",
            font=ctk.CTkFont(size=11), text_color=COLORS["muted"],
        ).pack(anchor="w", padx=16)

        self._api_entry = ctk.CTkEntry(
            side, placeholder_text="aistudio.google.com/apikey",
            height=32, font=ctk.CTkFont(size=11),
        )
        self._api_entry.pack(fill="x", padx=16, pady=(4, 6))

        ctk.CTkButton(
            side, text="Сохранить ключ", height=30,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["card"], hover_color="#30363d",
            command=self._save_api_key,
        ).pack(fill="x", padx=16)

        # --- Chat area ---
        chat_area = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        chat_area.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        chat_area.grid_columnconfigure(0, weight=1)
        chat_area.grid_rowconfigure(0, weight=1)

        self._chat = ctk.CTkScrollableFrame(chat_area, fg_color=COLORS["panel"], corner_radius=8)
        self._chat.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._chat.grid_columnconfigure(0, weight=1)

        input_row = ctk.CTkFrame(chat_area, fg_color="transparent")
        input_row.grid(row=1, column=0, sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)

        self._input = ctk.CTkEntry(
            input_row,
            placeholder_text='Кин, открой Discord...',
            height=40, font=ctk.CTkFont(size=13),
            fg_color=COLORS["card"], border_color=COLORS["card"],
        )
        self._input.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._input.bind("<Return>", lambda e: self._send())

        self._mic_btn = ctk.CTkButton(
            input_row, text="Mic", width=50, height=40,
            fg_color=COLORS["card"], hover_color="#30363d",
            command=self._voice_input,
        )
        self._mic_btn.grid(row=0, column=1, padx=(0, 6))

        ctk.CTkButton(
            input_row, text="Send", width=60, height=40,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._send,
        ).grid(row=0, column=2)

    def _bind_callbacks(self) -> None:
        self.assistant.on_status_change = lambda s: self.after(0, lambda: self._on_status(s))
        self.assistant.on_message = lambda r, t, ok: self.after(0, lambda: self._add_msg(r, t, ok))
        self.assistant.on_listening_change = lambda l: self.after(0, lambda: self._on_listening(l))

    def _on_status(self, status: str) -> None:
        self._status_label.configure(text=status)

    def _on_listening(self, listening: bool) -> None:
        if listening:
            self._toggle_btn.configure(text="Остановить", fg_color=COLORS["red"], hover_color="#da3633")
            self._status_label.configure(text_color=COLORS["green"])
        else:
            self._toggle_btn.configure(text="Активировать", fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
            self._status_label.configure(text_color=COLORS["muted"])

    def _add_msg(self, role: str, text: str, success: bool = True) -> None:
        if role == "user":
            prefix, color, bg = "Вы", COLORS["accent"], COLORS["user"]
        elif role == "system":
            prefix, color, bg = "—", COLORS["muted"], "transparent"
        else:
            prefix = "Кин"
            color = COLORS["text"] if success else COLORS["red"]
            bg = COLORS["bot"]

        frame = ctk.CTkFrame(self._chat, fg_color=bg, corner_radius=6)
        frame.pack(fill="x", padx=8, pady=3)

        ctk.CTkLabel(
            frame, text=f"{prefix}: {text}",
            font=ctk.CTkFont(size=13), text_color=color,
            wraplength=580, justify="left", anchor="w",
        ).pack(anchor="w", padx=10, pady=6)

        self._chat._parent_canvas.yview_moveto(1.0)  # type: ignore[attr-defined]

    def _toggle(self) -> None:
        if self.assistant.is_active:
            self.assistant.stop()
        else:
            threading.Thread(target=self.assistant.start, daemon=True).start()

    def _send(self) -> None:
        text = self._input.get().strip()
        if not text:
            return
        self._input.delete(0, "end")
        threading.Thread(target=self.assistant.send_text_command, args=(text,), daemon=True).start()

    def _voice_input(self) -> None:
        self._mic_btn.configure(fg_color=COLORS["red"])

        def listen() -> None:
            text = self.assistant.listener.listen_once(timeout=5, phrase_limit=10)
            self.after(0, lambda: self._mic_btn.configure(fg_color=COLORS["card"]))
            if text:
                self.after(0, lambda: self._input.insert(0, text))
                self.assistant.process_text(text, source="voice")

        threading.Thread(target=listen, daemon=True).start()

    def _check_api_key(self) -> None:
        if self.assistant.config.validate():
            self._add_msg("system", "Введите Gemini API Key слева и нажмите «Сохранить ключ»", False)

    def _save_api_key(self) -> None:
        key = self._api_entry.get().strip()
        if not key:
            return
        env_path = get_env_path()
        lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
        found = False
        for i, line in enumerate(lines):
            if line.startswith("GEMINI_API_KEY="):
                lines[i] = f"GEMINI_API_KEY={key}"
                found = True
                break
        if not found:
            lines.append(f"GEMINI_API_KEY={key}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.environ["GEMINI_API_KEY"] = key
        self.assistant.reload_api_key(key)
        self._add_msg("system", "API ключ сохранён", True)

    def run(self) -> None:
        self.mainloop()

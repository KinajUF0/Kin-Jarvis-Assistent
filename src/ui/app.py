"""GUI for Kin/Jarvis assistant — Russian, copyable chat, mic selection."""

from __future__ import annotations

import logging
import os
import threading
import tkinter as tk
from typing import TYPE_CHECKING

import customtkinter as ctk

from src.ai.gemini_utils import test_api_key
from src.core.config import WAKE_WORD_DISPLAY
from src.core.paths import get_assets_dir, get_env_path
from src.core.wake_word import strip_wake_word
from src.voice.listener import list_microphones

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
        self.title("Kin Jarvis — AI Ассистент")
        self.geometry("980x660")
        self.minsize(820, 540)
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
        side = ctk.CTkFrame(self, width=260, fg_color=COLORS["panel"], corner_radius=0)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        ctk.CTkLabel(
            side, text="KIN JARVIS",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(24, 2))

        ctk.CTkLabel(
            side, text="AI Ассистент",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).pack(pady=(0, 16))

        self._status_label = ctk.CTkLabel(
            side, text="● Остановлен",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["muted"],
        )
        self._status_label.pack(pady=(0, 10))

        self._toggle_btn = ctk.CTkButton(
            side, text="Активировать", height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._toggle,
        )
        self._toggle_btn.pack(fill="x", padx=16, pady=(0, 16))

        # Microphone
        ctk.CTkLabel(
            side, text="Микрофон",
            font=ctk.CTkFont(size=11), text_color=COLORS["muted"],
        ).pack(anchor="w", padx=16)

        mics = list_microphones()
        if mics:
            mic_labels = [name[:45] for _, name in mics]
            self._mic_map = {label: mics[i][0] for i, label in enumerate(mic_labels)}
        else:
            mic_labels = ["По умолчанию"]
            self._mic_map = {}

        self._mic_var = ctk.StringVar(value=mic_labels[0])
        self._mic_menu = ctk.CTkOptionMenu(
            side, values=mic_labels, variable=self._mic_var,
            height=32, font=ctk.CTkFont(size=11),
            fg_color=COLORS["card"], button_color=COLORS["card"],
            command=self._on_mic_change,
        )
        self._mic_menu.pack(fill="x", padx=16, pady=(4, 16))

        # Wake words
        ctk.CTkLabel(
            side, text="Обращайся:",
            font=ctk.CTkFont(size=11), text_color=COLORS["muted"],
        ).pack(anchor="w", padx=16)

        ctk.CTkLabel(
            side, text=", ".join(WAKE_WORD_DISPLAY.values()),
            font=ctk.CTkFont(size=11), text_color=COLORS["text"],
            wraplength=220, justify="left",
        ).pack(anchor="w", padx=16, pady=(2, 16))

        # API key
        ctk.CTkLabel(
            side, text="Gemini API ключ",
            font=ctk.CTkFont(size=11), text_color=COLORS["muted"],
        ).pack(anchor="w", padx=16)

        self._api_entry = ctk.CTkEntry(
            side, placeholder_text="Вставь ключ с aistudio.google.com",
            height=32, font=ctk.CTkFont(size=11), show="*",
        )
        self._api_entry.pack(fill="x", padx=16, pady=(4, 6))

        self._save_btn = ctk.CTkButton(
            side, text="Сохранить ключ", height=30,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["card"], hover_color="#30363d",
            command=self._save_api_key,
        )
        self._save_btn.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            side, text="Ctrl+C — копировать\nиз чата",
            font=ctk.CTkFont(size=10), text_color=COLORS["muted"],
        ).pack(anchor="w", padx=16, pady=(8, 0))

        # --- Chat ---
        chat_area = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        chat_area.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        chat_area.grid_columnconfigure(0, weight=1)
        chat_area.grid_rowconfigure(0, weight=1)

        chat_frame = ctk.CTkFrame(chat_area, fg_color=COLORS["panel"], corner_radius=8)
        chat_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)

        self._chat = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 12),
            relief=tk.FLAT,
            padx=12, pady=10,
            selectbackground=COLORS["accent"],
            insertbackground=COLORS["text"],
            state=tk.DISABLED,
            cursor="arrow",
        )
        self._chat.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        scrollbar = ctk.CTkScrollbar(chat_frame, command=self._chat.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=4)
        self._chat.configure(yscrollcommand=scrollbar.set)

        self._chat.tag_configure("user", foreground=COLORS["accent"])
        self._chat.tag_configure("bot", foreground=COLORS["text"])
        self._chat.tag_configure("error", foreground=COLORS["red"])
        self._chat.tag_configure("system", foreground=COLORS["muted"])
        self._chat.tag_configure("time", foreground=COLORS["muted"], font=("Segoe UI", 9))

        # Input row
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
            input_row, text="🎤", width=44, height=40,
            fg_color=COLORS["card"], hover_color="#30363d",
            command=self._voice_input,
        )
        self._mic_btn.grid(row=0, column=1, padx=(0, 6))

        ctk.CTkButton(
            input_row, text="→", width=44, height=40,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=16),
            command=self._send,
        ).grid(row=0, column=2)

    def _bind_callbacks(self) -> None:
        self.assistant.on_status_change = lambda s: self.after(0, lambda: self._on_status(s))
        self.assistant.on_message = lambda r, t, ok: self.after(0, lambda: self._add_msg(r, t, ok))
        self.assistant.on_listening_change = lambda l: self.after(0, lambda: self._on_listening(l))

    def _on_mic_change(self, choice: str) -> None:
        idx = self._mic_map.get(choice)
        self.assistant.listener.set_device(idx)
        was_active = self.assistant.is_active
        if was_active:
            self.assistant.stop()
            self.assistant.start()

    def _on_status(self, status: str) -> None:
        color = COLORS["green"] if "Слушаю" in status else COLORS["muted"]
        if "Обработка" in status:
            color = COLORS["accent"]
        self._status_label.configure(text=f"● {status}", text_color=color)

    def _on_listening(self, listening: bool) -> None:
        if listening:
            self._toggle_btn.configure(text="Остановить", fg_color=COLORS["red"], hover_color="#da3633")
        else:
            self._toggle_btn.configure(text="Активировать", fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])

    def _add_msg(self, role: str, text: str, success: bool = True) -> None:
        from datetime import datetime

        self._chat.configure(state=tk.NORMAL)

        time_str = datetime.now().strftime("%H:%M")
        self._chat.insert(tk.END, f"[{time_str}] ", "time")

        if role == "user":
            self._chat.insert(tk.END, f"Вы: {text}\n\n", "user")
        elif role == "system":
            tag = "error" if not success else "system"
            self._chat.insert(tk.END, f"{text}\n\n", tag)
        else:
            tag = "error" if not success else "bot"
            self._chat.insert(tk.END, f"Кин: {text}\n\n", tag)

        self._chat.configure(state=tk.DISABLED)
        self._chat.see(tk.END)

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
        threading.Thread(target=self._process_command, args=(text,), daemon=True).start()

    def _process_command(self, text: str) -> None:
        result = self.assistant.send_text_command(text)
        if result is None:
            self._add_msg(
                "system",
                f"Обращайся по имени: {', '.join(WAKE_WORD_DISPLAY.values())}",
                False,
            )

    def _voice_input(self) -> None:
        self._mic_btn.configure(fg_color=COLORS["red"])

        def listen() -> None:
            text = self.assistant.listener.listen_once(timeout=6, phrase_limit=12, silent=False)
            self.after(0, lambda: self._mic_btn.configure(fg_color=COLORS["card"]))
            if not text:
                return
            self.after(0, lambda: self._input.insert(0, text))
            if not strip_wake_word(text).detected:
                self.after(
                    0,
                    lambda: self._add_msg(
                        "system",
                        f"Скажи: «Кин, ...» — услышал: «{text}»",
                        False,
                    ),
                )
                return
            self.assistant.process_text(text, source="voice")

        threading.Thread(target=listen, daemon=True).start()

    def _check_api_key(self) -> None:
        self._add_msg(
            "system",
            "Команды (Discord, окна, браузер) работают БЕЗ ключа.\n"
            "Gemini — только для сложных вопросов.\n"
            "Или установи Ollama (ollama.com) — работает в РФ.",
            True,
        )

    def _save_api_key(self) -> None:
        key = self._api_entry.get().strip()
        if not key:
            self._add_msg("system", "Вставьте ключ в поле выше.", False)
            return

        self._save_btn.configure(text="Проверка...", state="disabled")

        def save() -> None:
            ok, msg = test_api_key(key, self.assistant.config.gemini_model)
            if not ok:
                self.after(0, lambda: self._add_msg("system", msg, False))
                self.after(0, lambda: self._save_btn.configure(text="Сохранить ключ", state="normal"))
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

            self.after(0, lambda: self._add_msg("system", f"Ключ сохранён и проверен.", True))
            self.after(0, lambda: self._save_btn.configure(text="Сохранить ключ", state="normal"))

        threading.Thread(target=save, daemon=True).start()

    def run(self) -> None:
        self.mainloop()

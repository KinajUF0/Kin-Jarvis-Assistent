"""Modern GUI for Kin/Jarvis assistant using CustomTkinter."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk
from PIL import Image

from src.core.config import WAKE_WORD_DISPLAY
from src.core.paths import get_assets_dir, get_env_path, get_paths_info
from src.actions.browser_detector import get_default_browser

if TYPE_CHECKING:
    from src.core.assistant import KinAssistant

logger = logging.getLogger(__name__)

# Color scheme — futuristic Jarvis aesthetic
COLORS = {
    "bg_dark": "#0a0e17",
    "bg_panel": "#111827",
    "bg_card": "#1a2332",
    "accent_cyan": "#00d4ff",
    "accent_gold": "#ffd700",
    "accent_green": "#00ff88",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "error": "#ff4757",
    "user_bubble": "#1e3a5f",
    "assistant_bubble": "#1a2332",
}


class KinApp(ctk.CTk):
    """Main application window."""

    def __init__(self, assistant: KinAssistant) -> None:
        super().__init__()
        self.assistant = assistant
        self._setup_window()
        self._build_ui()
        self._bind_assistant_callbacks()

    def _setup_window(self) -> None:
        self.title("Kin / Jarvis — AI Assistant")
        self.geometry("1100x750")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=COLORS["bg_dark"])

        # Icon
        logo_path = get_assets_dir() / "logo.png"
        if logo_path.exists():
            try:
                img = Image.open(logo_path)
                self._icon = ctk.CTkImage(img, size=(48, 48))
            except Exception:
                self._icon = None
        else:
            self._icon = None

    def _build_ui(self) -> None:
        # Main grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=280, fg_color=COLORS["bg_panel"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Logo & title
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(25, 10))

        if self._icon:
            ctk.CTkLabel(header, image=self._icon, text="").pack(pady=(0, 8))

        ctk.CTkLabel(
            header,
            text="KIN / JARVIS",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent_cyan"],
        ).pack()
        ctk.CTkLabel(
            header,
            text="AI Assistant v2.0",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack()

        # Status orb
        self._status_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=16)
        self._status_frame.pack(fill="x", padx=20, pady=20)

        self._status_dot = ctk.CTkLabel(
            self._status_frame,
            text="●",
            font=ctk.CTkFont(size=28),
            text_color=COLORS["text_muted"],
        )
        self._status_dot.pack(pady=(15, 0))

        self._status_label = ctk.CTkLabel(
            self._status_frame,
            text="Остановлен",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        self._status_label.pack()

        self._listening_label = ctk.CTkLabel(
            self._status_frame,
            text="Микрофон: выкл",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self._listening_label.pack(pady=(0, 15))

        # Start/Stop button
        self._toggle_btn = ctk.CTkButton(
            sidebar,
            text="▶  АКТИВИРОВАТЬ",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent_cyan"],
            hover_color="#00a8cc",
            text_color=COLORS["bg_dark"],
            height=45,
            corner_radius=12,
            command=self._toggle_assistant,
        )
        self._toggle_btn.pack(fill="x", padx=20, pady=(0, 15))

        # Wake words info
        wake_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=12)
        wake_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            wake_frame,
            text="Ключевые слова",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent_gold"],
        ).pack(anchor="w", padx=15, pady=(12, 5))

        wake_names = ", ".join(WAKE_WORD_DISPLAY.values())
        ctk.CTkLabel(
            wake_frame,
            text=wake_names,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=220,
        ).pack(anchor="w", padx=15, pady=(0, 12))

        # Quick actions
        ctk.CTkLabel(
            sidebar,
            text="Быстрые действия",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(15, 5))

        default_browser = get_default_browser().display_name
        quick_actions = [
            ("Discord", lambda: self._quick_command("Кин, открой Discord")),
            (f"Browser ({default_browser})", lambda: self._quick_command("Кин, открой браузер")),
            ("Steam", lambda: self._quick_command("Кин, открой Steam")),
            ("Lock PC", lambda: self._quick_command("Кин, заблокируй компьютер")),
        ]

        for label, cmd in quick_actions:
            ctk.CTkButton(
                sidebar,
                text=label,
                font=ctk.CTkFont(size=12),
                fg_color=COLORS["bg_card"],
                hover_color="#243044",
                text_color=COLORS["text_primary"],
                height=36,
                corner_radius=8,
                anchor="w",
                command=cmd,
            ).pack(fill="x", padx=20, pady=2)

        # Discord contacts
        contacts = self.assistant.router.discord.list_contacts()
        if contacts:
            ctk.CTkLabel(
                sidebar,
                text="Discord контакты",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=20, pady=(15, 5))

            for c in contacts[:5]:
                name = c.get("display_name", "")
                ctk.CTkButton(
                    sidebar,
                    text=f"👤 {name}",
                    font=ctk.CTkFont(size=11),
                    fg_color="transparent",
                    hover_color=COLORS["bg_card"],
                    text_color=COLORS["text_muted"],
                    height=30,
                    anchor="w",
                    command=lambda n=name: self._quick_command(f"Кин, открой в Discord чат с {n}"),
                ).pack(fill="x", padx=20, pady=1)

    def _build_main_area(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # Tabview
        self._tabs = ctk.CTkTabview(
            main,
            fg_color=COLORS["bg_panel"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent_cyan"],
            segmented_button_selected_hover_color="#00a8cc",
            segmented_button_unselected_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
        )
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        main.grid_rowconfigure(0, weight=1)

        tab_chat = self._tabs.add("💬 Чат")
        tab_chat.grid_columnconfigure(0, weight=1)
        tab_chat.grid_rowconfigure(0, weight=1)

        # Chat history
        self._chat_frame = ctk.CTkScrollableFrame(
            tab_chat,
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
        )
        self._chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self._chat_frame.grid_columnconfigure(0, weight=1)

        # Input area
        input_frame = ctk.CTkFrame(tab_chat, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self._input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text='Скажите или напишите: "Кин, открой Discord"...',
            font=ctk.CTkFont(size=13),
            height=42,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["accent_cyan"],
            text_color=COLORS["text_primary"],
        )
        self._input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._input_entry.bind("<Return>", lambda e: self._send_command())

        ctk.CTkButton(
            input_frame,
            text="➤",
            width=50,
            height=42,
            font=ctk.CTkFont(size=18),
            fg_color=COLORS["accent_cyan"],
            hover_color="#00a8cc",
            text_color=COLORS["bg_dark"],
            command=self._send_command,
        ).grid(row=0, column=1)

        # Voice button
        self._voice_btn = ctk.CTkButton(
            input_frame,
            text="🎤",
            width=50,
            height=42,
            font=ctk.CTkFont(size=18),
            fg_color=COLORS["bg_card"],
            hover_color="#243044",
            command=self._voice_input,
        )
        self._voice_btn.grid(row=0, column=2, padx=(8, 0))

        # Help tab
        tab_help = self._tabs.add("Help")
        self._build_help_tab(tab_help)

        tab_settings = self._tabs.add("Settings")
        self._build_settings_tab(tab_settings)

        # Show API key warning if not configured
        self.after(500, self._check_api_key)

    def _build_settings_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, fg_color=COLORS["bg_dark"])
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        paths = get_paths_info()
        browser = get_default_browser()

        settings_text = f"""
WHERE FILES ARE STORED
======================

Mode:           {paths['mode']}
Program:        {paths['install_dir']}
Your data:      {paths['data_dir']}
Config:         {paths['config_dir']}
Logs:           {paths['logs_dir']}
API Key (.env): {paths['env_file']}

Default browser: {browser.display_name}

WHAT GOES WHERE
===============

- KinJarvis.exe        -> Program folder (do not edit)
- .env                 -> Your Gemini API key
- config/contacts.json -> Discord friends
- config/apps.json     -> Programs list
- logs/kin.log         -> Error logs

FIRST TIME SETUP
================

1. Enter GEMINI_API_KEY below (or edit .env file)
2. Add Discord contacts in config/contacts.json
3. Click ACTIVATE and say: "Kin, open Discord"
        """

        ctk.CTkLabel(
            scroll,
            text=settings_text.strip(),
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLORS["text_secondary"],
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(scroll, text="GEMINI API KEY", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["accent_cyan"]).pack(anchor="w", padx=10, pady=(10, 5))

        self._api_key_entry = ctk.CTkEntry(scroll, width=500, height=36,
                                            placeholder_text="Paste your key from aistudio.google.com/apikey")
        self._api_key_entry.pack(anchor="w", padx=10, pady=5)

        ctk.CTkButton(scroll, text="Save API Key", fg_color=COLORS["accent_cyan"],
                      text_color=COLORS["bg_dark"], command=self._save_api_key).pack(anchor="w", padx=10, pady=10)

        ctk.CTkButton(scroll, text="Open Config Folder", fg_color=COLORS["bg_card"],
                      command=lambda: self._quick_command("Кин, открой папку config")).pack(anchor="w", padx=10, pady=5)

        ctk.CTkButton(scroll, text="Open Logs Folder", fg_color=COLORS["bg_card"],
                      command=lambda: self._quick_command("Кин, открой папку logs")).pack(anchor="w", padx=10, pady=5)

    def _check_api_key(self) -> None:
        errors = self.assistant.config.validate()
        if errors:
            self._tabs.set("Settings")
            self._add_chat_bubble("system", errors[0], success=False)

    def _save_api_key(self) -> None:
        key = self._api_key_entry.get().strip()
        if not key:
            return
        env_path = get_env_path()
        lines = []
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("GEMINI_API_KEY="):
                lines[i] = f"GEMINI_API_KEY={key}"
                updated = True
                break
        if not updated:
            lines.append(f"GEMINI_API_KEY={key}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        import os
        os.environ["GEMINI_API_KEY"] = key
        self._add_chat_bubble("system", f"API key saved to {env_path}", success=True)

    def _build_help_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, fg_color=COLORS["bg_dark"])
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        help_text = """
🎯 КАК ПОЛЬЗОВАТЬСЯ

1. Нажмите «АКТИВИРОВАТЬ» — ассистент начнёт слушать микрофон
2. Обращайтесь по имени: Джарвис, Кин, Jarvis, Астра или Astra
3. На другие имена ассистент НЕ реагирует

📝 ПРИМЕРЫ КОМАНД

• «Кин, как дела?» — обычный разговор
• «Джарвис, открой Discord» — запуск/переключение на Discord
• «Кин, открой в Discord чат с Сэмом» — поиск контакта и открытие DM
• «Jarvis, открой Steam» — запуск Steam
• «Астра, какая погода?» — любой вопрос
• «Кин, установи громкость 50» — управление громкостью
• «Джарvis, заблокируй компьютер» — блокировка экрана
• «Кин, найди рецепт борща» — поиск в Google

💬 DISCORD КОНТАКТЫ

Добавьте контакты в config/contacts.json:
{
  "display_name": "Сэм",
  "username": "[S_E_X_Y] Quinsames",
  "aliases": ["сэм", "sam", "quinsames"],
  "quick_switcher_query": "Quinsames"
}

Ассистент найдёт контакт по максимальному совпадению!

⚙️ НАСТРОЙКА

1. Скопируйте .env.example → .env
2. Вставьте GEMINI_API_KEY
3. Настройте config/contacts.json и config/apps.json
        """
        ctk.CTkLabel(
            scroll,
            text=help_text.strip(),
            font=ctk.CTkFont(family="Consolas", size=13),
            text_color=COLORS["text_secondary"],
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=10, pady=10)

    def _bind_assistant_callbacks(self) -> None:
        self.assistant.on_status_change = lambda s: self.after(0, lambda: self._update_status(s))
        self.assistant.on_message = lambda r, t, ok: self.after(0, lambda: self._add_chat_bubble(r, t, ok))
        self.assistant.on_listening_change = lambda l: self.after(0, lambda: self._update_listening(l))

    def _update_status(self, status: str) -> None:
        self._status_label.configure(text=status)
        if "Слушаю" in status:
            self._status_dot.configure(text_color=COLORS["accent_green"])
        elif "Обработка" in status:
            self._status_dot.configure(text_color=COLORS["accent_gold"])
        else:
            self._status_dot.configure(text_color=COLORS["text_muted"])

    def _update_listening(self, listening: bool) -> None:
        if listening:
            self._listening_label.configure(text="Микрофон: вкл 🎤", text_color=COLORS["accent_green"])
            self._toggle_btn.configure(
                text="⏹  ОСТАНОВИТЬ",
                fg_color=COLORS["error"],
                hover_color="#cc3344",
            )
        else:
            self._listening_label.configure(text="Микрофон: выкл", text_color=COLORS["text_muted"])
            self._toggle_btn.configure(
                text="▶  АКТИВИРОВАТЬ",
                fg_color=COLORS["accent_cyan"],
                hover_color="#00a8cc",
            )

    def _add_chat_bubble(self, role: str, text: str, success: bool = True) -> None:
        if role == "system":
            color = COLORS["text_muted"]
            prefix = "⚙ "
            bg = "transparent"
        elif role == "user":
            color = COLORS["accent_cyan"]
            prefix = "Вы: "
            bg = COLORS["user_bubble"]
        else:
            color = COLORS["accent_gold"] if success else COLORS["error"]
            prefix = "Кин: "
            bg = COLORS["assistant_bubble"]

        bubble = ctk.CTkFrame(self._chat_frame, fg_color=bg, corner_radius=10)
        bubble.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(
            bubble,
            text=f"{prefix}{text}",
            font=ctk.CTkFont(size=13),
            text_color=color,
            wraplength=650,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=8)

        # Auto-scroll
        self._chat_frame._parent_canvas.yview_moveto(1.0)  # type: ignore[attr-defined]

    def _toggle_assistant(self) -> None:
        if self.assistant.is_active:
            self.assistant.stop()
        else:
            threading.Thread(target=self.assistant.start, daemon=True).start()

    def _send_command(self) -> None:
        text = self._input_entry.get().strip()
        if not text:
            return
        self._input_entry.delete(0, "end")
        threading.Thread(
            target=self.assistant.send_text_command,
            args=(text,),
            daemon=True,
        ).start()

    def _quick_command(self, command: str) -> None:
        self._input_entry.delete(0, "end")
        self._input_entry.insert(0, command)
        self._send_command()

    def _voice_input(self) -> None:
        """One-shot voice input from UI button."""
        self._voice_btn.configure(text="🔴", fg_color=COLORS["error"])

        def _listen() -> None:
            text = self.assistant.listener.listen_once(timeout=5, phrase_limit=10)
            self.after(0, lambda: self._voice_btn.configure(text="🎤", fg_color=COLORS["bg_card"]))
            if text:
                self.after(0, lambda: self._input_entry.insert(0, text))
                self.assistant.process_text(text, source="voice")

        threading.Thread(target=_listen, daemon=True).start()

    def run(self) -> None:
        self.mainloop()

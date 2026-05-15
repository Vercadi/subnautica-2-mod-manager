from __future__ import annotations

import customtkinter as ctk

from ... import __app_name__, __version__
from ..ui_tokens import UiTokens


class CommandBar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        tokens: UiTokens,
        path_text: str = "Subnautica 2 install not detected",
        build_text: str = "",
        on_launch=None,
        on_check_updates=None,
        on_help=None,
        on_settings=None,
    ):
        colors = tokens.colors
        super().__init__(
            master,
            fg_color=colors.glass_black,
            corner_radius=tokens.panel_radius,
            border_width=1,
            border_color=colors.shell_border_dim,
        )
        self.tokens = tokens
        self.path_text = path_text
        self.build_text = build_text
        self.on_launch = on_launch
        self.on_check_updates = on_check_updates
        self.on_help = on_help
        self.on_settings = on_settings
        self.path_label: ctk.CTkLabel | None = None
        self.badge_label: ctk.CTkLabel | None = None
        self.grid_columnconfigure(2, weight=1)
        self._build()

    def _build(self) -> None:
        t = self.tokens
        c = t.colors
        title = ctk.CTkLabel(
            self,
            text=__app_name__,
            font=(t.font_family, t.page_title, "bold"),
            text_color=c.text_primary,
        )
        title.grid(row=0, column=0, sticky="w", padx=(22, 12), pady=16)

        self.badge_label = ctk.CTkLabel(
            self,
            text=self.build_text or f"Community Build  {__version__}",
            font=(t.font_family, t.tiny, "bold"),
            text_color=c.accent_biolume,
            fg_color=c.glass_cyan,
            corner_radius=5,
            padx=10,
            pady=4,
        )
        self.badge_label.grid(row=0, column=1, sticky="w", padx=(0, 16))

        self.path_label = ctk.CTkLabel(
            self,
            text=f"[DIR] {self._compact_path_text()}",
            font=(t.font_family, t.body),
            text_color=c.text_secondary,
            fg_color=c.glass_navy,
            corner_radius=7,
            padx=12,
            pady=9,
        )
        self.path_label.grid(row=0, column=2, sticky="ew", padx=(0, 18))

        launch = _command_button(self, t, "[>] Launch", primary=True, width=116)
        launch.configure(command=self._launch_clicked)
        launch.grid(row=0, column=3, padx=(0, 10), pady=12)

        updates = _command_button(self, t, "Updates", width=92)
        updates.configure(command=self._updates_clicked)
        updates.grid(row=0, column=4, padx=(0, 10), pady=12)

        help_button = _command_button(self, t, "Help", width=70)
        help_button.configure(command=self._help_clicked)
        help_button.grid(row=0, column=5, padx=(0, 10), pady=12)

        settings = _command_button(self, t, "Settings", width=96)
        settings.configure(command=self._settings_clicked)
        settings.grid(row=0, column=6, padx=(0, 20), pady=12)

    def _compact_path_text(self) -> str:
        text = str(self.path_text or "").strip()
        if len(text) <= 18:
            return text
        if "not detected" in text.casefold():
            return "Install not detected"
        return "S2 OK"

    def _settings_clicked(self) -> None:
        if self.on_settings:
            self.on_settings()

    def _launch_clicked(self) -> None:
        if self.on_launch:
            self.on_launch()

    def _updates_clicked(self) -> None:
        if self.on_check_updates:
            self.on_check_updates()

    def _help_clicked(self) -> None:
        if self.on_help:
            self.on_help()

    def set_status(self, *, path_text: str, build_text: str) -> None:
        self.path_text = path_text
        self.build_text = build_text
        if self.path_label is not None:
            self.path_label.configure(text=f"[DIR] {self._compact_path_text()}")
        if self.badge_label is not None:
            self.badge_label.configure(text=self.build_text or f"Community Build  {__version__}")


def _command_button(master, tokens: UiTokens, text: str, *, primary: bool = False, width: int = 112) -> ctk.CTkButton:
    colors = tokens.colors
    if primary:
        fg = "#176EC4"
        hover = "#2186E0"
        text_color = colors.text_primary
        border_color = "#2E9CF2"
    else:
        fg = colors.glass_navy
        hover = colors.panel_glass
        text_color = colors.text_primary
        border_color = colors.border_cold
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=34,
        corner_radius=tokens.button_radius,
        fg_color=fg,
        hover_color=hover,
        text_color=text_color,
        border_width=1,
        border_color=border_color,
        font=(tokens.font_family, tokens.body, "bold" if primary else "normal"),
    )

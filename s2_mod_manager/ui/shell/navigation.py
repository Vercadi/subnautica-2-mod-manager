from __future__ import annotations

import customtkinter as ctk

from ..ui_tokens import UiTokens
from .status_gauge import OxygenGauge


NAV_ITEMS = (
    ("Installed Mods", "[M]"),
    ("Profiles", "[@]"),
    ("Recovery", "[#]"),
    ("Diagnostics", "[~]"),
    ("Activity", "[A]"),
    ("Help / Support", "[?]"),
)


class NavigationRail(ctk.CTkFrame):
    def __init__(self, master, *, tokens: UiTokens, active: str = "Installed Mods", on_select=None):
        colors = tokens.colors
        super().__init__(
            master,
            width=tokens.nav_width,
            fg_color=colors.glass_black,
            corner_radius=tokens.panel_radius,
            border_width=1,
            border_color=colors.border_soft,
        )
        self.tokens = tokens
        self.active = active
        self.on_select = on_select
        self.grid_propagate(False)
        self._build()

    def _build(self) -> None:
        c = self.tokens.colors
        ctk.CTkLabel(
            self,
            text="DIVE SYSTEMS",
            text_color=c.text_muted,
            font=(self.tokens.font_family, self.tokens.tiny, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 5))
        for index, (label, icon) in enumerate(NAV_ITEMS):
            button = self._nav_button(label, icon)
            button.grid(row=index + 1, column=0, sticky="ew", padx=12, pady=(5 if index == 0 else 3, 3))
        self.grid_rowconfigure(len(NAV_ITEMS) + 1, weight=1)
        gauge = OxygenGauge(self, tokens=self.tokens, value=98)
        gauge.grid(row=len(NAV_ITEMS) + 2, column=0, sticky="s", padx=16, pady=(20, 18))

    def _nav_button(self, label: str, icon: str) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        active = label == self.active
        row = ctk.CTkFrame(self, fg_color="transparent", height=44)
        row.grid_propagate(False)
        row.grid_columnconfigure(1, weight=1)
        ctk.CTkFrame(
            row,
            width=4,
            height=30,
            fg_color=c.accent_lagoon if active else "transparent",
            corner_radius=3,
        ).grid(row=0, column=0, sticky="nsw", padx=(0, 6), pady=5)
        ctk.CTkButton(
            row,
            text=f"{icon}  {label}",
            anchor="w",
            height=40,
            corner_radius=7,
            fg_color=c.glass_cyan if active else "transparent",
            hover_color=c.panel_glass_hover,
            border_width=1 if active else 0,
            border_color=c.shell_border if active else c.border_soft,
            text_color=c.text_primary if active else c.text_secondary,
            font=(t.font_family, t.body, "bold" if active else "normal"),
            command=lambda value=label: self._clicked(value),
        ).grid(row=0, column=1, sticky="ew")
        return row

    def _clicked(self, label: str) -> None:
        self.set_active(label)
        if self.on_select:
            self.on_select(label)

    def set_active(self, label: str) -> None:
        self.active = label
        for child in self.winfo_children():
            child.destroy()
        self._build()

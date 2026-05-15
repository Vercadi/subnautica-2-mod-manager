from __future__ import annotations

import customtkinter as ctk

from ...models.activity import ActivityRecord
from ..ui_tokens import UiTokens
from ..window_utils import configure_dialog


class ActivityDialog(ctk.CTkToplevel):
    def __init__(self, master, *, tokens: UiTokens, records: list[ActivityRecord]):
        super().__init__(master)
        self.tokens = tokens
        self.records = records
        self.title("Activity / Recent Events")
        self.configure(fg_color=tokens.colors.bg_abyss)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        configure_dialog(self, master, width=820, height=600, min_width=700, min_height=480, modal=True, topmost=True)

    def _build(self) -> None:
        t = self.tokens
        c = t.colors
        header = ctk.CTkFrame(
            self,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.shell_border_dim,
        )
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        ctk.CTkLabel(
            header,
            text="Activity / Recent Events",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            header,
            text=f"Showing the latest {len(self.records)} recorded event(s).",
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
        ).pack(anchor="w", padx=14, pady=(0, 10))

        body = ctk.CTkScrollableFrame(
            self,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.border_soft,
            scrollbar_button_color=c.glass_cyan,
            scrollbar_button_hover_color=c.panel_glass_hover,
        )
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        body.grid_columnconfigure(1, weight=1)
        if not self.records:
            ctk.CTkLabel(body, text="No activity records yet.", text_color=c.text_muted, font=(t.font_family, t.small)).grid(row=0, column=0, sticky="w", padx=12, pady=12)
        for index, record in enumerate(reversed(self.records), start=1):
            ctk.CTkLabel(body, text=record.created_at.replace("+00:00", "Z"), text_color=c.text_muted, font=(t.mono_family, t.tiny)).grid(row=index, column=0, sticky="nw", padx=12, pady=4)
            ctk.CTkLabel(
                body,
                text=record.summary_text,
                text_color=c.text_secondary,
                font=(t.font_family, t.small),
                wraplength=590,
                justify="left",
            ).grid(row=index, column=1, sticky="ew", padx=(0, 12), pady=4)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            footer,
            text="Close",
            width=96,
            height=34,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            command=self.destroy,
        ).grid(row=0, column=1, sticky="e")

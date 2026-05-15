from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from ..ui_tokens import UiTokens


class ConsolePanel(ctk.CTkFrame):
    def __init__(self, master, *, tokens: UiTokens, on_recovery=None, on_activity=None):
        colors = tokens.colors
        super().__init__(
            master,
            fg_color=colors.glass_black,
            corner_radius=tokens.panel_radius,
            border_width=1,
            border_color=colors.shell_border_dim,
        )
        self.tokens = tokens
        self.on_recovery = on_recovery
        self.on_activity = on_activity
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()

    def _build(self) -> None:
        t = self.tokens
        c = t.colors
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 0))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Status Log",
            font=(t.font_family, t.small, "bold"),
            text_color=c.text_secondary,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            header,
            text="Activity",
            width=74,
            height=24,
            corner_radius=5,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            text_color=c.text_secondary,
            command=self._activity_clicked,
        ).grid(row=0, column=1, sticky="e", padx=(0, 6))
        ctk.CTkButton(
            header,
            text="Recovery",
            width=78,
            height=24,
            corner_radius=5,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            text_color=c.text_secondary,
            command=self._recovery_clicked,
        ).grid(row=0, column=2, sticky="e", padx=(0, 6))
        ctk.CTkButton(
            header,
            text="Clear",
            width=52,
            height=24,
            corner_radius=5,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            text_color=c.text_secondary,
            command=self.clear,
        ).grid(row=0, column=3, sticky="e")

        self.textbox = ctk.CTkTextbox(
            self,
            height=48,
            fg_color="#020B12",
            text_color=c.accent_kelp,
            border_width=1,
            border_color=c.border_soft,
            font=(t.mono_family, t.mono),
            wrap="none",
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 10))
        self.seed()

    def seed(self) -> None:
        lines = [
            "Console initialized.",
            "Preview & Apply can install safe managed plans and records every file in the manifest.",
            "Recovery removes only manifest-tracked managed files; unknown files are left alone.",
            "Loose root overlays are review-required and blocked from automatic apply.",
            "Scanner, library, profile, preview, manifest, recovery, and diagnostics services ready.",
            "Waiting for scan, import, profile, or preview action.",
        ]
        self.textbox.delete("1.0", "end")
        for line in lines:
            self.write(line)

    def write(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.textbox.insert("end", f"[{stamp}] {message}\n")
        self.textbox.see("end")

    def clear(self) -> None:
        self.textbox.delete("1.0", "end")

    def _recovery_clicked(self) -> None:
        if self.on_recovery:
            self.on_recovery()

    def _activity_clicked(self) -> None:
        if self.on_activity:
            self.on_activity()

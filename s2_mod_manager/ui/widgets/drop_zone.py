from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ..ui_tokens import UiTokens


class DropZone(ctk.CTkFrame):
    def __init__(self, master, *, tokens: UiTokens, on_browse_files=None, on_browse_folder=None, compact: bool = False):
        super().__init__(master, fg_color="transparent")
        self.tokens = tokens
        self.on_browse_files = on_browse_files
        self.on_browse_folder = on_browse_folder
        self.on_drop = None
        self.compact = compact
        self.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            self,
            width=112 if compact else 300,
            height=36 if compact else 94,
            highlightthickness=0,
            bd=0,
            bg=tokens.colors.glass_black,
        )
        self.canvas.grid(row=0, column=0, sticky="ew")
        self.canvas.bind("<Configure>", self._draw_drop_zone)
        self.canvas.bind("<Button-1>", self._browse_files_clicked)
        self._build_fallback_buttons()

    def enable_native_drop(self, callback) -> bool:
        self.on_drop = callback
        try:
            from tkinterdnd2 import DND_FILES

            for widget in (self, self.canvas):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._drop_received)
            return True
        except Exception:
            return False

    def _draw_drop_zone(self, _event=None) -> None:
        c = self.canvas
        colors = self.tokens.colors
        width = max(1, c.winfo_width())
        height = max(1, c.winfo_height())
        c.delete("all")
        c.create_rectangle(
            8,
            8,
            width - 8,
            height - 8,
            outline=colors.shell_border_dim,
            width=2,
            dash=(5, 4),
            fill="#031522",
        )
        cx = width // 2
        cy = height // 2
        for offset in range(16, width, 42):
            c.create_line(offset, height - 14, offset + 64, 14, fill="#092B3A", width=1)
        for radius, alpha_color in ((26, colors.border_soft), (46, colors.shell_border_dim), (66, "#063247")):
            c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=alpha_color, width=1)
        if self.compact:
            label = "Drop" if width < 180 else "Drop or browse pak bundles, archives, and UE4SS folders"
            c.create_text(
                18,
                cy,
                text="+",
                fill=colors.accent_lagoon,
                font=("Segoe UI", 18, "bold"),
            )
            c.create_text(
                36,
                cy,
                text=label,
                fill=colors.text_primary,
                anchor="w",
                font=("Segoe UI", 12, "bold"),
            )
            return
        c.create_text(cx, cy - 25, text="[ DROP ]", fill=colors.accent_lagoon, font=("Segoe UI", 12, "bold"))
        c.create_text(cx, cy, text="Drop .pak / UE4SS mods here", fill=colors.text_primary, font=("Segoe UI", 15, "bold"))
        c.create_text(cx, cy + 25, text="Browse or drop archives, pak bundles, and UE4SS folders", fill=colors.text_muted, font=("Segoe UI", 11))

    def _build_fallback_buttons(self) -> None:
        if self.compact:
            return
        t = self.tokens
        c = t.colors
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        controls.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            controls,
            text="Browse Files",
            width=112,
            height=26,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny, "bold"),
            command=self._browse_files_clicked,
        ).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(
            controls,
            text="Browse Folder",
            width=118,
            height=26,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny, "bold"),
            command=self._browse_folder_clicked,
        ).grid(row=0, column=2)

    def _browse_files_clicked(self, _event=None) -> None:
        if self.on_browse_files:
            self.on_browse_files()

    def _browse_folder_clicked(self) -> None:
        if self.on_browse_folder:
            self.on_browse_folder()

    def _drop_received(self, event) -> None:
        if self.on_drop:
            self.on_drop(event.data)

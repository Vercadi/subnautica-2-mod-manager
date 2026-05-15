from __future__ import annotations

import webbrowser
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...models.help_about import FolderShortcut, HelpAboutView
from ..ui_tokens import UiTokens
from ..window_utils import configure_dialog
from .mod_row import _fit_text


class HelpAboutDialog(ctk.CTkToplevel):
    def __init__(self, master, *, tokens: UiTokens, view: HelpAboutView, on_open_folder):
        super().__init__(master)
        self.tokens = tokens
        self.view = view
        self.on_open_folder = on_open_folder
        self.result_label: ctk.CTkLabel | None = None
        self.title("Help / About / Support")
        self.configure(fg_color=tokens.colors.bg_abyss)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        configure_dialog(self, master, width=960, height=700, min_width=820, min_height=580, modal=True, topmost=True)

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
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Help / About / Support",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            header,
            text=f"{self.view.app_name} {self.view.app_version} | {self.view.build_metadata}",
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
            wraplength=820,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

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
        body.grid_columnconfigure(0, weight=1)
        row = 0
        row = self._links_card(body, row)
        row = self._shortcuts_card(body, row)
        row = self._safety_card(body, row)
        self._support_card(body, row)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            footer,
            text=self.view.summary_text,
            text_color=c.text_muted,
            font=(t.font_family, t.small),
            anchor="w",
        )
        self.result_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
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
        ).grid(row=0, column=1)

    def _links_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Project Links")
        for index, (label, url) in enumerate(
            (
                ("GitHub", self.view.github_url),
                ("Releases", self.view.releases_url),
                ("Nexus", self.view.nexus_url),
                ("Issues", self.view.issues_url),
                ("Patreon", self.view.patreon_url),
                ("Ko-fi", self.view.kofi_url),
            ),
            start=1,
        ):
            self._button(card, 1 + ((index - 1) // 4), label, lambda value=url: webbrowser.open(value), column=((index - 1) % 4) + 1, disabled=not bool(url))
        return row + 1

    def _shortcuts_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Folder Shortcuts")
        for index, shortcut in enumerate(self.view.shortcuts, start=1):
            self._value(card, index, shortcut.label, shortcut.status_text)
            self._button(
                card,
                index,
                "Open",
                lambda item=shortcut: self._open_shortcut(item),
                column=2,
                disabled=not shortcut.available,
            )
        return row + 1

    def _safety_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Safety / Support Status")
        self._value(card, 1, "Safety", self.view.safety_text)
        self._value(card, 2, "Archives", self.view.archive_support_text)
        self._value(card, 3, "Nexus Support", "Support reports are local text only. Personal home paths and save paths are redacted or omitted.")
        return row + 1

    def _support_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Support Report")
        card.grid_columnconfigure(1, weight=1)
        text = ctk.CTkTextbox(
            card,
            height=190,
            fg_color="#020B12",
            text_color=self.tokens.colors.text_secondary,
            border_width=1,
            border_color=self.tokens.colors.border_soft,
            font=(self.tokens.mono_family, self.tokens.mono),
            wrap="word",
        )
        text.grid(row=1, column=0, columnspan=4, sticky="ew", padx=12, pady=(4, 8))
        text.insert("1.0", self.view.support_report)
        text.configure(state="disabled")
        self._button(card, 2, "Copy Report", self._copy_report, column=1)
        self._button(card, 2, "Save Report", self._save_report, column=2)
        return row + 1

    def _card(self, parent, row: int, title: str) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        card = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        card.grid(row=row, column=0, sticky="ew", padx=8, pady=8)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text=title, text_color=c.text_primary, font=(t.font_family, t.small, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(8, 4))
        return card

    def _value(self, card, row: int, label: str, value: str) -> None:
        t = self.tokens
        c = t.colors
        ctk.CTkLabel(card, text=label, width=112, anchor="w", text_color=c.text_muted, font=(t.font_family, t.tiny, "bold")).grid(row=row, column=0, sticky="nw", padx=12, pady=3)
        ctk.CTkLabel(
            card,
            text=_fit_text(value, 150),
            anchor="w",
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny),
            wraplength=640,
            justify="left",
        ).grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=3)

    def _button(self, card, row: int, text: str, command, *, column: int, disabled: bool = False) -> None:
        t = self.tokens
        c = t.colors
        ctk.CTkButton(
            card,
            text=text,
            width=104,
            height=28,
            fg_color=c.disabled if disabled else c.glass_black,
            hover_color=c.disabled if disabled else c.panel_glass,
            border_width=1,
            border_color=c.border_soft if disabled else c.border_cold,
            text_color=c.text_muted if disabled else c.text_secondary,
            font=(t.font_family, t.tiny, "bold"),
            state="disabled" if disabled else "normal",
            command=command,
        ).grid(row=row, column=column, sticky="e", padx=(0, 8), pady=4)

    def _open_shortcut(self, shortcut: FolderShortcut) -> None:
        message = self.on_open_folder(shortcut.path)
        if self.result_label is not None:
            self.result_label.configure(text=message)

    def _copy_report(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.view.support_report)
        if self.result_label is not None:
            self.result_label.configure(text="Support report copied to clipboard.", text_color=self.tokens.colors.accent_biolume)

    def _save_report(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save support report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        Path(path).write_text(self.view.support_report, encoding="utf-8")
        if self.result_label is not None:
            self.result_label.configure(text=f"Support report saved: {path}", text_color=self.tokens.colors.accent_biolume)

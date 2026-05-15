from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ...models.import_review import ImportReview, ImportSelection
from ..ui_tokens import UiTokens
from ..window_utils import configure_dialog
from .mod_row import _fit_text


class ImportReviewDialog(ctk.CTkToplevel):
    def __init__(self, master, *, tokens: UiTokens, review: ImportReview, on_import):
        super().__init__(master)
        self.tokens = tokens
        self.review = review
        self.on_import = on_import
        self.source_vars: dict[str, tk.BooleanVar] = {}
        self.component_vars: dict[tuple[str, str], tk.BooleanVar] = {}
        self.title("Scan Results / Import Review")
        self.configure(fg_color=tokens.colors.bg_abyss)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        configure_dialog(self, master, width=920, height=660, min_width=780, min_height=560, modal=True, topmost=True)

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
            text="Scan Results / Import Review",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            header,
            text=self.review.summary_text + "  Game install writes remain disabled.",
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
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
        if not self.review.sources:
            self._empty_state(body)
        for row, source in enumerate(self.review.sources):
            self._source_card(body, source).grid(row=row, column=0, sticky="ew", padx=8, pady=8)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            footer,
            text="Cancel",
            width=110,
            height=34,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            command=self.destroy,
        ).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(
            footer,
            text="Import Selected",
            width=150,
            height=34,
            fg_color=c.glass_cyan,
            hover_color=c.panel_glass_hover,
            border_width=1,
            border_color=c.shell_border,
            text_color=c.text_primary,
            state="normal" if self.review.importable_source_count else "disabled",
            command=self._import_clicked,
        ).grid(row=0, column=2)

    def _empty_state(self, parent) -> None:
        ctk.CTkLabel(
            parent,
            text="No sources were provided for review.",
            text_color=self.tokens.colors.text_secondary,
            font=(self.tokens.font_family, self.tokens.body),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=18)

    def _source_card(self, parent, source) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        card = ctk.CTkFrame(
            parent,
            fg_color=c.glass_navy,
            corner_radius=t.row_radius,
            border_width=1,
            border_color=c.warning if source.issue_count or source.ambiguous else c.border_soft,
        )
        card.grid_columnconfigure(1, weight=1)
        source_var = tk.BooleanVar(value=source.selected)
        self.source_vars[source.source_key] = source_var
        ctk.CTkCheckBox(
            card,
            text="",
            width=24,
            variable=source_var,
            fg_color=c.accent_lagoon,
            hover_color=c.panel_glass_hover,
            border_color=c.border_cold,
            state="normal" if source.importable and not source.already_imported else "disabled",
        ).grid(row=0, column=0, rowspan=3, sticky="n", padx=(12, 6), pady=12)
        ctk.CTkLabel(
            card,
            text=_fit_text(source.display_name, 72),
            text_color=c.text_primary,
            font=(t.font_family, t.row_title, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(10, 0))
        ctk.CTkLabel(
            card,
            text=_fit_text(f"{source.status_text} | {source.source_kind} | {source.source_path}", 118),
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(1, 5))
        self._issues(card, source).grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=(0, 6))
        component_frame = ctk.CTkFrame(card, fg_color="transparent")
        component_frame.grid(row=3, column=1, sticky="ew", padx=(0, 12), pady=(0, 10))
        component_frame.grid_columnconfigure(1, weight=1)
        if not source.components:
            ctk.CTkLabel(
                component_frame,
                text="No importable S2 component detected.",
                text_color=c.text_muted,
                font=(t.font_family, t.small),
            ).grid(row=0, column=0, sticky="w")
        for index, component in enumerate(source.components):
            grid_row = index * 2
            component_var = tk.BooleanVar(value=component.selected and source.selected)
            self.component_vars[(source.source_key, component.component_id)] = component_var
            ctk.CTkCheckBox(
                component_frame,
                text="",
                width=22,
                variable=component_var,
                fg_color=c.accent_lagoon,
                hover_color=c.panel_glass_hover,
                border_color=c.border_cold,
                state="normal" if source.importable and not source.already_imported and component.selected else "disabled",
            ).grid(row=grid_row, column=0, sticky="n", padx=(0, 8), pady=3)
            ctk.CTkLabel(
                component_frame,
                text=_fit_text(component.display_name, 58),
                text_color=c.text_primary,
                font=(t.font_family, t.small, "bold"),
                anchor="w",
            ).grid(row=grid_row, column=1, sticky="ew", pady=3)
            ctk.CTkLabel(
                component_frame,
                text=_fit_text(component.status_text, 72),
                text_color=c.warning if component.review_policy_text else c.text_muted,
                font=(t.font_family, t.tiny),
                anchor="e",
            ).grid(row=grid_row, column=2, sticky="e", padx=(8, 0), pady=3)
            if component.review_policy_text:
                ctk.CTkLabel(
                    component_frame,
                    text=_fit_text(component.review_policy_text, 136),
                    text_color=c.warning,
                    font=(t.font_family, t.tiny),
                    wraplength=720,
                    justify="left",
                    anchor="w",
                ).grid(row=grid_row + 1, column=1, columnspan=2, sticky="ew", pady=(0, 6))
        return card

    def _issues(self, parent, source) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        messages = []
        messages.extend(source.errors)
        messages.extend(source.warnings)
        messages.extend(f"Unsupported: {path}" for path in source.unsupported_files)
        messages.extend(f"Unsafe path rejected: {path}" for path in source.unsafe_entries)
        if not messages:
            ctk.CTkLabel(
                frame,
                text="No scan issues.",
                text_color=c.text_muted,
                font=(t.font_family, t.tiny),
            ).grid(row=0, column=0, sticky="w")
            return frame
        ctk.CTkLabel(
            frame,
            text=_fit_text(" | ".join(dict.fromkeys(messages)), 130),
            text_color=c.warning,
            font=(t.font_family, t.tiny),
            wraplength=720,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        return frame

    def _import_clicked(self) -> None:
        selected: dict[str, set[str]] = {}
        for source in self.review.sources:
            if not self.source_vars[source.source_key].get():
                continue
            component_ids = {
                component.component_id
                for component in source.components
                if self.component_vars.get((source.source_key, component.component_id), tk.BooleanVar(value=False)).get()
            }
            if component_ids:
                selected[source.source_key] = component_ids
        self.on_import(ImportSelection(selected))
        self.destroy()

from __future__ import annotations

import customtkinter as ctk

from ...models.apply_preview import ApplyPreview
from ..ui_tokens import UiTokens
from ..window_utils import configure_dialog
from .mod_row import _fit_text


class ApplyPreviewDialog(ctk.CTkToplevel):
    def __init__(self, master, *, tokens: UiTokens, preview: ApplyPreview, on_apply):
        super().__init__(master)
        self.tokens = tokens
        self.preview = preview
        self.on_apply = on_apply
        self.result_label: ctk.CTkLabel | None = None
        self.apply_button: ctk.CTkButton | None = None
        self.title("Preview & Apply Profile")
        self.configure(fg_color=tokens.colors.bg_abyss)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        configure_dialog(self, master, width=980, height=700, min_width=820, min_height=580, modal=True, topmost=True)

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
            text=f"Preview & Apply Profile: {self.preview.profile_name}",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            header,
            text=_fit_text(str(self.preview.target_root or "Target install not configured"), 110),
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 2))
        ctk.CTkLabel(
            header,
            text=f"{self.preview.mode_text} | {self.preview.summary_text}",
            text_color=c.accent_biolume if self.preview.allow_apply else c.warning if self.preview.blocked else c.text_secondary,
            font=(t.font_family, t.small, "bold"),
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 10))

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
        row = self._summary_grid(body, row)
        row = self._review_policy(body, row)
        row = self._messages(body, row, "Errors", self.preview.errors, c.danger)
        row = self._messages(body, row, "Warnings", self.preview.warnings, c.warning)
        row = self._skips(body, row)
        self._actions(body, row)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            footer,
            text=self.preview.disabled_reason or "Managed apply is available. Review the planned file actions before continuing.",
            text_color=c.accent_biolume if self.preview.allow_apply else c.text_muted,
            font=(t.font_family, t.small),
            anchor="w",
        )
        self.result_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkButton(
            footer,
            text="Close",
            width=100,
            height=34,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            command=self.destroy,
        ).grid(row=0, column=1, padx=(0, 8))
        self.apply_button = ctk.CTkButton(
            footer,
            text=self.preview.apply_button_text,
            width=190,
            height=34,
            fg_color=c.glass_cyan if self.preview.allow_apply else c.disabled,
            hover_color=c.panel_glass_hover if self.preview.allow_apply else c.disabled,
            border_width=1,
            border_color=c.shell_border if self.preview.allow_apply else c.border_soft,
            text_color=c.text_primary if self.preview.allow_apply else c.text_muted,
            state="normal" if self.preview.allow_apply else "disabled",
            command=self._apply_clicked,
        )
        self.apply_button.grid(row=0, column=2)

    def _summary_grid(self, parent, row: int) -> int:
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=8)
        for index, (label, value) in enumerate(
            (
                ("Mode", self.preview.mode_text),
                ("Blocked", self.preview.blocked_text),
                ("Creates", str(self.preview.creates)),
                ("Overwrites", str(self.preview.overwrites)),
                ("Deletes", str(self.preview.deletes)),
                ("Backups", str(self.preview.backup_count)),
                ("Skips", str(self.preview.skips)),
                ("Fake Test", "yes" if self.preview.fake_test_install else "no"),
                ("Real Apply", "enabled" if self.preview.real_apply_enabled else "disabled"),
            )
        ):
            frame.grid_columnconfigure(index, weight=1)
            cell = ctk.CTkFrame(frame, fg_color="transparent")
            cell.grid(row=0, column=index, sticky="nsew", padx=6, pady=8)
            ctk.CTkLabel(cell, text=label, text_color=c.text_muted, font=(t.font_family, t.tiny, "bold")).pack(anchor="w")
            ctk.CTkLabel(cell, text=value, text_color=c.text_primary, font=(t.font_family, t.small, "bold")).pack(anchor="w")
        return row + 1

    def _review_policy(self, parent, row: int) -> int:
        if not self.preview.review_policy_text:
            return row
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=f"Review Required ({self.preview.review_required_count} blocked file action(s))",
            text_color=c.warning,
            font=(t.font_family, t.small, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(
            frame,
            text=self.preview.review_policy_text,
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny),
            wraplength=820,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        return row + 1

    def _messages(self, parent, row: int, title: str, messages: list[str], color: str) -> int:
        if not messages:
            return row
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=title, text_color=color, font=(t.font_family, t.small, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))
        for index, message in enumerate(messages[:12], start=1):
            ctk.CTkLabel(
                frame,
                text=_fit_text(message, 132),
                text_color=c.text_secondary,
                font=(t.font_family, t.tiny),
                wraplength=820,
                justify="left",
            ).grid(row=index, column=0, sticky="w", padx=12, pady=(0, 2))
        if len(messages) > 12:
            ctk.CTkLabel(frame, text=f"... {len(messages) - 12} more", text_color=c.text_muted, font=(t.font_family, t.tiny)).grid(row=13, column=0, sticky="w", padx=12, pady=(0, 8))
        return row + 1

    def _skips(self, parent, row: int) -> int:
        if not self.preview.skip_items:
            return row
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 8))
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Skipped", text_color=c.text_secondary, font=(t.font_family, t.small, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 2))
        for index, skip in enumerate(self.preview.skip_items[:10], start=1):
            ctk.CTkLabel(frame, text=_fit_text(skip.component_name, 32), text_color=c.text_primary, font=(t.font_family, t.tiny, "bold")).grid(row=index, column=0, sticky="w", padx=12, pady=(0, 2))
            ctk.CTkLabel(frame, text=_fit_text(skip.reason, 82), text_color=c.text_muted, font=(t.font_family, t.tiny)).grid(row=index, column=1, sticky="w", padx=8, pady=(0, 2))
        return row + 1

    def _actions(self, parent, row: int) -> None:
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 8))
        frame.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(frame, text="Planned File Actions", text_color=c.text_primary, font=(t.font_family, t.small, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 4))
        if not self.preview.actions:
            ctk.CTkLabel(frame, text="No enabled imported components are ready to deploy.", text_color=c.text_muted, font=(t.font_family, t.small)).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))
            return
        for index, action in enumerate(self.preview.actions[:80], start=1):
            color = c.warning if action.action in {"overwrite", "blocked", "delete"} else c.accent_biolume if action.action == "create" else c.text_secondary
            ctk.CTkLabel(frame, text=action.action.upper(), text_color=color, font=(t.font_family, t.tiny, "bold")).grid(row=index, column=0, sticky="nw", padx=12, pady=2)
            ctk.CTkLabel(frame, text=_fit_text(action.component_name, 28), text_color=c.text_primary, font=(t.font_family, t.tiny, "bold")).grid(row=index, column=1, sticky="nw", padx=(0, 8), pady=2)
            detail = f"{action.source} -> {action.target}"
            if action.reason:
                detail += f" | {action.reason}"
            if action.warnings:
                detail += " | " + "; ".join(action.warnings)
            ctk.CTkLabel(
                frame,
                text=detail,
                text_color=c.text_secondary,
                font=(t.font_family, t.tiny),
                wraplength=710,
                justify="left",
            ).grid(row=index, column=2, sticky="ew", padx=(0, 12), pady=2)
        if len(self.preview.actions) > 80:
            ctk.CTkLabel(frame, text=f"... {len(self.preview.actions) - 80} more action(s)", text_color=c.text_muted, font=(t.font_family, t.tiny)).grid(row=81, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 8))

    def _apply_clicked(self) -> None:
        result = self.on_apply()
        if self.result_label is not None:
            self.result_label.configure(text=result)
        if self.apply_button is not None:
            self.apply_button.configure(state="disabled", text="Applied / Recorded", fg_color=self.tokens.colors.disabled)

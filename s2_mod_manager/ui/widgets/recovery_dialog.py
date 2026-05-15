from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ...models.recovery_view import RecoveryView
from ..ui_tokens import UiTokens
from ..window_utils import configure_dialog
from .mod_row import _fit_text


class RecoveryDialog(ctk.CTkToplevel):
    def __init__(self, master, *, tokens: UiTokens, view: RecoveryView, on_uninstall_selected, on_uninstall_all, on_create_backup=None):
        super().__init__(master)
        self.tokens = tokens
        self.view = view
        self.on_uninstall_selected = on_uninstall_selected
        self.on_uninstall_all = on_uninstall_all
        self.on_create_backup = on_create_backup
        self.record_vars: dict[str, tk.BooleanVar] = {}
        self.result_label: ctk.CTkLabel | None = None
        self.title("Recovery / Backups")
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
            text="Recovery / Backups",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))
        recovery_enabled = self.view.action_state.allow_uninstall_selected or self.view.action_state.allow_uninstall_all
        mode = "managed recovery enabled" if recovery_enabled else "no managed recovery actions"
        ctk.CTkLabel(
            header,
            text=f"{mode} | {self.view.summary_text}",
            text_color=c.accent_biolume if recovery_enabled else c.warning,
            font=(t.font_family, t.small, "bold"),
            wraplength=880,
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
        row = self._records(body, row)
        self._restore_preview(body, row)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            footer,
            text=self.view.action_state.disabled_reason or "Managed uninstall actions are available. Unknown files are left alone.",
            text_color=c.accent_biolume if recovery_enabled else c.text_muted,
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
        ).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(
            footer,
            text="Backup Manager State",
            width=154,
            height=34,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            command=self._create_backup_clicked,
        ).grid(row=0, column=2, padx=(0, 8))
        ctk.CTkButton(
            footer,
            text="Uninstall Selected Managed",
            width=178,
            height=34,
            fg_color=c.glass_cyan if self.view.action_state.allow_uninstall_selected else c.disabled,
            hover_color=c.panel_glass_hover if self.view.action_state.allow_uninstall_selected else c.disabled,
            border_width=1,
            border_color=c.shell_border if self.view.action_state.allow_uninstall_selected else c.border_soft,
            text_color=c.text_primary if self.view.action_state.allow_uninstall_selected else c.text_muted,
            state="normal" if self.view.action_state.allow_uninstall_selected else "disabled",
            command=self._uninstall_selected_clicked,
        ).grid(row=0, column=3, padx=(0, 8))
        ctk.CTkButton(
            footer,
            text="Uninstall All Managed",
            width=150,
            height=34,
            fg_color=c.glass_cyan if self.view.action_state.allow_uninstall_all else c.disabled,
            hover_color=c.panel_glass_hover if self.view.action_state.allow_uninstall_all else c.disabled,
            border_width=1,
            border_color=c.shell_border if self.view.action_state.allow_uninstall_all else c.border_soft,
            text_color=c.text_primary if self.view.action_state.allow_uninstall_all else c.text_muted,
            state="normal" if self.view.action_state.allow_uninstall_all else "disabled",
            command=self._uninstall_all_clicked,
        ).grid(row=0, column=4)

    def _records(self, parent, row: int) -> int:
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=8)
        frame.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(frame, text="Install Records", text_color=c.text_primary, font=(t.font_family, t.small, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(8, 4))
        if not self.view.records:
            ctk.CTkLabel(frame, text="No managed install records found.", text_color=c.text_muted, font=(t.font_family, t.small)).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))
            return row + 1
        for index, record in enumerate(self.view.records, start=1):
            var = tk.BooleanVar(value=record.selected)
            self.record_vars[record.install_id] = var
            ctk.CTkCheckBox(
                frame,
                text="",
                variable=var,
                width=22,
                fg_color=c.accent_lagoon,
                hover_color=c.panel_glass_hover,
                border_color=c.border_cold,
                state="normal" if record.can_uninstall and self.view.action_state.allow_uninstall_selected else "disabled",
            ).grid(row=index, column=0, sticky="n", padx=(12, 6), pady=4)
            ctk.CTkLabel(
                frame,
                text=_fit_text(record.install_id, 24),
                text_color=c.text_primary,
                font=(t.font_family, t.tiny, "bold"),
            ).grid(row=index, column=1, sticky="nw", padx=(0, 8), pady=5)
            details = f"{record.summary_text} | target={record.target_root or 'n/a'}"
            if record.errors:
                details += " | errors=" + "; ".join(record.errors)
            if record.warnings:
                details += " | warnings=" + "; ".join(record.warnings)
            ctk.CTkLabel(
                frame,
                text=details,
                text_color=c.text_secondary,
                font=(t.font_family, t.tiny),
                wraplength=700,
                justify="left",
            ).grid(row=index, column=2, sticky="ew", padx=(0, 12), pady=4)
        return row + 1

    def _restore_preview(self, parent, row: int) -> None:
        t = self.tokens
        c = t.colors
        preview = self.view.restore_preview
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text="Restore Vanilla / Quarantine Preview",
            text_color=c.text_primary,
            font=(t.font_family, t.small, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(
            frame,
            text=(
                f"Preview only: {len(preview.managed_files)} managed file(s), "
                f"{len(preview.unknown_files)} unknown file(s), "
                f"{len(preview.quarantine_candidates)} quarantine candidate(s). Unknown files are reported only."
            ),
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
            wraplength=820,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))
        paths = list(preview.managed_files[:5]) + list(preview.unknown_files[:8])
        if not paths:
            ctk.CTkLabel(frame, text="No managed or unknown mod files found in restore-preview locations.", text_color=c.text_muted, font=(t.font_family, t.tiny)).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 10))
            return
        for index, path in enumerate(paths, start=2):
            ctk.CTkLabel(
                frame,
                text=str(path),
                text_color=c.text_muted,
                font=(t.mono_family, t.tiny),
                wraplength=820,
                justify="left",
            ).grid(row=index, column=0, sticky="w", padx=12, pady=(0, 2))
        remaining = len(preview.managed_files) + len(preview.unknown_files) - len(paths)
        if remaining > 0:
            ctk.CTkLabel(frame, text=f"... {remaining} more file(s)", text_color=c.text_muted, font=(t.font_family, t.tiny)).grid(row=15, column=0, sticky="w", padx=12, pady=(0, 8))

    def _selected_ids(self) -> list[str]:
        return [install_id for install_id, var in self.record_vars.items() if var.get()]

    def _uninstall_selected_clicked(self) -> None:
        result = self.on_uninstall_selected(self._selected_ids())
        if self.result_label is not None:
            self.result_label.configure(text=result)

    def _uninstall_all_clicked(self) -> None:
        result = self.on_uninstall_all()
        if self.result_label is not None:
            self.result_label.configure(text=result)

    def _create_backup_clicked(self) -> None:
        if not self.on_create_backup:
            return
        result = self.on_create_backup()
        if self.result_label is not None:
            self.result_label.configure(text=result, text_color=self.tokens.colors.accent_biolume)

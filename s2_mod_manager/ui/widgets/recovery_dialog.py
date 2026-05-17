from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from ...models.recovery import RestoreVanillaPreview
from ...models.recovery_view import RecoveryRecordView, RecoveryView
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
        self.record_frames: dict[str, ctk.CTkFrame] = {}
        self.record_by_id = {record.install_id: record for record in view.records}
        self.selected_record_id = view.records[0].install_id if view.records else ""
        self.result_label: ctk.CTkLabel | None = None
        self.details_title: ctk.CTkLabel | None = None
        self.details_box: ctk.CTkTextbox | None = None
        self.title("Installed Files / Backups")
        self.configure(fg_color=tokens.colors.bg_abyss)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        configure_dialog(self, master, width=1020, height=720, min_width=880, min_height=600, modal=True, topmost=True)

    def _build(self) -> None:
        t = self.tokens
        c = t.colors
        recovery_enabled = self.view.action_state.allow_uninstall_selected or self.view.action_state.allow_uninstall_all

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
            text="Installed Files / Backups",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            header,
            text=_header_summary(self.view),
            text_color=c.accent_biolume if recovery_enabled else c.warning,
            font=(t.font_family, t.small, "bold"),
            wraplength=930,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 4))
        ctk.CTkLabel(
            header,
            text="Only manager-installed files from install_manifest.json are uninstallable. Unknown/manual files are reported only.",
            text_color=c.text_muted,
            font=(t.font_family, t.tiny),
            wraplength=930,
            justify="left",
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 10))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        body.grid_columnconfigure(0, weight=1, uniform="recovery")
        body.grid_columnconfigure(1, weight=1, uniform="recovery")
        body.grid_rowconfigure(0, weight=1)

        self._record_list(body).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._details_panel(body).grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._refresh_record_selection()
        self._show_record_details(self.selected_record_id)
        self._footer(recovery_enabled).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))

    def _record_list(self, parent) -> ctk.CTkScrollableFrame:
        t = self.tokens
        c = t.colors
        frame = ctk.CTkScrollableFrame(
            parent,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.border_soft,
            scrollbar_button_color=c.glass_cyan,
            scrollbar_button_hover_color=c.panel_glass_hover,
        )
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text="Managed Installs",
            text_color=c.text_primary,
            font=(t.font_family, t.small, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))
        if not self.view.records:
            ctk.CTkLabel(
                frame,
                text="No manager-installed files are currently recorded.",
                text_color=c.text_muted,
                font=(t.font_family, t.small),
                wraplength=420,
                justify="left",
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))
            return frame

        for index, record in enumerate(self.view.records, start=1):
            self._record_row(frame, record).grid(row=index, column=0, sticky="ew", padx=10, pady=(0, 8))
        return frame

    def _record_row(self, parent, record: RecoveryRecordView) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        row = ctk.CTkFrame(
            parent,
            fg_color=c.glass_navy,
            corner_radius=t.row_radius,
            border_width=1,
            border_color=c.border_soft,
        )
        row.grid_columnconfigure(1, weight=1)
        self.record_frames[record.install_id] = row
        var = tk.BooleanVar(value=record.selected)
        self.record_vars[record.install_id] = var
        ctk.CTkCheckBox(
            row,
            text="",
            variable=var,
            width=22,
            fg_color=c.accent_lagoon,
            hover_color=c.panel_glass_hover,
            border_color=c.border_cold,
            state="normal" if record.can_uninstall and self.view.action_state.allow_uninstall_selected else "disabled",
        ).grid(row=0, column=0, rowspan=3, sticky="n", padx=(10, 6), pady=10)
        ctk.CTkLabel(
            row,
            text=_fit_text(record.install_id, 28),
            text_color=c.text_primary,
            font=(t.font_family, t.tiny, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(8, 0))
        ctk.CTkLabel(
            row,
            text=record_summary_brief(record),
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny),
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(1, 0))
        ctk.CTkLabel(
            row,
            text=_fit_text(_short_path(record.target_root, 76), 76),
            text_color=c.text_muted,
            font=(t.mono_family, t.tiny),
            anchor="w",
        ).grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=(1, 8))
        ctk.CTkButton(
            row,
            text="Details",
            width=72,
            height=28,
            fg_color="transparent",
            hover_color=c.panel_glass_hover,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            command=lambda install_id=record.install_id: self._show_record_details(install_id),
        ).grid(row=0, column=2, rowspan=3, sticky="e", padx=(0, 10), pady=10)
        for widget in (row,):
            widget.bind("<Button-1>", lambda _event, install_id=record.install_id: self._show_record_details(install_id), add="+")
        return row

    def _details_panel(self, parent) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(
            parent,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.border_soft,
        )
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.details_title = ctk.CTkLabel(
            frame,
            text="Install Details",
            text_color=c.text_primary,
            font=(t.font_family, t.small, "bold"),
            anchor="w",
        )
        self.details_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        self.details_box = ctk.CTkTextbox(
            frame,
            fg_color=c.glass_navy,
            border_width=1,
            border_color=c.border_soft,
            text_color=c.text_secondary,
            font=(t.mono_family, t.tiny),
            wrap="word",
            activate_scrollbars=True,
        )
        self.details_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.details_box.configure(state="disabled")
        self._restore_preview(frame).grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        return frame

    def _restore_preview(self, parent) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        preview = self.view.restore_preview
        frame = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text="Reset to Vanilla Preview",
            text_color=c.text_primary,
            font=(t.font_family, t.small, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(
            frame,
            text=restore_preview_brief(preview),
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny),
            wraplength=430,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        return frame

    def _footer(self, recovery_enabled: bool) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            footer,
            text=self.view.action_state.disabled_reason or "Select install records to uninstall manager-installed files.",
            text_color=c.accent_biolume if recovery_enabled else c.text_muted,
            font=(t.font_family, t.small),
            anchor="w",
            wraplength=390,
            justify="left",
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
            text="Uninstall Selected",
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
            text="Uninstall All Mods",
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
        return footer

    def _show_record_details(self, install_id: str) -> None:
        self.selected_record_id = install_id
        self._refresh_record_selection()
        record = self.record_by_id.get(install_id)
        if self.details_title is not None:
            self.details_title.configure(text=f"Install Details: {_fit_text(install_id, 36)}" if record else "Install Details")
        if self.details_box is None:
            return
        self.details_box.configure(state="normal")
        self.details_box.delete("1.0", "end")
        self.details_box.insert("1.0", record_details_text(record) if record else "No install record selected.")
        self.details_box.configure(state="disabled")

    def _refresh_record_selection(self) -> None:
        c = self.tokens.colors
        for install_id, frame in self.record_frames.items():
            selected = install_id == self.selected_record_id
            frame.configure(border_color=c.shell_border if selected else c.border_soft, fg_color=c.glass_cyan if selected else c.glass_navy)

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


def _header_summary(view: RecoveryView) -> str:
    summary = view.summary
    return (
        f"{summary.install_count} install record(s) | "
        f"{summary.deployed_file_count} deployed file(s) | "
        f"{summary.backup_count} backup(s) | "
        f"{summary.completed_count} completed, {summary.failed_count} failed, {summary.refused_count} refused, "
        f"{summary.uninstalled_count} uninstalled | "
        f"{len(view.restore_preview.unknown_files)} unknown file(s) reported"
    )


def record_summary_brief(record: RecoveryRecordView) -> str:
    flags = []
    if record.warning_count:
        flags.append(f"{record.warning_count} warning(s)")
    if record.error_count:
        flags.append(f"{record.error_count} error(s)")
    suffix = f" | {', '.join(flags)}" if flags else ""
    return (
        f"{record.profile_name} | {record.status} | "
        f"{record.deployed_file_count} file(s) | {record.backup_count} backup(s){suffix}"
    )


def record_details_text(record: RecoveryRecordView) -> str:
    lines = [
        f"Install ID: {record.install_id}",
        f"Profile: {record.profile_name}",
        f"Status: {record.status}",
        f"Target root: {record.target_root or 'n/a'}",
        f"Deployed files: {record.deployed_file_count}",
        f"Backups: {record.backup_count}",
        f"Warnings: {record.warning_count}",
        f"Errors: {record.error_count}",
    ]
    if record.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in record.warnings)
    if record.errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in record.errors)
    if not record.warnings and not record.errors:
        lines.append("")
        lines.append("No warnings or errors recorded for this install.")
    return "\n".join(lines)


def restore_preview_brief(preview: RestoreVanillaPreview) -> str:
    return (
        f"{len(preview.managed_files)} managed file(s), "
        f"{len(preview.unknown_files)} unknown file(s), "
        f"{len(preview.quarantine_candidates)} quarantine candidate(s). "
        "Unknown files are not deleted automatically."
    )


def _short_path(path: Path | None, max_chars: int = 76) -> str:
    if path is None:
        return "target: n/a"
    value = str(path)
    if len(value) <= max_chars:
        return value
    parts = path.parts
    if len(parts) >= 3:
        tail = str(Path(*parts[-3:]))
        drive = parts[0]
        compact = f"{drive}...\\{tail}" if drive.endswith("\\") else f"{drive}\\...\\{tail}"
        if len(compact) <= max_chars:
            return compact
    return "..." + value[-(max_chars - 3) :]

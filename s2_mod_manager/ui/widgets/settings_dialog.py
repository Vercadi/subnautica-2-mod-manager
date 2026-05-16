from __future__ import annotations

import customtkinter as ctk

from ...models.settings_view import SettingsView
from ..ui_tokens import UiTokens
from ..window_utils import configure_dialog
from .mod_row import _fit_text


class SettingsDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        *,
        tokens: UiTokens,
        view: SettingsView,
        on_browse_install,
        on_auto_detect,
        on_browse_inbox,
        on_reset_inbox,
        on_toggle_auto_updates=None,
        on_toggle_popup_preference=None,
        on_set_popup_policy=None,
    ):
        super().__init__(master)
        self.tokens = tokens
        self.view = view
        self.on_browse_install = on_browse_install
        self.on_auto_detect = on_auto_detect
        self.on_browse_inbox = on_browse_inbox
        self.on_reset_inbox = on_reset_inbox
        self.on_toggle_auto_updates = on_toggle_auto_updates
        self.on_toggle_popup_preference = on_toggle_popup_preference
        self.on_set_popup_policy = on_set_popup_policy
        self.body: ctk.CTkScrollableFrame | None = None
        self.result_label: ctk.CTkLabel | None = None
        self.title("Settings")
        self.configure(fg_color=tokens.colors.bg_abyss)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        configure_dialog(self, master, width=920, height=680, min_width=780, min_height=560, modal=True, topmost=True)

    def set_view(self, view: SettingsView, message: str = "") -> None:
        self.view = view
        if self.body is not None:
            for child in self.body.winfo_children():
                child.destroy()
            self._populate_body(self.body)
        if self.result_label is not None and message:
            self.result_label.configure(text=message, text_color=self.tokens.colors.accent_biolume if "refused" not in message.casefold() and "invalid" not in message.casefold() else self.tokens.colors.warning)

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
            text="Settings",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            header,
            text="Path and safety configuration. Apply and recovery are limited to previewed or manifest-tracked files.",
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
            wraplength=820,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

        self.body = ctk.CTkScrollableFrame(
            self,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.border_soft,
            scrollbar_button_color=c.glass_cyan,
            scrollbar_button_hover_color=c.panel_glass_hover,
        )
        self.body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        self.body.grid_columnconfigure(0, weight=1)
        self._populate_body(self.body)

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

    def _populate_body(self, parent) -> None:
        row = 0
        row = self._install_card(parent, row)
        row = self._paths_card(parent, row)
        row = self._support_card(parent, row)
        row = self._safety_card(parent, row)
        self._about_card(parent, row)

    def _install_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Subnautica 2 Install")
        self._value(card, 1, "Status", self.view.install_status_text)
        self._value(card, 2, "Layout", self.view.install_variant)
        self._value(card, 3, "Project", str(self.view.project_root or "not configured"))
        self._value(card, 4, "Binaries", str(self.view.binaries_dir or "not configured"))
        self._value(card, 5, "Paks", str(self.view.pak_dir or "not configured"))
        self._value(card, 6, "UE4SS Mods", str(self.view.ue4ss_target_dir or "not configured"))
        self._value(card, 7, "Steam", self.view.steam_status)
        self._value(card, 8, "Build", self.view.build_status)
        if self.view.gamepass_experimental:
            self._value(card, 9, "Game Pass", "Experimental support. UE4SS base/runtime files target Content; standard Lua mods target WinGDK\\ue4ss\\Mods. Review Apply targets.")
            button_row = 10
        else:
            button_row = 9
        self._button(card, button_row, "Browse Install", self._browse_install_clicked, column=1)
        self._button(card, button_row, "Auto Detect", self._auto_detect_clicked, column=2)
        return row + 1

    def _paths_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Storage Paths")
        self._value(card, 1, "Mods Inbox", str(self.view.inbox_path or "not set"))
        self._value(card, 2, "Data", str(self.view.data_dir))
        self._value(card, 3, "Library", str(self.view.library_dir))
        self._value(card, 4, "Backups", str(self.view.backup_dir))
        self._value(card, 5, "Migration", "Data/library/backup relocation is read-only until a guarded migration flow exists.")
        self._button(card, 6, "Browse Inbox", self._browse_inbox_clicked, column=1)
        self._button(card, 6, "Reset Inbox", self._reset_inbox_clicked, column=2)
        return row + 1

    def _support_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Archive Support And UI")
        self._value(card, 1, "Archives", self.view.archive_support_text)
        self._value(card, 2, "UI Scale", self.view.ui_scale)
        self._value(card, 3, "Startup Updates", self.view.auto_update_text)
        self._button(card, 4, "Toggle Startup Updates", self._toggle_auto_updates_clicked, column=1)
        self._value(card, 5, "Popup Policy", self.view.popup_text)
        self._option_menu(
            card,
            6,
            values=list(self.view.popup_policy_options),
            current=self.view.popup_policy_label,
            command=self._popup_policy_changed,
            column=1,
            columnspan=2,
        )
        self._value(card, 7, "Critical Safety", "always shown; cannot be disabled")
        self._value(card, 8, "UE4SS Policy", self.view.ue4ss_policy_text)
        return row + 1

    def _safety_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "Safety State")
        self._value(card, 1, "Real Apply", self.view.safety.real_apply)
        self._value(card, 2, "Recovery", self.view.safety.destructive_recovery)
        self._value(card, 3, "Restore Vanilla", self.view.safety.restore_vanilla)
        self._value(card, 4, "Quarantine", self.view.safety.quarantine)
        self._value(card, 5, "Loose Overlays", self.view.safety.loose_overlays)
        self._value(card, 6, "Summary", self.view.safety.text)
        return row + 1

    def _about_card(self, parent, row: int) -> int:
        card = self._card(parent, row, "About / Release Metadata")
        self._value(card, 1, "Version", self.view.about_text)
        self._value(card, 2, "Package", "Portable PyInstaller one-folder build target. Release metadata is emitted during build.")
        return row + 1

    def _card(self, parent, row: int, title: str) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        card = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        card.grid(row=row, column=0, sticky="ew", padx=8, pady=8)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text=title, text_color=c.text_primary, font=(t.font_family, t.small, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 4))
        return card

    def _value(self, card, row: int, label: str, value: str) -> None:
        t = self.tokens
        c = t.colors
        ctk.CTkLabel(card, text=label, width=110, anchor="w", text_color=c.text_muted, font=(t.font_family, t.tiny, "bold")).grid(row=row, column=0, sticky="nw", padx=12, pady=3)
        ctk.CTkLabel(
            card,
            text=_fit_text(value, 150),
            anchor="w",
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny),
            wraplength=700,
            justify="left",
        ).grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=3)

    def _button(self, card, row: int, text: str, command, *, column: int) -> None:
        t = self.tokens
        c = t.colors
        ctk.CTkButton(
            card,
            text=text,
            width=116,
            height=28,
            fg_color=c.glass_black,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny, "bold"),
            command=command,
        ).grid(row=row, column=column, sticky="e", padx=(0, 8), pady=(6, 10))

    def _option_menu(self, card, row: int, *, values: list[str], current: str, command, column: int, columnspan: int = 1) -> None:
        t = self.tokens
        c = t.colors
        menu = ctk.CTkOptionMenu(
            card,
            values=values,
            command=command,
            width=240,
            height=30,
            fg_color=c.glass_black,
            button_color=c.glass_cyan,
            button_hover_color=c.panel_glass,
            dropdown_fg_color=c.glass_black,
            dropdown_hover_color=c.panel_glass,
            dropdown_text_color=c.text_secondary,
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny, "bold"),
        )
        menu.set(current)
        menu.grid(row=row, column=column, columnspan=columnspan, sticky="e", padx=(0, 8), pady=(6, 10))

    def _browse_install_clicked(self) -> None:
        result = self.on_browse_install()
        if result is not None:
            view, message = result
            self.set_view(view, message)

    def _auto_detect_clicked(self) -> None:
        result = self.on_auto_detect()
        if result is not None:
            view, message = result
            self.set_view(view, message)

    def _browse_inbox_clicked(self) -> None:
        result = self.on_browse_inbox()
        if result is not None:
            view, message = result
            self.set_view(view, message)

    def _reset_inbox_clicked(self) -> None:
        result = self.on_reset_inbox()
        if result is not None:
            view, message = result
            self.set_view(view, message)

    def _toggle_auto_updates_clicked(self) -> None:
        if not self.on_toggle_auto_updates:
            return
        result = self.on_toggle_auto_updates()
        if result is not None:
            view, message = result
            self.set_view(view, message)

    def _toggle_popup_clicked(self, preference_name: str) -> None:
        if not self.on_toggle_popup_preference:
            return
        result = self.on_toggle_popup_preference(preference_name)
        if result is not None:
            view, message = result
            self.set_view(view, message)

    def _popup_policy_changed(self, policy_label: str) -> None:
        if not self.on_set_popup_policy:
            return
        result = self.on_set_popup_policy(policy_label)
        if result is not None:
            view, message = result
            self.set_view(view, message)

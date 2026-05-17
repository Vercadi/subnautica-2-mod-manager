from __future__ import annotations

import customtkinter as ctk
import tkinter as tk

from ...models.archive_info import (
    COMPONENT_PAK_BUNDLE,
    COMPONENT_UE4SS_MOD,
    COMPONENT_UE4SS_RUNTIME,
    ScanResult,
)
from ...models.library_view import LibraryDisplayItem, LibraryViewState
from ...models.mod_state import mod_display_state, selection_action_states
from ..ui_tokens import UiTokens
from ..window_utils import prompt_dialog
from ..widgets.mod_inspector import ModInspector
from ..widgets.mod_row import ModRow, PlaceholderMod, _fit_text


PLACEHOLDER_MODS = [
    PlaceholderMod(
        name="Biome Lighting Overhaul",
        version="v1.2.0",
        description="Adds dynamic lighting and color grading to all biomes.",
        badges=["UE4SS", "Pak"],
        accent="#7E2AFF",
    ),
    PlaceholderMod(
        name="Tadpole HUD Enhancer",
        version="v2.1.1",
        description="Improves readability and adds extra HUD widgets.",
        badges=["UE4SS", "Pak"],
        accent="#21B8FF",
    ),
    PlaceholderMod(
        name="Co-op Ping Tools",
        version="v1.0.3",
        description="Adds advanced ping system and markers for co-op.",
        badges=["UE4SS", "Pak"],
        warning="Review dependencies",
        accent="#19D086",
    ),
    PlaceholderMod(
        name="Creature Scanner Plus",
        version="v1.3.0",
        description="Extended info and tracking for scanned creatures.",
        badges=["UE4SS", "Pak"],
        accent="#38D6D6",
    ),
    PlaceholderMod(
        name="Base Builder Tweaks",
        version="v0.9.2",
        description="Quality of life improvements for base building.",
        badges=["UE4SS", "Pak"],
        status="Conflicts",
        enabled=False,
        warning="Conflict",
        accent="#FFD166",
    ),
]


class InstalledModsTab(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        tokens: UiTokens,
        mods: list[PlaceholderMod] | None = None,
        on_scan=None,
        on_browse_sources=None,
        on_browse_folder=None,
        on_drop_sources=None,
        on_import_selected=None,
        on_import_all=None,
        profile_names: list[str] | None = None,
        active_profile_name: str = "Vanilla",
        active_profile_protected: bool = True,
        profile_warning_count: int = 0,
        on_profile_select=None,
        on_profile_create=None,
        on_profile_duplicate=None,
        on_profile_rename=None,
        on_profile_delete=None,
        on_add_to_profile=None,
        on_remove_from_profile=None,
        on_toggle_profile_entry=None,
        on_move_profile_entry=None,
        on_activate_all_profile_entries=None,
        on_deactivate_all_profile_entries=None,
        on_remove_all_profile_entries=None,
        on_remove_selected_profile_entries=None,
        on_remove_selected_mods=None,
        on_uninstall_selected_mods=None,
        on_reset_to_vanilla=None,
        on_open_mods_folder=None,
        on_open_source=None,
        on_review_warnings=None,
        on_preview_deployment=None,
        on_list_configs=None,
        on_read_config=None,
        on_save_config=None,
        on_restore_config=None,
        on_open_config_folder=None,
        ue4ss_policy: dict[str, bool] | None = None,
        on_toggle_ue4ss_policy=None,
        pending_change_count: int = 0,
    ):
        super().__init__(master, fg_color="transparent")
        self.tokens = tokens
        self.mods = PLACEHOLDER_MODS if mods is None else mods
        self.selected = self.mods[0] if self.mods else _empty_selection()
        self.on_scan = on_scan
        self.on_browse_sources = on_browse_sources
        self.on_browse_folder = on_browse_folder
        self.on_drop_sources = on_drop_sources
        self.on_import_selected = on_import_selected
        self.on_import_all = on_import_all
        self.profile_names = profile_names or [active_profile_name]
        self.active_profile_name = active_profile_name
        self.active_profile_protected = active_profile_protected
        self.profile_warning_count = profile_warning_count
        self.on_profile_select = on_profile_select
        self.on_profile_create = on_profile_create
        self.on_profile_duplicate = on_profile_duplicate
        self.on_profile_rename = on_profile_rename
        self.on_profile_delete = on_profile_delete
        self.on_add_to_profile = on_add_to_profile
        self.on_remove_from_profile = on_remove_from_profile
        self.on_toggle_profile_entry = on_toggle_profile_entry
        self.on_move_profile_entry = on_move_profile_entry
        self.on_activate_all_profile_entries = on_activate_all_profile_entries
        self.on_deactivate_all_profile_entries = on_deactivate_all_profile_entries
        self.on_remove_all_profile_entries = on_remove_all_profile_entries
        self.on_remove_selected_profile_entries = on_remove_selected_profile_entries
        self.on_remove_selected_mods = on_remove_selected_mods
        self.on_uninstall_selected_mods = on_uninstall_selected_mods
        self.on_reset_to_vanilla = on_reset_to_vanilla
        self.on_open_mods_folder = on_open_mods_folder
        self.on_open_source = on_open_source
        self.on_review_warnings = on_review_warnings
        self.on_preview_deployment = on_preview_deployment
        self.on_list_configs = on_list_configs
        self.on_read_config = on_read_config
        self.on_save_config = on_save_config
        self.on_restore_config = on_restore_config
        self.on_open_config_folder = on_open_config_folder
        self.ue4ss_policy = ue4ss_policy or {}
        self.on_toggle_ue4ss_policy = on_toggle_ue4ss_policy
        self.pending_change_count = pending_change_count
        self.native_drop_callback = None
        self.drop_target_widgets: list[object] = []
        self.rows: list[object] = []
        self.row_widgets: dict[str, ModRow] = {}
        self.selected_bulk_ids: set[str] = set()
        self.count_label: ctk.CTkLabel | None = None
        self.profile_menu: ctk.CTkOptionMenu | None = None
        self.profile_status_label: ctk.CTkLabel | None = None
        self.preview_button: ctk.CTkButton | None = None
        self.preview_reason_label: ctk.CTkLabel | None = None
        self.action_buttons: dict[str, ctk.CTkButton] = {}
        self.grid_columnconfigure(0, weight=0, minsize=330)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        t = self.tokens
        c = t.colors
        center = ctk.CTkFrame(
            self,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.shell_border_dim,
        )
        self.center_panel = center
        center.grid(row=0, column=1, sticky="nsew", padx=(t.panel_gap, 0), pady=0)
        center.grid_columnconfigure(0, weight=1)
        center.grid_columnconfigure(1, weight=0, minsize=150)
        center.grid_rowconfigure(0, weight=1)

        self.inspector = ModInspector(
            self,
            tokens=t,
            mod=self.selected,
            ue4ss_policy=self.ue4ss_policy,
            on_toggle_ue4ss_policy=self.on_toggle_ue4ss_policy,
            on_preview_deployment=self.on_preview_deployment,
            on_list_configs=self.on_list_configs,
            on_read_config=self.on_read_config,
            on_save_config=self.on_save_config,
            on_restore_config=self.on_restore_config,
            on_open_config_folder=self.on_open_config_folder,
        )
        self.inspector.grid(row=0, column=0, sticky="nsw", pady=0)

        self.list_frame = ctk.CTkScrollableFrame(
            center,
            fg_color="transparent",
            scrollbar_button_color=c.glass_cyan,
            scrollbar_button_hover_color=c.panel_glass_hover,
        )
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=12)
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.drop_target_widgets.extend([self, center, self.list_frame])
        self._render_rows()

        self._build_side_controls(center).grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)

    def set_mods(self, mods: list[PlaceholderMod], *, refresh_inspector: bool = True) -> None:
        visible_keys = {_mod_key(mod) for mod in mods}
        self.selected_bulk_ids.intersection_update(visible_keys)
        previous_keys = [_mod_key(mod) for mod in self.mods]
        next_keys = [_mod_key(mod) for mod in mods]
        selected_key = _mod_key(self.selected)
        previous_view = self._list_view_position()
        self.mods = mods
        next_by_key = {_mod_key(mod): mod for mod in self.mods}
        if selected_key in next_by_key:
            selected_mod = next_by_key[selected_key]
            if selected_mod != self.selected:
                self.selected = selected_mod
                if refresh_inspector:
                    self.inspector.set_mod(self.selected)
                else:
                    self.inspector.update_mod_summary(self.selected)
        elif self.selected not in self.mods:
            self.selected = self.mods[0] if self.mods else _empty_selection()
            self.inspector.set_mod(self.selected)
        if self.count_label is not None:
            self.count_label.configure(text=self._count_text())
        self._refresh_preview_button()
        self._refresh_action_buttons()
        if previous_keys == next_keys and self._update_rows_in_place():
            self._restore_list_view(previous_view)
            return
        self._render_rows()
        self._restore_list_view(previous_view)

    def set_ue4ss_policy(self, policy: dict[str, bool]) -> None:
        self.ue4ss_policy = dict(policy or {})
        if self.inspector is not None:
            self.inspector.set_ue4ss_policy(self.ue4ss_policy)

    def set_action_message(self, message: str, *, warning: bool = False) -> None:
        if self.preview_reason_label is None:
            return
        color = self.tokens.colors.warning if warning else self.tokens.colors.text_muted
        self.preview_reason_label.configure(text=message, text_color=color)

    def set_profile_state(
        self,
        *,
        profile_names: list[str],
        active_profile_name: str,
        active_profile_protected: bool,
        profile_warning_count: int,
        pending_change_count: int | None = None,
    ) -> None:
        self.profile_names = profile_names or [active_profile_name]
        self.active_profile_name = active_profile_name
        self.active_profile_protected = active_profile_protected
        self.profile_warning_count = profile_warning_count
        if pending_change_count is not None:
            self.pending_change_count = pending_change_count
        if self.profile_menu is not None:
            self.profile_menu.configure(values=self.profile_names)
            self.profile_menu.set(self.active_profile_name)
        if self.profile_status_label is not None:
            self.profile_status_label.configure(text=self._profile_status_text())
        self._refresh_preview_button()
        self._refresh_action_buttons()

    def enable_native_drop(self, callback=None) -> bool:
        self.native_drop_callback = callback or self._drop_sources_received
        ok = False
        for widget in self.drop_target_widgets:
            ok = self._register_drop_target(widget) or ok
        return ok

    def _render_rows(self) -> None:
        for row in self.rows:
            row.destroy()
        self.rows.clear()
        self.row_widgets.clear()
        if not self.mods:
            empty = self._empty_state()
            empty.grid(row=0, column=0, sticky="ew", padx=3, pady=18)
            self.rows.append(empty)
            self._refresh_action_buttons()
            return
        current_source = object()
        for index, mod in enumerate(self.mods):
            source_key = (mod.state, mod.source_name or mod.source_path or "Unknown Source")
            if source_key != current_source:
                current_source = source_key
                header = self._source_header(mod)
                header.grid(row=len(self.rows), column=0, sticky="ew", padx=3, pady=(8, 2))
                self.rows.append(header)
            row = ModRow(
                self.list_frame,
                tokens=self.tokens,
                mod=mod,
                selected=mod == self.selected,
                command=self._select,
                can_toggle=self._can_switch_mod(mod),
                can_reorder=False,
                profile_protected=self.active_profile_protected,
                compact=True,
                on_toggle=self._toggle_profile_entry_for_mod,
                on_menu=self._row_menu_clicked,
                on_warning=self._review_warnings_clicked,
                on_move=self._move_profile_entry_for_mod,
                bulk_selected=_mod_key(mod) in self.selected_bulk_ids,
                on_bulk_select=self._bulk_select_changed,
            )
            self._register_drop_target(row)
            row.grid(row=len(self.rows), column=0, sticky="ew", padx=2, pady=5)
            self.rows.append(row)
            self.row_widgets[_mod_key(mod)] = row
        self._refresh_action_buttons()

    def _update_rows_in_place(self) -> bool:
        for mod in self.mods:
            key = _mod_key(mod)
            row = self.row_widgets.get(key)
            if row is None:
                return False
            if not row.update_compact_state(
                mod=mod,
                selected=mod == self.selected,
                can_toggle=self._can_switch_mod(mod),
                profile_protected=self.active_profile_protected,
                bulk_selected=key in self.selected_bulk_ids,
            ):
                return False
        return True

    def _select(self, mod: PlaceholderMod, *, inspector_tab: str | None = None) -> None:
        previous_key = _mod_key(self.selected)
        self.selected = mod
        self.inspector.set_mod(mod, active_tab=inspector_tab)
        current_key = _mod_key(mod)
        if previous_key in self.row_widgets:
            self.row_widgets[previous_key].set_selected(False)
        if current_key in self.row_widgets:
            self.row_widgets[current_key].set_selected(True)
        self._refresh_action_buttons()

    def _source_header(self, mod: PlaceholderMod) -> ctk.CTkLabel:
        c = self.tokens.colors
        label = mod.source_name or "Placeholder Source"
        state = _state_label(mod)
        return ctk.CTkLabel(
            self.list_frame,
            text=_fit_text(f"{state}: {label}", 82),
            anchor="w",
            fg_color=c.glass_black,
            text_color=c.text_muted,
            corner_radius=4,
            padx=10,
            pady=3,
            font=(self.tokens.font_family, self.tokens.tiny, "bold"),
        )

    def _empty_state(self) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        frame = ctk.CTkFrame(
            self.list_frame,
            fg_color=c.glass_navy,
            corner_radius=t.row_radius,
            border_width=1,
            border_color=c.border_soft,
        )
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text="No manager library items or inbox candidates found.",
            text_color=c.text_primary,
            font=(t.font_family, t.body, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(
            frame,
            text="Drop pak bundles, archives, and UE4SS folders here, or use Install From File / Install Folder.",
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
            wraplength=480,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))
        return frame

    def _build_side_controls(self, parent) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        side = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        side.grid_columnconfigure(0, weight=1)
        self.count_label = ctk.CTkLabel(
            side,
            text=self._count_text(),
            font=(t.font_family, t.small, "bold"),
            text_color=c.text_primary,
        )
        self.count_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        ctk.CTkLabel(side, text="Profile", text_color=c.text_muted, font=(t.font_family, t.tiny, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=(4, 2))
        self.profile_menu = ctk.CTkOptionMenu(
            side,
            values=self.profile_names,
            command=self._profile_selected,
            fg_color=c.glass_black,
            button_color=c.glass_cyan,
            button_hover_color=c.panel_glass_hover,
            text_color=c.text_primary,
            width=112,
        )
        self.profile_menu.set(self.active_profile_name)
        self.profile_menu.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 4))
        self.profile_status_label = ctk.CTkLabel(
            side,
            text=self._profile_status_text(),
            text_color=c.text_muted,
            font=(t.font_family, t.tiny),
            wraplength=108,
            justify="left",
        )
        self.profile_status_label.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 8))
        _preview_text, _preview_enabled, preview_reason = self._preview_action_state()
        self.preview_reason_label = ctk.CTkLabel(
            side,
            text=preview_reason,
            text_color=c.text_muted,
            font=(t.font_family, t.tiny),
            wraplength=126,
            justify="left",
        )
        self.preview_reason_label.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 8))

        buttons = (
            ("Install From File", self._browse_sources_clicked, True),
            ("Install Folder", self._browse_folder_clicked, False),
            ("Open Mods Folder", self._open_mods_folder_clicked, False),
            ("Apply", self._preview_deployment_clicked, True),
            ("Enable", self._enable_selected_clicked, False),
            ("Disable", self._disable_selected_clicked, False),
            ("Remove", self._remove_selected_clicked, False),
            ("Uninstall", self._uninstall_selected_clicked, False),
            ("Reset to Vanilla", self._reset_to_vanilla_clicked, False),
        )
        for index, (text, command, primary) in enumerate(buttons, start=5):
            button = ctk.CTkButton(
                side,
                text=text,
                width=132,
                height=24,
                fg_color=c.glass_cyan if primary else c.glass_black,
                hover_color=c.panel_glass_hover if primary else c.panel_glass,
                border_width=1,
                border_color=c.shell_border if primary else c.border_cold,
                text_color=c.text_primary if primary else c.text_secondary,
                font=(t.font_family, t.tiny, "bold"),
                command=command,
            )
            button.grid(row=index, column=0, sticky="ew", padx=10, pady=(0, 4))
            self.action_buttons[text] = button
        self._refresh_preview_button()
        return side

    def _register_drop_target(self, widget) -> bool:
        if self.native_drop_callback is None:
            return False
        try:
            from tkinterdnd2 import DND_FILES
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._drop_received)
            for child in widget.winfo_children():
                try:
                    child.drop_target_register(DND_FILES)
                    child.dnd_bind("<<Drop>>", self._drop_received)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def _open_mods_folder_clicked(self) -> None:
        if self.on_open_mods_folder:
            self.on_open_mods_folder()

    def _build_profile_bar(self, parent) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        bar = ctk.CTkFrame(parent, fg_color=c.glass_navy, corner_radius=t.row_radius)
        bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            bar,
            text="Profile",
            text_color=c.text_secondary,
            font=(t.font_family, t.small, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(12, 8), pady=8)
        self.profile_menu = ctk.CTkOptionMenu(
            bar,
            values=self.profile_names,
            command=self._profile_selected,
            fg_color=c.glass_black,
            button_color=c.glass_cyan,
            button_hover_color=c.panel_glass_hover,
            text_color=c.text_primary,
            width=160,
        )
        self.profile_menu.set(self.active_profile_name)
        self.profile_menu.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=8)
        self.profile_status_label = ctk.CTkLabel(
            bar,
            text=self._profile_status_text(),
            text_color=c.text_muted,
            font=(t.font_family, t.tiny),
        )
        self.profile_status_label.grid(row=0, column=2, sticky="e", padx=(0, 8), pady=8)
        for index, (text, command, width) in enumerate(
            (
                ("New", self._profile_create_clicked, 50),
                ("Copy", self._profile_duplicate_clicked, 58),
                ("Name", self._profile_rename_clicked, 58),
                ("Del", self._profile_delete_clicked, 50),
            ),
            start=3,
        ):
            ctk.CTkButton(
                bar,
                text=text,
                width=width,
                height=28,
                fg_color=c.glass_black,
                hover_color=c.panel_glass,
                border_width=1,
                border_color=c.border_cold,
                text_color=c.text_secondary,
                command=command,
            ).grid(row=0, column=index, sticky="e", padx=(0, 7), pady=8)
        return bar

    def _count_text(self) -> str:
        available_count = sum(1 for mod in self.mods if mod.state == "library" or mod.state.startswith("candidate"))
        enabled_count = sum(1 for mod in self.mods if mod.in_active_profile and mod.profile_enabled)
        installed_count = sum(1 for mod in self.mods if mod.installed)
        if not self.mods:
            return "Mods (empty)"
        return f"Mods  {enabled_count} enabled  {available_count} available  {installed_count} installed"

    def _profile_status_text(self) -> str:
        bits = ["Vanilla profile" if self.active_profile_protected else "Modded profile"]
        if self.profile_warning_count:
            bits.append(f"{self.profile_warning_count} warning(s)")
        if self.pending_change_count:
            bits.append(f"{self.pending_change_count} pending")
        return " | ".join(bits)

    def _preview_action_state(self) -> tuple[str, bool, str]:
        return preview_apply_action_state(
            self.mods,
            has_preview_callback=self.on_preview_deployment is not None,
            pending_change_count=self.pending_change_count,
        )

    def _refresh_preview_button(self) -> None:
        text, enabled, reason = self._preview_action_state()
        c = self.tokens.colors
        for button in filter(None, (self.preview_button, self.action_buttons.get("Apply"))):
            button.configure(
                text=text,
                fg_color=c.glass_cyan if enabled else c.disabled,
                hover_color=c.panel_glass_hover if enabled else c.disabled,
                border_color=c.shell_border if enabled else c.border_soft,
                text_color=c.text_primary if enabled else c.text_muted,
                state="normal" if enabled else "disabled",
            )
        if self.preview_reason_label is not None:
            self.preview_reason_label.configure(text=reason)

    def _refresh_action_buttons(self) -> None:
        if not self.action_buttons:
            return
        selected = self._bulk_mods() or ([self.selected] if self.selected else [])
        states = selection_action_states(
            selected,
            active_profile_protected=self.active_profile_protected,
            pending_change_count=self.pending_change_count,
            has_apply_callback=self.on_preview_deployment is not None,
        )
        c = self.tokens.colors
        for name, action_state in states.items():
            button = self.action_buttons.get(name)
            if button is None:
                continue
            primary = name == "Apply"
            enabled = action_state.enabled
            button.configure(
                state="normal" if enabled else "disabled",
                fg_color=c.glass_cyan if primary and enabled else c.glass_black if enabled else c.disabled,
                hover_color=c.panel_glass_hover if enabled else c.disabled,
                border_color=c.shell_border if primary and enabled else c.border_cold if enabled else c.border_soft,
                text_color=c.text_primary if enabled else c.text_muted,
            )
        if self.preview_reason_label is not None and not states.get("Apply").enabled:
            reason = states.get("Apply").reason or ""
            self.preview_reason_label.configure(text=reason)

    def _scan_clicked(self) -> None:
        if self.on_scan:
            self.on_scan()

    def _browse_sources_clicked(self) -> None:
        if self.on_browse_sources:
            self.on_browse_sources()

    def _browse_folder_clicked(self) -> None:
        if self.on_browse_folder:
            self.on_browse_folder()

    def _drop_sources_received(self, data: str) -> None:
        if self.on_drop_sources:
            self.on_drop_sources(data)

    def _drop_received(self, event) -> None:
        self._drop_sources_received(event.data)

    def _import_selected_clicked(self) -> None:
        if self.on_import_selected:
            targets = self._bulk_mods() or [self.selected]
            for mod in targets:
                self.on_import_selected(mod)

    def _import_all_clicked(self) -> None:
        if self.on_import_all:
            self.on_import_all()

    def _profile_selected(self, name: str) -> None:
        if self.on_profile_select:
            self.on_profile_select(name)

    def _profile_create_clicked(self) -> None:
        name = _prompt(self, "New Profile", "Profile name:")
        if name and self.on_profile_create:
            self.on_profile_create(name)

    def _profile_duplicate_clicked(self) -> None:
        name = _prompt(self, "Save As Profile", "New profile name:")
        if name and self.on_profile_duplicate:
            self.on_profile_duplicate(name)

    def _profile_rename_clicked(self) -> None:
        name = _prompt(self, "Rename Profile", "Profile name:")
        if name and self.on_profile_rename:
            self.on_profile_rename(name)

    def _profile_delete_clicked(self) -> None:
        if self.on_profile_delete:
            self.on_profile_delete()

    def _add_to_profile_clicked(self) -> None:
        if self.on_add_to_profile:
            self.on_add_to_profile(self.selected)

    def _remove_from_profile_clicked(self) -> None:
        if self.on_remove_from_profile:
            self.on_remove_from_profile(self.selected)

    def _toggle_profile_entry_clicked(self) -> None:
        if self.on_toggle_profile_entry:
            self.on_toggle_profile_entry(self.selected)

    def _move_profile_entry_clicked(self, delta: int) -> None:
        if self.on_move_profile_entry:
            self.on_move_profile_entry(self.selected, delta)

    def _toggle_profile_entry_for_mod(self, mod: PlaceholderMod) -> None:
        self.selected = mod
        if self.on_toggle_profile_entry:
            self.on_toggle_profile_entry(mod)

    def _move_profile_entry_for_mod(self, mod: PlaceholderMod, direction: str) -> None:
        self.selected = mod
        if self.on_move_profile_entry:
            self.on_move_profile_entry(mod, direction)

    def _activate_all_clicked(self) -> None:
        if self.on_activate_all_profile_entries:
            self.on_activate_all_profile_entries()

    def _deactivate_all_clicked(self) -> None:
        if self.on_deactivate_all_profile_entries:
            self.on_deactivate_all_profile_entries()

    def _remove_all_clicked(self) -> None:
        if self.on_remove_all_profile_entries:
            self.on_remove_all_profile_entries()

    def _select_all_clicked(self) -> None:
        self.selected_bulk_ids = {
            _mod_key(mod)
            for mod in self.mods
            if mod.component_id and (mod.in_active_profile or mod.state in {"library", "candidate"})
        }
        self._render_rows()
        self._refresh_action_buttons()

    def _enable_selected_clicked(self) -> None:
        targets = self._bulk_mods() or [self.selected]
        if self.on_add_to_profile:
            for mod in targets:
                self.on_add_to_profile(mod)

    def _disable_selected_clicked(self) -> None:
        targets = self._bulk_mods() or [self.selected]
        if self.on_toggle_profile_entry:
            for mod in targets:
                if mod.in_active_profile and mod.profile_enabled:
                    self.on_toggle_profile_entry(mod)

    def _clear_selected_clicked(self) -> None:
        self.selected_bulk_ids.clear()
        self._render_rows()
        self._refresh_action_buttons()

    def _remove_selected_clicked(self) -> None:
        mods = self._bulk_mods() or [self.selected]
        component_ids = [mod.component_id for mod in mods if mod.in_active_profile and mod.component_id]
        if component_ids and self.on_remove_selected_profile_entries:
            self.on_remove_selected_profile_entries(component_ids)
            self.selected_bulk_ids.difference_update(_mod_key(mod) for mod in mods)
        list_component_ids = [mod.component_id for mod in mods if mod.component_id and not mod.installed]
        if list_component_ids and self.on_remove_selected_mods:
            self.on_remove_selected_mods(list_component_ids)
            self.selected_bulk_ids.difference_update(_mod_key(mod) for mod in mods)

    def _uninstall_selected_clicked(self) -> None:
        targets = self._bulk_mods() or [self.selected]
        component_ids = [mod.component_id for mod in targets if mod.component_id]
        if self.on_uninstall_selected_mods:
            self.on_uninstall_selected_mods(component_ids)

    def _reset_to_vanilla_clicked(self) -> None:
        if self.on_reset_to_vanilla:
            self.on_reset_to_vanilla()

    def _bulk_select_changed(self, mod: PlaceholderMod, selected: bool) -> None:
        key = _mod_key(mod)
        if selected:
            self.selected_bulk_ids.add(key)
        else:
            self.selected_bulk_ids.discard(key)
        self._refresh_action_buttons()

    def _bulk_mods(self) -> list[PlaceholderMod]:
        if not self.selected_bulk_ids:
            return []
        return [mod for mod in self.mods if _mod_key(mod) in self.selected_bulk_ids]

    def _review_warnings_clicked(self, mod: PlaceholderMod | None = None) -> None:
        target = mod or self.selected
        self._select(target, inspector_tab="Warnings")
        if self.on_review_warnings:
            self.on_review_warnings(target)

    def _open_source_clicked(self, mod: PlaceholderMod | None = None) -> None:
        target = mod or self.selected
        self.selected = target
        if self.on_open_source:
            self.on_open_source(target)

    def _row_menu_clicked(self, mod: PlaceholderMod, x_root: int, y_root: int) -> None:
        self.selected = mod
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(
            label="Enable",
            command=lambda: self._add_to_profile_for_mod(mod),
            state="normal" if self._can_add_mod_to_profile(mod) else "disabled",
        )
        menu.add_command(
            label="Remove",
            command=lambda: self._remove_from_profile_for_mod(mod),
            state="normal" if mod.in_active_profile and not self.active_profile_protected else "disabled",
        )
        menu.add_separator()
        menu.add_command(
            label="Enable / Disable",
            command=lambda: self._toggle_profile_entry_for_mod(mod),
            state="normal" if self._can_switch_mod(mod) else "disabled",
        )
        menu.add_separator()
        menu.add_command(
            label="Review Warnings",
            command=lambda: self._review_warnings_clicked(mod),
            state="normal" if (mod.warning or mod.profile_warning or mod.dependency_warnings or mod.source_warnings or mod.review_policy_text) else "disabled",
        )
        menu.add_command(
            label="Open Source",
            command=lambda: self._open_source_clicked(mod),
            state="normal" if (mod.source_path or mod.managed_path) else "disabled",
        )
        _label, apply_enabled, _reason = self._preview_action_state()
        menu.add_command(
            label="Apply",
            command=self._preview_deployment_clicked,
            state="normal" if apply_enabled else "disabled",
        )
        try:
            menu.tk_popup(x_root, y_root)
        finally:
            menu.grab_release()

    def _can_switch_mod(self, mod: PlaceholderMod) -> bool:
        if mod.review_policy_text:
            return bool(mod.in_active_profile and mod.profile_enabled and not self.active_profile_protected)
        if mod.in_active_profile:
            return not self.active_profile_protected
        return self._can_add_mod_to_profile(mod)

    def _can_add_mod_to_profile(self, mod: PlaceholderMod) -> bool:
        if mod.in_active_profile or not mod.component_id or mod.review_policy_text:
            return False
        return mod.state == "library"

    def _add_to_profile_for_mod(self, mod: PlaceholderMod) -> None:
        self.selected = mod
        if self.on_add_to_profile:
            self.on_add_to_profile(mod)

    def _remove_from_profile_for_mod(self, mod: PlaceholderMod) -> None:
        self.selected = mod
        if self.on_remove_from_profile:
            self.on_remove_from_profile(mod)

    def _preview_deployment_clicked(self) -> None:
        if self.on_preview_deployment:
            self.on_preview_deployment()

    def _list_view_position(self) -> float | None:
        try:
            return float(self.list_frame._parent_canvas.yview()[0])
        except Exception:
            return None

    def _restore_list_view(self, position: float | None) -> None:
        if position is None:
            return
        try:
            self.after_idle(lambda: self.list_frame._parent_canvas.yview_moveto(position))
        except Exception:
            pass


def placeholder_mods_from_scans(scans: list[ScanResult]) -> list[PlaceholderMod]:
    mods: list[PlaceholderMod] = []
    for scan in scans:
        for component in scan.components:
            warning = "; ".join(component.warnings or component.dependency_warnings or scan.warnings)
            mods.append(
                PlaceholderMod(
                    name=component.display_name,
                    version="scan",
                    description=_component_description(scan, component.file_count),
                    badges=list(component.badges),
                    status="Review" if warning or scan.ambiguous else "Scanned",
                    enabled=False,
                    warning=warning,
                    accent=_accent_for_component(component.component_type),
                )
            )
    return mods


def placeholder_mods_from_view_state(
    view_state: LibraryViewState,
    *,
    profile_membership: dict[str, tuple[bool, int]] | None = None,
    profile_name: str = "",
    profile_warnings: dict[str, str] | None = None,
    deployment_status: dict[str, str] | None = None,
    deployment_preview: str = "",
    installed_component_ids: set[str] | None = None,
) -> list[PlaceholderMod]:
    return [
        _placeholder_from_display_item(
            item,
            profile_membership=profile_membership or {},
            profile_name=profile_name,
            profile_warnings=profile_warnings or {},
            deployment_status=deployment_status or {},
            deployment_preview=deployment_preview,
            installed_component_ids=installed_component_ids or set(),
        )
        for item in view_state.all_items
    ]


def _placeholder_from_display_item(
    item: LibraryDisplayItem,
    *,
    profile_membership: dict[str, tuple[bool, int]],
    profile_name: str,
    profile_warnings: dict[str, str],
    deployment_status: dict[str, str],
    deployment_preview: str,
    installed_component_ids: set[str],
) -> PlaceholderMod:
    membership = profile_membership.get(item.component_id)
    profile_enabled = membership[0] if membership else False
    profile_order = membership[1] if membership else -1
    profile_warning = profile_warnings.get(item.component_id, "")
    preview_status = deployment_status.get(item.component_id, "")
    return PlaceholderMod(
        name=item.display_name,
        version=item.version_label,
        description=item.description,
        badges=list(item.badges),
        status=item.status,
        enabled=profile_enabled if membership else False,
        warning=item.warning,
        accent=item.accent,
        state=item.state,
        source_name=item.source_name,
        source_path=item.source_path,
        managed_path=item.managed_path,
        component_id=item.component_id,
        source_id=item.source_id,
        component_type=item.component_type,
        install_kind=item.install_kind,
        target_hint=item.target_hint,
        file_count=item.file_count,
        files=list(item.files),
        dependency_warnings=list(item.dependency_warnings),
        source_warnings=list(item.source_warnings),
        review_policy_text=item.review_policy_text,
        in_active_profile=membership is not None,
        profile_enabled=profile_enabled,
        profile_order=profile_order,
        profile_name=profile_name,
        profile_warning=profile_warning,
        deployment_status=preview_status,
        deployment_preview=deployment_preview,
        installed=item.component_id in installed_component_ids,
    )


def _component_description(scan: ScanResult, file_count: int) -> str:
    label = "file" if file_count == 1 else "files"
    return f"{file_count} {label} detected from {scan.display_name}. Import copies to manager storage only."


def _accent_for_component(component_type: str) -> str:
    if component_type == COMPONENT_PAK_BUNDLE:
        return "#7E2AFF"
    if component_type == COMPONENT_UE4SS_RUNTIME:
        return "#FFD166"
    if component_type == COMPONENT_UE4SS_MOD:
        return "#38D6D6"
    return "#67D38A"


def _prompt(master, title: str, text: str) -> str | None:
    return prompt_dialog(master.winfo_toplevel(), tokens=master.tokens, title=title, message=text)


def _empty_selection() -> PlaceholderMod:
    return PlaceholderMod(
        name="No Mod Selected",
        version="",
        description="Scan the Mods inbox or import a source to inspect real component details.",
        badges=[],
        status="Empty",
        enabled=False,
        state="empty",
        target_hint="No deployment target",
    )


def _mod_key(mod: PlaceholderMod) -> str:
    return mod.component_id or mod.source_path or mod.name


def preview_apply_action_state(
    mods: list[PlaceholderMod],
    *,
    has_preview_callback: bool = True,
    pending_change_count: int = 0,
) -> tuple[str, bool, str]:
    if not has_preview_callback:
        return "Apply", False, "Apply unavailable."
    if pending_change_count <= 0:
        return "Apply", False, "No pending changes. Enable a mod first."
    return "Apply", True, f"{pending_change_count} pending change(s). Click Apply to update the game."


def _state_label(mod: PlaceholderMod) -> str:
    return mod_display_state(mod)

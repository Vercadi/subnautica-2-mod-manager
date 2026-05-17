from __future__ import annotations

import logging
import shutil
import subprocess
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
import webbrowser

import customtkinter as ctk

try:
    from tkinterdnd2 import TkinterDnD
except Exception:  # pragma: no cover - depends on optional native runtime
    TkinterDnD = None

from .. import __app_name__, __version__
from ..core.app_dirs import AppDirs, resolve_app_dirs
from ..core.apply_workflow import apply_result_text, build_apply_preview
from ..core.activity_log import ActivityLog
from ..core.backup_store import BackupStore
from ..core.config_service import ConfigService
from ..core.diagnostics import collect_diagnostics
from ..core.discovery import discover_all
from ..core.first_run import prepare_first_run_state
from ..core.folder_targets import game_mods_folder_target
from ..core.gamepass_health import GamePassHealth, build_gamepass_health
from ..core.help_about import build_help_about_view
from ..core.library_store import LibraryStore
from ..core.library_workflow import (
    build_library_view_state,
    import_all_candidates,
    import_selected_candidates,
)
from ..core.import_review import (
    build_import_review,
    can_quick_install_review,
    import_review_selection as import_selected_review_sources,
    import_review_summary,
    parse_drop_paths,
    quick_install_selection,
)
from ..core.installer import Installer
from ..core.logging_service import setup_logging
from ..core.manifest_store import ManifestStore
from ..core.needs_attention import build_needs_attention
from ..core.profile_actions import (
    enable_imported_sources,
    smart_set_component_enabled,
    smart_toggle_component,
)
from ..core.profile_store import ProfileStore
from ..core.profile_workflow import (
    LoadoutWarning,
    build_loadout_warnings,
    component_profile_map,
)
from ..core.recovery_service import RecoveryService
from ..core.recovery_workflow import (
    build_recovery_view,
    can_execute_recovery_action,
    restore_preview_text,
    uninstall_result_text,
)
from ..core.settings_workflow import (
    auto_detect_install_path,
    build_settings_view,
    reset_inbox_path,
    settings_refresh_summary,
    update_auto_check_updates,
    update_inbox_path,
    update_manual_install_path,
    update_popup_preference,
    update_popup_policy,
    update_ue4ss_activation_preference,
)
from ..core.settings_store import load_preferences, load_settings, save_settings
from ..core.scan_cache import ScanCache
from ..core.sync_planner import build_sync_deployment_plan
from ..core.timing import timed_operation
from ..core.update_checker import ReleaseInfo, UpdateCheckResult, check_for_update
from ..models.app_state import AppRuntimeState
from ..models.config_file import ConfigFileInfo
from ..models.deployment import DeploymentPlan
from ..models.diagnostics import DiagnosticsReport
from ..models.import_review import ImportReview, ImportSelection
from ..models.mod_state import mod_display_state
from ..models.needs_attention import NeedsAttentionSummary
from ..models.profile import VANILLA_PROFILE_ID
from ..models.preferences import UserPreferences
from ..models.recovery import RecoverySummary, RestoreVanillaPreview
from .shell.background import BackgroundLayer
from .shell.command_bar import CommandBar
from .shell.navigation import NavigationRail
from .tabs.installed_mods_tab import InstalledModsTab, placeholder_mods_from_view_state
from .ui_tokens import UiTokens, ui_tokens_for_size
from .window_utils import apply_window_icon, configure_dialog, confirm_dialog, message_dialog, open_path_in_shell, report_dialog
from .widgets.activity_dialog import ActivityDialog
from .widgets.apply_preview_dialog import ApplyPreviewDialog
from .widgets.help_about_dialog import HelpAboutDialog
from .widgets.import_review_dialog import ImportReviewDialog
from .widgets.mod_row import PlaceholderMod
from .widgets.profiles_dialog import ProfilesDialog
from .widgets.recovery_dialog import RecoveryDialog
from .widgets.settings_dialog import SettingsDialog

log = logging.getLogger(__name__)


class AppWindow(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.tokens: UiTokens = ui_tokens_for_size("default")
        self.dirs: AppDirs = resolve_app_dirs()
        self.settings_path = self.dirs.data_dir / "settings.json"
        self.first_run_messages = prepare_first_run_state(self.dirs, self.settings_path)
        self.log_path = setup_logging(self.dirs.log_dir)
        self.preferences: UserPreferences = load_preferences(self.settings_path)
        self.app_state = self._load_app_state()
        self.preferences = load_preferences(self.settings_path)
        self.activity = ActivityLog(self.dirs.data_dir)
        self.scan_cache = ScanCache(self.dirs.data_dir)
        self.library_store = LibraryStore(self.dirs.data_dir)
        self.manifest_store = ManifestStore(self.dirs.data_dir)
        self.recovery_service = RecoveryService(self.manifest_store)
        self.config_service = ConfigService(self.manifest_store, BackupStore(self.dirs.backup_dir))
        self.recovery_summary: RecoverySummary = self.recovery_service.summary()
        self.restore_preview: RestoreVanillaPreview = self.recovery_service.restore_vanilla_preview(self.app_state.paths)
        self.gamepass_health: GamePassHealth = build_gamepass_health(self.app_state.paths)
        self.diagnostics_report: DiagnosticsReport | None = None
        self.update_check_result: UpdateCheckResult | None = None
        self.needs_attention: NeedsAttentionSummary = NeedsAttentionSummary()
        self.inbox_scans = self._scan_inbox_cached()
        self.hidden_inbox_hashes: set[str] = set()
        self.library_view = build_library_view_state(self.library_store, self._visible_inbox_scans())
        self.profile_store = ProfileStore(self.dirs.data_dir)
        self.loadout_warnings: list[LoadoutWarning] = []
        self.deployment_plan: DeploymentPlan | None = None
        self.scanned_mods = self._mods_from_library_view(refresh_diagnostics=True)
        self.status_log: list[str] = []
        self.installed_tab: InstalledModsTab | None = None
        self.command_bar: CommandBar | None = None

        self.native_file_drop_available = False
        self._init_native_file_drop()

        self.app_icon_path = self.dirs.assets_dir / "app.ico"
        self.app_icon_png_path = self.dirs.assets_dir / "app_icon.png"
        self.title(f"{__app_name__} v{__version__}")
        self._set_window_icon()
        self.geometry("1500x900")
        self.minsize(1280, 760)
        self.configure(fg_color=self.tokens.colors.bg_abyss)

        self._background: BackgroundLayer | None = None
        self._build_ui()
        self._record_activity("startup", "ready", details=self.app_state.paths.display_root)
        if self.preferences.auto_check_updates:
            self.check_updates(show_dialog=False)
        log.info("Started %s v%s", __app_name__, __version__)

    def _set_window_icon(self) -> None:
        if not apply_window_icon(self, self):  # pragma: no cover - platform/window-manager dependent
            log.debug("Window icon unavailable: %s", self.app_icon_path)

    def _load_app_state(self) -> AppRuntimeState:
        saved_paths = load_settings(self.settings_path)
        archive_inbox = saved_paths.archive_inbox_dir or self.dirs.root_dir.parent / "Mods"
        discovered_paths, messages = discover_all(
            extra_steamapps_dirs=saved_paths.steamapps_dirs,
            known_client_root=saved_paths.client_root,
            known_archive_inbox_dir=archive_inbox,
        )
        discovered_paths.data_dir = self.dirs.data_dir
        discovered_paths.backup_dir = self.dirs.backup_dir
        discovered_paths.archive_inbox_dir = archive_inbox
        save_settings(self.settings_path, discovered_paths)
        return AppRuntimeState(
            paths=discovered_paths,
            settings_path=self.settings_path,
            discovery_messages=messages,
        )

    def _init_native_file_drop(self) -> None:
        if TkinterDnD is None:
            return
        try:
            TkinterDnD._require(self)
            self.native_file_drop_available = True
        except Exception as exc:  # pragma: no cover - platform/runtime dependent
            log.debug("Native file drag/drop unavailable: %s", exc)

    def _build_ui(self) -> None:
        t = self.tokens
        c = t.colors

        self._background = BackgroundLayer(self, tokens=t, assets_dir=self.dirs.assets_dir)
        self._background.place(relx=0, rely=0, relwidth=1, relheight=1)

        shell = ctk.CTkFrame(
            self,
            fg_color="#041420",
            corner_radius=t.shell_radius,
            border_width=2,
            border_color=c.shell_border,
        )
        shell.place(relx=0.04, rely=0.052, relwidth=0.92, relheight=0.89)
        shell.grid_columnconfigure(0, minsize=t.nav_width)
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(0, minsize=t.top_bar_height)
        shell.grid_rowconfigure(1, weight=1)

        glow = ctk.CTkFrame(shell, fg_color="transparent", corner_radius=t.shell_radius)
        glow.grid(row=0, column=0, columnspan=2, rowspan=2, sticky="nsew", padx=2, pady=2)

        self.command_bar = CommandBar(
            shell,
            tokens=t,
            path_text=self.app_state.paths.display_root,
            build_text=self.app_state.paths.build_summary,
            on_launch=self.launch_game,
            on_check_updates=self.check_updates,
            on_help=self.open_help_dialog,
            on_settings=self.open_settings_dialog,
        )
        self.command_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))

        nav = NavigationRail(shell, tokens=t, active="Installed Mods", on_select=self.handle_navigation)
        nav.grid(row=1, column=0, sticky="nsew", padx=(12, 8), pady=(0, 12))

        self.installed_tab = InstalledModsTab(
            shell,
            tokens=t,
            mods=self.scanned_mods,
            on_scan=self.scan_mods_inbox,
            on_browse_sources=self.browse_import_sources,
            on_browse_folder=self.browse_import_folder,
            on_drop_sources=self.open_import_review_from_drop,
            on_import_selected=self.import_selected,
            on_import_all=self.import_all,
            profile_names=self._profile_names(),
            active_profile_name=self.profile_store.active_profile().name,
            active_profile_protected=self.profile_store.active_profile().protected,
            profile_warning_count=len(self.loadout_warnings),
            on_profile_select=self.select_profile,
            on_profile_create=self.create_profile,
            on_profile_duplicate=self.duplicate_profile,
            on_profile_rename=self.rename_profile,
            on_profile_delete=self.delete_profile,
            on_add_to_profile=self.add_to_profile,
            on_remove_from_profile=self.remove_from_profile,
            on_toggle_profile_entry=self.toggle_profile_entry,
            on_move_profile_entry=self.move_profile_entry,
            on_activate_all_profile_entries=self.activate_all_profile_entries,
            on_deactivate_all_profile_entries=self.deactivate_all_profile_entries,
            on_remove_all_profile_entries=self.remove_all_profile_entries,
            on_remove_selected_profile_entries=self.remove_selected_profile_entries,
            on_remove_selected_mods=self.remove_selected_mods_from_list,
            on_uninstall_selected_mods=self.uninstall_selected_mods,
            on_reset_to_vanilla=self.reset_to_vanilla,
            on_open_mods_folder=self.open_game_mods_folder,
            on_open_source=self.open_mod_source,
            on_review_warnings=self.open_warning_details,
            on_preview_deployment=self.preview_deployment,
            on_list_configs=self.list_mod_configs,
            on_read_config=self.read_mod_config,
            on_save_config=self.save_mod_config,
            on_restore_config=self.restore_mod_config,
            on_open_config_folder=self.open_config_folder,
            ue4ss_policy=self.preferences.ue4ss_activation_policy(),
            on_toggle_ue4ss_policy=self.toggle_ue4ss_activation_policy,
            pending_change_count=self._pending_change_count(),
        )
        self.installed_tab.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=(0, 12))
        if self.native_file_drop_available and self.installed_tab.enable_native_drop(self.open_import_review_from_drop):
            log.info("Native file drop enabled for import review.")

        for message in self.first_run_messages:
            self._console_write(message)
        for message in self.app_state.discovery_messages:
            self._console_write(message)
        self._console_write(self._inbox_summary())
        self._console_write(f"Settings: {self.settings_path}")
        self._console_write(f"Data dir: {self.dirs.data_dir}")
        self._console_write(f"Library: {self.library_store.library_dir}")
        self._console_write(f"Mods inbox: {self.app_state.paths.archive_inbox_dir}")
        self._console_write(f"Build state: {self.app_state.paths.build_summary}")
        self._console_write(f"Log file: {self.log_path}")
        if self.native_file_drop_available:
            self._console_write("Native drag/drop runtime available.")
        else:
            self._console_write("Native drag/drop placeholder only; tkinterdnd2 runtime not active.")
        if self.deployment_plan is not None:
            self._console_write(f"Deployment preview: {self.deployment_plan.summary_text}")
        self._console_write(self.recovery_summary.text)
        self._console_write(self.restore_preview.text)
        if self.diagnostics_report is not None:
            self._console_write(self.diagnostics_report.summary_text)
        self._refresh_needs_attention()
        self._console_write(self.needs_attention.summary_text)

        self._draw_outer_hud()

    def _draw_outer_hud(self) -> None:
        """Small non-interactive depth/radar HUD outside the shell."""
        t = self.tokens
        c = t.colors
        hud = tk.Canvas(self, width=150, height=190, highlightthickness=0, bg=c.bg_abyss, bd=0)
        self._outer_hud = hud
        hud.create_rectangle(8, 8, 142, 182, outline=c.shell_border_dim, fill="#04131E", width=1)
        hud.create_text(34, 30, text="DEPTH", fill=c.accent_lagoon, font=("Segoe UI", 10, "bold"))
        hud.create_text(51, 58, text="186", fill=c.accent_lagoon, font=("Segoe UI", 24, "bold"))
        hud.create_text(88, 60, text="m", fill=c.text_secondary, font=("Segoe UI", 11))
        cx, cy = 76, 124
        for radius in (24, 42, 58):
            hud.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=c.shell_border_dim)
        hud.create_line(cx, cy - 62, cx, cy + 62, fill=c.border_cold)
        hud.create_line(cx - 62, cy, cx + 62, cy, fill=c.border_cold)
        hud.create_line(cx, cy, cx + 44, cy - 38, fill=c.accent_lagoon, width=2)
        hud.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=c.accent_lagoon, outline="")
        self.bind("<Configure>", self._layout_outer_hud, add="+")
        self._layout_outer_hud()

    def _layout_outer_hud(self, event=None) -> None:
        hud = getattr(self, "_outer_hud", None)
        if hud is None:
            return
        width = self.winfo_width()
        if width < 1650:
            hud.place_forget()
            return
        hud.place(relx=0.952, rely=0.50, anchor="center")

    def _inbox_summary(self) -> str:
        summary = self.library_view.summary
        if not self.inbox_scans:
            return "Mods inbox scan: no sources found."
        return (
            f"Mods inbox scan: {summary.text}; "
            f"{summary.imported_source_count} already imported, {summary.candidate_source_count} candidate."
        )

    def _scan_inbox_cached(self):
        with timed_operation("scan inbox"):
            return self.scan_cache.scan_inbox(self.app_state.paths.archive_inbox_dir)

    def scan_mods_inbox(self) -> None:
        self.inbox_scans = self._scan_inbox_cached()
        self._refresh_library_view(refresh_diagnostics=True)
        self._console_write(self._inbox_summary())
        self._record_activity("scan inbox", "completed", target=str(self.app_state.paths.archive_inbox_dir or ""), details=self.library_view.summary.text)
        if self.library_view.summary.candidate_source_count:
            self._console_write("Inbox candidates are visible in the mod list. Use Install & Enable from the review dialog, or browse/drop for review.")

    def import_selected(self, mod: PlaceholderMod) -> None:
        if not mod.source_path:
            self._console_write("Import selected: no source selected.")
            return
        imported = import_selected_candidates(self.library_store, self._visible_inbox_scans(), {mod.source_path})
        enable_result = None
        if imported:
            enable_result = enable_imported_sources(
                self.profile_store,
                imported,
                self.library_store.list_components(),
            )
        self._refresh_library_view(refresh_diagnostics=True)
        self._console_write(f"Import selected: {len(imported)} source(s) now in manager library. {self.library_view.summary.text}")
        if enable_result is not None:
            self._console_write(enable_result.message)
        self._record_activity("import selected", f"{len(imported)} source(s) + enable", target=mod.name)

    def import_all(self) -> None:
        imported = import_all_candidates(self.library_store, self._visible_inbox_scans())
        enable_result = None
        if imported:
            enable_result = enable_imported_sources(
                self.profile_store,
                imported,
                self.library_store.list_components(),
            )
        self._refresh_library_view(refresh_diagnostics=True)
        self._console_write(f"Import all: {len(imported)} source(s) now in manager library. {self.library_view.summary.text}")
        if enable_result is not None:
            self._console_write(enable_result.message)
        self._record_activity("import all", f"{len(imported)} source(s) + enable", details=self.library_view.summary.text)

    def browse_import_sources(self) -> None:
        paths = filedialog.askopenfilenames(
            parent=self,
            title="Select Subnautica 2 mod sources",
            filetypes=[
                ("Supported mod sources", "*.pak *.ucas *.utoc *.zip *.7z *.rar"),
                ("Unreal pak bundles", "*.pak *.ucas *.utoc"),
                ("Archives", "*.zip *.7z *.rar"),
                ("All files", "*.*"),
            ],
        )
        if paths:
            self.open_import_review(paths)

    def browse_import_folder(self) -> None:
        path = filedialog.askdirectory(parent=self, title="Select a mod folder")
        if path:
            self.open_import_review([path])

    def open_import_review_from_drop(self, data: str) -> None:
        paths = parse_drop_paths(data)
        if not paths:
            self._console_write("Drop ignored: no file or folder paths were received.")
            return
        self.open_import_review(paths)

    def open_import_review(self, paths) -> None:
        imported_hashes = {source.source_hash for source in self.library_store.list_sources() if source.source_hash}
        with timed_operation("build import review"):
            review = build_import_review(paths, imported_hashes=imported_hashes)
        self._console_write(import_review_summary(review))
        self._record_activity("import review", "opened", details=review.summary_text)
        if can_quick_install_review(review):
            self._console_write("Safe supported source detected: installing and enabling without extra review.")
            self.import_review_selection(review, quick_install_selection(review), enable=True)
            return
        ImportReviewDialog(
            self,
            tokens=self.tokens,
            review=review,
            on_import=lambda selection, enable=False: self.import_review_selection(review, selection, enable=enable),
        )

    def import_review_selection(self, review: ImportReview, selection: ImportSelection, *, enable: bool = False) -> None:
        imported = import_selected_review_sources(self.library_store, review, selection)
        for source in imported:
            if source.source_hash:
                self.hidden_inbox_hashes.discard(source.source_hash)
        enable_result = None
        if enable and imported:
            selected_component_ids = {
                component_id
                for component_ids in selection.selected_sources.values()
                for component_id in component_ids
            }
            enable_result = enable_imported_sources(
                self.profile_store,
                imported,
                self.library_store.list_components(),
                selected_component_ids=selected_component_ids,
            )
        self.inbox_scans = self._scan_inbox_cached()
        self._refresh_library_view(refresh_diagnostics=True)
        self._console_write(import_review_summary(review, imported_count=len(imported)))
        if enable_result is not None:
            self._console_write(enable_result.message)
        state = f"imported {len(imported)} source(s)"
        if enable:
            state += " + enable"
        self._record_activity("import review", state, details=review.summary_text)

    def open_recovery_dialog(self) -> None:
        self._refresh_recovery_state()
        view = build_recovery_view(self.manifest_store, self.app_state.paths, recovery_service=self.recovery_service)
        self._console_write(view.summary_text)
        self._console_write(restore_preview_text(view.restore_preview))
        self._record_activity("recovery", "preview opened", details=view.summary_text)
        RecoveryDialog(
            self,
            tokens=self.tokens,
            view=view,
            on_uninstall_selected=self.recovery_uninstall_selected,
            on_uninstall_all=self.recovery_uninstall_all,
            on_create_backup=self.create_manager_state_backup,
        )

    def recovery_uninstall_selected(self, install_ids: list[str]) -> str:
        self._refresh_recovery_state()
        view = build_recovery_view(self.manifest_store, self.app_state.paths, recovery_service=self.recovery_service)
        allowed, reason = can_execute_recovery_action(view, install_ids)
        if not allowed:
            self._console_write(f"Recovery refused: {reason}")
            self._record_activity("recovery uninstall selected", "refused", details=reason)
            return reason
        if not confirm_dialog(
            self,
            tokens=self.tokens,
            title="Uninstall Selected",
            message=(
                f"Uninstall {len(install_ids)} selected manager-installed record(s)? "
                "Only files recorded in install_manifest.json are removed or restored. Unknown/manual files are left alone."
            ),
            confirm_text="Uninstall",
        ):
            return "Uninstall cancelled."
        service = RecoveryService(self.manifest_store, BackupStore(self.dirs.backup_dir))
        result = service.uninstall_selected(install_ids)
        self._refresh_library_view(refresh_recovery=True, refresh_diagnostics=True)
        text = uninstall_result_text(result)
        self._console_write(text)
        self._console_write(self.recovery_summary.text)
        self._record_activity("recovery uninstall selected", "completed" if result.ok else "failed", details=text)
        return text

    def recovery_uninstall_all(self) -> str:
        self._refresh_recovery_state()
        view = build_recovery_view(self.manifest_store, self.app_state.paths, recovery_service=self.recovery_service)
        install_ids = view.uninstallable_install_ids
        allowed, reason = can_execute_recovery_action(view, install_ids)
        if not allowed:
            self._console_write(f"Recovery refused: {reason}")
            self._record_activity("recovery uninstall all", "refused", details=reason)
            return reason
        if not confirm_dialog(
            self,
            tokens=self.tokens,
            title="Uninstall All Mods",
            message=(
                "Uninstall all manager-installed files? Only files recorded in install_manifest.json are removed or restored. "
                "Unknown/manual files are reported only and left alone."
            ),
            confirm_text="Uninstall All Mods",
        ):
            return "Uninstall all cancelled."
        service = RecoveryService(self.manifest_store, BackupStore(self.dirs.backup_dir))
        result = service.uninstall_all()
        self._refresh_library_view(refresh_recovery=True, refresh_diagnostics=True)
        text = uninstall_result_text(result)
        self._console_write(text)
        self._console_write(self.recovery_summary.text)
        self._record_activity("recovery uninstall all", "completed" if result.ok else "failed", details=text)
        return text

    def create_manager_state_backup(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = self.dirs.backup_dir / "manager_state" / stamp
        backup_root.mkdir(parents=True, exist_ok=True)
        files = [
            self.settings_path,
            self.dirs.data_dir / "profiles.json",
            self.dirs.data_dir / "library_state.json",
            self.dirs.data_dir / "install_manifest.json",
            self.dirs.data_dir / "activity.json",
        ]
        copied = 0
        for path in files:
            if path.is_file():
                shutil.copy2(path, backup_root / path.name)
                copied += 1
        message = f"Manager state backup created: {backup_root} ({copied} file(s)). Game files were not touched."
        self._console_write(message)
        self._record_activity("backup", "manager state", target=str(backup_root), details=f"{copied} file(s)")
        return message

    def open_settings_dialog(self) -> None:
        view = self._settings_view()
        self._console_write(view.summary_text)
        SettingsDialog(
            self,
            tokens=self.tokens,
            view=view,
            on_browse_install=self.settings_browse_install,
            on_auto_detect=self.settings_auto_detect,
            on_browse_inbox=self.settings_browse_inbox,
            on_reset_inbox=self.settings_reset_inbox,
            on_toggle_auto_updates=self.settings_toggle_auto_updates,
            on_toggle_popup_preference=self.settings_toggle_popup_preference,
            on_set_popup_policy=self.settings_set_popup_policy,
        )
        self._record_activity("settings", "opened")

    def settings_browse_install(self):
        path = filedialog.askdirectory(parent=self, title="Select Subnautica 2 install root")
        if not path:
            return None
        result = update_manual_install_path(
            self.settings_path,
            self.app_state.paths,
            Path(path),
            data_dir=self.dirs.data_dir,
            backup_dir=self.dirs.backup_dir,
        )
        return self._apply_settings_result(result, apply_paths=result.ok)

    def settings_auto_detect(self):
        result = auto_detect_install_path(
            self.settings_path,
            self.app_state.paths,
            data_dir=self.dirs.data_dir,
            backup_dir=self.dirs.backup_dir,
        )
        return self._apply_settings_result(result, apply_paths=True)

    def settings_browse_inbox(self):
        path = filedialog.askdirectory(parent=self, title="Select Mods inbox folder")
        if not path:
            return None
        result = update_inbox_path(
            self.settings_path,
            self.app_state.paths,
            Path(path),
            data_dir=self.dirs.data_dir,
            backup_dir=self.dirs.backup_dir,
        )
        return self._apply_settings_result(result, apply_paths=result.ok)

    def settings_reset_inbox(self):
        result = reset_inbox_path(
            self.settings_path,
            self.app_state.paths,
            self.dirs.root_dir.parent / "Mods",
            data_dir=self.dirs.data_dir,
            backup_dir=self.dirs.backup_dir,
        )
        return self._apply_settings_result(result, apply_paths=result.ok)

    def settings_toggle_auto_updates(self):
        self.preferences = update_auto_check_updates(self.settings_path, not self.preferences.auto_check_updates)
        state = "enabled" if self.preferences.auto_check_updates else "disabled"
        message = f"Startup update checks {state}. Manual update checks remain available."
        self._console_write(f"Settings saved: {message}")
        self._record_activity("settings", "saved", details=message)
        return self._settings_view(), message

    def settings_toggle_popup_preference(self, preference_name: str):
        current = bool(getattr(self.preferences, preference_name))
        self.preferences = update_popup_preference(self.settings_path, preference_name, not current)
        label = preference_name.replace("show_", "").replace("_", " ").replace("popups", "popups")
        state = "enabled" if getattr(self.preferences, preference_name) else "disabled"
        message = f"{label.title()} {state}. Critical safety popups remain always enabled."
        self._console_write(f"Settings saved: {message}")
        self._record_activity("settings", "saved", details=message)
        return self._settings_view(), message

    def settings_set_popup_policy(self, policy_label: str):
        self.preferences = update_popup_policy(self.settings_path, policy_label)
        message = f"Popup policy saved: {self.preferences.popup_policy_label}. Critical safety confirmations remain always enabled."
        self._console_write(f"Settings saved: {message}")
        self._record_activity("settings", "saved", details=message)
        return self._settings_view(), message

    def toggle_ue4ss_activation_policy(self, preference_name: str) -> dict[str, bool]:
        current = bool(getattr(self.preferences, preference_name))
        self.preferences = update_ue4ss_activation_preference(self.settings_path, preference_name, not current)
        message = f"UE4SS activation policy saved: {self.preferences.ue4ss_policy_text}. Real writes still require guarded apply."
        self._console_write(message)
        self._record_activity("settings", "saved", details=message)
        if self.installed_tab is not None:
            self.installed_tab.set_ue4ss_policy(self.preferences.ue4ss_activation_policy())
        return self.preferences.ue4ss_activation_policy()

    def handle_navigation(self, label: str) -> None:
        if label == "Installed Mods":
            self._console_write("Navigation: Installed Mods / Library is already active.")
            return
        if label == "Profiles":
            self.open_profiles_dialog()
        elif label in {"Recovery", "Installed Files / Backups"}:
            self.open_recovery_dialog()
        elif label == "Diagnostics":
            self.open_diagnostics_dialog()
        elif label == "Activity":
            self.open_activity_dialog()
        elif label == "Help / Support":
            self.open_help_dialog()
        else:
            self._console_write(f"Navigation target is not implemented: {label}")

    def select_profile(self, name: str) -> None:
        profile = self.profile_store.get_profile_by_name(name)
        if profile is None:
            self._console_write(f"Profile not found: {name}")
            return
        self.profile_store.set_active_profile(profile.profile_id)
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Active profile: {profile.name}. Click Apply to update the game.")
        self._record_activity("profile", "selected", target=profile.name)

    def create_profile(self, name: str) -> None:
        profile = self.profile_store.create_profile(name)
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Created profile: {profile.name}")
        self._record_activity("profile", "created", target=profile.name)

    def duplicate_profile(self, name: str) -> None:
        try:
            profile = self.profile_store.duplicate_profile(self.profile_store.active_profile().profile_id, name)
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Saved profile as: {profile.name}")
        self._record_activity("profile", "duplicated", target=profile.name)

    def rename_profile(self, name: str) -> None:
        try:
            profile = self.profile_store.rename_profile(self.profile_store.active_profile().profile_id, name)
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Renamed active profile: {profile.name}")
        self._record_activity("profile", "renamed", target=profile.name)

    def delete_profile(self) -> None:
        active = self.profile_store.active_profile()
        try:
            self.profile_store.delete_profile(active.profile_id)
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Deleted profile: {active.name}")
        self._record_activity("profile", "deleted", target=active.name)

    def add_to_profile(self, mod: PlaceholderMod) -> None:
        if not mod.component_id:
            self._console_write("Import this mod before adding it to a profile.")
            return
        if mod.state.startswith("candidate"):
            self._console_write("Import this inbox candidate before enabling it.")
            return
        if mod.review_policy_text:
            self._console_write(f"Needs review before profile enable: {mod.review_policy_text}")
            return
        result = smart_set_component_enabled(
            self.profile_store,
            mod.component_id,
            self.library_store.list_components(),
            enabled=True,
        )
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"{result.message} {self._pending_change_text()}")
        self._record_activity(
            "profile loadout",
            "enabled" if result.ok else "refused",
            target=mod.name,
            details=result.message,
        )

    def remove_from_profile(self, mod: PlaceholderMod) -> None:
        active = self.profile_store.active_profile()
        try:
            changed = self.profile_store.remove_component(active.profile_id, mod.component_id)
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Remove from profile: {'removed' if changed else 'not present'} {mod.name}. {self._pending_change_text()}")
        self._record_activity("profile loadout", "removed" if changed else "not present", target=mod.name)

    def toggle_profile_entry(self, mod: PlaceholderMod) -> None:
        if not mod.component_id:
            self._console_write("Import this mod before enabling it.")
            return
        if mod.state.startswith("candidate"):
            self._console_write("Import this inbox candidate before enabling it.")
            return
        if mod.review_policy_text and not mod.in_active_profile:
            self._console_write(f"Needs review before profile enable: {mod.review_policy_text}")
            return
        result = smart_toggle_component(
            self.profile_store,
            mod.component_id,
            self.library_store.list_components(),
        )
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"{result.message} {self._pending_change_text()}")
        self._record_activity(
            "profile loadout",
            "toggled" if result.ok else "refused",
            target=mod.name,
            details=result.message,
        )

    def move_profile_entry(self, mod: PlaceholderMod, delta: int) -> None:
        active = self.profile_store.active_profile()
        if not mod.in_active_profile:
            self._console_write("Reorder requires a component in the active profile.")
            return
        try:
            if delta == "top":
                changed = self.profile_store.move_component_to_top(active.profile_id, mod.component_id)
            elif delta == "bottom":
                changed = self.profile_store.move_component_to_bottom(active.profile_id, mod.component_id)
            else:
                step = -1 if delta == "up" else 1 if delta == "down" else int(delta)
                changed = self.profile_store.move_component(active.profile_id, mod.component_id, step)
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Loadout order {'updated' if changed else 'unchanged'}: {mod.name}")
        self._record_activity("profile loadout", "reordered" if changed else "unchanged", target=mod.name)

    def activate_all_profile_entries(self) -> None:
        self._set_all_profile_entries(True)

    def deactivate_all_profile_entries(self) -> None:
        self._set_all_profile_entries(False)

    def remove_all_profile_entries(self) -> None:
        active = self.profile_store.active_profile()
        try:
            removed = self.profile_store.remove_all_components(active.profile_id)
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Profile loadout cleared: {removed} component(s) removed from {active.name}.")
        self._record_activity("profile loadout", "cleared", target=active.name, details=f"{removed} removed")

    def remove_selected_profile_entries(self, component_ids: list[str]) -> None:
        active = self.profile_store.active_profile()
        removed = 0
        try:
            for component_id in dict.fromkeys(component_ids):
                if self.profile_store.remove_component(active.profile_id, component_id):
                    removed += 1
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        self._console_write(f"Profile selection removed: {removed} component(s) removed from {active.name}. {self._pending_change_text()}")
        self._record_activity("profile loadout", "selection removed", target=active.name, details=f"{removed} removed")

    def _set_all_profile_entries(self, enabled: bool) -> None:
        active = self.profile_store.active_profile()
        try:
            changed = self.profile_store.set_all_enabled(active.profile_id, enabled)
        except ValueError as exc:
            self._console_write(str(exc))
            return
        self._refresh_library_view(rebuild_library=False)
        state = "enabled" if enabled else "disabled"
        self._console_write(f"Profile loadout {state}: {changed} component(s) changed in {active.name}. {self._pending_change_text()}")
        self._record_activity("profile loadout", state, target=active.name, details=f"{changed} changed")

    def uninstall_selected_mods(self, component_ids: list[str]) -> None:
        component_ids = list(dict.fromkeys(component_id for component_id in component_ids if component_id))
        if not component_ids:
            self._console_write("Uninstall: select one or more installed mods first.")
            return
        if not confirm_dialog(
            self,
            tokens=self.tokens,
            title="Uninstall Selected",
            message=(
                f"Uninstall selected manager-installed files for {len(component_ids)} mod(s)? "
                "Only files recorded in install_manifest.json are removed or restored. Unknown/manual files are left alone."
            ),
            confirm_text="Uninstall",
        ):
            self._console_write("Uninstall selected cancelled.")
            return
        service = RecoveryService(self.manifest_store, BackupStore(self.dirs.backup_dir))
        result = service.uninstall_components(component_ids)
        self._remove_components_from_active_profile(component_ids)
        self.hidden_inbox_hashes.update(self._source_hashes_for_components(component_ids))
        removed_from_list = self.library_store.remove_components(component_ids)
        self._refresh_library_view(refresh_recovery=True, refresh_diagnostics=True)
        text = uninstall_result_text(result)
        if removed_from_list:
            text += f" Removed {removed_from_list} mod(s) from the manager list."
        self._console_write(text)
        self._console_write(self.recovery_summary.text)
        self._record_activity("uninstall selected mods", "completed" if result.ok else "failed", details=text)

    def remove_selected_mods_from_list(self, component_ids: list[str]) -> None:
        component_ids = list(dict.fromkeys(component_id for component_id in component_ids if component_id))
        if not component_ids:
            self._console_write("Remove: select one or more mods first.")
            return
        installed = self._installed_component_ids()
        blocked = [component_id for component_id in component_ids if component_id in installed]
        removable = [component_id for component_id in component_ids if component_id not in installed]
        if blocked:
            self._console_write("Remove: installed mods need Uninstall first. Unknown/manual files are left alone.")
        if not removable:
            return
        self._remove_components_from_active_profile(removable)
        self.hidden_inbox_hashes.update(self._source_hashes_for_components(removable))
        removed = self.library_store.remove_components(removable)
        self._refresh_library_view(refresh_recovery=True, refresh_diagnostics=True)
        self._console_write(f"Removed {removed} mod(s) from the manager list.")
        self._record_activity("mod list", "removed", details=f"{removed} removed")

    def _remove_components_from_active_profile(self, component_ids: list[str]) -> int:
        active = self.profile_store.active_profile()
        if active.protected:
            return 0
        removed = 0
        for component_id in dict.fromkeys(component_ids):
            try:
                if self.profile_store.remove_component(active.profile_id, component_id):
                    removed += 1
            except ValueError:
                break
        return removed

    def reset_to_vanilla(self) -> None:
        if not confirm_dialog(
            self,
            tokens=self.tokens,
            title="Reset to Vanilla",
            message=(
                "Switch to the Vanilla profile and remove manager-installed files now? "
                "Only files recorded in install_manifest.json are removed or restored. Unknown/manual files are left alone."
            ),
            confirm_text="Reset to Vanilla",
        ):
            self._console_write("Reset to Vanilla cancelled.")
            return
        self.profile_store.set_active_profile(VANILLA_PROFILE_ID)
        self._refresh_library_view(rebuild_library=False, refresh_recovery=True)
        self._console_write(f"Active profile: Vanilla. {self._pending_change_text()}")
        self._record_activity("profile", "reset preview", target="Vanilla")
        self.preview_deployment()

    def preview_deployment(self) -> None:
        self._refresh_library_view(rebuild_library=False)
        plan = self._build_apply_dialog_plan()
        if plan is None:
            self._console_write("Deployment preview unavailable.")
            return
        preview = build_apply_preview(plan)
        if not preview.allow_apply:
            message = preview.disabled_reason or "No installable changes."
            self._console_write(f"Apply skipped: {message}")
            self._record_activity("apply", "skipped", details=message)
            if self.installed_tab is not None:
                self.installed_tab.set_action_message(message, warning=True)
            return
        if preview.blocked:
            self._console_write(
                f"Apply will skip {preview.review_required_count} review-required file action(s) and install supported changes."
            )
        self._apply_profile_from_dialog(plan)

    def center_dialog(self, window, width: int, height: int, *, modal: bool = True) -> None:
        configure_dialog(window, self, width=width, height=height, modal=modal, topmost=True)

    def launch_game(self) -> None:
        executable = next(
            (
                path
                for path in (self.app_state.paths.shipping_exe, self.app_state.paths.client_exe)
                if path is not None and path.is_file()
            ),
            None,
        )
        if executable is None or not executable.is_file():
            message = "Launch refused: Subnautica 2 executable is not configured or does not exist."
            self._console_write(message)
            self._record_activity("launch game", "refused", details=message)
            self._show_message("warning", "Launch Game", message)
            return
        try:
            subprocess.Popen([str(executable)], cwd=str(executable.parent))
        except Exception as exc:
            message = f"Launch failed: {exc}"
            self._console_write(message)
            self._record_activity("launch game", "failed", target=str(executable), details=str(exc))
            self._show_message("warning", "Launch Game", message)
            return
        message = f"Launched {executable.name}."
        self._console_write(message)
        self._record_activity("launch game", "started", target=str(executable))

    def check_updates(self, show_dialog: bool = True) -> None:
        self._console_write("Checking GitHub Releases for app updates...")
        self._record_activity("update check", "started")

        def _available(release: ReleaseInfo) -> None:
            self.after(0, lambda: self._update_available(release, show_dialog=show_dialog))

        def _current() -> None:
            self.after(0, lambda: self._update_current(show_dialog=show_dialog))

        def _error(message: str) -> None:
            self.after(0, lambda: self._update_error(message, show_dialog=show_dialog))

        check_for_update(__version__, _available, _current, _error)

    def _update_available(self, release: ReleaseInfo, *, show_dialog: bool) -> None:
        self.update_check_result = UpdateCheckResult("available", f"Update available: {release.display_version}", release)
        url = release.html_url or "release URL unavailable"
        preferred = release.preferred_asset.name if release.preferred_asset else "no preferred asset"
        message = f"Update available: {release.display_version}. Preferred asset: {preferred}. Release: {url}"
        self._console_write(message)
        self._record_activity("update check", "available", target=release.display_version, details=url)
        self._refresh_needs_attention()
        if show_dialog and self.preferences.show_update_popups:
            message_dialog(self, tokens=self.tokens, title="Update Available", message=message)

    def _update_current(self, *, show_dialog: bool) -> None:
        self.update_check_result = UpdateCheckResult("current", f"Already up to date: {__version__}")
        self._console_write(self.update_check_result.message)
        self._record_activity("update check", "current", details=self.update_check_result.message)
        self._refresh_needs_attention()
        if show_dialog and self.preferences.show_update_popups:
            message_dialog(self, tokens=self.tokens, title="Check Updates", message=self.update_check_result.message)

    def _update_error(self, message: str, *, show_dialog: bool) -> None:
        self.update_check_result = UpdateCheckResult("error", message)
        self._console_write(f"Update check failed: {message}")
        self._record_activity("update check", "error", details=message)
        self._refresh_needs_attention()
        if show_dialog and self.preferences.show_update_popups:
            message_dialog(self, tokens=self.tokens, title="Check Updates", message=f"Update check failed: {message}")

    def open_help_dialog(self) -> None:
        self._refresh_diagnostics()
        report_text = self.diagnostics_report.support_report_text() if self.diagnostics_report else "Diagnostics unavailable."
        view = build_help_about_view(
            paths=self.app_state.paths,
            data_dir=self.dirs.data_dir,
            library_dir=self.library_store.library_dir,
            backup_dir=self.dirs.backup_dir,
            log_dir=self.dirs.log_dir,
            docs_dir=self.dirs.root_dir / "docs",
            support_report=report_text,
            release_metadata_path=self.dirs.root_dir / "release-metadata.json",
        )
        self._console_write(view.summary_text)
        self._record_activity("help", "opened")
        HelpAboutDialog(self, tokens=self.tokens, view=view, on_open_folder=self.open_folder)

    def open_activity_dialog(self) -> None:
        records = self.activity.list_records(limit=80)
        self._console_write(f"Activity: {len(records)} recent event(s).")
        ActivityDialog(self, tokens=self.tokens, records=records)

    def open_profiles_dialog(self) -> None:
        active = self.profile_store.active_profile()
        self._record_activity("navigation", "profiles opened", target=active.name)
        ProfilesDialog(
            self,
            tokens=self.tokens,
            get_profiles=self.profile_store.list_profiles,
            get_active_profile=self.profile_store.active_profile,
            on_select=self.select_profile,
            on_create=self.create_profile,
            on_duplicate=self.duplicate_profile,
            on_rename=self.rename_profile,
            on_delete=self.delete_profile,
        )

    def open_diagnostics_dialog(self) -> None:
        self._refresh_diagnostics()
        self._refresh_needs_attention()
        report = self.diagnostics_report.support_report_text() if self.diagnostics_report else "Diagnostics unavailable."
        message = "\n".join(
            [
                "Needs Attention",
                _compact_needs_attention_text(self.needs_attention),
                "",
                "Diagnostics / Support Report",
                report,
                "",
                "Recent Status Log",
                "\n".join(self.status_log[-40:]) if self.status_log else "No status messages captured.",
            ]
        )
        self._console_write(self.needs_attention.summary_text)
        self._record_activity("diagnostics", "opened")
        report_dialog(
            self,
            tokens=self.tokens,
            title="Diagnostics / Needs Attention",
            message=message,
            width=900,
            height=680,
            copy_text=message,
            save_text=message,
        )

    def open_warning_details(self, mod: PlaceholderMod) -> None:
        warnings = []
        if mod.warning:
            warnings.append(mod.warning)
        if mod.profile_warning:
            warnings.append(mod.profile_warning)
        warnings.extend(mod.dependency_warnings)
        warnings.extend(mod.source_warnings)
        if mod.review_policy_text:
            warnings.append(mod.review_policy_text)
        lines = [
            mod.name,
            f"State: {mod_display_state(mod)}",
            f"Profile: {'Enabled in active profile' if mod.in_active_profile and mod.profile_enabled else 'Disabled in active profile' if mod.in_active_profile else 'Not in Profile'}",
            "",
            "Warnings:",
        ]
        if warnings:
            lines.extend(f"- {message}" for message in dict.fromkeys(warnings))
        else:
            lines.append("- No warnings for this component.")
        lines.extend(
            [
                "",
                "Next actions:",
                "- Install candidates before adding them to profiles.",
                "- Add UE4SS Runtime to the same profile before UE4SS mods when warned.",
                "- Keep review-required loose overlays out of release profiles until manually reviewed.",
                "- Use Apply to inspect exact target paths before installing changes.",
            ]
        )
        self._record_activity("warning details", "opened", target=mod.name)
        self._console_write(f"Warnings for {mod.name}: " + ("; ".join(dict.fromkeys(warnings)) if warnings else "none"))

    def open_mod_source(self, mod: PlaceholderMod) -> None:
        path_text = mod.managed_path or mod.source_path
        path = Path(path_text) if path_text else None
        ok, message = open_path_in_shell(path)
        self._console_write(message)
        self._record_activity("open source", "opened" if ok else "refused", target=mod.name, details=message)

    def list_mod_configs(self, mod: PlaceholderMod) -> list[ConfigFileInfo]:
        if not mod.installed or not mod.component_id:
            return []
        return self.config_service.list_component_configs(mod.component_id)

    def read_mod_config(self, info: ConfigFileInfo) -> tuple[bool, str]:
        return self.config_service.read_config(info)

    def save_mod_config(self, mod: PlaceholderMod, info: ConfigFileInfo, text: str):
        result = self.config_service.save_config(info, text)
        self._console_write(result.message)
        self._record_activity("config edit", "saved" if result.ok else "refused", target=mod.name, details=result.message)
        self._refresh_recovery_state()
        return result

    def restore_mod_config(self, mod: PlaceholderMod, info: ConfigFileInfo):
        result = self.config_service.restore_original(info)
        self._console_write(result.message)
        self._record_activity("config restore", "restored" if result.ok else "refused", target=mod.name, details=result.message)
        self._refresh_recovery_state()
        return result

    def open_config_folder(self, info: ConfigFileInfo) -> None:
        self.open_folder(info.installed_path.parent)

    def _show_message(self, kind: str, title: str, message: str, *, force: bool = False) -> None:
        if force or self.preferences.popup_enabled(kind):
            message_dialog(self, tokens=self.tokens, title=title, message=message)
        else:
            self._console_write(f"{title}: {message}")

    def open_folder(self, path: Path | None) -> str:
        ok, message = open_path_in_shell(path)
        self._console_write(message)
        self._record_activity("open folder", "opened" if ok else "refused", target=str(path or ""), details=message)
        return message

    def open_game_mods_folder(self) -> str:
        target = game_mods_folder_target(self.app_state.paths)
        ok, message = open_path_in_shell(target.path)
        if ok:
            message = f"Opened {target.label}: {target.path}"
        else:
            message = f"Open Mods Folder refused: {message}"
        self._console_write(message)
        self._record_activity("open mods folder", "opened" if ok else "refused", target=str(target.path or ""), details=message)
        return message

    def open_release_url(self) -> None:
        if self.update_check_result and self.update_check_result.release and self.update_check_result.release.html_url:
            webbrowser.open(self.update_check_result.release.html_url)

    def _refresh_library_view(
        self,
        *,
        rebuild_library: bool = True,
        refresh_recovery: bool = False,
        refresh_diagnostics: bool = False,
        refresh_inspector: bool | None = None,
    ) -> None:
        if refresh_inspector is None:
            refresh_inspector = rebuild_library
        if refresh_recovery:
            self._refresh_recovery_state()
        if rebuild_library:
            self.library_view = build_library_view_state(self.library_store, self._visible_inbox_scans())
        self.scanned_mods = self._mods_from_library_view(refresh_diagnostics=refresh_diagnostics)
        if self.installed_tab is not None:
            self.installed_tab.set_mods(self.scanned_mods, refresh_inspector=refresh_inspector)
            self.installed_tab.set_profile_state(
                profile_names=self._profile_names(),
                active_profile_name=self.profile_store.active_profile().name,
                active_profile_protected=self.profile_store.active_profile().protected,
                profile_warning_count=len(self.loadout_warnings),
                pending_change_count=self._pending_change_count(),
            )

    def _settings_view(self):
        return build_settings_view(
            self.app_state.paths,
            data_dir=self.dirs.data_dir,
            library_dir=self.library_store.library_dir,
            backup_dir=self.dirs.backup_dir,
            preferences=self.preferences,
        )

    def _apply_settings_result(self, result, *, apply_paths: bool):
        if apply_paths:
            self.app_state.paths = result.paths
            self.app_state.discovery_messages = result.discovery_messages
            self.gamepass_health = build_gamepass_health(self.app_state.paths)
            self.inbox_scans = self._scan_inbox_cached()
            self._refresh_library_view(refresh_recovery=True, refresh_diagnostics=True)
            if self.command_bar is not None:
                self.command_bar.set_status(
                    path_text=self.app_state.paths.display_root,
                    build_text=self.app_state.paths.build_summary,
                )
        message = settings_refresh_summary(result, len(self.inbox_scans))
        self._console_write(message)
        for discovery_message in result.discovery_messages:
            self._console_write(discovery_message)
        self._record_activity("settings", "saved" if result.ok else "refused", details=result.message)
        return self._settings_view(), message

    def _console_write(self, message: str) -> None:
        text = str(message or "")
        self.status_log.append(text)
        if len(self.status_log) > 300:
            self.status_log = self.status_log[-300:]

    def _mods_from_library_view(self, *, refresh_diagnostics: bool = False) -> list[PlaceholderMod]:
        active = self.profile_store.active_profile()
        self.loadout_warnings = build_loadout_warnings(
            active,
            self.library_store.list_components(),
            ue4ss_runtime_installed=self._ue4ss_runtime_installed(),
        )
        self.deployment_plan = self._build_deployment_plan(active)
        if refresh_diagnostics or self.diagnostics_report is None:
            self._refresh_diagnostics()
        self._refresh_needs_attention()
        return placeholder_mods_from_view_state(
            self.library_view,
            profile_membership=component_profile_map(active),
            profile_name=active.name,
            profile_warnings=self._profile_warning_map(),
            deployment_status=self._deployment_status_map(),
            deployment_preview=self._preview_text(),
            installed_component_ids=self._installed_component_ids(),
        )

    def _profile_warning_map(self) -> dict[str, str]:
        grouped: dict[str, list[str]] = {}
        for warning in self.loadout_warnings:
            grouped.setdefault(warning.component_id, []).append(warning.message)
        return {
            component_id: "; ".join(dict.fromkeys(messages))
            for component_id, messages in grouped.items()
        }

    def _profile_names(self) -> list[str]:
        return [profile.name for profile in self.profile_store.list_profiles()]

    def _refresh_recovery_state(self) -> None:
        self.manifest_store = ManifestStore(self.dirs.data_dir)
        self.recovery_service = RecoveryService(self.manifest_store)
        self.config_service = ConfigService(self.manifest_store, BackupStore(self.dirs.backup_dir))
        self.recovery_summary = self.recovery_service.summary()
        self.restore_preview = self.recovery_service.restore_vanilla_preview(self.app_state.paths)

    def _refresh_diagnostics(self) -> None:
        self.diagnostics_report = collect_diagnostics(
            paths=self.app_state.paths,
            data_dir=self.dirs.data_dir,
            library_store=self.library_store,
            profile_store=self.profile_store,
            manifest_store=self.manifest_store,
            deployment_plan=self.deployment_plan,
            recovery_summary=self.recovery_summary,
            log_path=self.log_path,
        )

    def _refresh_needs_attention(self) -> None:
        self.needs_attention = build_needs_attention(
            paths=self.app_state.paths,
            scans=self._visible_inbox_scans(),
            library_sources=self.library_store.list_sources(),
            library_components=self.library_store.list_components(),
            loadout_warnings=self.loadout_warnings,
            deployment_plan=self.deployment_plan,
            recovery_summary=self.recovery_summary,
            update_result=self.update_check_result,
        )

    def _preview_text(self) -> str:
        lines: list[str] = []
        if self.deployment_plan is not None:
            lines.append(self.deployment_plan.preview_text())
        lines.extend(
            [
                "",
                "Recovery Summary",
                self.recovery_summary.text,
                self.restore_preview.text,
                "",
                "Diagnostics",
                self.diagnostics_report.summary_text if self.diagnostics_report else "Diagnostics unavailable.",
                "Managed recovery uses the manifest and leaves unknown files alone.",
            ]
        )
        return "\n".join(lines).strip()

    def _build_deployment_plan(self, active_profile) -> DeploymentPlan:
        return build_sync_deployment_plan(
            active_profile,
            sources=self.library_store.list_sources(),
            components=self.library_store.list_components(),
            paths=self.app_state.paths,
            installed_records=self.manifest_store.list_installs(),
            ue4ss_runtime_installed=self._ue4ss_runtime_installed(),
            dry_run=True,
            real_apply_enabled=False,
            ue4ss_activation_policy=self.preferences.ue4ss_activation_policy(),
        )

    def _build_apply_dialog_plan(self) -> DeploymentPlan | None:
        active = self.profile_store.active_profile()
        return build_sync_deployment_plan(
            active,
            sources=self.library_store.list_sources(),
            components=self.library_store.list_components(),
            paths=self.app_state.paths,
            installed_records=self.manifest_store.list_installs(),
            ue4ss_runtime_installed=self._ue4ss_runtime_installed(),
            dry_run=False,
            real_apply_enabled=True,
            ue4ss_activation_policy=self.preferences.ue4ss_activation_policy(),
        )

    def _apply_profile_from_dialog(self, plan: DeploymentPlan) -> str:
        preview = build_apply_preview(plan)
        if not preview.allow_apply:
            message = preview.disabled_reason or "Apply is disabled for this plan."
            self._console_write(f"Apply refused: {message}")
            self._record_activity("apply", "refused", details=message)
            return message
        installer = Installer(
            manifest_store=ManifestStore(self.dirs.data_dir),
            backup_store=BackupStore(self.dirs.backup_dir),
        )
        result = installer.apply(plan, allow_real_apply=preview.real_apply_enabled)
        self._refresh_library_view(refresh_recovery=True, refresh_diagnostics=True)
        text = apply_result_text(
            result.ok,
            result.record.status,
            len(result.record.deployed_files),
            len(result.record.backups),
            result.record.errors,
        )
        self._console_write(text)
        self._console_write(self.recovery_summary.text)
        self._record_activity("apply", "completed" if result.ok else "failed", details=text)
        if self.installed_tab is not None:
            self.installed_tab.set_action_message(text, warning=not result.ok)
        return text

    def _deployment_status_map(self) -> dict[str, str]:
        if self.deployment_plan is None:
            return {}
        status: dict[str, list[str]] = {}
        for action in self.deployment_plan.actions:
            status.setdefault(action.component_id, []).append(action.action)
        for skip in self.deployment_plan.skips:
            status.setdefault(skip.component_id, []).append("skip")
        return {
            component_id: _summarize_actions(actions)
            for component_id, actions in status.items()
        }

    def _installed_component_ids(self) -> set[str]:
        installed: set[str] = set()
        for record in self.manifest_store.list_installs():
            if record.status == "uninstalled":
                continue
            for deployed in record.deployed_files:
                if deployed.action == "delete":
                    continue
                if deployed.component_id and deployed.target_path.exists():
                    installed.add(deployed.component_id)
        return installed

    def _pending_change_count(self) -> int:
        if self.deployment_plan is None:
            return 0
        return len(self.deployment_plan.creates) + len(self.deployment_plan.overwrites) + len(self.deployment_plan.deletes)

    def _pending_change_text(self) -> str:
        count = self._pending_change_count()
        if count <= 0:
            return "No pending game changes."
        return f"{count} pending change(s). Click Apply to update the game."

    def _visible_inbox_scans(self):
        if not self.hidden_inbox_hashes:
            return self.inbox_scans
        return [
            scan for scan in self.inbox_scans
            if not scan.source_hash or scan.source_hash not in self.hidden_inbox_hashes
        ]

    def _source_hashes_for_components(self, component_ids: list[str]) -> set[str]:
        selected = set(component_ids)
        source_ids = {
            component.source_id
            for component in self.library_store.list_components()
            if component.component_id in selected
        }
        return {
            source.source_hash
            for source in self.library_store.list_sources()
            if source.source_id in source_ids and source.source_hash
        }

    def _ue4ss_runtime_installed(self) -> bool:
        paths = self.app_state.paths
        win64 = paths.win64
        runtime_root = paths.ue4ss_runtime_root
        ue4ss_root = paths.ue4ss_root
        for root in (runtime_root, win64):
            if root and any((root / name).exists() for name in ("UE4SS.dll", "dwmapi.dll", "xinput1_3.dll")):
                return True
        return bool(ue4ss_root and ((ue4ss_root / "UE4SS.dll").exists() or ue4ss_root.exists()))

    def _record_activity(self, action: str, result: str, *, target: str = "", details: str = "") -> None:
        try:
            self.activity.append(action=action, result=result, target=target, details=details)
        except Exception as exc:
            log.debug("Could not write activity record: %s", exc)


def main() -> None:
    app = AppWindow()
    app.mainloop()


def _summarize_actions(actions: list[str]) -> str:
    display = {"create": "install", "delete": "remove"}
    counts = {action: actions.count(action) for action in sorted(set(actions))}
    return ", ".join(f"{count} {display.get(name, name)}" for name, count in counts.items())


def _compact_needs_attention_text(summary, *, limit: int = 8) -> str:
    if not getattr(summary, "items", None):
        return summary.summary_text
    lines = [summary.summary_text]
    for item in summary.items[:limit]:
        lines.append(f"- {item.title}: {_compact_line(item.detail, 130)}")
    remaining = len(summary.items) - limit
    if remaining > 0:
        lines.append(f"- ... {remaining} more")
    return "\n".join(lines)


def _compact_line(value: str, max_chars: int) -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."

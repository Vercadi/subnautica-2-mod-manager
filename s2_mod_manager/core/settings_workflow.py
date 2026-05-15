from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .. import __app_name__, __version__
from ..models.app_paths import S2AppPaths
from ..models.preferences import UserPreferences
from ..models.settings_view import SettingsSafetyState, SettingsUpdateResult, SettingsView
from .archive_handler import archive_support_status
from .discovery import discover_all, validate_client_root
from .settings_store import load_preferences, save_preferences, save_settings


def build_settings_view(
    paths: S2AppPaths,
    *,
    data_dir: Path,
    library_dir: Path,
    backup_dir: Path,
    preferences: UserPreferences | None = None,
) -> SettingsView:
    preferences = preferences or UserPreferences()
    return SettingsView(
        app_name=__app_name__,
        app_version=__version__,
        install_path=paths.client_root,
        install_valid=validate_client_root(paths.client_root),
        steam_status=_steam_status(paths),
        build_status=paths.build_summary,
        inbox_path=paths.archive_inbox_dir,
        data_dir=data_dir,
        library_dir=library_dir,
        backup_dir=backup_dir,
        archive_support=archive_support_status(),
        auto_check_updates=preferences.auto_check_updates,
        show_update_popups=preferences.show_update_popups,
        show_info_popups=preferences.show_info_popups,
        show_success_popups=preferences.show_success_popups,
        show_warning_popups=preferences.show_warning_popups,
        ue4ss_write_enabled_txt=preferences.ue4ss_write_enabled_txt,
        ue4ss_write_mods_json=preferences.ue4ss_write_mods_json,
        ue4ss_write_mods_txt=preferences.ue4ss_write_mods_txt,
        safety=SettingsSafetyState(),
    )


def update_manual_install_path(
    settings_path: Path,
    current_paths: S2AppPaths,
    selected_root: Path,
    *,
    data_dir: Path,
    backup_dir: Path,
) -> SettingsUpdateResult:
    selected_root = Path(selected_root)
    if not validate_client_root(selected_root):
        return SettingsUpdateResult(
            ok=False,
            message=f"Invalid Subnautica 2 install path refused: {selected_root}",
            paths=current_paths,
        )
    updated, messages = discover_all(
        extra_steamapps_dirs=current_paths.steamapps_dirs,
        known_client_root=selected_root,
        known_archive_inbox_dir=current_paths.archive_inbox_dir,
    )
    _carry_runtime_dirs(updated, data_dir=data_dir, backup_dir=backup_dir)
    save_settings(settings_path, updated)
    return SettingsUpdateResult(
        ok=True,
        message=f"Saved Subnautica 2 install path: {selected_root}",
        paths=updated,
        discovery_messages=messages,
    )


def auto_detect_install_path(
    settings_path: Path,
    current_paths: S2AppPaths,
    *,
    data_dir: Path,
    backup_dir: Path,
) -> SettingsUpdateResult:
    updated, messages = discover_all(
        extra_steamapps_dirs=current_paths.steamapps_dirs,
        known_archive_inbox_dir=current_paths.archive_inbox_dir,
    )
    _carry_runtime_dirs(updated, data_dir=data_dir, backup_dir=backup_dir)
    save_settings(settings_path, updated)
    message = "Auto detect completed: " + ("S2 install validated." if updated.client_root else "S2 install not detected.")
    return SettingsUpdateResult(ok=bool(updated.client_root), message=message, paths=updated, discovery_messages=messages)


def update_inbox_path(
    settings_path: Path,
    current_paths: S2AppPaths,
    selected_inbox: Path,
    *,
    data_dir: Path,
    backup_dir: Path,
) -> SettingsUpdateResult:
    selected_inbox = Path(selected_inbox)
    if not selected_inbox.is_dir():
        return SettingsUpdateResult(
            ok=False,
            message=f"Invalid Mods inbox path refused: {selected_inbox}",
            paths=current_paths,
        )
    updated = _clone_paths(current_paths)
    updated.archive_inbox_dir = selected_inbox
    _carry_runtime_dirs(updated, data_dir=data_dir, backup_dir=backup_dir)
    save_settings(settings_path, updated)
    return SettingsUpdateResult(ok=True, message=f"Saved Mods inbox path: {selected_inbox}", paths=updated)


def reset_inbox_path(
    settings_path: Path,
    current_paths: S2AppPaths,
    default_inbox: Path,
    *,
    data_dir: Path,
    backup_dir: Path,
) -> SettingsUpdateResult:
    default_inbox.mkdir(parents=True, exist_ok=True)
    return update_inbox_path(
        settings_path,
        current_paths,
        default_inbox,
        data_dir=data_dir,
        backup_dir=backup_dir,
    )


def settings_refresh_summary(result: SettingsUpdateResult, inbox_scan_count: int) -> str:
    state = "saved" if result.ok else "refused"
    return f"Settings {state}: {result.message}; inbox scan now has {inbox_scan_count} source(s)."


def update_auto_check_updates(settings_path: Path, enabled: bool) -> UserPreferences:
    preferences = replace(load_preferences(settings_path), auto_check_updates=bool(enabled))
    save_preferences(settings_path, preferences)
    return preferences


def update_popup_preference(settings_path: Path, preference_name: str, enabled: bool) -> UserPreferences:
    if preference_name not in {
        "show_update_popups",
        "show_info_popups",
        "show_success_popups",
        "show_warning_popups",
    }:
        raise ValueError(f"Unknown popup preference: {preference_name}")
    preferences = replace(load_preferences(settings_path), **{preference_name: bool(enabled)})
    save_preferences(settings_path, preferences)
    return preferences


def update_popup_policy(settings_path: Path, policy_text: str) -> UserPreferences:
    preferences = load_preferences(settings_path).with_popup_policy(policy_text)
    save_preferences(settings_path, preferences)
    return preferences


def update_ue4ss_activation_preference(settings_path: Path, preference_name: str, enabled: bool) -> UserPreferences:
    if preference_name not in {
        "ue4ss_write_enabled_txt",
        "ue4ss_write_mods_json",
        "ue4ss_write_mods_txt",
    }:
        raise ValueError(f"Unknown UE4SS activation preference: {preference_name}")
    preferences = replace(load_preferences(settings_path), **{preference_name: bool(enabled)})
    save_preferences(settings_path, preferences)
    return preferences


def _steam_status(paths: S2AppPaths) -> str:
    manifest = paths.client_manifest
    if manifest is None:
        return "Steam manifest not found."
    bits = [f"appid {manifest.appid}"]
    if manifest.buildid:
        bits.append(f"build {manifest.buildid}")
    if manifest.manifest_path:
        bits.append(str(manifest.manifest_path))
    return " / ".join(bits)


def _carry_runtime_dirs(paths: S2AppPaths, *, data_dir: Path, backup_dir: Path) -> None:
    paths.data_dir = data_dir
    paths.backup_dir = backup_dir


def _clone_paths(paths: S2AppPaths) -> S2AppPaths:
    return S2AppPaths.from_dict(paths.to_dict())

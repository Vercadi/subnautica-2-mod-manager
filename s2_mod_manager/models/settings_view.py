from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .app_paths import S2AppPaths
from .preferences import POPUP_POLICY_LABELS, POPUP_POLICY_OPTIONS, popup_policy_from_flags


@dataclass(frozen=True)
class SettingsSafetyState:
    real_apply: str = "enabled for non-blocked Apply plans"
    destructive_recovery: str = "enabled only for manifest-tracked managed files"
    restore_vanilla: str = "preview-only; never deletes saves"
    quarantine: str = "preview-only; unknown files are reported, not moved"
    loose_overlays: str = "review-required; root DLL/config overlays are blocked"

    @property
    def text(self) -> str:
        return (
            f"Real apply: {self.real_apply}; recovery: {self.destructive_recovery}; "
            f"restore vanilla: {self.restore_vanilla}; quarantine: {self.quarantine}; "
            f"loose overlays: {self.loose_overlays}."
        )


@dataclass(frozen=True)
class SettingsView:
    app_name: str
    app_version: str
    install_path: Path | None
    install_valid: bool
    steam_status: str
    build_status: str
    inbox_path: Path | None
    data_dir: Path
    library_dir: Path
    backup_dir: Path
    install_variant: str = "Unknown/manual"
    project_root: Path | None = None
    binaries_dir: Path | None = None
    pak_dir: Path | None = None
    ue4ss_target_dir: Path | None = None
    gamepass_experimental: bool = False
    archive_support: dict[str, bool] = field(default_factory=dict)
    auto_check_updates: bool = True
    show_update_popups: bool = False
    show_info_popups: bool = False
    show_success_popups: bool = False
    show_warning_popups: bool = False
    ue4ss_write_enabled_txt: bool = True
    ue4ss_write_mods_json: bool = False
    ue4ss_write_mods_txt: bool = False
    ui_scale: str = "Default (placeholder)"
    safety: SettingsSafetyState = field(default_factory=SettingsSafetyState)

    @property
    def install_status_text(self) -> str:
        if self.install_valid and self.install_path:
            text = f"Valid S2 install: {self.install_path} ({self.install_variant})"
            if self.gamepass_experimental:
                text += " - experimental Game Pass support"
            return text
        return "Subnautica 2 install not configured or invalid."

    @property
    def install_layout_text(self) -> str:
        if not self.install_valid:
            return "Layout: not configured"
        bits = [f"Variant: {self.install_variant}"]
        if self.project_root:
            bits.append(f"Project: {self.project_root}")
        if self.binaries_dir:
            bits.append(f"Binaries: {self.binaries_dir}")
        if self.pak_dir:
            bits.append(f"Paks: {self.pak_dir}")
        if self.ue4ss_target_dir:
            bits.append(f"UE4SS Mods: {self.ue4ss_target_dir}")
        return "\n".join(bits)

    @property
    def about_text(self) -> str:
        return f"{self.app_name} {self.app_version} | Portable build metadata is generated during packaging."

    @property
    def archive_support_text(self) -> str:
        if not self.archive_support:
            return "Archive support unknown."
        return ", ".join(
            f"{suffix}: {'available' if available else 'missing'}"
            for suffix, available in sorted(self.archive_support.items())
        )

    @property
    def auto_update_text(self) -> str:
        return "enabled; checks GitHub Releases on startup" if self.auto_check_updates else "disabled; manual checks only"

    @property
    def popup_policy(self) -> str:
        return popup_policy_from_flags(
            update=self.show_update_popups,
            info=self.show_info_popups,
            success=self.show_success_popups,
            warning=self.show_warning_popups,
        )

    @property
    def popup_policy_label(self) -> str:
        return POPUP_POLICY_LABELS[self.popup_policy]

    @property
    def popup_policy_options(self) -> tuple[str, ...]:
        if self.popup_policy_label in POPUP_POLICY_OPTIONS:
            return POPUP_POLICY_OPTIONS
        return (*POPUP_POLICY_OPTIONS, self.popup_policy_label)

    @property
    def popup_text(self) -> str:
        return f"{self.popup_policy_label}; critical safety confirmations still show"

    @property
    def ue4ss_policy_text(self) -> str:
        return (
            f"enabled.txt={'on' if self.ue4ss_write_enabled_txt else 'off'}, "
            f"mods.json={'on' if self.ue4ss_write_mods_json else 'off'}, "
            f"mods.txt={'on' if self.ue4ss_write_mods_txt else 'off'}; "
            "writes stay guarded by Apply"
        )

    @property
    def summary_text(self) -> str:
        return (
            f"Settings: install={'valid' if self.install_valid else 'invalid'}, "
            f"variant={self.install_variant}, "
            f"inbox={self.inbox_path or 'not set'}, "
            f"archives=({self.archive_support_text}), startup_updates={'on' if self.auto_check_updates else 'off'}, "
            f"popups=({self.popup_text}), ue4ss=({self.ue4ss_policy_text})"
        )


@dataclass(frozen=True)
class SettingsUpdateResult:
    ok: bool
    message: str
    paths: S2AppPaths
    discovery_messages: list[str] = field(default_factory=list)

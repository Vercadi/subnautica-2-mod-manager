from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiagnosticsReport:
    app_version: str
    install_detected: bool
    install_root: str
    build_summary: str
    steam_manifest_status: str
    install_variant: str = "Unknown/manual"
    project_root: str = ""
    binaries_dir: str = ""
    pak_dir: str = ""
    ue4ss_runtime_dir: str = ""
    ue4ss_target_dir: str = ""
    experimental_warning: str = ""
    archive_support: dict[str, bool] = field(default_factory=dict)
    library_source_count: int = 0
    library_component_count: int = 0
    profile_count: int = 0
    active_profile_name: str = "Vanilla"
    active_loadout_count: int = 0
    deployment_summary: str = ""
    recovery_summary: str = ""
    manifest_install_count: int = 0
    backup_count: int = 0
    ue4ss_runtime_state: str = "unknown"
    safety_summary: str = "managed apply enabled through Apply; installed-file recovery uses manifest-tracked files only; loose overlays review-required"
    app_data_dir: str = ""
    log_excerpt: list[str] = field(default_factory=list)

    @property
    def summary_text(self) -> str:
        archive_bits = ", ".join(
            f"{suffix}:{'ok' if supported else 'missing'}"
            for suffix, supported in sorted(self.archive_support.items())
        )
        return (
            f"Diagnostics: install={'detected' if self.install_detected else 'missing'}, "
            f"variant={self.install_variant}, build={self.build_summary}, archives=[{archive_bits}], "
            f"library={self.library_source_count}/{self.library_component_count}, "
            f"profiles={self.profile_count}, manifest={self.manifest_install_count}, "
            f"backups={self.backup_count}, ue4ss={self.ue4ss_runtime_state}, safety=guarded."
        )

    def support_report_text(self) -> str:
        lines = [
            "Subnautica 2 Mod Manager Support Report",
            f"App Version: {self.app_version}",
            f"Install Detected: {self.install_detected}",
            f"Install Root: {self.install_root}",
            f"Install Variant: {self.install_variant}",
            f"Project Root: {self.project_root}",
            f"Binaries Folder: {self.binaries_dir}",
            f"Pak Folder: {self.pak_dir}",
            f"UE4SS Runtime Root: {self.ue4ss_runtime_dir}",
            f"UE4SS Target Folder: {self.ue4ss_target_dir}",
            f"Experimental Warning: {self.experimental_warning or 'none'}",
            f"Build: {self.build_summary}",
            f"Steam Manifest: {self.steam_manifest_status}",
            "Archive Support:",
        ]
        lines.extend(
            f"- {suffix}: {'available' if supported else 'unavailable'}"
            for suffix, supported in sorted(self.archive_support.items())
        )
        lines.extend(
            [
                f"Library Sources: {self.library_source_count}",
                f"Library Components: {self.library_component_count}",
                f"Profiles: {self.profile_count}",
                f"Active Profile: {self.active_profile_name}",
                f"Active Loadout Entries: {self.active_loadout_count}",
                f"Deployment Preview: {self.deployment_summary}",
                f"Recovery: {self.recovery_summary}",
                f"Manifest Installs: {self.manifest_install_count}",
                f"Backups: {self.backup_count}",
                f"UE4SS Runtime: {self.ue4ss_runtime_state}",
                f"Safety: {self.safety_summary}",
                f"App Data: {self.app_data_dir}",
                "Save Paths: intentionally omitted",
                "Support Workflow: copy this report, the mod archive name, the profile name, the action you clicked, and the visible error text. Do not paste save folders or personal account paths.",
                "Last Log Excerpt:",
            ]
        )
        lines.extend(f"- {line}" for line in self.log_excerpt)
        return "\n".join(lines)

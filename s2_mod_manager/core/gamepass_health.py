from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..models.app_paths import S2AppPaths


@dataclass(frozen=True)
class GamePassHealth:
    variant: str
    experimental: bool
    project_root: str
    binaries_dir: str
    pak_dir: str
    runtime_root: str
    ue4ss_mods: str
    present_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def runtime_present(self) -> bool:
        return any(name.casefold() == "ue4ss.dll" for name in self.present_files)

    @property
    def proxy_present(self) -> bool:
        return any(name.casefold() in {"dwmapi.dll", "xinput1_3.dll", "version.dll"} for name in self.present_files)

    @property
    def summary_text(self) -> str:
        state = "runtime detected" if self.runtime_present else "runtime not detected"
        if self.experimental:
            state += ", Game Pass experimental"
        return f"UE4SS health: {self.variant}, {state}, target={self.ue4ss_mods or 'not configured'}"

    def report_text(self) -> str:
        lines = [
            f"Variant: {self.variant}",
            f"Experimental: {self.experimental}",
            f"Project Root: {self.project_root or 'not configured'}",
            f"Binaries Folder: {self.binaries_dir or 'not configured'}",
            f"Pak Folder: {self.pak_dir or 'not configured'}",
            f"UE4SS Runtime Root: {self.runtime_root or 'not configured'}",
            f"UE4SS Mods Folder: {self.ue4ss_mods or 'not configured'}",
            "Runtime Files: " + (", ".join(self.present_files) if self.present_files else "none detected"),
        ]
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n".join(lines)


def build_gamepass_health(paths: S2AppPaths) -> GamePassHealth:
    marker_roots = [root for root in (paths.ue4ss_runtime_root, paths.binaries_dir, paths.ue4ss_root) if root is not None]
    present: list[str] = []
    for root in marker_roots:
        for name in ("UE4SS.dll", "dwmapi.dll", "xinput1_3.dll", "version.dll", "UE4SS-settings.ini", "UE4SS.log"):
            if (root / name).exists() and name not in present:
                present.append(name)
    warnings: list[str] = []
    if paths.is_gamepass_experimental:
        warnings.append(
            "Game Pass WinGDK support is experimental. Standard Lua mods target WinGDK\\ue4ss\\Mods; runtime/base packages may use a Game Pass-specific Content-root layout."
        )
        content_mods = paths.gamepass_content_root / "ue4ss" / "Mods" if paths.gamepass_content_root else None
        if content_mods and content_mods.exists() and paths.ue4ss_mods and content_mods != paths.ue4ss_mods:
            warnings.append(f"UE4SS mods also found at Content-root path: {content_mods}")
    if not any(name.casefold() == "ue4ss.dll" for name in present):
        warnings.append("UE4SS.dll was not detected in the runtime target.")
    if present and not any(name.casefold() in {"dwmapi.dll", "xinput1_3.dll", "version.dll"} for name in present):
        warnings.append("UE4SS runtime was detected without a known proxy DLL.")
    return GamePassHealth(
        variant=paths.install_variant_label,
        experimental=paths.is_gamepass_experimental,
        project_root=_display(paths.project_root),
        binaries_dir=_display(paths.binaries_dir),
        pak_dir=_display(paths.content_paks),
        runtime_root=_display(paths.ue4ss_runtime_root),
        ue4ss_mods=_display(paths.ue4ss_mods),
        present_files=sorted(present),
        warnings=warnings,
    )


def _display(path: Path | None) -> str:
    return str(path) if path else ""

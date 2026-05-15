from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


S2_APP_ID = "1962700"
INSTALL_VARIANT_UNKNOWN = "unknown"
INSTALL_VARIANT_STEAM_WIN64 = "steam_win64"
INSTALL_VARIANT_MANUAL_WIN64 = "manual_win64"
INSTALL_VARIANT_GAMEPASS_WINGDK = "gamepass_wingdk"

INSTALL_VARIANT_LABELS = {
    INSTALL_VARIANT_STEAM_WIN64: "Steam Win64",
    INSTALL_VARIANT_MANUAL_WIN64: "Manual/Epic Win64",
    INSTALL_VARIANT_GAMEPASS_WINGDK: "Game Pass WinGDK (experimental)",
    INSTALL_VARIANT_UNKNOWN: "Unknown/manual",
}


def _path_to_str(path: Path | None) -> str | None:
    return str(path) if path else None


def path_from_setting(value: str | None) -> Path | None:
    if isinstance(value, str) and value.strip().casefold() in {"", "none", "null"}:
        return None
    return Path(value) if value else None


@dataclass
class SteamAppManifest:
    appid: str
    name: str = ""
    installdir: str = ""
    buildid: str = ""
    last_updated: str = ""
    size_on_disk: str = ""
    manifest_path: Path | None = None
    library_root: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "appid": self.appid,
            "name": self.name,
            "installdir": self.installdir,
            "buildid": self.buildid,
            "last_updated": self.last_updated,
            "size_on_disk": self.size_on_disk,
            "manifest_path": _path_to_str(self.manifest_path),
            "library_root": _path_to_str(self.library_root),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SteamAppManifest | None":
        if not isinstance(data, dict) or not data.get("appid"):
            return None
        return cls(
            appid=str(data.get("appid") or ""),
            name=str(data.get("name") or ""),
            installdir=str(data.get("installdir") or ""),
            buildid=str(data.get("buildid") or ""),
            last_updated=str(data.get("last_updated") or ""),
            size_on_disk=str(data.get("size_on_disk") or ""),
            manifest_path=path_from_setting(data.get("manifest_path")),
            library_root=path_from_setting(data.get("library_root")),
        )


@dataclass
class S2GameVersion:
    changelist: str = ""
    build_number: str = ""
    build_label: str = ""
    timestamp: str = ""
    branch: str = ""
    raw_version_txt: str = ""

    @property
    def summary(self) -> str:
        parts: list[str] = []
        if self.build_number:
            parts.append(f"Build {self.build_number}")
        if self.changelist:
            parts.append(f"CL {self.changelist}")
        if self.timestamp:
            parts.append(self.timestamp[:10])
        return " / ".join(parts) if parts else "Version unknown"

    def to_dict(self) -> dict[str, str]:
        return {
            "changelist": self.changelist,
            "build_number": self.build_number,
            "build_label": self.build_label,
            "timestamp": self.timestamp,
            "branch": self.branch,
            "raw_version_txt": self.raw_version_txt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "S2GameVersion":
        if not isinstance(data, dict):
            return cls()
        return cls(
            changelist=str(data.get("changelist") or ""),
            build_number=str(data.get("build_number") or ""),
            build_label=str(data.get("build_label") or ""),
            timestamp=str(data.get("timestamp") or ""),
            branch=str(data.get("branch") or ""),
            raw_version_txt=str(data.get("raw_version_txt") or ""),
        )


@dataclass
class S2InstallLayout:
    variant: str = INSTALL_VARIANT_UNKNOWN
    client_root: Path | None = None
    project_root: Path | None = None
    binaries_dir: Path | None = None
    content_paks: Path | None = None
    shipping_exe: Path | None = None
    root_exe: Path | None = None
    selected_path: Path | None = None
    source: str = ""

    @property
    def variant_label(self) -> str:
        return INSTALL_VARIANT_LABELS.get(self.variant, INSTALL_VARIANT_LABELS[INSTALL_VARIANT_UNKNOWN])

    @property
    def is_gamepass_experimental(self) -> bool:
        return self.variant == INSTALL_VARIANT_GAMEPASS_WINGDK

    @property
    def binaries_name(self) -> str:
        return self.binaries_dir.name if self.binaries_dir else ""

    @property
    def gamepass_content_root(self) -> Path | None:
        if not self.is_gamepass_experimental:
            return None
        if self.project_root and self.project_root.parent.name.casefold() == "content":
            return self.project_root.parent
        if self.client_root:
            content_root = self.client_root / "Content"
            if content_root.is_dir() or (content_root / "Subnautica2").exists():
                return content_root
        return None

    @property
    def ue4ss_runtime_root(self) -> Path | None:
        if self.is_gamepass_experimental and self.gamepass_content_root:
            return self.gamepass_content_root
        return self.binaries_dir

    @property
    def ue4ss_root(self) -> Path | None:
        if self.is_gamepass_experimental and self.binaries_dir:
            return self.binaries_dir / "ue4ss"
        return self.binaries_dir / "ue4ss" if self.binaries_dir else None

    @property
    def ue4ss_mods(self) -> Path | None:
        return self.ue4ss_root / "Mods" if self.ue4ss_root else None

    @property
    def is_valid_now(self) -> bool:
        return bool(
            self.client_root
            and self.project_root
            and self.binaries_dir
            and self.content_paks
            and self.shipping_exe
            and self.binaries_dir.is_dir()
            and self.content_paks.is_dir()
            and self.shipping_exe.is_file()
            and (self.variant != INSTALL_VARIANT_STEAM_WIN64 or (self.root_exe is not None and self.root_exe.is_file()))
        )

    @property
    def summary(self) -> str:
        if not self.client_root:
            return "Layout not configured"
        bits = [self.variant_label]
        if self.binaries_name:
            bits.append(f"binaries={self.binaries_name}")
        return " / ".join(bits)

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "client_root": _path_to_str(self.client_root),
            "project_root": _path_to_str(self.project_root),
            "binaries_dir": _path_to_str(self.binaries_dir),
            "content_paks": _path_to_str(self.content_paks),
            "shipping_exe": _path_to_str(self.shipping_exe),
            "root_exe": _path_to_str(self.root_exe),
            "selected_path": _path_to_str(self.selected_path),
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "S2InstallLayout":
        if not isinstance(data, dict):
            return cls()
        return cls(
            variant=str(data.get("variant") or INSTALL_VARIANT_UNKNOWN),
            client_root=path_from_setting(data.get("client_root")),
            project_root=path_from_setting(data.get("project_root")),
            binaries_dir=path_from_setting(data.get("binaries_dir")),
            content_paks=path_from_setting(data.get("content_paks")),
            shipping_exe=path_from_setting(data.get("shipping_exe")),
            root_exe=path_from_setting(data.get("root_exe")),
            selected_path=path_from_setting(data.get("selected_path")),
            source=str(data.get("source") or ""),
        )


@dataclass
class S2AppPaths:
    client_root: Path | None = None
    steamapps_dirs: list[Path] = field(default_factory=list)
    client_manifest: SteamAppManifest | None = None
    game_version: S2GameVersion = field(default_factory=S2GameVersion)
    data_dir: Path | None = None
    backup_dir: Path | None = None
    archive_inbox_dir: Path | None = None
    install_layout: S2InstallLayout = field(default_factory=S2InstallLayout)

    @property
    def layout(self) -> S2InstallLayout:
        if self.install_layout.client_root:
            return self.install_layout
        return self._default_win64_layout()

    @property
    def client_exe(self) -> Path | None:
        return self.layout.root_exe

    @property
    def shipping_exe(self) -> Path | None:
        return self.layout.shipping_exe

    @property
    def project_root(self) -> Path | None:
        return self.layout.project_root

    @property
    def binaries_dir(self) -> Path | None:
        return self.layout.binaries_dir

    @property
    def content_paks(self) -> Path | None:
        return self.layout.content_paks

    @property
    def gamepass_content_root(self) -> Path | None:
        return self.layout.gamepass_content_root

    @property
    def mods_paks(self) -> Path | None:
        return self.content_paks / "~mods" if self.content_paks else None

    @property
    def logic_mods(self) -> Path | None:
        return self.content_paks / "LogicMods" if self.content_paks else None

    @property
    def win64(self) -> Path | None:
        return self.binaries_dir

    @property
    def ue4ss_runtime_root(self) -> Path | None:
        return self.layout.ue4ss_runtime_root

    @property
    def ue4ss_root(self) -> Path | None:
        return self.layout.ue4ss_root

    @property
    def ue4ss_mods(self) -> Path | None:
        return self.layout.ue4ss_mods

    @property
    def save_games(self) -> Path | None:
        return self.project_root / "Saved" / "SaveGames" if self.project_root else None

    @property
    def version_json(self) -> Path | None:
        return self.client_root / "version.json" if self.client_root else None

    @property
    def version_txt(self) -> Path | None:
        return self.client_root / "version.txt" if self.client_root else None

    @property
    def is_configured(self) -> bool:
        return self.client_root is not None

    @property
    def has_valid_layout(self) -> bool:
        return self.layout.is_valid_now

    @property
    def install_variant(self) -> str:
        return self.layout.variant

    @property
    def install_variant_label(self) -> str:
        return self.layout.variant_label

    @property
    def is_gamepass_experimental(self) -> bool:
        return self.layout.is_gamepass_experimental

    @property
    def layout_summary(self) -> str:
        return self.layout.summary

    @property
    def display_root(self) -> str:
        return str(self.client_root) if self.client_root else "Subnautica 2 install not detected"

    @property
    def build_summary(self) -> str:
        game = self.game_version.summary
        steam = self.client_manifest.buildid if self.client_manifest else ""
        if steam and game != "Version unknown":
            return f"{game} / Steam {steam} / {self.install_variant_label}"
        if steam:
            return f"Steam Build {steam} / {self.install_variant_label}"
        if self.client_root:
            return f"{game} / {self.install_variant_label}"
        return game

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_root": _path_to_str(self.client_root),
            "steamapps_dirs": [str(path) for path in self.steamapps_dirs],
            "client_manifest": self.client_manifest.to_dict() if self.client_manifest else None,
            "game_version": self.game_version.to_dict(),
            "data_dir": _path_to_str(self.data_dir),
            "backup_dir": _path_to_str(self.backup_dir),
            "archive_inbox_dir": _path_to_str(self.archive_inbox_dir),
            "install_layout": self.layout.to_dict() if self.client_root else self.install_layout.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "S2AppPaths":
        if not isinstance(data, dict):
            return cls()
        return cls(
            client_root=path_from_setting(data.get("client_root")),
            steamapps_dirs=[Path(value) for value in data.get("steamapps_dirs", []) if value],
            client_manifest=SteamAppManifest.from_dict(data.get("client_manifest")),
            game_version=S2GameVersion.from_dict(data.get("game_version")),
            data_dir=path_from_setting(data.get("data_dir")),
            backup_dir=path_from_setting(data.get("backup_dir")),
            archive_inbox_dir=path_from_setting(data.get("archive_inbox_dir")),
            install_layout=S2InstallLayout.from_dict(data.get("install_layout")),
        )

    def _default_win64_layout(self) -> S2InstallLayout:
        if not self.client_root:
            return S2InstallLayout()
        project_root = self.client_root / "Subnautica2"
        binaries_dir = project_root / "Binaries" / "Win64"
        variant = INSTALL_VARIANT_STEAM_WIN64 if self.client_manifest else INSTALL_VARIANT_MANUAL_WIN64
        return S2InstallLayout(
            variant=variant,
            client_root=self.client_root,
            project_root=project_root,
            binaries_dir=binaries_dir,
            content_paks=project_root / "Content" / "Paks",
            shipping_exe=binaries_dir / "Subnautica2-Win64-Shipping.exe",
            root_exe=self.client_root / "Subnautica2.exe",
            selected_path=self.client_root,
            source="steam" if self.client_manifest else "manual",
        )

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


S2_APP_ID = "1962700"


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
class S2AppPaths:
    client_root: Path | None = None
    steamapps_dirs: list[Path] = field(default_factory=list)
    client_manifest: SteamAppManifest | None = None
    game_version: S2GameVersion = field(default_factory=S2GameVersion)
    data_dir: Path | None = None
    backup_dir: Path | None = None
    archive_inbox_dir: Path | None = None

    @property
    def client_exe(self) -> Path | None:
        return self.client_root / "Subnautica2.exe" if self.client_root else None

    @property
    def shipping_exe(self) -> Path | None:
        if not self.client_root:
            return None
        return self.client_root / "Subnautica2" / "Binaries" / "Win64" / "Subnautica2-Win64-Shipping.exe"

    @property
    def content_paks(self) -> Path | None:
        return self.client_root / "Subnautica2" / "Content" / "Paks" if self.client_root else None

    @property
    def mods_paks(self) -> Path | None:
        return self.content_paks / "~mods" if self.content_paks else None

    @property
    def win64(self) -> Path | None:
        return self.client_root / "Subnautica2" / "Binaries" / "Win64" if self.client_root else None

    @property
    def ue4ss_root(self) -> Path | None:
        return self.win64 / "ue4ss" if self.win64 else None

    @property
    def ue4ss_mods(self) -> Path | None:
        return self.ue4ss_root / "Mods" if self.ue4ss_root else None

    @property
    def save_games(self) -> Path | None:
        return self.client_root / "Subnautica2" / "Saved" / "SaveGames" if self.client_root else None

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
    def display_root(self) -> str:
        return str(self.client_root) if self.client_root else "Subnautica 2 install not detected"

    @property
    def build_summary(self) -> str:
        game = self.game_version.summary
        steam = self.client_manifest.buildid if self.client_manifest else ""
        if steam and game != "Version unknown":
            return f"{game} / Steam {steam}"
        if steam:
            return f"Steam Build {steam}"
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
        )

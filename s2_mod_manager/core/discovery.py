from __future__ import annotations

import ctypes
import os
import string
from pathlib import Path
from typing import Iterable

from ..models.app_paths import S2_APP_ID, S2AppPaths, SteamAppManifest
from ..utils.filesystem import safe_is_dir, safe_is_file
from .steam_manifest import parse_acf_text, read_app_manifest
from .version_info import read_game_version


CLIENT_FOLDER_NAMES = ("Subnautica2", "Subnautica 2")


def discover_all(
    *,
    extra_steamapps_dirs: Iterable[Path] | None = None,
    known_client_root: Path | None = None,
    known_archive_inbox_dir: Path | None = None,
) -> tuple[S2AppPaths, list[str]]:
    messages: list[str] = []
    steamapps_dirs = discover_steamapps_dirs(extra_steamapps_dirs=extra_steamapps_dirs)
    if steamapps_dirs:
        messages.append(f"Steam libraries scanned: {len(steamapps_dirs)}")
    else:
        messages.append("No Steam libraries found during discovery.")

    manifest = find_app_manifest(S2_APP_ID, steamapps_dirs)
    if manifest:
        messages.append(f"Steam manifest found: {manifest.manifest_path}")

    client_root = _valid_or_none(known_client_root)
    if client_root:
        messages.append(f"Using saved S2 path: {client_root}")
    else:
        client_root = root_from_manifest(manifest)
        if client_root:
            messages.append(f"Detected S2 path from Steam manifest: {client_root}")

    if client_root is None:
        client_root = find_root_by_folder_names(steamapps_dirs, CLIENT_FOLDER_NAMES)
        if client_root:
            messages.append(f"Detected S2 path by folder scan: {client_root}")

    if client_root is None:
        messages.append("Subnautica 2 install not detected.")
    else:
        messages.append("Subnautica 2 install validated.")

    paths = S2AppPaths(
        client_root=client_root,
        steamapps_dirs=steamapps_dirs,
        client_manifest=manifest,
        game_version=read_game_version(client_root),
        archive_inbox_dir=known_archive_inbox_dir,
    )
    return paths, messages


def discover_steamapps_dirs(*, extra_steamapps_dirs: Iterable[Path] | None = None) -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        normalized = str(path)
        if normalized.casefold() not in seen:
            seen.add(normalized.casefold())
            candidates.append(path)

    for path in extra_steamapps_dirs or []:
        add(Path(path))

    for env_key in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        base = os.environ.get(env_key)
        if base:
            add(Path(base) / "Steam" / "steamapps")

    for drive_root in available_drive_roots():
        root = Path(drive_root)
        add(root / "SteamLibrary" / "steamapps")
        add(root / "Steam" / "steamapps")

    for path in list(candidates):
        add_libraryfolders(path, add)

    return [path for path in candidates if safe_is_dir(path)]


def add_libraryfolders(steamapps_dir: Path, add) -> None:
    library_file = steamapps_dir / "libraryfolders.vdf"
    if not library_file.is_file():
        return
    try:
        data = parse_acf_text(library_file.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return
    for value in data.values():
        if isinstance(value, dict) and value.get("path"):
            add(Path(str(value["path"])) / "steamapps")


def available_drive_roots() -> list[str]:
    if os.name != "nt":
        return ["/"]
    try:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    except Exception:
        return [f"{letter}:\\" for letter in "CDEFGH"]

    roots: list[str] = []
    for index, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << index):
            roots.append(f"{letter}:\\")
    return roots or ["C:\\"]


def find_app_manifest(appid: str, steamapps_dirs: Iterable[Path]) -> SteamAppManifest | None:
    filename = f"appmanifest_{appid}.acf"
    for steamapps_dir in steamapps_dirs:
        candidate = steamapps_dir / filename
        if candidate.is_file():
            manifest = read_app_manifest(candidate, library_root=steamapps_dir.parent)
            if manifest and manifest.appid == appid:
                return manifest
    return None


def root_from_manifest(manifest: SteamAppManifest | None) -> Path | None:
    if not manifest or not manifest.library_root or not manifest.installdir:
        return None
    candidate = manifest.library_root / "steamapps" / "common" / manifest.installdir
    return candidate if validate_client_root(candidate) else None


def find_root_by_folder_names(steamapps_dirs: Iterable[Path], names: Iterable[str]) -> Path | None:
    for steamapps_dir in steamapps_dirs:
        common = steamapps_dir / "common"
        for name in names:
            candidate = common / name
            if validate_client_root(candidate):
                return candidate
    return None


def validate_client_root(path: Path | None) -> bool:
    if not safe_is_dir(path):
        return False
    root = Path(path)
    return (
        safe_is_file(root / "Subnautica2.exe")
        and safe_is_file(root / "Subnautica2" / "Binaries" / "Win64" / "Subnautica2-Win64-Shipping.exe")
        and safe_is_dir(root / "Subnautica2" / "Content" / "Paks")
    )


def _valid_or_none(path: Path | None) -> Path | None:
    return Path(path) if path and validate_client_root(path) else None

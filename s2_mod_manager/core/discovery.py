from __future__ import annotations

import ctypes
import os
import string
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass

from ..models.app_paths import (
    INSTALL_VARIANT_GAMEPASS_WINGDK,
    INSTALL_VARIANT_MANUAL_WIN64,
    INSTALL_VARIANT_STEAM_WIN64,
    S2_APP_ID,
    S2AppPaths,
    S2InstallLayout,
    SteamAppManifest,
)
from ..utils.filesystem import safe_is_dir, safe_is_file
from .steam_manifest import parse_acf_text, read_app_manifest
from .version_info import read_game_version


CLIENT_FOLDER_NAMES = ("Subnautica2", "Subnautica 2")


@dataclass(frozen=True)
class InstallValidationResult:
    ok: bool
    layout: S2InstallLayout | None = None
    missing: list[str] | None = None
    message: str = ""

    @property
    def missing_text(self) -> str:
        return "; ".join(self.missing or [])


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
    manifest_layout = layout_from_manifest(manifest)

    layout = normalize_install_path(known_client_root, source="manual")
    if layout and manifest_layout and _same_path(layout.client_root, manifest_layout.client_root):
        layout = manifest_layout
    if layout:
        messages.append(f"Using saved S2 path: {layout.client_root} ({layout.variant_label})")
    else:
        layout = manifest_layout
        if layout:
            messages.append(f"Detected S2 path from Steam manifest: {layout.client_root}")

    if layout is None:
        layout = find_layout_by_folder_names(steamapps_dirs, CLIENT_FOLDER_NAMES)
        if layout:
            messages.append(f"Detected S2 path by folder scan: {layout.client_root}")

    if layout is None:
        messages.append("Subnautica 2 install not detected.")
    else:
        messages.append(f"Subnautica 2 install validated: {layout.variant_label}.")
        if layout.is_gamepass_experimental:
            messages.append("Game Pass support is experimental; UE4SS mods target WinGDK\\ue4ss\\Mods and apply previews will call this out.")

    paths = S2AppPaths(
        client_root=layout.client_root if layout else None,
        steamapps_dirs=steamapps_dirs,
        client_manifest=manifest if layout and layout.variant == INSTALL_VARIANT_STEAM_WIN64 else None,
        game_version=read_game_version(layout.client_root if layout else None),
        archive_inbox_dir=known_archive_inbox_dir,
        install_layout=layout or S2InstallLayout(),
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
    layout = layout_from_manifest(manifest)
    return layout.client_root if layout else None


def layout_from_manifest(manifest: SteamAppManifest | None) -> S2InstallLayout | None:
    if not manifest or not manifest.library_root or not manifest.installdir:
        return None
    candidate = manifest.library_root / "steamapps" / "common" / manifest.installdir
    return normalize_install_path(candidate, manifest=manifest, source="steam")


def find_root_by_folder_names(steamapps_dirs: Iterable[Path], names: Iterable[str]) -> Path | None:
    layout = find_layout_by_folder_names(steamapps_dirs, names)
    return layout.client_root if layout else None


def find_layout_by_folder_names(steamapps_dirs: Iterable[Path], names: Iterable[str]) -> S2InstallLayout | None:
    for steamapps_dir in steamapps_dirs:
        common = steamapps_dir / "common"
        for name in names:
            candidate = common / name
            layout = normalize_install_path(candidate, source="steam-scan")
            if layout:
                return layout
    return None


def validate_client_root(path: Path | None) -> bool:
    return validate_install_path(path).ok


def validate_install_path(path: Path | None) -> InstallValidationResult:
    if not safe_is_dir(path):
        return InstallValidationResult(
            ok=False,
            missing=["selected path is not a folder"],
            message=(
                f"Invalid Subnautica 2 install path refused: {path}. "
                "Selected path is not a folder. Select the outer install root, inner Subnautica2 folder, "
                "Subnautica2/Binaries/Win64, Content, Content/Subnautica2, or Content/Subnautica2/Binaries/WinGDK."
            ),
        )
    layout = normalize_install_path(path)
    if layout:
        return InstallValidationResult(ok=True, layout=layout, missing=[], message=f"Valid {layout.variant_label} install.")

    missing = _missing_requirements_for(path)
    missing_text = "; ".join(missing[:8])
    return InstallValidationResult(
        ok=False,
        missing=missing,
        message=(
            f"Invalid Subnautica 2 install path refused: {path}. "
            f"Missing expected layout item(s): {missing_text}. "
            "Try selecting the outer install root, inner Subnautica2 folder, Subnautica2/Binaries/Win64, "
            "Content, Content/Subnautica2, or Content/Subnautica2/Binaries/WinGDK."
        ),
    )


def normalize_install_path(
    path: Path | None,
    *,
    manifest: SteamAppManifest | None = None,
    source: str = "manual",
) -> S2InstallLayout | None:
    if not safe_is_dir(path):
        return None
    selected = Path(path)
    for client_root, project_root, binaries_dir, variant in _candidate_layout_roots(selected):
        layout = _build_layout(
            selected=selected,
            client_root=client_root,
            project_root=project_root,
            binaries_dir=binaries_dir,
            variant=INSTALL_VARIANT_STEAM_WIN64 if manifest and variant == INSTALL_VARIANT_MANUAL_WIN64 else variant,
            source=source,
        )
        if layout and layout.is_valid_now:
            return layout
    return None


def _candidate_layout_roots(selected: Path) -> list[tuple[Path, Path, Path, str]]:
    output: list[tuple[Path, Path, Path, str]] = []
    seen: set[tuple[str, str, str, str]] = set()

    def add(client_root: Path, project_root: Path, binaries_dir: Path, variant: str) -> None:
        key = (
            str(client_root.resolve() if client_root.exists() else client_root).casefold(),
            str(project_root.resolve() if project_root.exists() else project_root).casefold(),
            str(binaries_dir.resolve() if binaries_dir.exists() else binaries_dir).casefold(),
            variant,
        )
        if key in seen:
            return
        seen.add(key)
        output.append((client_root, project_root, binaries_dir, variant))

    lowered_name = selected.name.casefold()
    parent_name = selected.parent.name.casefold()
    if lowered_name in {"win64", "wingdk"} and parent_name == "binaries":
        project_root = selected.parent.parent
        if lowered_name == "wingdk":
            client_root = project_root.parent.parent if project_root.parent.name.casefold() == "content" else project_root.parent
            add(client_root, project_root, selected, INSTALL_VARIANT_GAMEPASS_WINGDK)
        else:
            add(project_root.parent, project_root, selected, INSTALL_VARIANT_MANUAL_WIN64)

    if lowered_name == "subnautica2":
        if selected.parent.name.casefold() == "content":
            add(selected.parent.parent, selected, selected / "Binaries" / "WinGDK", INSTALL_VARIANT_GAMEPASS_WINGDK)
        add(selected.parent, selected, selected / "Binaries" / "Win64", INSTALL_VARIANT_MANUAL_WIN64)
        add(selected, selected, selected / "Binaries" / "Win64", INSTALL_VARIANT_MANUAL_WIN64)

    # Outer install roots and nearby ancestors. This lets users pick the wrapper folder,
    # the inner project folder, or common binaries folders without needing to know the exact root.
    anchors = [selected, *list(selected.parents)[:4]]
    for anchor in anchors:
        add(anchor, anchor / "Subnautica2", anchor / "Subnautica2" / "Binaries" / "Win64", INSTALL_VARIANT_MANUAL_WIN64)
        gamepass_project = anchor / "Content" / "Subnautica2"
        add(anchor, gamepass_project, gamepass_project / "Binaries" / "WinGDK", INSTALL_VARIANT_GAMEPASS_WINGDK)
    return output


def _build_layout(
    *,
    selected: Path,
    client_root: Path,
    project_root: Path,
    binaries_dir: Path,
    variant: str,
    source: str,
) -> S2InstallLayout | None:
    content_paks = project_root / "Content" / "Paks"
    shipping_exe = _find_shipping_exe(binaries_dir, variant)
    return S2InstallLayout(
        variant=variant,
        client_root=client_root,
        project_root=project_root,
        binaries_dir=binaries_dir,
        content_paks=content_paks,
        shipping_exe=shipping_exe,
        root_exe=client_root / "Subnautica2.exe",
        selected_path=selected,
        source=source,
    )


def _find_shipping_exe(binaries_dir: Path, variant: str) -> Path:
    if variant == INSTALL_VARIANT_GAMEPASS_WINGDK:
        preferred = binaries_dir / "Subnautica2-WinGDK-Shipping.exe"
    else:
        preferred = binaries_dir / "Subnautica2-Win64-Shipping.exe"
    if preferred.is_file():
        return preferred
    if binaries_dir.is_dir():
        shipping = sorted(binaries_dir.glob("*Shipping*.exe"), key=lambda item: item.name.casefold())
        if shipping:
            return shipping[0]
        if variant == INSTALL_VARIANT_GAMEPASS_WINGDK:
            exes = sorted(binaries_dir.glob("*.exe"), key=lambda item: item.name.casefold())
            if exes:
                return exes[0]
    return preferred


def _missing_requirements_for(path: Path) -> list[str]:
    selected = Path(path)
    missing: list[str] = []
    for _client_root, _project_root, binaries_dir, variant in _candidate_layout_roots(selected)[:6]:
        content_paks = _project_root / "Content" / "Paks"
        shipping_exe = _find_shipping_exe(binaries_dir, variant)
        label = "Game Pass WinGDK" if variant == INSTALL_VARIANT_GAMEPASS_WINGDK else "Win64"
        if not safe_is_dir(binaries_dir):
            missing.append(f"{label} binaries folder: {binaries_dir}")
        if not safe_is_file(shipping_exe):
            missing.append(f"{label} shipping exe: {shipping_exe}")
        if not safe_is_dir(content_paks):
            missing.append(f"{label} pak folder: {content_paks}")
    return list(dict.fromkeys(missing)) or ["recognized Subnautica 2 Win64 or WinGDK layout"]


def _same_path(left: Path | None, right: Path | None) -> bool:
    if left is None or right is None:
        return False
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return str(left).casefold() == str(right).casefold()

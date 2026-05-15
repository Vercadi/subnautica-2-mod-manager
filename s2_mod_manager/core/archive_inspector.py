from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath

from ..models.archive_info import (
    COMPONENT_LOOSE_OVERLAY,
    COMPONENT_MIXED,
    COMPONENT_PAK_BUNDLE,
    COMPONENT_UE4SS_MOD,
    COMPONENT_UE4SS_RUNTIME,
    COMPONENT_UNKNOWN,
    INSTALL_KIND_LOOSE_OVERLAY,
    INSTALL_KIND_STANDARD,
    INSTALL_KIND_UE4SS_MOD,
    INSTALL_KIND_UE4SS_RUNTIME,
    SOURCE_ARCHIVE,
    SOURCE_FOLDER,
    SOURCE_LOCAL_FILES,
    SUPPORTED_ARCHIVE_SUFFIXES,
    ComponentFile,
    ScanEntry,
    ScanResult,
    ScannedComponent,
)
from ..utils.hashing import hash_file
from .archive_handler import archive_support_status, is_supported_archive, open_archive
from .review_policy import review_required_warning

UE4SS_CORE_NAMES = {
    "ue4ss.dll",
    "ue4ss-settings.ini",
    "ue4ss.ini",
    "dwmapi.dll",
    "dwmappi.dll",
    "xinput1_3.dll",
}
UE4SS_MOD_MARKERS = {"enabled.txt", "settings.ini", "main.lua"}
UE4SS_MOD_FOLDER_MARKERS = {"scripts", "dlls"}
UE4SS_RESERVED_ROOTS = {"subnautica2", "engine", "content", "binaries", "win64", "ue4ss", "paks"}
UE4SS_PROTECTED_NATIVE_MOD_NAMES = {
    "bpml_genericfunctions",
    "bpmodloadermod",
    "cheatmanagerenablermod",
    "consolecommandsmod",
    "consoleenablermod",
    "keybinds",
    "consolecommands",
}


def scan_inbox(inbox_dir: Path | None) -> list[ScanResult]:
    if inbox_dir is None or not inbox_dir.is_dir():
        return []
    results: list[ScanResult] = []
    for path in sorted(inbox_dir.iterdir(), key=lambda item: item.name.casefold()):
        if path.name.casefold() == "readme.md":
            continue
        if path.is_file() or path.is_dir():
            results.append(scan_source(path))
    return results


def scan_source(path: Path) -> ScanResult:
    if path.is_dir():
        return inspect_folder(path)
    if path.is_file() and path.suffix.casefold() in SUPPORTED_ARCHIVE_SUFFIXES:
        return inspect_archive(path)
    if path.is_file() and path.suffix.casefold() in {".pak", ".ucas", ".utoc"}:
        return inspect_local_files([path])
    return ScanResult(
        source_path=str(path),
        source_kind=SOURCE_LOCAL_FILES,
        display_name=path.stem,
        source_paths=[str(path)],
        unsupported_files=[str(path)],
        warnings=[f"Unsupported source type: {path.name}"],
    )


def inspect_archive(path: Path) -> ScanResult:
    result = ScanResult(
        source_path=str(path),
        source_kind=SOURCE_ARCHIVE,
        display_name=_display_name(path.stem),
        source_paths=[str(path)],
    )
    if not path.is_file():
        result.errors.append(f"Archive not found: {path}")
        return result
    if not is_supported_archive(path):
        result.errors.append(f"Unsupported archive format: {path.suffix}")
        return result
    support = archive_support_status()
    if path.suffix.casefold() in support and not support[path.suffix.casefold()]:
        result.errors.append(f"Archive support not available for {path.suffix}")
        return result

    try:
        result.source_hash = hash_file(path)
    except OSError as exc:
        result.warnings.append(f"Could not hash source archive: {exc}")

    try:
        reader = open_archive(path)
    except Exception as exc:
        result.errors.append(f"Failed to open archive: {exc}")
        return result

    try:
        entries = [
            ScanEntry(info.filename.replace("\\", "/"), info.is_dir, info.file_size)
            for info in reader.list_entries()
        ]
    except Exception as exc:
        result.errors.append(f"Failed to read archive entries: {exc}")
        reader.close()
        return result
    finally:
        try:
            reader.close()
        except Exception:
            pass

    _complete_scan(result, entries)
    return result


def inspect_folder(path: Path) -> ScanResult:
    result = ScanResult(
        source_path=str(path),
        source_kind=SOURCE_FOLDER,
        display_name=_display_name(path.name),
        source_paths=[str(path)],
    )
    if not path.is_dir():
        result.errors.append(f"Folder not found: {path}")
        return result

    entries: list[ScanEntry] = []
    for child in sorted(path.rglob("*"), key=lambda item: str(item).casefold()):
        rel = child.relative_to(path).as_posix()
        entries.append(ScanEntry(rel, child.is_dir(), child.stat().st_size if child.is_file() else 0))
    _complete_scan(result, entries)
    return result


def inspect_local_files(paths: list[Path]) -> ScanResult:
    existing_paths = [path for path in paths if path.is_file()]
    display = _display_name(existing_paths[0].stem) if existing_paths else "Local files"
    result = ScanResult(
        source_path=str(existing_paths[0]) if existing_paths else "",
        source_kind=SOURCE_LOCAL_FILES,
        display_name=display,
        source_paths=[str(path) for path in existing_paths],
        source_hash=_local_files_hash(existing_paths),
    )
    entries = [
        ScanEntry(path.name, False, path.stat().st_size if path.is_file() else 0)
        for path in existing_paths
    ]
    _complete_scan(result, entries)
    return result


def _complete_scan(result: ScanResult, entries: list[ScanEntry]) -> None:
    safe_entries: list[ScanEntry] = []
    for entry in entries:
        if entry.is_dir:
            safe_entries.append(entry)
            continue
        if _is_safe_relative_path(entry.path):
            safe_entries.append(entry)
        else:
            result.unsafe_entries.append(entry.path)
    if result.unsafe_entries:
        result.warnings.append(f"Skipped {len(result.unsafe_entries)} unsafe archive path(s).")

    result.entries = safe_entries
    file_entries = [entry for entry in safe_entries if entry.is_file]
    if not file_entries:
        result.warnings.append("No files found to classify.")
        return

    used_paths: set[str] = set()
    components: list[ScannedComponent] = []

    runtime = _detect_ue4ss_runtime(file_entries, used_paths)
    if runtime:
        components.append(runtime)

    ue4ss_mods = _detect_ue4ss_mods(file_entries, used_paths, result.display_name)
    components.extend(ue4ss_mods)

    pak_components = _detect_pak_bundles(file_entries, used_paths)
    components.extend(pak_components)

    loose = [
        entry
        for entry in file_entries
        if entry.path not in used_paths and not entry.is_unreal_asset
    ]
    if loose:
        component_type = COMPONENT_MIXED if components else COMPONENT_LOOSE_OVERLAY
        loose_files = [
            ComponentFile(entry.path, role="loose", target_hint=_loose_target_hint(entry.path), size=entry.size)
            for entry in loose
        ]
        components.append(
            ScannedComponent(
                component_id=_new_id("loose"),
                display_name=f"{result.display_name} Loose Files",
                component_type=component_type,
                install_kind=INSTALL_KIND_LOOSE_OVERLAY,
                files=loose_files,
                badges=["Loose"],
                target_hint="review required: root overlay",
                warnings=[review_required_warning(target_hints=[file.target_hint for file in loose_files])],
            )
        )

    if not components:
        components.append(
            ScannedComponent(
                component_id=_new_id("unknown"),
                display_name=result.display_name,
                component_type=COMPONENT_UNKNOWN,
                install_kind=INSTALL_KIND_STANDARD,
                warnings=["No recognizable S2 mod component found."],
            )
        )

    result.components = components
    if len([component for component in components if component.component_type == COMPONENT_PAK_BUNDLE]) > 1:
        result.ambiguous = True
        result.warnings.append("Multiple pak components found; user review is recommended.")


def _detect_ue4ss_runtime(entries: list[ScanEntry], used_paths: set[str]) -> ScannedComponent | None:
    names = {entry.name.casefold() for entry in entries}
    paths = [entry.path.replace("\\", "/").casefold() for entry in entries]
    has_core = bool(names & UE4SS_CORE_NAMES)
    has_ue4ss_folder = any(path.startswith("ue4ss/") or "/ue4ss/" in path for path in paths)
    has_mod_tree = any("/ue4ss/mods/" in path or path.startswith("ue4ss/mods/") for path in paths)
    if not has_core and not (has_ue4ss_folder and not has_mod_tree):
        return None

    runtime_files = [
        entry
        for entry in entries
        if _runtime_relative_path(entry.path) is not None
        or entry.name.casefold() in UE4SS_CORE_NAMES
    ]
    if not runtime_files:
        return None
    for entry in runtime_files:
        used_paths.add(entry.path)
    return ScannedComponent(
        component_id=_new_id("runtime"),
        display_name="UE4SS Runtime",
        component_type=COMPONENT_UE4SS_RUNTIME,
        install_kind=INSTALL_KIND_UE4SS_RUNTIME,
        files=[
            ComponentFile(entry.path, role="runtime", target_hint=_runtime_relative_path(entry.path) or entry.name, size=entry.size)
            for entry in runtime_files
        ],
        badges=["Runtime", "UE4SS"],
        target_hint=r"Subnautica2\Binaries\Win64",
    )


def _detect_ue4ss_mods(entries: list[ScanEntry], used_paths: set[str], default_mod_name: str) -> list[ScannedComponent]:
    grouped: dict[str, list[tuple[ScanEntry, str]]] = {}
    wrapper_roots = _ue4ss_wrapper_roots(entries, used_paths)
    for entry in entries:
        if entry.path in used_paths:
            continue
        rel = _ue4ss_mod_relative_path(entry.path, default_mod_name=default_mod_name, wrapper_roots=wrapper_roots)
        if rel is None:
            continue
        parts = PurePosixPath(rel).parts
        if not parts:
            continue
        mod_name = parts[0]
        grouped.setdefault(mod_name, []).append((entry, rel))

    components: list[ScannedComponent] = []
    for mod_name, members in sorted(grouped.items(), key=lambda item: item[0].casefold()):
        for entry, _rel in members:
            used_paths.add(entry.path)
        warnings: list[str] = []
        badges = ["UE4SS"]
        if mod_name.casefold() in UE4SS_PROTECTED_NATIVE_MOD_NAMES:
            badges.append("Core")
            warnings.append(
                "Protected native UE4SS core mod detected; changing or disabling it may break UE4SS."
            )
        if any(PurePosixPath(entry.path.replace("\\", "/")).parts[:1] and PurePosixPath(entry.path.replace("\\", "/")).parts[0].casefold() in UE4SS_MOD_FOLDER_MARKERS for entry, _rel in members):
            warnings.append(
                f"Root scripts/dlls archive shape will be wrapped as the UE4SS mod folder '{mod_name}'."
            )
        components.append(
            ScannedComponent(
                component_id=_new_id("ue4ss"),
                display_name=_display_name(mod_name),
                component_type=COMPONENT_UE4SS_MOD,
                install_kind=INSTALL_KIND_UE4SS_MOD,
                files=[
                    ComponentFile(entry.path, role="ue4ss_mod", target_hint=rel, size=entry.size)
                    for entry, rel in members
                ],
                badges=badges,
                target_hint=rf"Subnautica2\Binaries\Win64\ue4ss\Mods\{mod_name}",
                dependency_warnings=["Requires UE4SS runtime to be installed first."],
                warnings=warnings,
            )
        )
    return components


def _detect_pak_bundles(entries: list[ScanEntry], used_paths: set[str]) -> list[ScannedComponent]:
    by_parent_stem: dict[tuple[str, str], list[ScanEntry]] = {}
    for entry in entries:
        if entry.path in used_paths:
            continue
        if not entry.is_unreal_asset:
            continue
        stripped = _pak_relative_path(entry.path)
        path = PurePosixPath(stripped)
        key = (str(path.parent), path.stem.casefold())
        by_parent_stem.setdefault(key, []).append(entry)

    components: list[ScannedComponent] = []
    for (_parent, _stem), group in sorted(by_parent_stem.items(), key=lambda item: item[0]):
        paks = [entry for entry in group if entry.is_pak]
        if not paks:
            continue
        pak = sorted(paks, key=lambda entry: entry.path.casefold())[0]
        companions = sorted([entry for entry in group if entry.is_companion], key=lambda entry: entry.suffix)
        files = [pak] + companions
        for entry in files:
            used_paths.add(entry.path)
        display = _display_name(PurePosixPath(_pak_relative_path(pak.path)).stem)
        components.append(
            ScannedComponent(
                component_id=_new_id("pak"),
                display_name=display,
                component_type=COMPONENT_PAK_BUNDLE,
                install_kind=INSTALL_KIND_STANDARD,
                files=[
                    ComponentFile(
                        entry.path,
                        role="pak" if entry.is_pak else "companion",
                        target_hint=PurePosixPath(_pak_relative_path(entry.path)).name,
                        size=entry.size,
                    )
                    for entry in files
                ],
                badges=["Pak"],
                target_hint=r"Subnautica2\Content\Paks\~mods",
            )
        )
    return components


def _is_safe_relative_path(value: str) -> bool:
    for cls in (PurePosixPath, PureWindowsPath):
        path = cls(value)
        if path.is_absolute():
            return False
        if ".." in path.parts:
            return False
    return True


def _runtime_relative_path(value: str) -> str | None:
    parts = PurePosixPath(value.replace("\\", "/")).parts
    for marker in (("Subnautica2", "Binaries", "Win64"), ("Binaries", "Win64"), ("Win64",)):
        rel = _parts_after(parts, marker)
        if rel:
            return str(PurePosixPath(*rel))
    stripped = _strip_wrapper(value)
    stripped_parts = PurePosixPath(stripped).parts
    if stripped_parts and (stripped_parts[0].casefold() == "ue4ss" or stripped_parts[-1].casefold() in UE4SS_CORE_NAMES):
        return str(PurePosixPath(*stripped_parts))
    return None


def _ue4ss_wrapper_roots(entries: list[ScanEntry], used_paths: set[str]) -> set[str]:
    candidates: dict[str, list[tuple[str, ...]]] = {}
    for entry in entries:
        if entry.path in used_paths:
            continue
        parts = PurePosixPath(entry.path.replace("\\", "/")).parts
        if len(parts) < 2 or parts[0].casefold() in UE4SS_RESERVED_ROOTS | UE4SS_MOD_FOLDER_MARKERS:
            continue
        candidates.setdefault(parts[0], []).append(parts[1:])

    roots: set[str] = set()
    for root, relative_parts in candidates.items():
        if any(_looks_like_ue4ss_mod_member(parts) for parts in relative_parts):
            roots.add(root)
    return roots


def _looks_like_ue4ss_mod_member(parts: tuple[str, ...]) -> bool:
    lowered = tuple(part.casefold() for part in parts)
    return bool(
        parts
        and (
            lowered[0] in UE4SS_MOD_FOLDER_MARKERS
            or lowered[-1] in UE4SS_MOD_MARKERS
            or "scripts" in lowered
            or "dlls" in lowered
        )
    )


def _ue4ss_mod_relative_path(value: str, *, default_mod_name: str = "", wrapper_roots: set[str] | None = None) -> str | None:
    parts = PurePosixPath(value.replace("\\", "/")).parts
    after_mods = _parts_after(parts, ("ue4ss", "Mods"))
    if after_mods:
        return str(PurePosixPath(*after_mods))

    if wrapper_roots and parts and parts[0] in wrapper_roots:
        return str(PurePosixPath(*parts))

    stripped = _strip_wrapper(value)
    stripped_parts = PurePosixPath(stripped).parts
    if _looks_like_ue4ss_mod_member(stripped_parts):
        mod_name = _safe_folder_name(default_mod_name) or "ImportedMod"
        return str(PurePosixPath(mod_name, *stripped_parts))
    return None


def _pak_relative_path(value: str) -> str:
    parts = PurePosixPath(value.replace("\\", "/")).parts
    for marker in (("Subnautica2", "Content", "Paks"), ("Content", "Paks"), ("Paks",)):
        rel = _parts_after(parts, marker)
        if rel:
            return str(PurePosixPath(*rel))
    return _strip_wrapper(value)


def _loose_target_hint(value: str) -> str:
    parts = PurePosixPath(value.replace("\\", "/")).parts
    for marker in (("Subnautica2",),):
        rel = _parts_after(parts, marker)
        if rel:
            return str(PurePosixPath(*rel))
    return _strip_wrapper(value)


def _strip_wrapper(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    parts = path.parts
    if len(parts) > 1 and parts[0].casefold() not in UE4SS_RESERVED_ROOTS | UE4SS_MOD_FOLDER_MARKERS:
        return str(PurePosixPath(*parts[1:]))
    return str(path)


def _parts_after(parts: tuple[str, ...], marker: tuple[str, ...]) -> tuple[str, ...] | None:
    lowered = tuple(part.casefold() for part in parts)
    marker_lowered = tuple(part.casefold() for part in marker)
    length = len(marker_lowered)
    for index in range(0, len(parts) - length + 1):
        if lowered[index:index + length] == marker_lowered:
            return parts[index + length:]
    return None


def _display_name(value: str) -> str:
    text = value.replace("_", " ").replace("-", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    return text or "Unnamed mod"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _safe_folder_name(value: str) -> str:
    text = "".join(ch for ch in value.strip() if ch not in '<>:"/\\|?*')
    return text.strip() or "ImportedMod"


def copy_source_to_library(source: Path, destination: Path) -> None:
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _local_files_hash(paths: list[Path]) -> str:
    if not paths:
        return ""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: (item.name.casefold(), str(item).casefold())):
        digest.update(path.name.encode("utf-8", errors="replace"))
        digest.update(b"\0")
        try:
            digest.update(hash_file(path).encode("ascii"))
        except OSError:
            return ""
        digest.update(b"\0")
    return digest.hexdigest()

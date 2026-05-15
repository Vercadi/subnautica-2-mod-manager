from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..models.archive_info import (
    COMPONENT_UNKNOWN,
    SOURCE_LOCAL_FILES,
    SUPPORTED_ARCHIVE_SUFFIXES,
    UNREAL_ASSET_SUFFIXES,
    ScanResult,
)
from ..models.import_review import ImportComponentReview, ImportReview, ImportSelection, ImportSourceReview
from ..models.library import LibrarySource
from .archive_inspector import inspect_local_files, scan_source
from .library_store import LibraryStore
from .review_policy import review_policy_for_fields


def parse_drop_paths(data: str) -> list[Path]:
    text = str(data or "").strip()
    if not text:
        return []
    try:
        import tkinter as tk

        values = tk.Tcl().splitlist(text)
    except Exception:
        values = _split_drop_text(text)
    return [Path(value) for value in values if str(value).strip()]


def normalize_import_sources(paths: Iterable[str | Path]) -> list[list[Path]]:
    unique_paths: list[Path] = []
    seen: set[str] = set()
    for raw in paths:
        path = Path(raw)
        key = str(path.resolve() if path.exists() else path)
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(path)

    groups: list[list[Path]] = []
    unreal_groups: dict[tuple[str, str], list[Path]] = {}
    for path in unique_paths:
        suffix = path.suffix.casefold()
        if path.is_dir() or suffix in SUPPORTED_ARCHIVE_SUFFIXES:
            groups.append([path])
            continue
        if suffix in UNREAL_ASSET_SUFFIXES:
            key = (str(path.parent.resolve() if path.parent.exists() else path.parent), path.stem.casefold())
            unreal_groups.setdefault(key, []).append(path)
            continue
        groups.append([path])

    groups.extend(_sorted_unreal_groups(unreal_groups))
    return groups


def scan_import_sources(paths: Iterable[str | Path]) -> list[ScanResult]:
    scans: list[ScanResult] = []
    for group in normalize_import_sources(paths):
        if len(group) == 1 and group[0].suffix.casefold() not in UNREAL_ASSET_SUFFIXES:
            scans.append(scan_source(group[0]))
        else:
            scans.append(inspect_local_files(group))
    return scans


def build_import_review(paths: Iterable[str | Path], *, imported_hashes: set[str] | None = None) -> ImportReview:
    scans = scan_import_sources(paths)
    hashes = imported_hashes or set()
    sources = [_source_review(scan, hashes) for scan in scans]
    return ImportReview(sources=sources, scans=scans)


def selection_from_review(review: ImportReview) -> ImportSelection:
    selected: dict[str, set[str]] = {}
    for source in review.sources:
        if not source.selected or not source.importable or source.already_imported:
            continue
        component_ids = {component.component_id for component in source.components if component.selected}
        if component_ids:
            selected[source.source_key] = component_ids
    return ImportSelection(selected)


def import_review_selection(
    store: LibraryStore,
    review: ImportReview,
    selection: ImportSelection,
) -> list[LibrarySource]:
    imported: list[LibrarySource] = []
    scans_by_key = {_source_key(scan): scan for scan in review.scans}
    for source_key, component_ids in selection.selected_sources.items():
        scan = scans_by_key.get(source_key)
        if scan is None or not component_ids:
            continue
        selected_scan = _scan_with_components(scan, component_ids)
        source = store.import_scan(selected_scan)
        if source is not None and source not in imported:
            imported.append(source)
    return imported


def import_review_summary(review: ImportReview, imported_count: int = 0) -> str:
    if imported_count:
        return f"Import review: {review.summary_text}; imported {imported_count} source(s) into manager library."
    return f"Import review: {review.summary_text}."


def _source_review(scan: ScanResult, imported_hashes: set[str]) -> ImportSourceReview:
    components = [_component_review(component) for component in scan.components]
    already_imported = bool(scan.source_hash and scan.source_hash in imported_hashes)
    importable = scan.ok and bool(components) and not all(
        component.component_type == COMPONENT_UNKNOWN for component in scan.components
    )
    warnings = list(dict.fromkeys(scan.warnings))
    if scan.ambiguous:
        warnings.append("Ambiguous source; confirm selected components before import.")
    selected = importable and not already_imported
    return ImportSourceReview(
        source_key=_source_key(scan),
        display_name=scan.display_name,
        source_path=scan.source_path,
        source_kind=scan.source_kind,
        source_hash=scan.source_hash,
        already_imported=already_imported,
        importable=importable,
        ambiguous=scan.ambiguous,
        warnings=list(dict.fromkeys(warnings)),
        errors=list(scan.errors),
        unsupported_files=list(scan.unsupported_files),
        unsafe_entries=list(scan.unsafe_entries),
        components=components,
        selected=selected,
    )


def _component_review(component) -> ImportComponentReview:
    warnings = list(dict.fromkeys(list(component.warnings) + list(component.dependency_warnings)))
    policy = review_policy_for_fields(
        component.component_type,
        component.install_kind,
        target_hints=[file.target_hint for file in component.files],
    )
    if policy is not None:
        warnings.append(policy.text)
    return ImportComponentReview(
        component_id=component.component_id,
        display_name=component.display_name,
        component_type=component.component_type,
        install_kind=component.install_kind,
        badges=list(component.badges),
        file_count=component.file_count,
        target_hint=component.target_hint,
        warnings=list(dict.fromkeys(warnings)),
        review_policy_text=policy.text if policy else "",
        selected=component.component_type != COMPONENT_UNKNOWN,
    )


def _source_key(scan: ScanResult) -> str:
    if scan.source_hash:
        return f"hash:{scan.source_hash}"
    if scan.source_kind == SOURCE_LOCAL_FILES and scan.source_paths:
        return "local:" + "|".join(scan.source_paths)
    return f"path:{scan.source_path}"


def _scan_with_components(scan: ScanResult, component_ids: set[str]) -> ScanResult:
    return ScanResult(
        source_path=scan.source_path,
        source_kind=scan.source_kind,
        display_name=scan.display_name,
        source_hash=scan.source_hash,
        source_paths=list(scan.source_paths),
        components=[component for component in scan.components if component.component_id in component_ids],
        entries=list(scan.entries),
        unsupported_files=list(scan.unsupported_files),
        unsafe_entries=list(scan.unsafe_entries),
        warnings=list(scan.warnings),
        errors=list(scan.errors),
        ambiguous=scan.ambiguous,
    )


def _sorted_unreal_groups(groups: dict[tuple[str, str], list[Path]]) -> list[list[Path]]:
    suffix_order = {".pak": 0, ".ucas": 1, ".utoc": 2}
    return [
        sorted(group, key=lambda path: (suffix_order.get(path.suffix.casefold(), 99), path.name.casefold()))
        for _key, group in sorted(groups.items(), key=lambda item: item[0])
    ]


def _split_drop_text(text: str) -> list[str]:
    values: list[str] = []
    current: list[str] = []
    in_brace = False
    for char in text:
        if char == "{":
            in_brace = True
            continue
        if char == "}":
            in_brace = False
            values.append("".join(current))
            current = []
            continue
        if char.isspace() and not in_brace:
            if current:
                values.append("".join(current))
                current = []
            continue
        current.append(char)
    if current:
        values.append("".join(current))
    return values

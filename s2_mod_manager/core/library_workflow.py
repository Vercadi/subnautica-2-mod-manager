from __future__ import annotations

from ..models.archive_info import (
    COMPONENT_PAK_BUNDLE,
    COMPONENT_UE4SS_MOD,
    COMPONENT_UE4SS_RUNTIME,
    ScanResult,
)
from ..models.library import LibraryComponent, LibrarySource
from ..models.library_view import LibraryDisplayItem, LibraryViewState, ScanSummary
from .library_store import LibraryStore
from .review_policy import review_policy_for_fields


def build_library_view_state(store: LibraryStore, scans: list[ScanResult]) -> LibraryViewState:
    imported_hashes = {source.source_hash for source in store.list_sources() if source.source_hash}
    library_items = _library_items(store)
    candidate_items = _candidate_items(scans, imported_hashes)
    return LibraryViewState(
        library_items=library_items,
        candidate_items=candidate_items,
        summary=scan_summary(scans, imported_hashes=imported_hashes),
    )


def scan_summary(scans: list[ScanResult], *, imported_hashes: set[str] | None = None) -> ScanSummary:
    imported_hashes = imported_hashes or set()
    return ScanSummary(
        source_count=len(scans),
        component_count=sum(len(scan.components) for scan in scans),
        warning_count=sum(len(scan.warnings) + len(scan.unsafe_entries) for scan in scans),
        error_count=sum(len(scan.errors) for scan in scans),
        ambiguous_count=sum(1 for scan in scans if scan.ambiguous),
        imported_source_count=sum(1 for scan in scans if scan.source_hash and scan.source_hash in imported_hashes),
        candidate_source_count=sum(1 for scan in scans if not (scan.source_hash and scan.source_hash in imported_hashes)),
    )


def import_all_candidates(store: LibraryStore, scans: list[ScanResult]) -> list[LibrarySource]:
    imported: list[LibrarySource] = []
    imported_hashes = {source.source_hash for source in store.list_sources() if source.source_hash}
    for scan in scans:
        if scan.source_hash and scan.source_hash in imported_hashes:
            continue
        source = store.import_scan(scan)
        if source is not None and source not in imported:
            imported.append(source)
            if source.source_hash:
                imported_hashes.add(source.source_hash)
    return imported


def import_selected_candidates(
    store: LibraryStore,
    scans: list[ScanResult],
    selected_source_paths: set[str],
) -> list[LibrarySource]:
    imported: list[LibrarySource] = []
    imported_hashes = {source.source_hash for source in store.list_sources() if source.source_hash}
    for scan in scans:
        if scan.source_path not in selected_source_paths:
            continue
        if scan.source_hash and scan.source_hash in imported_hashes:
            continue
        source = store.import_scan(scan)
        if source is not None and source not in imported:
            imported.append(source)
            if source.source_hash:
                imported_hashes.add(source.source_hash)
    return imported


def _library_items(store: LibraryStore) -> list[LibraryDisplayItem]:
    sources_by_id = {source.source_id: source for source in store.list_sources()}
    items: list[LibraryDisplayItem] = []
    for component in store.list_components():
        source = sources_by_id.get(component.source_id)
        items.append(_item_from_library_component(component, source))
    return sorted(items, key=lambda item: (item.source_name.casefold(), item.display_name.casefold()))


def _candidate_items(scans: list[ScanResult], imported_hashes: set[str]) -> list[LibraryDisplayItem]:
    items: list[LibraryDisplayItem] = []
    for scan_index, scan in enumerate(scans):
        already_imported = bool(scan.source_hash and scan.source_hash in imported_hashes)
        if already_imported:
            continue
        if not scan.components:
            warnings = list(scan.warnings) + list(scan.errors) + [
                f"Unsupported file: {path}" for path in scan.unsupported_files
            ]
            items.append(
                LibraryDisplayItem(
                    item_id=f"candidate:{scan_index}:source",
                    display_name=scan.display_name,
                    version_label="candidate",
                    description="No importable S2 mod component detected.",
                    badges=["Unsupported"],
                    status="Needs Review",
                    enabled=False,
                    warning="; ".join(dict.fromkeys(warnings)) or "Unsupported or empty source.",
                    accent="#FF7A59",
                    state="candidate",
                    source_name=scan.display_name,
                    source_path=scan.source_path,
                    source_warnings=warnings,
                )
            )
            continue
        for component_index, component in enumerate(scan.components):
            status = "Imported" if already_imported else "Ready to Import"
            warnings = list(component.warnings) + list(component.dependency_warnings) + list(scan.warnings)
            policy = review_policy_for_fields(
                component.component_type,
                component.install_kind,
                target_hints=[file.target_hint for file in component.files],
            )
            if policy is not None:
                warnings.append(policy.text)
            if scan.ambiguous:
                warnings.append("Ambiguous multi-component source; review before import.")
            items.append(
                LibraryDisplayItem(
                    item_id=f"candidate:{scan_index}:{component_index}",
                    display_name=component.display_name,
                    version_label="candidate",
                    description=_candidate_description(scan.display_name, component.file_count, policy_text=policy.text if policy else ""),
                    badges=list(component.badges),
                    status=status if not warnings else "Needs Review",
                    enabled=False,
                    warning="; ".join(dict.fromkeys(warnings)),
                    accent=_accent_for_component(component.component_type),
                    state="imported_candidate" if already_imported else "candidate",
                    source_name=scan.display_name,
                    source_path=scan.source_path,
                    component_id=component.component_id,
                    component_type=component.component_type,
                    install_kind=component.install_kind,
                    target_hint=component.target_hint,
                    file_count=component.file_count,
                    files=[file.source_path for file in component.files],
                    dependency_warnings=list(component.dependency_warnings),
                    source_warnings=list(scan.warnings) + list(scan.errors),
                    review_policy_text=policy.text if policy else "",
                )
            )
    return items


def _item_from_library_component(component: LibraryComponent, source: LibrarySource | None) -> LibraryDisplayItem:
    warning = "; ".join(component.warnings)
    policy = review_policy_for_fields(
        component.component_type,
        component.install_kind,
        target_hints=[file.target_hint for file in component.files],
    )
    if policy is not None:
        warning = "; ".join(dict.fromkeys(value for value in [warning, policy.text] if value))
    return LibraryDisplayItem(
        item_id=f"library:{component.component_id}",
        display_name=component.display_name,
        version_label="library",
        description=_library_description(component.file_count, source.display_name if source else "library source", policy_text=policy.text if policy else ""),
        badges=list(component.badges),
        status="Imported" if not warning else "Needs Review",
        enabled=True,
        warning=warning,
        accent=_accent_for_component(component.component_type),
        state="library",
        source_name=source.display_name if source else "",
        source_path=str(source.original_path) if source else "",
        managed_path=str(source.managed_path) if source else "",
        component_id=component.component_id,
        source_id=component.source_id,
        component_type=component.component_type,
        install_kind=component.install_kind,
        target_hint=component.target_hint,
        file_count=component.file_count,
        files=[file.source_path for file in component.files],
        source_warnings=list(component.warnings),
        review_policy_text=policy.text if policy else "",
    )


def _accent_for_component(component_type: str) -> str:
    if component_type == COMPONENT_PAK_BUNDLE:
        return "#7E2AFF"
    if component_type == COMPONENT_UE4SS_RUNTIME:
        return "#FFD166"
    if component_type == COMPONENT_UE4SS_MOD:
        return "#38D6D6"
    return "#67D38A"


def _candidate_description(source_name: str, file_count: int, *, policy_text: str = "") -> str:
    base = f"{file_count} file(s) from {source_name}. Import copies to manager storage only."
    if policy_text:
        return base + " Review required before any deployment."
    return base


def _library_description(file_count: int, source_name: str, *, policy_text: str = "") -> str:
    base = f"{file_count} file(s) imported from {source_name}. Ready to apply through Preview & Apply Profile."
    if policy_text:
        return base + " Review-required loose overlays stay blocked from automatic apply."
    return base

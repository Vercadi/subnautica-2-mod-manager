from __future__ import annotations

import shutil
from pathlib import Path

from ..models.archive_info import SOURCE_LOCAL_FILES, ScanResult, ScannedComponent
from ..models.archive_info import COMPONENT_PAK_BUNDLE
from ..models.library import LibraryComponent, LibrarySource, LibraryState
from ..utils.hashing import hash_file
from ..utils.json_io import read_json, write_json
from .library_duplicates import DuplicateCleanupResult, duplicate_key
from .pak_targets import pak_component_target_hint, pak_file_target_hint


class LibraryStore:
    """Manager-owned imported source store.

    Importing here copies archives/folders into data/library only. It never
    writes to the real game install.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.library_dir = data_dir / "library"
        self.sources_dir = self.library_dir / "sources"
        self.state_path = self.library_dir / "library_state.json"
        self.state = LibraryState.from_dict(read_json(self.state_path))
        if self._normalize_pak_targets():
            self.save()

    def list_sources(self) -> list[LibrarySource]:
        return list(self.state.sources)

    def list_components(self) -> list[LibraryComponent]:
        return list(self.state.components)

    def remove_components(self, component_ids: list[str], *, delete_sources_when_empty: bool = True) -> int:
        selected = set(component_ids)
        if not selected:
            return 0
        before = len(self.state.components)
        removed_components = [component for component in self.state.components if component.component_id in selected]
        self.state.components = [component for component in self.state.components if component.component_id not in selected]
        for source in self.state.sources:
            source.component_ids = [component_id for component_id in source.component_ids if component_id not in selected]
        if delete_sources_when_empty:
            removed_source_paths: list[Path] = []
            kept_sources: list[LibrarySource] = []
            for source in self.state.sources:
                if source.component_ids:
                    kept_sources.append(source)
                else:
                    removed_source_paths.append(source.managed_path)
            self.state.sources = kept_sources
            for path in removed_source_paths:
                _remove_path(path)
        removed = before - len(self.state.components)
        if removed or removed_components:
            self.save()
        return removed

    def import_scan(self, scan: ScanResult) -> LibrarySource | None:
        if not scan.ok or not scan.components:
            return None
        source_paths = _scan_source_paths(scan)
        if not source_paths or any(not source_path.exists() for source_path in source_paths):
            return None
        source_path = source_paths[0]

        source_hash = scan.source_hash or _source_hashes(source_paths)
        existing = self._find_by_hash(source_hash)
        if existing is not None:
            self._merge_scan_components(existing, scan)
            return existing

        source_id = f"src_{source_hash[:12]}" if source_hash else _fallback_source_id(source_path)
        managed_path = self._managed_path(source_id, source_path, source_kind=scan.source_kind, source_count=len(source_paths))
        _copy_sources(source_paths, managed_path, source_kind=scan.source_kind)

        source_warnings = list(scan.warnings) + list(scan.errors)
        if scan.ambiguous:
            source_warnings.append("Ambiguous multi-component source; review before adding to a profile.")
        components = []
        for component in scan.components:
            library_component = LibraryComponent.from_scan(source_id, component)
            library_component.warnings = _dedupe(library_component.warnings + source_warnings)
            components.append(library_component)
        source = LibrarySource(
            source_id=source_id,
            source_kind=scan.source_kind,
            display_name=scan.display_name,
            original_path=source_path,
            managed_path=managed_path,
            source_hash=source_hash,
            component_ids=[component.component_id for component in components],
        )
        self.state.sources.append(source)
        self.state.components.extend(components)
        self.save()
        return source

    def remove_uninstalled_duplicates_for_sources(
        self,
        sources: list[LibrarySource],
        *,
        protected_component_ids: set[str] | None = None,
    ) -> DuplicateCleanupResult:
        protected = protected_component_ids or set()
        new_source_ids = {source.source_id for source in sources}
        if not new_source_ids:
            return DuplicateCleanupResult([], [])
        new_components = [
            component for component in self.state.components
            if component.source_id in new_source_ids
        ]
        if not new_components:
            return DuplicateCleanupResult([], [])

        removal_ids: list[str] = []
        protected_ids: list[str] = []
        for new_component in new_components:
            key = duplicate_key(new_component)
            if not key[0]:
                continue
            for existing in self.state.components:
                if existing.component_id == new_component.component_id or existing.source_id in new_source_ids:
                    continue
                if duplicate_key(existing) != key:
                    continue
                if existing.component_id in protected:
                    protected_ids.append(existing.component_id)
                    continue
                removal_ids.append(existing.component_id)

        unique_removal_ids = list(dict.fromkeys(removal_ids))
        self.remove_components(unique_removal_ids)
        return DuplicateCleanupResult(unique_removal_ids, list(dict.fromkeys(protected_ids)))

    def save(self) -> None:
        self.library_dir.mkdir(parents=True, exist_ok=True)
        write_json(self.state_path, self.state.to_dict())

    def _find_by_hash(self, source_hash: str) -> LibrarySource | None:
        if not source_hash:
            return None
        for source in self.state.sources:
            if source.source_hash == source_hash and source.managed_path.exists():
                return source
        return None

    def _managed_path(self, source_id: str, source_path: Path, *, source_kind: str = "", source_count: int = 1) -> Path:
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        if source_path.is_dir() or source_kind == SOURCE_LOCAL_FILES or source_count > 1:
            return self.sources_dir / source_id
        return self.sources_dir / f"{source_id}{source_path.suffix.casefold()}"

    def _merge_scan_components(self, source: LibrarySource, scan: ScanResult) -> None:
        existing_signatures = {
            _library_component_signature(component)
            for component in self.state.components
            if component.source_id == source.source_id
        }
        added = False
        source_warnings = list(scan.warnings) + list(scan.errors)
        if scan.ambiguous:
            source_warnings.append("Ambiguous multi-component source; review before adding to a profile.")
        for component in scan.components:
            signature = _scan_component_signature(component)
            if signature in existing_signatures:
                continue
            library_component = LibraryComponent.from_scan(source.source_id, component)
            library_component.warnings = _dedupe(library_component.warnings + source_warnings)
            self.state.components.append(library_component)
            source.component_ids.append(library_component.component_id)
            existing_signatures.add(signature)
            added = True
        if added:
            source.component_ids = _dedupe(source.component_ids)
            self.save()

    def _normalize_pak_targets(self) -> bool:
        changed = False
        for component in self.state.components:
            if component.component_type != COMPONENT_PAK_BUNDLE:
                continue
            pak_file = next((file for file in component.files if file.role == "pak"), None)
            source_hint = pak_file.target_hint if pak_file is not None else component.target_hint
            if pak_file is not None:
                target_hint = pak_component_target_hint(source_hint or pak_file.source_path)
                if component.target_hint != target_hint:
                    component.target_hint = target_hint
                    changed = True
            for file in component.files:
                normalized = pak_file_target_hint(file.target_hint or file.source_path)
                if file.target_hint != normalized:
                    file.target_hint = normalized
                    changed = True
        return changed


def _copy_source(source: Path, destination: Path) -> None:
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _remove_path(path: Path) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    except OSError:
        pass


def _copy_sources(sources: list[Path], destination: Path, *, source_kind: str = "") -> None:
    if len(sources) == 1 and source_kind != SOURCE_LOCAL_FILES:
        _copy_source(sources[0], destination)
        return
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    destination.mkdir(parents=True, exist_ok=True)
    for source in sources:
        if source.is_dir():
            _copy_source(source, destination / source.name)
        else:
            shutil.copy2(source, destination / source.name)


def _source_hash(source: Path) -> str:
    if source.is_file():
        return hash_file(source)
    digest_parts: list[str] = []
    for child in sorted(path for path in source.rglob("*") if path.is_file()):
        rel = child.relative_to(source).as_posix()
        digest_parts.append(f"{rel}:{hash_file(child)}")
    import hashlib

    digest = hashlib.sha256()
    digest.update("\n".join(digest_parts).encode("utf-8"))
    return digest.hexdigest()


def _source_hashes(sources: list[Path]) -> str:
    if len(sources) == 1:
        return _source_hash(sources[0])
    import hashlib

    digest = hashlib.sha256()
    for source in sorted(sources, key=lambda item: (item.name.casefold(), str(item).casefold())):
        digest.update(source.name.encode("utf-8", errors="replace"))
        digest.update(b"\0")
        digest.update(_source_hash(source).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _fallback_source_id(source_path: Path) -> str:
    import uuid

    return f"src_{source_path.stem}_{uuid.uuid4().hex[:8]}"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _scan_source_paths(scan: ScanResult) -> list[Path]:
    values = list(scan.source_paths) if scan.source_paths else [scan.source_path]
    paths: list[Path] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        path = Path(value)
        key = str(path.resolve() if path.exists() else path)
        if key in seen:
            continue
        seen.add(key)
        paths.append(path)
    return paths


def _scan_component_signature(component: ScannedComponent) -> tuple[str, str, tuple[tuple[str, str, str], ...]]:
    return (
        component.display_name.casefold(),
        component.component_type,
        tuple(sorted((file.source_path.casefold(), file.role, file.target_hint.casefold()) for file in component.files)),
    )


def _library_component_signature(component: LibraryComponent) -> tuple[str, str, tuple[tuple[str, str, str], ...]]:
    return (
        component.display_name.casefold(),
        component.component_type,
        tuple(sorted((file.source_path.casefold(), file.role, file.target_hint.casefold()) for file in component.files)),
    )

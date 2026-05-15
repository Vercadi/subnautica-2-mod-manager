from __future__ import annotations

import zipfile
from pathlib import Path

from s2_mod_manager.core.archive_inspector import inspect_archive, scan_inbox
from s2_mod_manager.core.library_store import LibraryStore
from s2_mod_manager.core.library_workflow import (
    build_library_view_state,
    import_all_candidates,
    import_selected_candidates,
    scan_summary,
)


def test_library_persistence_loads_imported_components(tmp_path: Path) -> None:
    archive = _archive(tmp_path, "lights.zip", {"Lights/Lights_P.pak": b"pak"})
    scan = inspect_archive(archive)
    store = LibraryStore(tmp_path / "data")

    source = store.import_scan(scan)
    reloaded = LibraryStore(tmp_path / "data")

    assert source is not None
    assert len(reloaded.list_sources()) == 1
    assert len(reloaded.list_components()) == 1
    assert reloaded.list_components()[0].display_name == "Lights P"
    assert reloaded.list_components()[0].files[0].source_path == "Lights/Lights_P.pak"


def test_import_all_reuses_duplicate_hashes(tmp_path: Path) -> None:
    archive = _archive(tmp_path, "oxygen.zip", {"Oxygen/Oxygen_P.pak": b"pak"})
    scan = inspect_archive(archive)
    store = LibraryStore(tmp_path / "data")

    first = import_all_candidates(store, [scan])
    second = import_all_candidates(store, [scan])

    assert len(first) == 1
    assert len(second) == 0
    assert len(store.list_sources()) == 1
    assert len(store.list_components()) == 1


def test_import_selected_only_imports_matching_source_path(tmp_path: Path) -> None:
    first_archive = _archive(tmp_path, "one.zip", {"One/One_P.pak": b"one"})
    second_archive = _archive(tmp_path, "two.zip", {"Two/Two_P.pak": b"two"})
    scans = [inspect_archive(first_archive), inspect_archive(second_archive)]
    store = LibraryStore(tmp_path / "data")

    imported = import_selected_candidates(store, scans, {str(second_archive)})

    assert len(imported) == 1
    assert imported[0].original_path == second_archive
    assert len(store.list_components()) == 1
    assert store.list_components()[0].display_name == "Two P"


def test_scan_summary_counts_imported_and_candidates(tmp_path: Path) -> None:
    first_archive = _archive(tmp_path, "one.zip", {"One/One_P.pak": b"one"})
    second_archive = _archive(tmp_path, "two.zip", {"Two/Two_P.pak": b"two"})
    scans = [inspect_archive(first_archive), inspect_archive(second_archive)]
    store = LibraryStore(tmp_path / "data")
    store.import_scan(scans[0])
    imported_hashes = {source.source_hash for source in store.list_sources()}

    summary = scan_summary(scans, imported_hashes=imported_hashes)

    assert summary.source_count == 2
    assert summary.component_count == 2
    assert summary.imported_source_count == 1
    assert summary.candidate_source_count == 1


def test_view_state_separates_library_and_candidates(tmp_path: Path) -> None:
    first_archive = _archive(tmp_path, "one.zip", {"One/One_P.pak": b"one"})
    second_archive = _archive(tmp_path, "two.zip", {"Two/Two_P.pak": b"two"})
    scans = [inspect_archive(first_archive), inspect_archive(second_archive)]
    store = LibraryStore(tmp_path / "data")
    store.import_scan(scans[0])

    view = build_library_view_state(store, scans)

    assert len(view.library_items) == 1
    assert len(view.candidate_items) == 1
    assert view.library_items[0].state == "library"
    assert {item.state for item in view.candidate_items} == {"candidate"}


def test_scan_inbox_summary_with_unsupported_file(tmp_path: Path) -> None:
    inbox = tmp_path / "Mods"
    inbox.mkdir()
    _archive(inbox, "ok.zip", {"Ok/Ok_P.pak": b"pak"})
    (inbox / "notes.txt").write_text("unsupported", encoding="utf-8")

    scans = scan_inbox(inbox)
    summary = scan_summary(scans)

    assert summary.source_count == 2
    assert summary.component_count == 1
    assert summary.warning_count == 1

    view = build_library_view_state(LibraryStore(tmp_path / "data"), scans)
    unsupported = [item for item in view.candidate_items if "Unsupported" in item.badges]
    assert len(unsupported) == 1
    assert unsupported[0].warning


def _archive(root: Path, name: str, members: dict[str, bytes]) -> Path:
    path = root / name
    with zipfile.ZipFile(path, "w") as archive:
        for member, data in members.items():
            archive.writestr(member, data)
    return path

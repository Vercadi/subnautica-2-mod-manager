from __future__ import annotations

import zipfile
from pathlib import Path

from s2_mod_manager.core.import_review import (
    build_import_review,
    import_review_selection,
    import_review_summary,
    normalize_import_sources,
    parse_drop_paths,
    selection_from_review,
)
from s2_mod_manager.core.library_store import LibraryStore
from s2_mod_manager.models.archive_info import COMPONENT_PAK_BUNDLE
from s2_mod_manager.models.import_review import ImportSelection


def test_parse_drop_paths_handles_braced_windows_paths() -> None:
    paths = parse_drop_paths(r"{H:\Mods\Cool Mod.zip} {H:\Mods\Loose Folder}")

    assert [path.name for path in paths] == ["Cool Mod.zip", "Loose Folder"]


def test_normalize_import_sources_groups_local_pak_bundle(tmp_path: Path) -> None:
    pak = tmp_path / "Bundle_P.pak"
    ucas = tmp_path / "Bundle_P.ucas"
    utoc = tmp_path / "Bundle_P.utoc"
    for path in (utoc, pak, ucas):
        path.write_bytes(path.suffix.encode("ascii"))

    groups = normalize_import_sources([utoc, pak, ucas])
    review = build_import_review([utoc, pak, ucas])

    assert len(groups) == 1
    assert [path.suffix for path in groups[0]] == [".pak", ".ucas", ".utoc"]
    assert review.component_count == 1
    component = review.sources[0].components[0]
    assert component.component_type == COMPONENT_PAK_BUNDLE
    assert component.file_count == 3


def test_import_review_duplicate_source_does_not_duplicate_library(tmp_path: Path) -> None:
    archive = _archive(tmp_path, "lights.zip", {"Lights/Lights_P.pak": b"pak"})
    store = LibraryStore(tmp_path / "data")
    review = build_import_review([archive])
    selection = selection_from_review(review)

    first = import_review_selection(store, review, selection)
    second = import_review_selection(store, review, selection)

    assert len(first) == 1
    assert len(second) == 1
    assert len(store.list_sources()) == 1
    assert len(store.list_components()) == 1


def test_import_review_selected_components_can_merge_same_source(tmp_path: Path) -> None:
    archive = _archive(
        tmp_path,
        "multi.zip",
        {
            "One/One_P.pak": b"one",
            "Two/Two_P.pak": b"two",
        },
    )
    store = LibraryStore(tmp_path / "data")
    review = build_import_review([archive])
    source = review.sources[0]
    first_component = source.components[0]
    second_component = source.components[1]

    import_review_selection(store, review, ImportSelection({source.source_key: {first_component.component_id}}))
    import_review_selection(store, review, ImportSelection({source.source_key: {second_component.component_id}}))

    assert len(store.list_sources()) == 1
    assert len(store.list_components()) == 2


def test_import_review_surfaces_ambiguous_multi_pak_state(tmp_path: Path) -> None:
    archive = _archive(
        tmp_path,
        "ambiguous.zip",
        {
            "One/One_P.pak": b"one",
            "Two/Two_P.pak": b"two",
        },
    )

    review = build_import_review([archive])
    source = review.sources[0]

    assert source.ambiguous
    assert source.status_text == "Needs Review"
    assert any("Ambiguous" in warning for warning in source.warnings)


def test_import_review_surfaces_unsupported_source(tmp_path: Path) -> None:
    unsupported = tmp_path / "notes.txt"
    unsupported.write_text("not a mod", encoding="utf-8")

    review = build_import_review([unsupported])
    source = review.sources[0]

    assert not source.importable
    assert source.status_text == "Not importable"
    assert source.unsupported_files == [str(unsupported)]
    assert review.importable_source_count == 0


def test_import_review_summary_counts_results(tmp_path: Path) -> None:
    archive = _archive(tmp_path, "ok.zip", {"Ok/Ok_P.pak": b"pak"})
    unsupported = tmp_path / "notes.txt"
    unsupported.write_text("not a mod", encoding="utf-8")
    review = build_import_review([archive, unsupported])

    summary = import_review_summary(review, imported_count=1)

    assert "2 source(s)" in summary
    assert "1 component(s)" in summary
    assert "imported 1 source(s)" in summary


def _archive(root: Path, name: str, members: dict[str, bytes]) -> Path:
    path = root / name
    with zipfile.ZipFile(path, "w") as archive:
        for member, data in members.items():
            archive.writestr(member, data)
    return path

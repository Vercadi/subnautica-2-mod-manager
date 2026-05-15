from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from s2_mod_manager.core.archive_handler import archive_support_status
from s2_mod_manager.core.archive_inspector import inspect_archive, inspect_folder, scan_inbox
from s2_mod_manager.core.library_store import LibraryStore
from s2_mod_manager.models.archive_info import (
    COMPONENT_LOOSE_OVERLAY,
    COMPONENT_PAK_BUNDLE,
    COMPONENT_UE4SS_MOD,
    COMPONENT_UE4SS_RUNTIME,
)


def test_zip_pak_bundle_groups_companions(tmp_path: Path) -> None:
    archive = tmp_path / "Infinite Oxygen.zip"
    _write_zip(
        archive,
        {
            "InfiniteOxygen/InfiniteOxygen_P.pak": b"pak",
            "InfiniteOxygen/InfiniteOxygen_P.ucas": b"ucas",
            "InfiniteOxygen/InfiniteOxygen_P.utoc": b"utoc",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert len(scan.components) == 1
    component = scan.components[0]
    assert component.component_type == COMPONENT_PAK_BUNDLE
    assert component.target_hint.endswith(r"Content\Paks\~mods")
    assert {file.target_hint for file in component.files} == {
        "~mods/InfiniteOxygen_P.pak",
        "~mods/InfiniteOxygen_P.ucas",
        "~mods/InfiniteOxygen_P.utoc",
    }
    assert [file.role for file in component.files] == ["pak", "companion", "companion"]


def test_non_patch_pak_bundle_targets_logicmods(tmp_path: Path) -> None:
    archive = tmp_path / "SeaSprint.zip"
    _write_zip(
        archive,
        {
            "SeaSprint/SeaSprint.pak": b"pak",
            "SeaSprint/SeaSprint.ucas": b"ucas",
            "SeaSprint/SeaSprint.utoc": b"utoc",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    component = scan.components[0]
    assert component.component_type == COMPONENT_PAK_BUNDLE
    assert component.target_hint.endswith(r"Content\Paks\LogicMods")
    assert {file.target_hint for file in component.files} == {
        "LogicMods/SeaSprint.pak",
        "LogicMods/SeaSprint.ucas",
        "LogicMods/SeaSprint.utoc",
    }


def test_explicit_logicmods_prefix_is_preserved(tmp_path: Path) -> None:
    archive = tmp_path / "ExplicitLogic.zip"
    _write_zip(archive, {"Subnautica2/Content/Paks/LogicMods/SeaSprint.pak": b"pak"})

    scan = inspect_archive(archive)

    component = scan.components[0]
    assert component.target_hint.endswith(r"Content\Paks\LogicMods")
    assert component.files[0].target_hint == "LogicMods/SeaSprint.pak"


def test_zip_ue4ss_runtime_detects_core_files(tmp_path: Path) -> None:
    archive = tmp_path / "UE4SS SN2.zip"
    _write_zip(
        archive,
        {
            "ue4ss/UE4SS.dll": b"dll",
            "ue4ss/UE4SS-settings.ini": b"settings",
            "dwmapi.dll": b"loader",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert len(scan.components) == 1
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_RUNTIME
    assert "Runtime" in component.badges
    assert any(file.target_hint == "dwmapi.dll" for file in component.files)


def test_gamepass_content_root_runtime_strips_content_prefix(tmp_path: Path) -> None:
    archive = tmp_path / "UE4SS GamePass.zip"
    _write_zip(
        archive,
        {
            "Content/ue4ss/UE4SS.dll": b"dll",
            "Content/ue4ss/UE4SS-settings.ini": b"settings",
            "Content/dwmapi.dll": b"loader",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_RUNTIME
    assert {file.target_hint for file in component.files} == {
        "ue4ss/UE4SS.dll",
        "ue4ss/UE4SS-settings.ini",
        "dwmapi.dll",
    }


def test_gamepass_wingdk_runtime_preserves_explicit_project_prefix(tmp_path: Path) -> None:
    archive = tmp_path / "UE4SS GamePass WinGDK.zip"
    _write_zip(
        archive,
        {
            "Content/Subnautica2/Binaries/WinGDK/ue4ss/UE4SS.dll": b"dll",
            "Content/Subnautica2/Binaries/WinGDK/ue4ss/UE4SS-settings.ini": b"settings",
            "Content/Subnautica2/Binaries/WinGDK/dwmapi.dll": b"loader",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_RUNTIME
    assert {file.target_hint for file in component.files} == {
        "Subnautica2/Binaries/WinGDK/ue4ss/UE4SS.dll",
        "Subnautica2/Binaries/WinGDK/ue4ss/UE4SS-settings.ini",
        "Subnautica2/Binaries/WinGDK/dwmapi.dll",
    }


def test_zip_ue4ss_mod_strips_full_win64_prefix(tmp_path: Path) -> None:
    archive = tmp_path / "SN2ModSettings.zip"
    _write_zip(
        archive,
        {
            "Subnautica2/Binaries/Win64/ue4ss/Mods/SN2ModSettings/enabled.txt": b"",
            "Subnautica2/Binaries/Win64/ue4ss/Mods/SN2ModSettings/Scripts/main.lua": b"print('ok')",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert len(scan.components) == 1
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_MOD
    assert component.display_name == "SN2ModSettings"
    assert any("Import/add a UE4SS Runtime package" in warning for warning in component.dependency_warnings)
    assert {file.target_hint for file in component.files} == {
        "SN2ModSettings/enabled.txt",
        "SN2ModSettings/Scripts/main.lua",
    }


def test_zip_ue4ss_mod_strips_full_wingdk_prefix(tmp_path: Path) -> None:
    archive = tmp_path / "SN2ModSettings GamePass.zip"
    _write_zip(
        archive,
        {
            "Content/Subnautica2/Binaries/WinGDK/ue4ss/Mods/SN2ModSettings/enabled.txt": b"",
            "Content/Subnautica2/Binaries/WinGDK/ue4ss/Mods/SN2ModSettings/Scripts/main.lua": b"print('ok')",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert len(scan.components) == 1
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_MOD
    assert {file.target_hint for file in component.files} == {
        "SN2ModSettings/enabled.txt",
        "SN2ModSettings/Scripts/main.lua",
    }


def test_wrapped_ue4ss_mod_keeps_inner_mod_folder_and_extra_files(tmp_path: Path) -> None:
    archive = tmp_path / "ScannerSpeedMod-57-1-8-0.zip"
    _write_zip(
        archive,
        {
            "ScannerSpeedMod/enabled.txt": b"",
            "ScannerSpeedMod/Scripts/main.lua": b"require('original_durations')",
            "ScannerSpeedMod/original_durations.lua": b"return {}",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert len(scan.components) == 1
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_MOD
    assert component.display_name == "ScannerSpeedMod"
    assert component.target_hint.endswith(r"ue4ss\Mods\ScannerSpeedMod")
    assert {file.target_hint for file in component.files} == {
        "ScannerSpeedMod/enabled.txt",
        "ScannerSpeedMod/Scripts/main.lua",
        "ScannerSpeedMod/original_durations.lua",
    }


def test_root_level_ue4ss_mod_still_uses_source_name_as_folder(tmp_path: Path) -> None:
    archive = tmp_path / "Hide HUD.zip"
    _write_zip(
        archive,
        {
            "enabled.txt": b"",
            "Scripts/main.lua": b"print('hide')",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert len(scan.components) == 1
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_MOD
    assert component.display_name == "Hide HUD"
    assert {file.target_hint for file in component.files} == {
        "Hide HUD/enabled.txt",
        "Hide HUD/Scripts/main.lua",
    }


def test_mixed_multi_pak_archive_is_ambiguous(tmp_path: Path) -> None:
    archive = tmp_path / "mixed.zip"
    _write_zip(
        archive,
        {
            "A/A_P.pak": b"a",
            "B/B_P.pak": b"b",
            "readme.txt": b"notes",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert scan.ambiguous
    assert sum(1 for component in scan.components if component.component_type == COMPONENT_PAK_BUNDLE) == 2
    assert any(component.component_type == COMPONENT_LOOSE_OVERLAY or component.component_type == "mixed" for component in scan.components)


def test_unsafe_archive_entries_are_skipped(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    _write_zip(
        archive,
        {
            "../evil.pak": b"bad",
            "Safe/Safe_P.pak": b"safe",
        },
    )

    scan = inspect_archive(archive)

    assert scan.ok
    assert scan.unsafe_entries == ["../evil.pak"]
    assert len(scan.components) == 1
    assert scan.components[0].display_name == "Safe P"


def test_folder_scan_detects_root_ue4ss_mod(tmp_path: Path) -> None:
    folder = tmp_path / "HideHUD"
    (folder / "Scripts").mkdir(parents=True)
    (folder / "Scripts" / "main.lua").write_text("print('hide')", encoding="utf-8")
    (folder / "enabled.txt").write_text("", encoding="utf-8")

    scan = inspect_folder(folder)

    assert scan.ok
    assert len(scan.components) == 1
    component = scan.components[0]
    assert component.component_type == COMPONENT_UE4SS_MOD
    assert component.display_name == "HideHUD"


def test_library_import_copies_source_and_reuses_duplicate_hash(tmp_path: Path) -> None:
    archive = tmp_path / "mod.zip"
    _write_zip(archive, {"Mod/Mod_P.pak": b"pak"})
    scan = inspect_archive(archive)
    store = LibraryStore(tmp_path / "data")

    first = store.import_scan(scan)
    second = store.import_scan(scan)

    assert first is not None
    assert second is first
    assert first.managed_path.is_file()
    assert len(store.list_sources()) == 1
    assert len(store.list_components()) == 1


def test_scan_inbox_skips_readme_and_scans_sources(tmp_path: Path) -> None:
    inbox = tmp_path / "Mods"
    inbox.mkdir()
    (inbox / "README.md").write_text("docs", encoding="utf-8")
    _write_zip(inbox / "mod.zip", {"Mod/Mod_P.pak": b"pak"})

    scans = scan_inbox(inbox)

    assert len(scans) == 1
    assert scans[0].component_count == 1


def test_7z_archive_reader_when_available(tmp_path: Path) -> None:
    if not archive_support_status()[".7z"]:
        pytest.skip("py7zr is not installed")

    import py7zr

    source = tmp_path / "source"
    (source / "Seven").mkdir(parents=True)
    (source / "Seven" / "Seven_P.pak").write_bytes(b"pak")
    archive = tmp_path / "seven.7z"
    with py7zr.SevenZipFile(archive, "w") as seven:
        seven.writeall(source, arcname="")

    scan = inspect_archive(archive)

    assert scan.ok
    assert scan.components[0].component_type == COMPONENT_PAK_BUNDLE


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)

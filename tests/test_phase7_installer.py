from __future__ import annotations

import zipfile
from pathlib import Path

from s2_mod_manager.core.backup_store import BackupStore
from s2_mod_manager.core.deployment_planner import build_deployment_plan
from s2_mod_manager.core.installer import Installer
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.archive_info import (
    COMPONENT_LOOSE_OVERLAY,
    COMPONENT_PAK_BUNDLE,
    COMPONENT_UE4SS_MOD,
    INSTALL_KIND_LOOSE_OVERLAY,
    INSTALL_KIND_STANDARD,
    INSTALL_KIND_UE4SS_MOD,
)
from s2_mod_manager.models.deployment import ACTION_CREATE, ACTION_DELETE, ACTION_OVERWRITE
from s2_mod_manager.models.library import LibraryComponent, LibraryComponentFile, LibrarySource
from s2_mod_manager.models.manifest import STATUS_COMPLETED, STATUS_FAILED, STATUS_REFUSED
from s2_mod_manager.models.profile import LoadoutEntry, ModProfile


def test_installer_creates_targets_in_fake_install(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source_folder(tmp_path, files={"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )

    result = _installer(tmp_path).apply(plan)

    assert result.ok
    assert result.record.status == STATUS_COMPLETED
    assert (paths.mods_paks / "Mod_P.pak").read_bytes() == b"new"
    assert result.record.deployed_files[0].action == ACTION_CREATE


def test_installer_backs_up_overwrites(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    target = paths.mods_paks / "Mod_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"old")
    source = _source_folder(tmp_path, files={"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )

    result = _installer(tmp_path).apply(plan)

    assert result.ok
    assert target.read_bytes() == b"new"
    assert result.record.deployed_files[0].action == ACTION_OVERWRITE
    assert result.record.backups
    assert result.record.backups[0].backup_path.read_bytes() == b"old"
    assert result.record.deployed_files[0].backup_id == result.record.backups[0].backup_id


def test_manifest_roundtrip_after_apply(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source_folder(tmp_path, files={"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )
    installer = _installer(tmp_path)

    result = installer.apply(plan)
    reloaded = ManifestStore(tmp_path / "data")

    assert result.ok
    assert len(reloaded.list_installs()) == 1
    assert reloaded.list_installs()[0].install_id == result.record.install_id
    assert reloaded.list_installs()[0].deployed_files[0].target_path == paths.mods_paks / "Mod_P.pak"


def test_blocked_plan_is_refused(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source_folder(tmp_path, files={"Subnautica2/Config/Game.ini": b"cfg"})
    component = LibraryComponent(
        component_id="loose",
        source_id=source.source_id,
        display_name="Loose",
        component_type=COMPONENT_LOOSE_OVERLAY,
        install_kind=INSTALL_KIND_LOOSE_OVERLAY,
        files=[_file("Subnautica2/Config/Game.ini", "Subnautica2/Config/Game.ini")],
    )
    plan = build_deployment_plan(
        _profile(["loose"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )

    result = _installer(tmp_path).apply(plan)

    assert not result.ok
    assert result.record.status == STATUS_REFUSED
    assert not (paths.client_root / "Subnautica2" / "Config" / "Game.ini").exists()


def test_missing_source_refuses_without_writes(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source_folder(tmp_path, files={"Other/Other_P.pak": b"other"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )

    result = _installer(tmp_path).apply(plan)

    assert not result.ok
    assert result.record.status == STATUS_REFUSED
    assert not (paths.mods_paks / "Mod_P.pak").exists()


def test_partial_failure_manifest_records_previous_success(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source_archive(tmp_path, {"Good/Good_P.pak": b"good"})
    component = _component(
        "pak",
        source.source_id,
        [
            _file("Good/Good_P.pak", "Good_P.pak"),
            _file("Missing/Missing_P.pak", "Missing_P.pak"),
        ],
    )
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )

    result = _installer(tmp_path).apply(plan)
    reloaded = ManifestStore(tmp_path / "data").list_installs()[0]

    assert not result.ok
    assert result.record.status == STATUS_FAILED
    assert (paths.mods_paks / "Good_P.pak").read_bytes() == b"good"
    assert len(reloaded.deployed_files) == 1
    assert reloaded.errors


def test_no_writes_when_allow_real_apply_is_false_for_non_test_install(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    source = _source_folder(tmp_path, files={"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )

    result = _installer(tmp_path).apply(plan, allow_real_apply=False)

    assert not result.ok
    assert result.record.status == STATUS_REFUSED
    assert not (paths.mods_paks / "Mod_P.pak").exists()


def test_allow_real_apply_can_write_non_test_install(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    source = _source_folder(tmp_path, files={"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
    )

    result = _installer(tmp_path).apply(plan, allow_real_apply=True)

    assert result.ok
    assert (paths.mods_paks / "Mod_P.pak").read_bytes() == b"new"


def test_dry_run_plan_is_refused(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source_folder(tmp_path, files={"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(_profile(["pak"]), sources=[source], components=[component], paths=paths)

    result = _installer(tmp_path).apply(plan)

    assert not result.ok
    assert result.record.status == STATUS_REFUSED
    assert not (paths.mods_paks / "Mod_P.pak").exists()


def test_installer_writes_generated_ue4ss_activation_files(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source_folder(tmp_path, files={"HUD/Scripts/main.lua": b"print('hud')"})
    component = LibraryComponent(
        component_id="hud",
        source_id=source.source_id,
        display_name="HUD",
        component_type=COMPONENT_UE4SS_MOD,
        install_kind=INSTALL_KIND_UE4SS_MOD,
        files=[_file("HUD/Scripts/main.lua", "HUD/Scripts/main.lua")],
    )
    plan = build_deployment_plan(
        _profile(["hud"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
        ue4ss_activation_policy={"ue4ss_write_enabled_txt": True, "ue4ss_write_mods_txt": True},
    )

    result = _installer(tmp_path).apply(plan)

    assert result.ok
    assert (paths.ue4ss_mods / "HUD" / "Scripts" / "main.lua").read_bytes() == b"print('hud')"
    assert (paths.ue4ss_mods / "HUD" / "enabled.txt").read_text(encoding="utf-8") == ""
    assert "HUD : 1" in (paths.ue4ss_mods / "mods.txt").read_text(encoding="utf-8")
    assert any(record.source_member.startswith("generated:") for record in result.record.deployed_files)


def test_installer_deletes_disabled_ue4ss_enabled_marker_with_backup(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    marker = paths.ue4ss_mods / "HUD" / "enabled.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("old", encoding="utf-8")
    source = _source_folder(tmp_path, files={"HUD/Scripts/main.lua": b"print('hud')"})
    component = LibraryComponent(
        component_id="hud",
        source_id=source.source_id,
        display_name="HUD",
        component_type=COMPONENT_UE4SS_MOD,
        install_kind=INSTALL_KIND_UE4SS_MOD,
        files=[_file("HUD/Scripts/main.lua", "HUD/Scripts/main.lua")],
    )
    profile = ModProfile(
        profile_id="profile_test",
        name="Test Profile",
        entries=[LoadoutEntry(component_id="hud", display_name="HUD", enabled=False, order=0)],
    )
    plan = build_deployment_plan(
        profile,
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
        ue4ss_activation_policy={"ue4ss_write_enabled_txt": True},
    )

    result = _installer(tmp_path).apply(plan)

    assert result.ok
    assert not marker.exists()
    assert result.record.deployed_files[0].action == ACTION_DELETE
    assert result.record.backups[0].backup_path.read_text(encoding="utf-8") == "old"


def _installer(tmp_path: Path) -> Installer:
    return Installer(
        manifest_store=ManifestStore(tmp_path / "data"),
        backup_store=BackupStore(tmp_path / "backups"),
    )


def _paths(tmp_path: Path, *, fake: bool) -> S2AppPaths:
    root = tmp_path / "Subnautica2Install"
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True)
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True)
    if fake:
        (root / ".s2mm_fake_install").write_text("test-only", encoding="utf-8")
    return S2AppPaths(client_root=root)


def _source_folder(tmp_path: Path, *, files: dict[str, bytes]) -> LibrarySource:
    managed = tmp_path / "data" / "library" / "sources" / "src_folder"
    for rel, data in files.items():
        path = managed / Path(*rel.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return LibrarySource(
        source_id="src_folder",
        source_kind="folder",
        display_name="Folder Source",
        original_path=tmp_path / "source",
        managed_path=managed,
        source_hash="folder_hash",
    )


def _source_archive(tmp_path: Path, members: dict[str, bytes]) -> LibrarySource:
    archive_path = tmp_path / "data" / "library" / "sources" / "src_archive.zip"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return LibrarySource(
        source_id="src_archive",
        source_kind="archive",
        display_name="Archive Source",
        original_path=tmp_path / "source.zip",
        managed_path=archive_path,
        source_hash="archive_hash",
    )


def _component(component_id: str, source_id: str, files: list[LibraryComponentFile]) -> LibraryComponent:
    return LibraryComponent(
        component_id=component_id,
        source_id=source_id,
        display_name="Pak Mod",
        component_type=COMPONENT_PAK_BUNDLE,
        install_kind=INSTALL_KIND_STANDARD,
        target_hint="",
        file_count=len(files),
        files=files,
    )


def _file(source_path: str, target_hint: str) -> LibraryComponentFile:
    return LibraryComponentFile(source_path=source_path, target_hint=target_hint, role="file", size=3)


def _profile(component_ids: list[str]) -> ModProfile:
    return ModProfile(
        profile_id="profile_test",
        name="Test Profile",
        entries=[
            LoadoutEntry(component_id=component_id, display_name=component_id, enabled=True, order=index)
            for index, component_id in enumerate(component_ids)
        ],
    )

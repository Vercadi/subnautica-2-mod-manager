from __future__ import annotations

from pathlib import Path

from s2_mod_manager.core.apply_workflow import apply_result_text, build_apply_preview
from s2_mod_manager.core.backup_store import BackupStore
from s2_mod_manager.core.deployment_planner import build_deployment_plan
from s2_mod_manager.core.installer import Installer
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.core.recovery_service import RecoveryService
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.archive_info import (
    COMPONENT_LOOSE_OVERLAY,
    COMPONENT_PAK_BUNDLE,
    INSTALL_KIND_LOOSE_OVERLAY,
    INSTALL_KIND_STANDARD,
)
from s2_mod_manager.models.library import LibraryComponent, LibraryComponentFile, LibrarySource
from s2_mod_manager.models.manifest import STATUS_COMPLETED, STATUS_REFUSED
from s2_mod_manager.models.profile import LoadoutEntry, ModProfile


def test_apply_preview_dry_run_real_install_stays_disabled(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    source = _source(tmp_path, {"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(_profile(["pak"]), sources=[source], components=[component], paths=paths)

    preview = build_apply_preview(plan)

    assert preview.dry_run
    assert not preview.allow_apply
    assert preview.apply_button_text == "Apply Disabled"
    assert "dry-run" in preview.disabled_reason
    assert preview.creates == 1


def test_apply_preview_real_install_execution_plan_allows_managed_apply(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    source = _source(tmp_path, {"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
        real_apply_enabled=True,
    )

    preview = build_apply_preview(plan)

    assert preview.allow_apply
    assert preview.apply_button_text == "Apply Profile"
    assert preview.mode_text == "managed apply enabled"


def test_apply_preview_blocked_plan_disables_apply(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source(tmp_path, {"Subnautica2/Config/Game.ini": b"cfg"})
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

    preview = build_apply_preview(plan)

    assert preview.blocked
    assert not preview.allow_apply
    assert preview.apply_button_text == "Apply Blocked"
    assert preview.actions[0].action == "blocked"
    assert preview.errors


def test_apply_preview_empty_profile_disables_apply(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    plan = build_deployment_plan(
        _profile([]),
        sources=[],
        components=[],
        paths=paths,
        dry_run=False,
        real_apply_enabled=True,
    )

    preview = build_apply_preview(plan)

    assert not preview.allow_apply
    assert preview.apply_button_text == "Apply Disabled"
    assert "No enabled imported components" in preview.disabled_reason


def test_fake_test_install_preview_allows_test_apply(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source(tmp_path, {"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
        real_apply_enabled=True,
    )

    preview = build_apply_preview(plan)

    assert preview.allow_apply
    assert preview.apply_button_text == "Apply To Test Install"
    assert preview.mode_text == "test apply enabled"


def test_fake_test_install_apply_refreshes_manifest_and_recovery_summary(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    source = _source(tmp_path, {"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(_profile(["pak"]), sources=[source], components=[component], paths=paths, dry_run=False)
    manifest = ManifestStore(tmp_path / "data")
    installer = Installer(manifest_store=manifest, backup_store=BackupStore(tmp_path / "backups"))

    result = installer.apply(plan)
    summary = RecoveryService(ManifestStore(tmp_path / "data")).summary()

    assert result.ok
    assert result.record.status == STATUS_COMPLETED
    assert (paths.mods_paks / "Mod_P.pak").read_bytes() == b"new"
    assert summary.install_count == 1
    assert summary.deployed_file_count == 1


def test_real_install_execution_plan_is_refused_without_writes(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    source = _source(tmp_path, {"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(_profile(["pak"]), sources=[source], components=[component], paths=paths, dry_run=False)

    result = Installer(
        manifest_store=ManifestStore(tmp_path / "data"),
        backup_store=BackupStore(tmp_path / "backups"),
    ).apply(plan, allow_real_apply=False)

    assert not result.ok
    assert result.record.status == STATUS_REFUSED
    assert "non-test install" in result.record.errors[0]
    assert not (paths.mods_paks / "Mod_P.pak").exists()


def test_warning_error_summary_text_includes_backups_and_errors(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    target = paths.mods_paks / "Mod_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"old")
    source = _source(tmp_path, {"Mod/Mod_P.pak": b"new"})
    component = _component("pak", source.source_id, [_file("Mod/Mod_P.pak", "Mod_P.pak")])
    plan = build_deployment_plan(_profile(["pak", "missing"]), sources=[source], components=[component], paths=paths, dry_run=False)

    preview = build_apply_preview(plan)

    assert preview.overwrites == 1
    assert preview.backup_count == 1
    assert preview.errors
    assert "1 backup(s)" in preview.summary_text
    assert "1 error(s)" in preview.summary_text


def test_apply_result_text_reports_refusal_details() -> None:
    text = apply_result_text(False, STATUS_REFUSED, 0, 0, ["Refusing to apply a dry-run deployment plan."])

    assert "Apply refused/failed" in text
    assert "status=refused" in text
    assert "dry-run" in text


def _paths(tmp_path: Path, *, fake: bool) -> S2AppPaths:
    root = tmp_path / "Subnautica2Install"
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True)
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True)
    if fake:
        (root / ".s2mm_fake_install").write_text("test-only", encoding="utf-8")
    return S2AppPaths(client_root=root)


def _source(tmp_path: Path, files: dict[str, bytes]) -> LibrarySource:
    managed = tmp_path / "data" / "library" / "sources" / "src_test"
    for rel, data in files.items():
        path = managed / Path(*rel.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return LibrarySource(
        source_id="src_test",
        source_kind="folder",
        display_name="Source",
        original_path=tmp_path / "source",
        managed_path=managed,
        source_hash="hash",
    )


def _component(component_id: str, source_id: str, files: list[LibraryComponentFile]) -> LibraryComponent:
    return LibraryComponent(
        component_id=component_id,
        source_id=source_id,
        display_name="Pak Mod",
        component_type=COMPONENT_PAK_BUNDLE,
        install_kind=INSTALL_KIND_STANDARD,
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

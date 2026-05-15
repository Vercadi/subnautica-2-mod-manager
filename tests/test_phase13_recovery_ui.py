from __future__ import annotations

from pathlib import Path

from s2_mod_manager.core.backup_store import BackupStore
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.core.recovery_service import RecoveryService
from s2_mod_manager.core.recovery_workflow import (
    build_recovery_view,
    can_execute_recovery_action,
    restore_preview_text,
    uninstall_result_text,
)
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.deployment import ACTION_CREATE, ACTION_OVERWRITE
from s2_mod_manager.models.manifest import (
    STATUS_COMPLETED,
    STATUS_UNINSTALLED,
    BackupRecord,
    DeployedFileRecord,
    InstallRecord,
)


def test_recovery_view_model_summarizes_install_records(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"managed")
    store = ManifestStore(tmp_path / "data")
    record = _record("install_1", paths.client_root, [target])
    record.warnings.append("warning")
    record.errors.append("error")
    store.add_or_update(record)

    view = build_recovery_view(store, paths)

    assert len(view.records) == 1
    assert "Profile [completed]" in view.records[0].summary_text
    assert "1 deployed" in view.records[0].summary_text
    assert view.summary.install_count == 1


def test_real_install_recovery_actions_are_manifest_limited_and_allowed(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=False)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"managed")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_real", paths.client_root, [target]))

    view = build_recovery_view(store, paths)
    allowed, reason = can_execute_recovery_action(view, ["install_real"])

    assert view.action_state.allow_uninstall_selected
    assert allowed
    assert reason == ""


def test_fake_install_selected_and_all_action_state_is_enabled(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"managed")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_fake", paths.client_root, [target]))

    view = build_recovery_view(store, paths)
    allowed, reason = can_execute_recovery_action(view, ["install_fake"])

    assert view.action_state.allow_uninstall_selected
    assert view.action_state.allow_uninstall_all
    assert allowed
    assert reason == ""


def test_fake_test_uninstall_execution_removes_manifest_file(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"managed")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_fake", paths.client_root, [target]))
    view = build_recovery_view(store, paths)
    allowed, _reason = can_execute_recovery_action(view, ["install_fake"])

    result = RecoveryService(store, BackupStore(tmp_path / "backups")).uninstall_selected(["install_fake"])
    text = uninstall_result_text(result)

    assert allowed
    assert result.ok
    assert not target.exists()
    assert "1 removed" in text
    assert ManifestStore(tmp_path / "data").list_installs()[0].status == STATUS_UNINSTALLED


def test_backup_restore_preview_is_visible_in_record_summary(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"new")
    backup_path = tmp_path / "backups" / "installs" / "install_backup" / "bak_1" / "Managed_P.pak"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_bytes(b"old")
    backup = BackupRecord("bak_1", target, backup_path, "component")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_backup", paths.client_root, [target], action=ACTION_OVERWRITE, backup=backup))

    view = build_recovery_view(store, paths)

    assert view.records[0].backup_count == 1
    assert "1 backup" in view.records[0].summary_text


def test_unknown_files_are_reported_but_not_deleted(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    managed = paths.mods_paks / "Managed_P.pak"
    unknown = paths.mods_paks / "Unknown_P.pak"
    for path, data in ((managed, b"managed"), (unknown, b"unknown")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_managed", paths.client_root, [managed]))

    view = build_recovery_view(store, paths)
    text = restore_preview_text(view.restore_preview)

    assert unknown in view.restore_preview.unknown_files
    assert "Unknown files are not deleted" in text
    assert unknown.read_bytes() == b"unknown"


def test_recovery_preview_does_not_touch_saves(tmp_path: Path) -> None:
    paths = _paths(tmp_path, fake=True)
    managed = paths.mods_paks / "Managed_P.pak"
    save = paths.save_games / "slot0001" / "save.dat"
    managed.parent.mkdir(parents=True, exist_ok=True)
    save.parent.mkdir(parents=True, exist_ok=True)
    managed.write_bytes(b"managed")
    save.write_bytes(b"save")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_managed", paths.client_root, [managed]))

    view = build_recovery_view(store, paths)

    assert save not in view.restore_preview.managed_files
    assert save not in view.restore_preview.unknown_files
    assert save.read_bytes() == b"save"


def _paths(tmp_path: Path, *, fake: bool) -> S2AppPaths:
    root = tmp_path / "Subnautica2Install"
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True)
    (root / "Subnautica2" / "Binaries" / "Win64" / "ue4ss" / "Mods").mkdir(parents=True)
    (root / "Subnautica2" / "Saved" / "SaveGames").mkdir(parents=True)
    if fake:
        (root / ".s2mm_fake_install").write_text("test-only", encoding="utf-8")
    return S2AppPaths(client_root=root)


def _record(
    install_id: str,
    target_root: Path,
    targets: list[Path],
    *,
    action: str = ACTION_CREATE,
    backup: BackupRecord | None = None,
) -> InstallRecord:
    record = InstallRecord(
        install_id=install_id,
        profile_id="profile",
        profile_name="Profile",
        target_root=target_root,
        status=STATUS_COMPLETED,
    )
    for index, target in enumerate(targets):
        record.deployed_files.append(
            DeployedFileRecord(
                component_id="component",
                component_name="Component",
                source_path=None,
                source_member=f"source_{index}",
                target_path=target,
                action=action,
                backup_id=backup.backup_id if backup else "",
            )
        )
    if backup is not None:
        record.backups.append(backup)
    return record

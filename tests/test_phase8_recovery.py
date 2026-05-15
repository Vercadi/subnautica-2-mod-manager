from __future__ import annotations

from pathlib import Path

from s2_mod_manager.core.backup_store import BackupStore
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.core.recovery_service import RecoveryService
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.deployment import ACTION_CREATE, ACTION_OVERWRITE
from s2_mod_manager.models.manifest import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_REFUSED,
    STATUS_UNINSTALLED,
    BackupRecord,
    DeployedFileRecord,
    InstallRecord,
)


def test_selected_uninstall_removes_manifest_tracked_file(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"managed")
    other_target = paths.mods_paks / "Other_P.pak"
    other_target.write_bytes(b"other")
    store = ManifestStore(tmp_path / "data")
    selected = _record("install_selected", paths.client_root, [target])
    other = _record("install_other", paths.client_root, [other_target])
    store.add_or_update(selected)
    store.add_or_update(other)

    result = RecoveryService(store).uninstall_selected(["install_selected"])
    reloaded = {record.install_id: record for record in ManifestStore(tmp_path / "data").list_installs()}

    assert result.ok
    assert target in result.removed_files
    assert not target.exists()
    assert other_target.exists()
    assert reloaded["install_selected"].status == STATUS_UNINSTALLED
    assert reloaded["install_other"].status == STATUS_COMPLETED


def test_uninstall_all_removes_all_managed_files(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    first = paths.mods_paks / "First_P.pak"
    second = paths.ue4ss_mods / "Hud" / "Scripts" / "main.lua"
    first.parent.mkdir(parents=True, exist_ok=True)
    second.parent.mkdir(parents=True, exist_ok=True)
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_first", paths.client_root, [first]))
    store.add_or_update(_record("install_second", paths.client_root, [second]))

    result = RecoveryService(store).uninstall_all()

    assert result.ok
    assert not first.exists()
    assert not second.exists()
    assert {record.status for record in ManifestStore(tmp_path / "data").list_installs()} == {STATUS_UNINSTALLED}


def test_uninstall_all_skips_records_without_deployed_files(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"managed")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_real", paths.client_root, [target]))
    refused = _record("install_refused", paths.client_root, [], status=STATUS_REFUSED)
    store.add_or_update(refused)

    result = RecoveryService(store).uninstall_all()
    reloaded = {record.install_id: record for record in ManifestStore(tmp_path / "data").list_installs()}

    assert result.install_ids == ["install_real"]
    assert not target.exists()
    assert reloaded["install_real"].status == STATUS_UNINSTALLED
    assert reloaded["install_refused"].status == STATUS_REFUSED


def test_uninstall_restores_overwritten_backup(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    target = paths.mods_paks / "Managed_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"new")
    backup_path = tmp_path / "backups" / "installs" / "install_backup" / "bak_1" / "Managed_P.pak"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_bytes(b"old")
    backup = BackupRecord("bak_1", target, backup_path, "component")
    record = _record("install_backup", paths.client_root, [target], action=ACTION_OVERWRITE, backup=backup)
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(record)

    result = RecoveryService(store, BackupStore(tmp_path / "backups")).uninstall_selected(["install_backup"])

    assert result.ok
    assert target in result.restored_files
    assert target.read_bytes() == b"old"


def test_missing_deployed_files_are_tolerated(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    missing = paths.mods_paks / "Missing_P.pak"
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_missing", paths.client_root, [missing]))

    result = RecoveryService(store).uninstall_selected(["install_missing"])

    assert result.ok
    assert missing in result.missing_files
    assert ManifestStore(tmp_path / "data").list_installs()[0].status == STATUS_UNINSTALLED


def test_unknown_files_are_untouched_by_uninstall(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    managed = paths.mods_paks / "Managed_P.pak"
    unknown = paths.mods_paks / "Unknown_P.pak"
    managed.parent.mkdir(parents=True, exist_ok=True)
    managed.write_bytes(b"managed")
    unknown.write_bytes(b"unknown")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_managed", paths.client_root, [managed]))

    result = RecoveryService(store).uninstall_all()

    assert result.ok
    assert not managed.exists()
    assert unknown.read_bytes() == b"unknown"


def test_restore_vanilla_preview_reports_managed_and_unknown_without_deleting(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    managed = paths.mods_paks / "Managed_P.pak"
    unknown_pak = paths.mods_paks / "Unknown_P.pak"
    unknown_ue4ss = paths.ue4ss_mods / "Unknown" / "enabled.txt"
    save = paths.save_games / "slot0001" / "save.dat"
    for path, content in (
        (managed, b"managed"),
        (unknown_pak, b"unknown_pak"),
        (unknown_ue4ss, b"unknown_ue4ss"),
        (save, b"save"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_managed", paths.client_root, [managed]))

    preview = RecoveryService(store).restore_vanilla_preview(paths)

    assert managed in preview.managed_files
    assert set(preview.unknown_files) == {unknown_pak, unknown_ue4ss}
    assert [item.path for item in preview.quarantine_candidates] == [unknown_pak, unknown_ue4ss]
    assert preview.save_paths_checked == []
    assert save.read_bytes() == b"save"
    assert unknown_pak.exists()
    assert unknown_ue4ss.exists()


def test_failed_partial_install_is_uninstallable(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    deployed = paths.mods_paks / "Good_P.pak"
    missing = paths.mods_paks / "Missing_P.pak"
    deployed.parent.mkdir(parents=True, exist_ok=True)
    deployed.write_bytes(b"good")
    record = _record("install_failed", paths.client_root, [deployed, missing], status=STATUS_FAILED)
    record.errors.append("second file failed")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(record)

    result = RecoveryService(store).uninstall_selected(["install_failed"])

    assert result.ok
    assert not deployed.exists()
    assert missing in result.missing_files
    assert ManifestStore(tmp_path / "data").list_installs()[0].status == STATUS_UNINSTALLED


def test_no_save_deletion(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    managed = paths.mods_paks / "Managed_P.pak"
    save = paths.save_games / "slot0001" / "save.dat"
    managed.parent.mkdir(parents=True, exist_ok=True)
    save.parent.mkdir(parents=True, exist_ok=True)
    managed.write_bytes(b"managed")
    save.write_bytes(b"save")
    store = ManifestStore(tmp_path / "data")
    store.add_or_update(_record("install_managed", paths.client_root, [managed]))

    RecoveryService(store).uninstall_all()
    preview = RecoveryService(ManifestStore(tmp_path / "data")).restore_vanilla_preview(paths)

    assert save.read_bytes() == b"save"
    assert save not in preview.unknown_files
    assert save not in preview.managed_files


def test_recovery_summary_counts_manifest_records(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    store = ManifestStore(tmp_path / "data")
    completed = _record("install_completed", paths.client_root, [paths.mods_paks / "A.pak"], status=STATUS_COMPLETED)
    failed = _record("install_failed", paths.client_root, [paths.mods_paks / "B.pak"], status=STATUS_FAILED)
    backup = BackupRecord("bak_1", paths.mods_paks / "C.pak", tmp_path / "backup" / "C.pak", "component")
    completed.backups.append(backup)
    store.add_or_update(completed)
    store.add_or_update(failed)

    summary = RecoveryService(store).summary()

    assert summary.install_count == 2
    assert summary.deployed_file_count == 2
    assert summary.backup_count == 1
    assert summary.completed_count == 1
    assert summary.failed_count == 1
    assert "2 install record" in summary.text


def _paths(tmp_path: Path) -> S2AppPaths:
    root = tmp_path / "Subnautica2Install"
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True)
    (root / "Subnautica2" / "Binaries" / "Win64" / "ue4ss" / "Mods").mkdir(parents=True)
    (root / "Subnautica2" / "Saved" / "SaveGames").mkdir(parents=True)
    return S2AppPaths(client_root=root)


def _record(
    install_id: str,
    target_root: Path,
    targets: list[Path],
    *,
    action: str = ACTION_CREATE,
    backup: BackupRecord | None = None,
    status: str = STATUS_COMPLETED,
) -> InstallRecord:
    record = InstallRecord(
        install_id=install_id,
        profile_id="profile",
        profile_name="Profile",
        target_root=target_root,
        status=status,
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

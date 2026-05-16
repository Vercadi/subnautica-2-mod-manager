from __future__ import annotations

from ..models.app_paths import S2AppPaths
from ..models.manifest import InstallRecord
from ..models.recovery import RecoverySummary, RestoreVanillaPreview, UninstallResult
from ..models.recovery_view import RecoveryActionState, RecoveryRecordView, RecoveryView
from .manifest_store import ManifestStore
from .recovery_service import RecoveryService


def build_recovery_view(
    manifest_store: ManifestStore,
    paths: S2AppPaths,
    *,
    recovery_service: RecoveryService | None = None,
) -> RecoveryView:
    service = recovery_service or RecoveryService(manifest_store)
    records = [_record_view(record) for record in manifest_store.list_installs()]
    summary = service.summary()
    restore_preview = service.restore_vanilla_preview(paths)
    uninstallable = [record for record in records if record.can_uninstall]
    action_state = _action_state(uninstallable_count=len(uninstallable))
    return RecoveryView(
        records=records,
        summary=summary,
        restore_preview=restore_preview,
        fake_test_install=False,
        action_state=action_state,
    )


def can_execute_recovery_action(view: RecoveryView, install_ids: list[str]) -> tuple[bool, str]:
    if not install_ids:
        return False, "No uninstallable managed install record is selected."
    blocked = sorted(set(install_ids) - set(view.uninstallable_install_ids))
    if blocked:
        return False, "Selected install record is not uninstallable: " + ", ".join(blocked)
    return True, ""


def uninstall_result_text(result: UninstallResult) -> str:
    status = "completed" if result.ok else "completed with errors"
    return (
        f"Uninstall {status}: {len(result.install_ids)} record(s), "
        f"{len(result.removed_files)} removed, {len(result.restored_files)} restored, "
        f"{len(result.missing_files)} missing, {len(result.errors)} error(s)."
    )


def restore_preview_text(preview: RestoreVanillaPreview) -> str:
    return (
        f"Restore vanilla preview only: {len(preview.managed_files)} managed file(s), "
        f"{len(preview.unknown_files)} unknown file(s), "
        f"{len(preview.quarantine_candidates)} quarantine candidate(s). Unknown files are not deleted."
    )


def _record_view(record: InstallRecord) -> RecoveryRecordView:
    active_files = [
        deployed
        for deployed in record.deployed_files
        if deployed.action != "delete" and deployed.target_path and deployed.target_path.exists()
    ]
    return RecoveryRecordView(
        install_id=record.install_id,
        status=record.status,
        profile_name=record.profile_name,
        target_root=record.target_root,
        deployed_file_count=len(active_files),
        backup_count=len(record.backups),
        warning_count=len(record.warnings),
        error_count=len(record.errors),
        warnings=list(record.warnings),
        errors=list(record.errors),
        selected=bool(record.deployed_files) and record.status != "uninstalled",
    )


def _action_state(*, uninstallable_count: int) -> RecoveryActionState:
    if uninstallable_count > 0:
        return RecoveryActionState(True, True)
    return RecoveryActionState(False, False, "No uninstallable managed install records were found.")

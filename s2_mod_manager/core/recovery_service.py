from __future__ import annotations

from pathlib import Path

from ..models.app_paths import S2AppPaths
from ..models.manifest import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_REFUSED,
    STATUS_UNINSTALLED,
    InstallRecord,
)
from ..models.recovery import (
    QuarantinePreviewItem,
    RecoverySummary,
    RestoreVanillaPreview,
    UninstallResult,
)
from .manifest_store import ManifestStore
from .backup_store import BackupStore


class RecoveryService:
    """Manifest-driven uninstall and recovery.

    This service removes or restores only paths recorded in install_manifest.json.
    Unknown files are reported by preview helpers but never deleted here.
    """

    def __init__(self, manifest_store: ManifestStore, backup_store: BackupStore | None = None):
        self.manifest_store = manifest_store
        self.backup_store = backup_store

    def summary(self) -> RecoverySummary:
        installs = self.manifest_store.list_installs()
        return RecoverySummary(
            install_count=len(installs),
            deployed_file_count=sum(len(record.deployed_files) for record in installs),
            backup_count=sum(len(record.backups) for record in installs),
            completed_count=sum(1 for record in installs if record.status == STATUS_COMPLETED),
            failed_count=sum(1 for record in installs if record.status == STATUS_FAILED),
            refused_count=sum(1 for record in installs if record.status == STATUS_REFUSED),
            uninstalled_count=sum(1 for record in installs if record.status == STATUS_UNINSTALLED),
        )

    def uninstall_selected(self, install_ids: list[str]) -> UninstallResult:
        selected = set(install_ids)
        result = UninstallResult(install_ids=list(install_ids))
        for record in self.manifest_store.list_installs():
            if record.install_id not in selected:
                continue
            self._uninstall_record(record, result)
        self.manifest_store.save()
        return result

    def uninstall_all(self) -> UninstallResult:
        ids = [
            record.install_id
            for record in self.manifest_store.list_installs()
            if record.deployed_files and record.status != STATUS_UNINSTALLED
        ]
        return self.uninstall_selected(ids)

    def restore_vanilla_preview(self, paths: S2AppPaths) -> RestoreVanillaPreview:
        managed = _manifest_targets(self.manifest_store.list_installs())
        roots = [path for path in (paths.mods_paks, paths.logic_mods, paths.ue4ss_mods) if path is not None]
        unknown: list[Path] = []
        for root in roots:
            if not root.is_dir():
                continue
            for file in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: str(item).casefold()):
                if file not in managed:
                    unknown.append(file)
        return RestoreVanillaPreview(
            managed_files=sorted(managed, key=lambda item: str(item).casefold()),
            unknown_files=unknown,
            quarantine_candidates=[QuarantinePreviewItem(path) for path in unknown],
            save_paths_checked=[],
        )

    def _uninstall_record(self, record: InstallRecord, result: UninstallResult) -> None:
        backups_by_id = {backup.backup_id: backup for backup in record.backups if backup.backup_id}
        for deployed in reversed(record.deployed_files):
            target = deployed.target_path
            backup = backups_by_id.get(deployed.backup_id)
            try:
                if backup is not None and backup.backup_path.is_file():
                    if self.backup_store is not None:
                        restored = self.backup_store.restore_backup(backup)
                    else:
                        import shutil

                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup.backup_path, target)
                        restored = target
                    result.restored_files.append(restored)
                    continue
                if target.exists():
                    target.unlink()
                    result.removed_files.append(target)
                else:
                    result.missing_files.append(target)
            except OSError as exc:
                result.errors.append(f"{target}: {exc}")
        record.status = STATUS_UNINSTALLED
        record.finished_at = record.finished_at or record.started_at
        self.manifest_store.add_or_update(record)


def _manifest_targets(records: list[InstallRecord]) -> set[Path]:
    targets: set[Path] = set()
    for record in records:
        if record.status == STATUS_UNINSTALLED:
            continue
        for deployed in record.deployed_files:
            if deployed.target_path and deployed.target_path.exists():
                targets.add(deployed.target_path)
    return targets

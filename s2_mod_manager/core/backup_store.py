from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from ..models.manifest import BackupRecord


class BackupStore:
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir / "installs"

    def backup_existing(self, target: Path, *, install_id: str, component_id: str, target_root: Path | None) -> BackupRecord | None:
        if not target.exists():
            return None
        backup_id = f"bak_{uuid.uuid4().hex[:12]}"
        relative = _relative_target(target, target_root)
        backup_path = self.backup_dir / install_id / backup_id / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_path)
        return BackupRecord(
            backup_id=backup_id,
            original_path=target,
            backup_path=backup_path,
            component_id=component_id,
        )

    def restore_backup(self, backup: BackupRecord) -> Path:
        if not backup.backup_path.is_file():
            raise FileNotFoundError(f"Backup file not found: {backup.backup_path}")
        backup.original_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup.backup_path, backup.original_path)
        return backup.original_path


def _relative_target(target: Path, target_root: Path | None) -> Path:
    if target_root is not None:
        try:
            return target.resolve().relative_to(target_root.resolve())
        except ValueError:
            pass
    safe_parts = [part.replace(":", "") for part in target.parts if part not in {target.anchor, "\\"}]
    return Path(*safe_parts[-8:]) if safe_parts else Path(target.name)

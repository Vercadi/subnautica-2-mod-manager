from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RecoverySummary:
    install_count: int = 0
    deployed_file_count: int = 0
    backup_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    refused_count: int = 0
    uninstalled_count: int = 0

    @property
    def text(self) -> str:
        return (
            f"Recovery: {self.install_count} install record(s), "
            f"{self.deployed_file_count} deployed file(s), "
            f"{self.backup_count} backup(s), "
            f"{self.completed_count} completed, {self.failed_count} failed, "
            f"{self.refused_count} refused, {self.uninstalled_count} uninstalled."
        )


@dataclass
class UninstallResult:
    install_ids: list[str] = field(default_factory=list)
    removed_files: list[Path] = field(default_factory=list)
    restored_files: list[Path] = field(default_factory=list)
    missing_files: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class QuarantinePreviewItem:
    path: Path
    reason: str = "unknown unmanaged file"


@dataclass(frozen=True)
class RestoreVanillaPreview:
    managed_files: list[Path] = field(default_factory=list)
    unknown_files: list[Path] = field(default_factory=list)
    quarantine_candidates: list[QuarantinePreviewItem] = field(default_factory=list)
    save_paths_checked: list[Path] = field(default_factory=list)

    @property
    def text(self) -> str:
        return (
            f"Restore vanilla preview: {len(self.managed_files)} managed file(s), "
            f"{len(self.unknown_files)} unknown file(s), "
            f"{len(self.quarantine_candidates)} quarantine candidate(s)."
        )

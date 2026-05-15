from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .recovery import RecoverySummary, RestoreVanillaPreview


@dataclass(frozen=True)
class RecoveryRecordView:
    install_id: str
    status: str
    profile_name: str
    target_root: Path | None
    deployed_file_count: int = 0
    backup_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    selected: bool = True

    @property
    def summary_text(self) -> str:
        return (
            f"{self.profile_name} [{self.status}]: "
            f"{self.deployed_file_count} deployed, {self.backup_count} backup(s), "
            f"{self.warning_count} warning(s), {self.error_count} error(s)"
        )

    @property
    def can_uninstall(self) -> bool:
        return self.deployed_file_count > 0 and self.status != "uninstalled"


@dataclass(frozen=True)
class RecoveryActionState:
    allow_uninstall_selected: bool
    allow_uninstall_all: bool
    disabled_reason: str = ""


@dataclass(frozen=True)
class RecoveryView:
    records: list[RecoveryRecordView] = field(default_factory=list)
    summary: RecoverySummary = field(default_factory=RecoverySummary)
    restore_preview: RestoreVanillaPreview = field(default_factory=RestoreVanillaPreview)
    fake_test_install: bool = False
    action_state: RecoveryActionState = field(default_factory=lambda: RecoveryActionState(False, False))

    @property
    def selected_install_ids(self) -> list[str]:
        return [record.install_id for record in self.records if record.selected and record.can_uninstall]

    @property
    def uninstallable_install_ids(self) -> list[str]:
        return [record.install_id for record in self.records if record.can_uninstall]

    @property
    def summary_text(self) -> str:
        return (
            f"{self.summary.text} Restore preview: "
            f"{len(self.restore_preview.managed_files)} managed, "
            f"{len(self.restore_preview.unknown_files)} unknown, "
            f"{len(self.restore_preview.quarantine_candidates)} quarantine candidate(s)."
        )

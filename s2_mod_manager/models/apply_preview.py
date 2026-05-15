from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ApplyActionPreview:
    component_name: str
    action: str
    source: str
    target: str
    reason: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ApplySkipPreview:
    component_name: str
    reason: str


@dataclass(frozen=True)
class ApplyPreview:
    profile_name: str
    target_root: Path | None
    dry_run: bool
    real_apply_enabled: bool
    fake_test_install: bool
    allow_apply: bool
    disabled_reason: str
    blocked: bool
    creates: int
    overwrites: int
    skips: int
    deletes: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    review_required_count: int = 0
    review_policy_text: str = ""
    actions: list[ApplyActionPreview] = field(default_factory=list)
    skip_items: list[ApplySkipPreview] = field(default_factory=list)

    @property
    def backup_count(self) -> int:
        return self.overwrites + self.deletes

    @property
    def mode_text(self) -> str:
        if self.allow_apply:
            return "test apply enabled" if self.fake_test_install else "managed apply enabled"
        if self.dry_run:
            return "dry-run preview"
        return "apply refused"

    @property
    def blocked_text(self) -> str:
        return "blocked" if self.blocked else "ready"

    @property
    def summary_text(self) -> str:
        return (
            f"{self.profile_name}: {self.creates} create(s), {self.overwrites} overwrite(s), "
            f"{self.deletes} delete(s), "
            f"{self.skips} skip(s), {len(self.warnings)} warning(s), {len(self.errors)} error(s), "
            f"{self.backup_count} backup(s) - {self.blocked_text}"
        )

    @property
    def apply_button_text(self) -> str:
        if self.allow_apply:
            return "Apply To Test Install" if self.fake_test_install else "Apply Profile"
        if self.blocked:
            return "Apply Blocked"
        return "Apply Disabled"

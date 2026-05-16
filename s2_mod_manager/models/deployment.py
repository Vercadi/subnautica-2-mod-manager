from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


ACTION_CREATE = "create"
ACTION_OVERWRITE = "overwrite"
ACTION_SKIP = "skip"
ACTION_BLOCKED = "blocked"
ACTION_DELETE = "delete"


@dataclass(frozen=True)
class DeploymentFileAction:
    component_id: str
    component_name: str
    source_path: Path | None
    source_member: str
    target_path: Path | None
    action: str
    reason: str = ""
    warnings: list[str] = field(default_factory=list)
    generated_content: str = ""

    @property
    def target_display(self) -> str:
        return str(self.target_path) if self.target_path else "n/a"

    @property
    def source_display(self) -> str:
        if self.generated_content or (self.source_path is None and self.source_member.startswith("generated:")):
            return self.source_member or "generated"
        if self.source_path is None:
            return self.source_member or "n/a"
        if self.source_member:
            return f"{self.source_path} :: {self.source_member}"
        return str(self.source_path)


@dataclass(frozen=True)
class DeploymentSkip:
    component_id: str
    component_name: str
    reason: str


@dataclass
class DeploymentPlan:
    profile_id: str
    profile_name: str
    target_root: Path | None
    dry_run: bool = True
    real_apply_enabled: bool = False
    actions: list[DeploymentFileAction] = field(default_factory=list)
    skips: list[DeploymentSkip] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return bool(self.errors) or any(action.action == ACTION_BLOCKED for action in self.actions)

    @property
    def creates(self) -> list[DeploymentFileAction]:
        return [action for action in self.actions if action.action == ACTION_CREATE]

    @property
    def overwrites(self) -> list[DeploymentFileAction]:
        return [action for action in self.actions if action.action == ACTION_OVERWRITE]

    @property
    def deletes(self) -> list[DeploymentFileAction]:
        return [action for action in self.actions if action.action == ACTION_DELETE]

    @property
    def blocked_actions(self) -> list[DeploymentFileAction]:
        return [action for action in self.actions if action.action == ACTION_BLOCKED]

    @property
    def summary_text(self) -> str:
        state = "blocked" if self.blocked else "ready"
        return (
            f"{self.profile_name}: {len(self.creates)} install(s), "
            f"{len(self.overwrites)} overwrite(s), {len(self.deletes)} remove(s), {len(self.skips)} skip(s), "
            f"{len(self.warnings)} warning(s), {len(self.errors)} error(s) - {state}"
        )

    def preview_text(self, *, limit: int = 80) -> str:
        lines = [
            f"Deployment preview for {self.profile_name}",
            f"Mode: {'dry-run' if self.dry_run else 'apply'}",
            f"Real apply: {'enabled' if self.real_apply_enabled else 'disabled'}",
            "Apply guard: blocked/review-required actions are refused; writes are tracked in the manifest.",
            f"Target root: {self.target_root or 'not configured'}",
            "",
            self.summary_text,
        ]
        if self.errors:
            lines.append("")
            lines.append("Errors:")
            lines.extend(f"- {message}" for message in self.errors)
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(f"- {message}" for message in self.warnings)
        if self.skips:
            lines.append("")
            lines.append("Skipped:")
            lines.extend(f"- {skip.component_name}: {skip.reason}" for skip in self.skips)
        if self.actions:
            lines.append("")
            lines.append("Planned file actions:")
            for action in self.actions[:limit]:
                lines.append(f"- {action.action}: {action.source_display} -> {action.target_display}")
                if action.reason:
                    lines.append(f"  reason: {action.reason}")
                for warning in action.warnings:
                    lines.append(f"  warning: {warning}")
            if len(self.actions) > limit:
                lines.append(f"- ... {len(self.actions) - limit} more action(s)")
        if len(lines) == 6:
            lines.append("")
            lines.append("No profile changes need to be applied.")
        return "\n".join(lines)

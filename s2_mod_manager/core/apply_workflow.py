from __future__ import annotations

from ..models.apply_preview import ApplyActionPreview, ApplyPreview, ApplySkipPreview
from ..models.deployment import ACTION_BLOCKED
from ..models.deployment import DeploymentPlan
from .installer import is_fake_test_install
from .review_policy import loose_overlay_policy


def build_apply_preview(plan: DeploymentPlan) -> ApplyPreview:
    fake = is_fake_test_install(plan.target_root)
    has_executable_actions = bool(plan.creates or plan.overwrites or plan.deletes)
    allow_apply = bool(plan.real_apply_enabled) and not plan.dry_run and has_executable_actions and not _has_blocking_errors(plan)
    disabled_reason = _disabled_reason(plan, fake=fake, allow_apply=allow_apply)
    blocked_actions = [action for action in plan.actions if action.action == ACTION_BLOCKED]
    review_policy = loose_overlay_policy(target_hints=[action.target_display for action in blocked_actions]) if blocked_actions else None
    return ApplyPreview(
        profile_name=plan.profile_name,
        target_root=plan.target_root,
        dry_run=plan.dry_run,
        real_apply_enabled=plan.real_apply_enabled,
        fake_test_install=fake,
        allow_apply=allow_apply,
        disabled_reason=disabled_reason,
        blocked=bool(blocked_actions or _has_blocking_errors(plan)),
        creates=len(plan.creates),
        overwrites=len(plan.overwrites),
        deletes=len(plan.deletes),
        skips=len(plan.skips),
        warnings=list(plan.warnings),
        errors=list(plan.errors),
        review_required_count=len(blocked_actions),
        review_policy_text=review_policy.text if review_policy else "",
        actions=[
            ApplyActionPreview(
                component_name=action.component_name,
                action=action.action,
                source=action.source_display,
                target=action.target_display,
                reason=action.reason,
                warnings=list(action.warnings),
            )
            for action in plan.actions
        ],
        skip_items=[
            ApplySkipPreview(component_name=skip.component_name, reason=skip.reason)
            for skip in plan.skips
        ],
    )


def apply_result_text(ok: bool, status: str, deployed_count: int, backup_count: int, errors: list[str]) -> str:
    prefix = "Apply completed" if ok else "Apply refused/failed"
    text = f"{prefix}: status={status}, deployed={deployed_count}, backups={backup_count}"
    if errors:
        text += ", errors=" + "; ".join(errors)
    return text


def _disabled_reason(plan: DeploymentPlan, *, fake: bool, allow_apply: bool) -> str:
    if allow_apply:
        return ""
    blocking_errors = _blocking_errors(plan)
    if blocking_errors:
        return "Plan has errors that must be fixed before install: " + "; ".join(blocking_errors[:3])
    if plan.blocked_actions:
        return (
            "Only review-required items are selected. manual review is needed for blocked loose overlays; "
            "select at least one supported mod, or remove the blocked item."
        )
    if plan.dry_run and fake:
        return "Preview is dry-run only; build an execution plan for the fake test install to apply."
    if plan.dry_run:
        return "Preview is dry-run only; click Apply to review and install changes."
    if not plan.real_apply_enabled:
        return "Apply is disabled for this plan."
    if not (plan.creates or plan.overwrites or plan.deletes):
        return "No profile changes need to be applied."
    return "Apply is not available for this plan."


def _has_blocking_errors(plan: DeploymentPlan) -> bool:
    return bool(_blocking_errors(plan))


def _blocking_errors(plan: DeploymentPlan) -> list[str]:
    return [error for error in plan.errors if not _is_review_only_error(error)]


def _is_review_only_error(error: str) -> bool:
    lowered = str(error or "").casefold()
    return "requires manual review before deployment" in lowered or "loose overlay" in lowered

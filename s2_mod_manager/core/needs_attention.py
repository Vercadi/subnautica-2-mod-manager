from __future__ import annotations

from ..models.app_paths import S2AppPaths
from ..models.archive_info import ScanResult
from ..models.deployment import DeploymentPlan
from ..models.library import LibraryComponent, LibrarySource
from ..models.needs_attention import AttentionItem, NeedsAttentionSummary
from ..models.recovery import RecoverySummary
from .archive_handler import archive_support_status
from .discovery import validate_client_root
from .profile_workflow import LoadoutWarning
from .review_policy import review_policy_for_component
from .update_checker import UpdateCheckResult


def build_needs_attention(
    *,
    paths: S2AppPaths,
    scans: list[ScanResult],
    library_sources: list[LibrarySource],
    library_components: list[LibraryComponent],
    loadout_warnings: list[LoadoutWarning],
    deployment_plan: DeploymentPlan | None,
    recovery_summary: RecoverySummary,
    update_result: UpdateCheckResult | None = None,
) -> NeedsAttentionSummary:
    items: list[AttentionItem] = []

    if not paths.client_root or not validate_client_root(paths.client_root):
        items.append(AttentionItem("S2 install", "Subnautica 2 install is missing or invalid.", "error"))

    for suffix, supported in sorted(archive_support_status().items()):
        if not supported and suffix in {".7z", ".rar"}:
            items.append(AttentionItem("Archive support", f"{suffix} support is unavailable.", "warning"))

    for scan in scans:
        if scan.errors:
            items.append(AttentionItem("Inbox scan", f"{scan.display_name}: {'; '.join(scan.errors[:2])}", "error"))
        warnings = list(scan.warnings) + [f"Unsafe path rejected: {path}" for path in scan.unsafe_entries]
        if warnings:
            items.append(AttentionItem("Inbox scan", f"{scan.display_name}: {'; '.join(warnings[:2])}", "warning"))
        if scan.ambiguous:
            items.append(AttentionItem("Ambiguous source", f"{scan.display_name} has multiple components and needs review.", "warning"))

    source_ids = {source.source_id for source in library_sources}
    for component in library_components:
        if component.source_id not in source_ids:
            items.append(AttentionItem("Library source", f"{component.display_name} references a missing library source.", "error"))
        policy = review_policy_for_component(component)
        if policy is not None:
            items.append(AttentionItem("Review required", f"{component.display_name}: {policy.title}.", "warning"))
        for warning in component.warnings[:2]:
            items.append(AttentionItem("Library warning", f"{component.display_name}: {warning}", "warning"))

    for warning in loadout_warnings:
        items.append(AttentionItem("Profile", warning.message, warning.severity))

    if deployment_plan is not None:
        for error in deployment_plan.errors[:4]:
            items.append(AttentionItem("Apply preview", error, "error"))
        for warning in deployment_plan.warnings[:4]:
            items.append(AttentionItem("Apply preview", warning, "warning"))
        if deployment_plan.blocked:
            items.append(AttentionItem("Apply blocked", "The active profile has blocked or review-required actions.", "warning"))

    if recovery_summary.failed_count:
        items.append(AttentionItem("Recovery", f"{recovery_summary.failed_count} failed install record(s) need review.", "warning"))

    if update_result is not None and update_result.update_available:
        items.append(AttentionItem("App update", update_result.message, "info"))
    elif update_result is not None and update_result.status == "error":
        items.append(AttentionItem("Update check", update_result.message, "warning"))

    return NeedsAttentionSummary(_dedupe(items))


def _dedupe(items: list[AttentionItem]) -> list[AttentionItem]:
    seen: set[tuple[str, str, str]] = set()
    output: list[AttentionItem] = []
    for item in items:
        key = (item.title, item.detail, item.severity)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output

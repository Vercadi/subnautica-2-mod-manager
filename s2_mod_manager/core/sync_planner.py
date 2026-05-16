from __future__ import annotations

from pathlib import Path

from ..models.app_paths import S2AppPaths
from ..models.deployment import (
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_OVERWRITE,
    DeploymentFileAction,
    DeploymentPlan,
    DeploymentSkip,
)
from ..models.library import LibraryComponent, LibrarySource
from ..models.manifest import STATUS_UNINSTALLED, InstallRecord
from ..models.profile import ModProfile
from .deployment_planner import build_deployment_plan


SYNC_DELETE_SOURCE_MEMBER_PREFIX = "managed:remove:"


def build_sync_deployment_plan(
    profile: ModProfile,
    *,
    sources: list[LibrarySource],
    components: list[LibraryComponent],
    paths: S2AppPaths,
    installed_records: list[InstallRecord],
    ue4ss_runtime_installed: bool = False,
    dry_run: bool = True,
    real_apply_enabled: bool = False,
    ue4ss_activation_policy: dict[str, bool] | None = None,
) -> DeploymentPlan:
    """Build an apply plan that makes the game match the active profile.

    The base deployment planner knows how to install enabled profile entries.
    This sync layer adds the inverse side of the operation: manager-installed
    files that are no longer desired are planned for removal. It only considers
    files recorded in install_manifest.json and never plans removal for unknown
    or manually installed files.
    """

    plan = build_deployment_plan(
        profile,
        sources=sources,
        components=components,
        paths=paths,
        ue4ss_runtime_installed=ue4ss_runtime_installed,
        dry_run=dry_run,
        real_apply_enabled=real_apply_enabled,
        ue4ss_activation_policy=ue4ss_activation_policy,
    )
    current = _current_managed_files(installed_records)
    desired_component_ids = {
        entry.component_id
        for entry in profile.ordered_entries()
        if entry.enabled
    }

    desired_targets: set[Path] = set()
    filtered_actions: list[DeploymentFileAction] = []
    for action in plan.actions:
        if _is_already_installed_desired_action(action, current, desired_component_ids):
            desired_targets.add(action.target_path)  # type: ignore[arg-type]
            plan.skips.append(
                DeploymentSkip(
                    action.component_id,
                    action.component_name,
                    "already installed by manager",
                )
            )
            continue
        filtered_actions.append(action)
        if action.action in {ACTION_CREATE, ACTION_OVERWRITE} and action.target_path is not None:
            desired_targets.add(action.target_path)
    plan.actions = filtered_actions

    for component_id in desired_component_ids:
        for deployed in current.by_component.get(component_id, []):
            if deployed.target_path.exists():
                desired_targets.add(deployed.target_path)

    for record in installed_records:
        if record.status == STATUS_UNINSTALLED:
            continue
        for deployed in record.deployed_files:
            if deployed.action == ACTION_DELETE:
                continue
            target = deployed.target_path
            if not target or not target.exists() or target in desired_targets:
                continue
            plan.actions.append(
                DeploymentFileAction(
                    component_id=deployed.component_id,
                    component_name=deployed.component_name,
                    source_path=None,
                    source_member=f"{SYNC_DELETE_SOURCE_MEMBER_PREFIX}{record.install_id}:{deployed.source_member}",
                    target_path=target,
                    action=ACTION_DELETE,
                    reason="remove manager-installed file not in the active profile",
                    warnings=[
                        "Only this manager-tracked file will be removed. Unknown/manual files are left alone."
                    ],
                )
            )
    return plan


def is_sync_delete_action(action: DeploymentFileAction) -> bool:
    return action.action == ACTION_DELETE and action.source_member.startswith(SYNC_DELETE_SOURCE_MEMBER_PREFIX)


class _CurrentManagedFiles:
    def __init__(self) -> None:
        self.by_component: dict[str, list] = {}
        self.targets_by_component: dict[str, set[Path]] = {}

    def add(self, deployed) -> None:
        self.by_component.setdefault(deployed.component_id, []).append(deployed)
        self.targets_by_component.setdefault(deployed.component_id, set()).add(deployed.target_path)


def _current_managed_files(records: list[InstallRecord]) -> _CurrentManagedFiles:
    current = _CurrentManagedFiles()
    for record in records:
        if record.status == STATUS_UNINSTALLED:
            continue
        for deployed in record.deployed_files:
            if deployed.action == ACTION_DELETE or not deployed.target_path:
                continue
            current.add(deployed)
    return current


def _is_already_installed_desired_action(
    action: DeploymentFileAction,
    current: _CurrentManagedFiles,
    desired_component_ids: set[str],
) -> bool:
    if action.action not in {ACTION_CREATE, ACTION_OVERWRITE}:
        return False
    if action.target_path is None:
        return False
    if action.source_member.startswith("generated:"):
        return _generated_target_is_current(action)
    if action.component_id not in desired_component_ids:
        return False
    return (
        action.target_path.exists()
        and action.target_path in current.targets_by_component.get(action.component_id, set())
    )


def _generated_target_is_current(action: DeploymentFileAction) -> bool:
    if action.target_path is None or not action.target_path.is_file():
        return False
    try:
        return action.target_path.read_text(encoding="utf-8", errors="replace") == action.generated_content
    except OSError:
        return False

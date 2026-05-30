from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath

from ..models.app_paths import S2AppPaths
from ..models.archive_info import (
    COMPONENT_LOOSE_OVERLAY,
    COMPONENT_MIXED,
    COMPONENT_PAK_BUNDLE,
    COMPONENT_UE4SS_MOD,
    COMPONENT_UE4SS_RUNTIME,
    INSTALL_KIND_LOOSE_OVERLAY,
)
from ..models.deployment import (
    ACTION_BLOCKED,
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_OVERWRITE,
    DeploymentFileAction,
    DeploymentPlan,
    DeploymentSkip,
)
from ..models.library import LibraryComponent, LibraryComponentFile, LibrarySource
from ..models.profile import ModProfile
from .pak_targets import pak_target_path
from .review_policy import review_policy_for_component, review_required_action_reason


UE4SS_RUNTIME_APPLY_GUIDANCE = (
    "Requires UE4SS runtime. Import/add a UE4SS Runtime package to this profile, "
    "or install UE4SS manually first."
)


def build_deployment_plan(
    profile: ModProfile,
    *,
    sources: list[LibrarySource],
    components: list[LibraryComponent],
    paths: S2AppPaths,
    ue4ss_runtime_installed: bool = False,
    dry_run: bool = True,
    real_apply_enabled: bool = False,
    ue4ss_activation_policy: dict[str, bool] | None = None,
) -> DeploymentPlan:
    plan = DeploymentPlan(
        profile_id=profile.profile_id,
        profile_name=profile.name,
        target_root=paths.client_root,
        dry_run=dry_run,
        real_apply_enabled=real_apply_enabled and not dry_run,
    )
    if paths.client_root is None:
        plan.errors.append("Subnautica 2 install root is not configured. Next: open Settings and select the game folder.")
    elif paths.is_gamepass_experimental:
        plan.warnings.append(
            "Game Pass / WinGDK support is experimental. UE4SS base/runtime files target the Game Pass Content root, while standard Lua mods target WinGDK\\ue4ss\\Mods; review every target before applying."
        )

    sources_by_id = {source.source_id: source for source in sources}
    components_by_id = {component.component_id: component for component in components}
    enabled_components: list[LibraryComponent] = []
    profile_ue4ss_states: list[tuple[LibraryComponent, bool]] = []
    activation_policy = ue4ss_activation_policy or {}
    skip_source_enabled_txt = bool(activation_policy.get("ue4ss_write_enabled_txt", False))

    for entry in profile.ordered_entries():
        component = components_by_id.get(entry.component_id)
        if component is None:
            if not entry.enabled:
                plan.skips.append(
                    DeploymentSkip(
                        entry.component_id,
                        entry.display_name or entry.component_id,
                        "disabled entry no longer exists in the manager library",
                    )
                )
                continue
            plan.errors.append(
                f"{entry.display_name or entry.component_id} is missing from the imported library. "
                "Next: remove it from the profile or reinstall it, then click Apply again."
            )
            continue
        if component.component_type == COMPONENT_UE4SS_MOD:
            profile_ue4ss_states.append((component, bool(entry.enabled)))
        if not entry.enabled:
            plan.skips.append(DeploymentSkip(component.component_id, component.display_name, "disabled in active profile"))
            continue
        enabled_components.append(component)
        _plan_component(
            plan,
            component,
            sources_by_id.get(component.source_id),
            paths,
            skip_ue4ss_enabled_txt=skip_source_enabled_txt,
        )

    if any(component.component_type == COMPONENT_UE4SS_MOD for component in enabled_components):
        has_profile_runtime = any(
            _is_ue4ss_runtime_component(component)
            for component in enabled_components
        )
        if not ue4ss_runtime_installed and not has_profile_runtime:
            plan.warnings.append(UE4SS_RUNTIME_APPLY_GUIDANCE)

    _plan_ue4ss_activation_files(plan, profile_ue4ss_states, paths, activation_policy)
    _detect_target_conflicts(plan)
    return plan


def _plan_component(
    plan: DeploymentPlan,
    component: LibraryComponent,
    source: LibrarySource | None,
    paths: S2AppPaths,
    *,
    skip_ue4ss_enabled_txt: bool = False,
) -> None:
    if source is None:
        plan.errors.append(
            f"{component.display_name} is missing its library source record. "
            "Next: Delete From List and reinstall this mod, or Remove from Profile."
        )
        return
    if not source.managed_path.exists():
        plan.errors.append(
            f"{component.display_name} source copy is missing: {source.managed_path}. "
            "Next: Delete From List and reinstall this mod, or Remove from Profile."
        )
        return
    if not component.files:
        plan.errors.append(f"{component.display_name} has no stored file list. Next: Delete From List and reinstall this mod.")
        return

    review_messages = _review_messages(component)
    for message in review_messages:
        plan.warnings.append(f"{component.display_name}: {message}")
    if _requires_review_block(component):
        for file in component.files:
            plan.actions.append(
                DeploymentFileAction(
                    component_id=component.component_id,
                    component_name=component.display_name,
                    source_path=source.managed_path,
                    source_member=file.source_path,
                    target_path=_target_for_file(component, file, paths),
                    action=ACTION_BLOCKED,
                    reason=review_required_action_reason(),
                    warnings=review_messages,
                )
            )
        policy = review_policy_for_component(component)
        if policy is not None:
            plan.errors.append(f"{component.display_name} requires manual review before deployment. {policy.text}")
        else:
            plan.errors.append(f"{component.display_name} requires manual review before deployment.")
        return

    for file in component.files:
        if skip_ue4ss_enabled_txt and component.component_type == COMPONENT_UE4SS_MOD and _is_enabled_txt_target(file):
            continue
        if not _safe_relative(file.source_path):
            plan.errors.append(f"{component.display_name} has unsafe source path: {file.source_path}. Next: do not install this archive; send a support report.")
            continue
        if file.target_hint and not _safe_relative(file.target_hint):
            plan.errors.append(f"{component.display_name} has unsafe target hint: {file.target_hint}. Next: do not install this archive; send a support report.")
            continue
        target = _target_for_file(component, file, paths)
        if target is None:
            plan.errors.append(f"{component.display_name} has no valid deployment target for {file.source_path}. Next: send a support report with this mod name.")
            continue
        source_missing = _source_member_missing(source.managed_path, file.source_path)
        if source_missing:
            plan.errors.append(
                f"{component.display_name} source file is missing: {file.source_path}. "
                "Next: Delete From List and reinstall this mod, or Remove from Profile."
            )
            continue
        plan.actions.append(
            DeploymentFileAction(
                component_id=component.component_id,
                component_name=component.display_name,
                source_path=source.managed_path,
                source_member=file.source_path,
                target_path=target,
                action=ACTION_OVERWRITE if target.exists() else ACTION_CREATE,
                warnings=[f"Existing target will be overwritten: {target}"] if target.exists() else [],
            )
        )
        if target.exists():
            plan.warnings.append(f"{component.display_name} will overwrite existing target: {target}")


def _plan_ue4ss_activation_files(
    plan: DeploymentPlan,
    ue4ss_states: list[tuple[LibraryComponent, bool]],
    paths: S2AppPaths,
    policy: dict[str, bool],
) -> None:
    if not ue4ss_states or paths.ue4ss_mods is None:
        return
    states = _ue4ss_mod_states(ue4ss_states)
    if not states:
        return

    if policy.get("ue4ss_write_enabled_txt", False):
        for mod_name, enabled in states:
            target = paths.ue4ss_mods / mod_name / "enabled.txt"
            if enabled:
                plan.actions.append(
                    _generated_action(
                        component_id=f"ue4ss_activation:{mod_name}:enabled_txt",
                        component_name=f"UE4SS activation: {mod_name}",
                        target=target,
                        content="",
                        reason="generated enabled.txt marker from active profile",
                    )
                )
            elif target.exists():
                plan.actions.append(
                    DeploymentFileAction(
                        component_id=f"ue4ss_activation:{mod_name}:enabled_txt",
                        component_name=f"UE4SS activation: {mod_name}",
                        source_path=None,
                        source_member="generated:remove enabled.txt",
                        target_path=target,
                        action=ACTION_DELETE,
                        reason="remove enabled.txt marker because profile entry is disabled",
                        warnings=["Existing enabled.txt will be backed up before deletion."],
                    )
                )

    if policy.get("ue4ss_write_mods_txt", False):
        target = paths.ue4ss_mods / "mods.txt"
        content = _mods_txt_content(target, states)
        plan.actions.append(
            _generated_action(
                component_id="ue4ss_activation:mods_txt",
                component_name="UE4SS activation: mods.txt",
                target=target,
                content=content,
                reason="generated from active profile UE4SS mod states",
                warning="Existing mods.txt entries are preserved where possible and the file is backed up on apply.",
            )
        )

    if policy.get("ue4ss_write_mods_json", False):
        target = paths.ue4ss_mods / "mods.json"
        content, warning = _mods_json_content(target, states)
        plan.actions.append(
            _generated_action(
                component_id="ue4ss_activation:mods_json",
                component_name="UE4SS activation: mods.json",
                target=target,
                content=content,
                reason="generated from active profile UE4SS mod states",
                warning=warning or "Existing mods.json entries are preserved where possible and the file is backed up on apply.",
            )
        )


def _ue4ss_mod_states(ue4ss_states: list[tuple[LibraryComponent, bool]]) -> list[tuple[str, bool]]:
    states: list[tuple[str, bool]] = []
    seen: set[str] = set()
    for component, enabled in ue4ss_states:
        mod_name = _ue4ss_mod_name(component)
        if not mod_name:
            continue
        key = mod_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        states.append((mod_name, enabled))
    return states


def _ue4ss_mod_name(component: LibraryComponent) -> str:
    for file in component.files:
        rel = _target_relative(file)
        if rel.parts:
            return rel.parts[0]
    return _safe_mod_folder_name(component.display_name)


def _safe_mod_folder_name(value: str) -> str:
    cleaned = "".join(char for char in value.strip() if char not in '<>:"/\\|?*')
    return cleaned or "UE4SSMod"


def _is_enabled_txt_target(file: LibraryComponentFile) -> bool:
    rel = _target_relative(file)
    return bool(rel.parts) and rel.parts[-1].casefold() == "enabled.txt"


def _generated_action(
    *,
    component_id: str,
    component_name: str,
    target: Path,
    content: str,
    reason: str,
    warning: str = "",
) -> DeploymentFileAction:
    warnings = [warning] if warning else []
    if target.exists():
        warnings.append(f"Existing target will be overwritten: {target}")
    return DeploymentFileAction(
        component_id=component_id,
        component_name=component_name,
        source_path=None,
        source_member="generated:UE4SS activation file",
        target_path=target,
        action=ACTION_OVERWRITE if target.exists() else ACTION_CREATE,
        reason=reason,
        warnings=warnings,
        generated_content=content,
    )


def _mods_txt_content(target: Path, states: list[tuple[str, bool]]) -> str:
    state_by_name = {name.casefold(): (name, enabled) for name, enabled in states}
    lines = _read_text_lines(target)
    if not lines:
        return "".join(f"{name} : {1 if enabled else 0}\n" for name, enabled in states)

    seen: set[str] = set()
    output: list[str] = []
    keybinds_index: int | None = None
    for line in lines:
        parsed = _parse_mods_txt_line(line)
        if parsed is None:
            output.append(line)
            continue
        name, suffix = parsed
        if name.casefold() == "keybinds" and keybinds_index is None:
            keybinds_index = len(output)
        configured = state_by_name.get(name.casefold())
        if configured is None:
            output.append(line)
            continue
        configured_name, enabled = configured
        seen.add(name.casefold())
        output.append(f"{configured_name} : {1 if enabled else 0}{suffix}")

    missing = [f"{name} : {1 if enabled else 0}" for name, enabled in states if name.casefold() not in seen]
    if missing:
        insert_at = keybinds_index if keybinds_index is not None else len(output)
        if insert_at > 0 and output[insert_at - 1].strip():
            missing.insert(0, "")
        output[insert_at:insert_at] = missing
    return "\n".join(output).rstrip() + "\n"


def _parse_mods_txt_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith(";") or stripped.startswith("#") or ":" not in line:
        return None
    name, rest = line.split(":", 1)
    mod_name = name.strip()
    if not mod_name:
        return None
    value = rest.strip()
    if not value or value[0] not in {"0", "1"}:
        return None
    suffix = ""
    marker_index = rest.find(";")
    if marker_index >= 0:
        suffix = " " + rest[marker_index:].strip()
    return mod_name, suffix


def _mods_json_content(target: Path, states: list[tuple[str, bool]]) -> tuple[str, str]:
    state_by_name = {name.casefold(): (name, enabled) for name, enabled in states}
    warning = ""
    existing = []
    if target.is_file():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = [item for item in loaded if isinstance(item, dict)]
            else:
                warning = "Existing mods.json is not a JSON array; it will be replaced and backed up on apply."
        except (OSError, json.JSONDecodeError):
            warning = "Existing mods.json could not be parsed; it will be replaced and backed up on apply."

    output: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in existing:
        mod_name = str(item.get("mod_name") or "")
        configured = state_by_name.get(mod_name.casefold())
        if configured is None:
            output.append(dict(item))
            continue
        configured_name, enabled = configured
        updated = dict(item)
        updated["mod_name"] = configured_name
        updated["mod_enabled"] = bool(enabled)
        output.append(updated)
        seen.add(mod_name.casefold())
    for name, enabled in states:
        if name.casefold() not in seen:
            output.append({"mod_name": name, "mod_enabled": bool(enabled)})
    return json.dumps(output, indent=2) + "\n", warning


def _read_text_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _target_for_file(component: LibraryComponent, file: LibraryComponentFile, paths: S2AppPaths) -> Path | None:
    if component.component_type == COMPONENT_PAK_BUNDLE:
        return pak_target_path(paths.content_paks, file.target_hint, file.source_path)
    if component.component_type == COMPONENT_UE4SS_RUNTIME:
        if paths.ue4ss_runtime_root is None:
            return None
        return paths.ue4ss_runtime_root / _target_relative(file)
    if component.component_type == COMPONENT_UE4SS_MOD:
        if paths.ue4ss_mods is None:
            return None
        return paths.ue4ss_mods / _target_relative(file)
    if component.component_type in {COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED} or component.install_kind == INSTALL_KIND_LOOSE_OVERLAY:
        if paths.client_root is None:
            return None
        return paths.client_root / _target_relative(file)
    return None


def _target_name(file: LibraryComponentFile) -> str:
    value = file.target_hint or file.source_path
    return PurePosixPath(value.replace("\\", "/")).name


def _target_relative(file: LibraryComponentFile) -> Path:
    value = file.target_hint or file.source_path
    parts = PurePosixPath(value.replace("\\", "/")).parts
    return Path(*parts)


def _source_member_missing(source_path: Path, member: str) -> bool:
    if source_path.is_file():
        return False
    if not _safe_relative(member):
        return True
    candidate = (source_path / Path(*PurePosixPath(member.replace("\\", "/")).parts)).resolve()
    try:
        candidate.relative_to(source_path.resolve())
    except ValueError:
        return True
    return not candidate.is_file()


def _detect_target_conflicts(plan: DeploymentPlan) -> None:
    by_target: dict[Path, list[DeploymentFileAction]] = {}
    for action in plan.actions:
        if action.target_path is None or action.action == ACTION_BLOCKED:
            continue
        by_target.setdefault(action.target_path, []).append(action)
    for target, actions in by_target.items():
        component_ids = {action.component_id for action in actions}
        if len(actions) > 1 and len(component_ids) > 1:
            plan.errors.append(
                "Target conflict: "
                + str(target)
                + " is written by "
                + ", ".join(sorted({action.component_name for action in actions}))
                + ". Next: disable or Remove from Profile one of those mods, then click Apply again."
            )


def _review_messages(component: LibraryComponent) -> list[str]:
    messages: list[str] = []
    for warning in component.warnings:
        lowered = warning.casefold()
        if "ambiguous" in lowered or "review" in lowered:
            messages.append(warning)
    policy = review_policy_for_component(component)
    if policy is not None:
        messages.append(policy.text)
    return list(dict.fromkeys(messages))


def _requires_review_block(component: LibraryComponent) -> bool:
    if component.component_type in {COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED}:
        return True
    if component.install_kind == INSTALL_KIND_LOOSE_OVERLAY:
        return True
    return False


def _is_ue4ss_runtime_component(component: LibraryComponent) -> bool:
    if component.component_type == COMPONENT_UE4SS_RUNTIME:
        return True
    if component.install_kind == COMPONENT_UE4SS_RUNTIME:
        return True
    badges = " ".join(component.badges).casefold()
    if "ue4ss" in badges and "runtime" in badges:
        return True
    name = component.display_name.casefold()
    return "ue4ss" in name and "runtime" in name


def _safe_relative(value: str) -> bool:
    if not value:
        return False
    for cls in (PurePosixPath, PureWindowsPath):
        path = cls(value)
        if path.is_absolute():
            return False
        if ".." in path.parts:
            return False
    return True

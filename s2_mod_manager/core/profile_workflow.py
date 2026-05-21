from __future__ import annotations

from dataclasses import dataclass

from ..models.archive_info import COMPONENT_UE4SS_MOD, COMPONENT_UE4SS_RUNTIME
from ..models.library import LibraryComponent, static_library_warnings
from ..models.profile import ModProfile
from .review_policy import review_policy_for_component


UE4SS_RUNTIME_PROFILE_GUIDANCE = (
    "Requires UE4SS runtime. Import/add a UE4SS Runtime package to this profile, "
    "or install UE4SS manually first."
)


@dataclass(frozen=True)
class LoadoutWarning:
    component_id: str
    message: str
    severity: str = "warning"


@dataclass(frozen=True)
class LoadoutChip:
    component_id: str
    label: str
    enabled: bool
    warning: bool = False


def component_profile_map(profile: ModProfile) -> dict[str, tuple[bool, int]]:
    return {
        entry.component_id: (entry.enabled, entry.order)
        for entry in profile.ordered_entries()
    }


def build_loadout_warnings(
    profile: ModProfile,
    library_components: list[LibraryComponent],
    *,
    ue4ss_runtime_installed: bool = False,
) -> list[LoadoutWarning]:
    components_by_id = {component.component_id: component for component in library_components}
    enabled_components = [
        components_by_id[entry.component_id]
        for entry in profile.ordered_entries()
        if entry.enabled and entry.component_id in components_by_id
    ]
    has_runtime = ue4ss_runtime_installed or any(
        _is_ue4ss_runtime_component(component) for component in enabled_components
    )

    warnings: list[LoadoutWarning] = []
    for entry in profile.ordered_entries():
        component = components_by_id.get(entry.component_id)
        if component is None:
            warnings.append(
                LoadoutWarning(
                    entry.component_id,
                    f"{entry.display_name or entry.component_id} is missing from the imported library.",
                    "error",
                )
            )
            continue
        for message in static_library_warnings(component.warnings):
            warnings.append(LoadoutWarning(component.component_id, message))
        policy = review_policy_for_component(component)
        if policy is not None:
            warnings.append(LoadoutWarning(component.component_id, policy.text, "warning"))
        if entry.enabled and _is_ue4ss_mod_component(component) and not has_runtime:
            warnings.append(
                LoadoutWarning(
                    component.component_id,
                    UE4SS_RUNTIME_PROFILE_GUIDANCE,
                )
            )
    return _dedupe_warnings(warnings)


def loadout_chips(
    profile: ModProfile,
    library_components: list[LibraryComponent],
    *,
    warnings: list[LoadoutWarning] | None = None,
    ue4ss_runtime_installed: bool = False,
) -> list[LoadoutChip]:
    components_by_id = {component.component_id: component for component in library_components}
    warnings = warnings if warnings is not None else build_loadout_warnings(
        profile,
        library_components,
        ue4ss_runtime_installed=ue4ss_runtime_installed,
    )
    warnings_by_id = {warning.component_id for warning in warnings}
    chips: list[LoadoutChip] = []
    for entry in profile.ordered_entries():
        component = components_by_id.get(entry.component_id)
        label = component.display_name if component is not None else entry.display_name or entry.component_id
        chips.append(
            LoadoutChip(
                component_id=entry.component_id,
                label=label,
                enabled=entry.enabled,
                warning=entry.component_id in warnings_by_id,
            )
        )
    return chips


def profile_contains(profile: ModProfile, component_id: str) -> bool:
    return any(entry.component_id == component_id for entry in profile.entries)


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


def _is_ue4ss_mod_component(component: LibraryComponent) -> bool:
    if component.component_type == COMPONENT_UE4SS_MOD:
        return True
    if component.install_kind == COMPONENT_UE4SS_MOD:
        return True
    badges = " ".join(component.badges).casefold()
    return "ue4ss" in badges and "runtime" not in badges


def _dedupe_warnings(warnings: list[LoadoutWarning]) -> list[LoadoutWarning]:
    seen: set[tuple[str, str]] = set()
    deduped: list[LoadoutWarning] = []
    for warning in warnings:
        key = (warning.component_id, warning.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(warning)
    return deduped

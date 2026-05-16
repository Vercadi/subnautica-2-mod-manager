from __future__ import annotations

from dataclasses import dataclass, field

from ..models.library import LibraryComponent, LibrarySource
from ..models.profile import ModProfile
from .profile_store import ProfileStore
from .review_policy import review_policy_for_component


DEFAULT_MODDED_PROFILE_NAME = "Default Modded"


@dataclass(frozen=True)
class ProfileActionResult:
    ok: bool
    message: str
    profile: ModProfile | None = None
    changed_count: int = 0
    enabled_component_ids: list[str] = field(default_factory=list)
    refused_component_ids: list[str] = field(default_factory=list)
    created_profile: bool = False


def ensure_editable_profile(
    store: ProfileStore,
    *,
    default_name: str = DEFAULT_MODDED_PROFILE_NAME,
) -> tuple[ModProfile, bool]:
    active = store.active_profile()
    if not active.protected:
        return active, False

    existing = store.get_profile_by_name(default_name)
    if existing is not None and not existing.protected:
        return store.set_active_profile(existing.profile_id), False
    return store.create_profile(default_name), True


def smart_toggle_component(
    store: ProfileStore,
    component_id: str,
    library_components: list[LibraryComponent],
    *,
    default_name: str = DEFAULT_MODDED_PROFILE_NAME,
) -> ProfileActionResult:
    active = store.active_profile()
    entry = next((item for item in active.entries if item.component_id == component_id), None)
    if entry is None:
        return smart_set_component_enabled(
            store,
            component_id,
            library_components,
            enabled=True,
            default_name=default_name,
        )
    return smart_set_component_enabled(
        store,
        component_id,
        library_components,
        enabled=not entry.enabled,
        default_name=default_name,
    )


def smart_set_component_enabled(
    store: ProfileStore,
    component_id: str,
    library_components: list[LibraryComponent],
    *,
    enabled: bool,
    default_name: str = DEFAULT_MODDED_PROFILE_NAME,
) -> ProfileActionResult:
    component = _component_by_id(library_components, component_id)
    if component is None:
        return ProfileActionResult(False, "Import this mod before enabling it.")

    active = store.active_profile()
    if active.protected and not enabled:
        return ProfileActionResult(False, "Vanilla has no editable mod entries.")

    if enabled:
        policy = review_policy_for_component(component)
        if policy is not None:
            return ProfileActionResult(
                False,
                f"{component.display_name} needs review and cannot be enabled automatically. {policy.text}",
                refused_component_ids=[component.component_id],
            )

    created_profile = False
    if active.protected:
        active, created_profile = ensure_editable_profile(store, default_name=default_name)

    entry = next((item for item in active.entries if item.component_id == component.component_id), None)
    changed = False
    if entry is None:
        if not enabled:
            return ProfileActionResult(True, f"{component.display_name} is not in {active.name}.", profile=active)
        store.add_component(active.profile_id, component.component_id, library_components)
        changed = True
        if not enabled:
            store.set_component_enabled(active.profile_id, component.component_id, False)
    else:
        changed = store.set_component_enabled(active.profile_id, component.component_id, enabled)

    state = "Enabled" if enabled else "Disabled"
    created_text = "Created Default Modded profile and " if created_profile else ""
    unchanged_text = "" if changed else " already"
    return ProfileActionResult(
        True,
        f"{created_text}{state}{unchanged_text}: {component.display_name} in {active.name}.",
        profile=active,
        changed_count=1 if changed else 0,
        enabled_component_ids=[component.component_id] if enabled else [],
        created_profile=created_profile,
    )


def enable_imported_sources(
    store: ProfileStore,
    sources: list[LibrarySource],
    library_components: list[LibraryComponent],
    *,
    selected_component_ids: set[str] | None = None,
    default_name: str = DEFAULT_MODDED_PROFILE_NAME,
) -> ProfileActionResult:
    selected_component_ids = selected_component_ids or set()
    component_ids = _component_ids_from_sources(sources)
    if selected_component_ids:
        component_ids = [component_id for component_id in component_ids if component_id in selected_component_ids]
    if not component_ids:
        return ProfileActionResult(False, "Install & Enable found no imported components to enable.")

    messages: list[str] = []
    enabled_ids: list[str] = []
    refused_ids: list[str] = []
    changed_count = 0
    created_profile = False
    profile: ModProfile | None = None
    ok = True

    for component_id in component_ids:
        result = smart_set_component_enabled(
            store,
            component_id,
            library_components,
            enabled=True,
            default_name=default_name,
        )
        messages.append(result.message)
        enabled_ids.extend(result.enabled_component_ids)
        refused_ids.extend(result.refused_component_ids)
        changed_count += result.changed_count
        created_profile = created_profile or result.created_profile
        profile = result.profile or profile
        ok = ok and result.ok

    enabled_count = len(dict.fromkeys(enabled_ids))
    refused_count = len(dict.fromkeys(refused_ids))
    summary = f"Install & Enable: enabled {enabled_count} component(s)"
    if profile is not None:
        summary += f" in {profile.name}"
    if refused_count:
        summary += f"; {refused_count} review-required component(s) not enabled"
    if messages:
        summary += ". " + " ".join(dict.fromkeys(messages[:3]))
    return ProfileActionResult(
        ok=ok,
        message=summary,
        profile=profile,
        changed_count=changed_count,
        enabled_component_ids=list(dict.fromkeys(enabled_ids)),
        refused_component_ids=list(dict.fromkeys(refused_ids)),
        created_profile=created_profile,
    )


def _component_by_id(components: list[LibraryComponent], component_id: str) -> LibraryComponent | None:
    for component in components:
        if component.component_id == component_id:
            return component
    return None


def _component_ids_from_sources(sources: list[LibrarySource]) -> list[str]:
    component_ids: list[str] = []
    for source in sources:
        component_ids.extend(source.component_ids)
    return list(dict.fromkeys(component_ids))

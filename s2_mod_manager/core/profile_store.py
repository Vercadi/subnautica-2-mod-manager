from __future__ import annotations

import uuid
from pathlib import Path

from ..models.library import LibraryComponent
from ..models.profile import (
    LoadoutEntry,
    ModProfile,
    ProfileState,
    VANILLA_PROFILE_ID,
    VANILLA_PROFILE_NAME,
    vanilla_profile,
)
from ..utils.json_io import read_json, write_json


class ProfileStore:
    """Persistent manager-side profiles and loadouts.

    Profiles only reference imported library component ids. This store does not
    deploy files and does not inspect or write the game install.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.state_path = data_dir / "profiles.json"
        self.state = ProfileState.from_dict(read_json(self.state_path))
        self._normalize()

    def list_profiles(self) -> list[ModProfile]:
        return sorted(self.state.profiles, key=lambda profile: (not profile.protected, profile.name.casefold()))

    def active_profile(self) -> ModProfile:
        profile = self.get_profile(self.state.active_profile_id)
        if profile is None:
            self.state.active_profile_id = VANILLA_PROFILE_ID
            profile = self.get_profile(VANILLA_PROFILE_ID)
        if profile is None:
            profile = vanilla_profile()
            self.state.profiles.insert(0, profile)
        return profile

    def get_profile(self, profile_id: str) -> ModProfile | None:
        for profile in self.state.profiles:
            if profile.profile_id == profile_id:
                return profile
        return None

    def get_profile_by_name(self, name: str) -> ModProfile | None:
        normalized = name.casefold()
        for profile in self.state.profiles:
            if profile.name.casefold() == normalized:
                return profile
        return None

    def set_active_profile(self, profile_id: str) -> ModProfile:
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile not found: {profile_id}")
        self.state.active_profile_id = profile.profile_id
        self.save()
        return profile

    def create_profile(self, name: str = "New Profile") -> ModProfile:
        profile = ModProfile(
            profile_id=_new_profile_id(),
            name=self._unique_name(name),
        )
        self.state.profiles.append(profile)
        self.state.active_profile_id = profile.profile_id
        self.save()
        return profile

    def duplicate_profile(self, profile_id: str, name: str | None = None) -> ModProfile:
        source = self._require_profile(profile_id)
        duplicate = ModProfile(
            profile_id=_new_profile_id(),
            name=self._unique_name(name or f"{source.name} Copy"),
            entries=[
                LoadoutEntry(
                    component_id=entry.component_id,
                    display_name=entry.display_name,
                    enabled=entry.enabled,
                    order=index,
                    profile_notes=entry.profile_notes,
                    last_known_component_type=entry.last_known_component_type,
                    last_known_source_id=entry.last_known_source_id,
                )
                for index, entry in enumerate(source.ordered_entries())
            ],
            notes=source.notes,
        )
        self.state.profiles.append(duplicate)
        self.state.active_profile_id = duplicate.profile_id
        self.save()
        return duplicate

    def rename_profile(self, profile_id: str, name: str) -> ModProfile:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        profile.name = self._unique_name(name, ignore_profile_id=profile.profile_id)
        profile.touch()
        self.save()
        return profile

    def delete_profile(self, profile_id: str) -> None:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        self.state.profiles = [item for item in self.state.profiles if item.profile_id != profile_id]
        if self.state.active_profile_id == profile_id:
            self.state.active_profile_id = VANILLA_PROFILE_ID
        self.save()

    def add_component(self, profile_id: str, component_id: str, library_components: list[LibraryComponent]) -> bool:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        component = _component_by_id(library_components, component_id)
        if component is None:
            raise ValueError(f"Component is not in the imported library: {component_id}")
        if any(entry.component_id == component_id for entry in profile.entries):
            return False
        profile.entries.append(
            LoadoutEntry(
                component_id=component.component_id,
                display_name=component.display_name,
                enabled=True,
                order=len(profile.entries),
                last_known_component_type=component.component_type,
                last_known_source_id=component.source_id,
            )
        )
        self._renumber(profile)
        profile.touch()
        self.save()
        return True

    def remove_component(self, profile_id: str, component_id: str) -> bool:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        before = len(profile.entries)
        profile.entries = [entry for entry in profile.entries if entry.component_id != component_id]
        changed = len(profile.entries) != before
        if changed:
            self._renumber(profile)
            profile.touch()
            self.save()
        return changed

    def remove_components_from_all_profiles(self, component_ids: list[str]) -> int:
        selected = set(component_id for component_id in component_ids if component_id)
        if not selected:
            return 0
        removed = 0
        changed = False
        for profile in self.state.profiles:
            if profile.protected:
                continue
            before = len(profile.entries)
            profile.entries = [entry for entry in profile.entries if entry.component_id not in selected]
            profile_removed = before - len(profile.entries)
            if profile_removed:
                removed += profile_removed
                self._renumber(profile)
                profile.touch()
                changed = True
        if changed:
            self.save()
        return removed

    def set_component_enabled(self, profile_id: str, component_id: str, enabled: bool) -> bool:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        for entry in profile.entries:
            if entry.component_id == component_id:
                if entry.enabled == enabled:
                    return False
                entry.enabled = enabled
                profile.touch()
                self.save()
                return True
        return False

    def move_component(self, profile_id: str, component_id: str, delta: int) -> bool:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        entries = profile.ordered_entries()
        old_index = next((index for index, entry in enumerate(entries) if entry.component_id == component_id), None)
        if old_index is None:
            return False
        new_index = max(0, min(len(entries) - 1, old_index + delta))
        if new_index == old_index:
            return False
        entry = entries.pop(old_index)
        entries.insert(new_index, entry)
        profile.entries = entries
        self._renumber(profile)
        profile.touch()
        self.save()
        return True

    def move_component_to_top(self, profile_id: str, component_id: str) -> bool:
        return self._move_component_to_index(profile_id, component_id, 0)

    def move_component_to_bottom(self, profile_id: str, component_id: str) -> bool:
        profile = self._require_profile(profile_id)
        return self._move_component_to_index(profile_id, component_id, max(0, len(profile.entries) - 1))

    def set_all_enabled(self, profile_id: str, enabled: bool) -> int:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        changed = 0
        for entry in profile.entries:
            if entry.enabled != enabled:
                entry.enabled = enabled
                changed += 1
        if changed:
            profile.touch()
            self.save()
        return changed

    def remove_all_components(self, profile_id: str) -> int:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        removed = len(profile.entries)
        if removed:
            profile.entries = []
            profile.touch()
            self.save()
        return removed

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        write_json(self.state_path, self.state.to_dict())

    def _normalize(self) -> None:
        changed = False
        vanilla = self.get_profile(VANILLA_PROFILE_ID)
        if vanilla is None:
            self.state.profiles.insert(0, vanilla_profile())
            changed = True
        else:
            if vanilla.name != VANILLA_PROFILE_NAME:
                vanilla.name = VANILLA_PROFILE_NAME
                changed = True
            if vanilla.entries:
                vanilla.entries = []
                changed = True
            notes = vanilla.notes or "Protected baseline profile with no manager-side mods."
            if vanilla.notes != notes:
                vanilla.notes = notes
                changed = True
        if self.get_profile(self.state.active_profile_id) is None:
            self.state.active_profile_id = VANILLA_PROFILE_ID
            changed = True
        for profile in self.state.profiles:
            ordered = profile.ordered_entries()
            if profile.entries != ordered:
                profile.entries = ordered
                changed = True
            for index, entry in enumerate(profile.entries):
                if entry.order != index:
                    entry.order = index
                    changed = True
        if changed or not self.state_path.is_file():
            self.save()

    def _renumber(self, profile: ModProfile) -> None:
        for index, entry in enumerate(profile.entries):
            entry.order = index

    def _move_component_to_index(self, profile_id: str, component_id: str, new_index: int) -> bool:
        profile = self._require_profile(profile_id)
        self._ensure_mutable(profile)
        entries = profile.ordered_entries()
        old_index = next((index for index, entry in enumerate(entries) if entry.component_id == component_id), None)
        if old_index is None:
            return False
        new_index = max(0, min(len(entries) - 1, int(new_index)))
        if old_index == new_index:
            return False
        entry = entries.pop(old_index)
        entries.insert(new_index, entry)
        profile.entries = entries
        self._renumber(profile)
        profile.touch()
        self.save()
        return True

    def _unique_name(self, name: str, *, ignore_profile_id: str = "") -> str:
        base = (name or "New Profile").strip() or "New Profile"
        existing = {
            profile.name.casefold()
            for profile in self.state.profiles
            if profile.profile_id != ignore_profile_id
        }
        if base.casefold() not in existing:
            return base
        suffix = 2
        while f"{base} {suffix}".casefold() in existing:
            suffix += 1
        return f"{base} {suffix}"

    def _require_profile(self, profile_id: str) -> ModProfile:
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile not found: {profile_id}")
        return profile

    def _ensure_mutable(self, profile: ModProfile) -> None:
        if profile.protected:
            raise ValueError("The Vanilla profile is protected.")


def _component_by_id(components: list[LibraryComponent], component_id: str) -> LibraryComponent | None:
    for component in components:
        if component.component_id == component_id:
            return component
    return None


def _new_profile_id() -> str:
    return f"profile_{uuid.uuid4().hex[:12]}"

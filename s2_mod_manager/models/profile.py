from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


VANILLA_PROFILE_ID = "vanilla"
VANILLA_PROFILE_NAME = "Vanilla"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class LoadoutEntry:
    component_id: str
    display_name: str
    enabled: bool = True
    order: int = 0
    profile_notes: str = ""
    last_known_component_type: str = ""
    last_known_source_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "order": self.order,
            "profile_notes": self.profile_notes,
            "last_known_component_type": self.last_known_component_type,
            "last_known_source_id": self.last_known_source_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoadoutEntry":
        return cls(
            component_id=str(data.get("component_id") or ""),
            display_name=str(data.get("display_name") or ""),
            enabled=bool(data.get("enabled", True)),
            order=int(data.get("order") or 0),
            profile_notes=str(data.get("profile_notes") or ""),
            last_known_component_type=str(data.get("last_known_component_type") or ""),
            last_known_source_id=str(data.get("last_known_source_id") or ""),
        )


@dataclass
class ModProfile:
    profile_id: str
    name: str
    entries: list[LoadoutEntry] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    @property
    def protected(self) -> bool:
        return self.profile_id == VANILLA_PROFILE_ID

    def ordered_entries(self) -> list[LoadoutEntry]:
        return sorted(self.entries, key=lambda entry: (entry.order, entry.display_name.casefold()))

    def touch(self) -> None:
        self.updated_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "entries": [entry.to_dict() for entry in self.ordered_entries()],
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModProfile":
        return cls(
            profile_id=str(data.get("profile_id") or ""),
            name=str(data.get("name") or ""),
            entries=[
                LoadoutEntry.from_dict(item)
                for item in data.get("entries", [])
                if isinstance(item, dict)
            ],
            notes=str(data.get("notes") or ""),
            created_at=str(data.get("created_at") or utc_now_iso()),
            updated_at=str(data.get("updated_at") or utc_now_iso()),
        )


@dataclass
class ProfileState:
    profiles: list[ModProfile] = field(default_factory=list)
    active_profile_id: str = VANILLA_PROFILE_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_profile_id": self.active_profile_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ProfileState":
        if not isinstance(data, dict):
            return cls()
        return cls(
            profiles=[
                ModProfile.from_dict(item)
                for item in data.get("profiles", [])
                if isinstance(item, dict)
            ],
            active_profile_id=str(data.get("active_profile_id") or VANILLA_PROFILE_ID),
        )


def vanilla_profile() -> ModProfile:
    return ModProfile(
        profile_id=VANILLA_PROFILE_ID,
        name=VANILLA_PROFILE_NAME,
        entries=[],
        notes="Protected baseline profile with no manager-side mods.",
    )

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

POPUP_POLICY_ALL = "all"
POPUP_POLICY_WARNINGS_AND_CRITICAL = "warnings_and_critical"
POPUP_POLICY_CRITICAL_ONLY = "critical_only"
POPUP_POLICY_CUSTOM = "custom"

POPUP_POLICY_LABELS = {
    POPUP_POLICY_ALL: "Show all popups",
    POPUP_POLICY_WARNINGS_AND_CRITICAL: "Warnings + critical only",
    POPUP_POLICY_CRITICAL_ONLY: "Disable noncritical popups",
    POPUP_POLICY_CUSTOM: "Custom popup settings",
}
POPUP_POLICY_OPTIONS = (
    POPUP_POLICY_LABELS[POPUP_POLICY_ALL],
    POPUP_POLICY_LABELS[POPUP_POLICY_WARNINGS_AND_CRITICAL],
    POPUP_POLICY_LABELS[POPUP_POLICY_CRITICAL_ONLY],
)


def popup_policy_from_flags(*, update: bool, info: bool, success: bool, warning: bool) -> str:
    enabled = (bool(update), bool(info), bool(success), bool(warning))
    if enabled == (True, True, True, True):
        return POPUP_POLICY_ALL
    if enabled == (False, False, False, True):
        return POPUP_POLICY_WARNINGS_AND_CRITICAL
    if enabled == (False, False, False, False):
        return POPUP_POLICY_CRITICAL_ONLY
    return POPUP_POLICY_CUSTOM


def popup_policy_from_text(value: str) -> str:
    normalized = str(value or "").strip().casefold()
    if normalized in {"critical safety only", "disable all popups", "disable non-critical popups"}:
        return POPUP_POLICY_CRITICAL_ONLY
    for policy, label in POPUP_POLICY_LABELS.items():
        if normalized in {policy.casefold(), label.casefold()}:
            return policy
    raise ValueError(f"Unknown popup policy: {value}")


@dataclass(frozen=True)
class UserPreferences:
    auto_check_updates: bool = True
    show_update_popups: bool = False
    show_info_popups: bool = False
    show_success_popups: bool = False
    show_warning_popups: bool = False
    ue4ss_write_enabled_txt: bool = True
    ue4ss_write_mods_json: bool = False
    ue4ss_write_mods_txt: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "auto_check_updates": bool(self.auto_check_updates),
            "popup_policy": self.popup_policy,
            "show_update_popups": bool(self.show_update_popups),
            "show_info_popups": bool(self.show_info_popups),
            "show_success_popups": bool(self.show_success_popups),
            "show_warning_popups": bool(self.show_warning_popups),
            "ue4ss_write_enabled_txt": bool(self.ue4ss_write_enabled_txt),
            "ue4ss_write_mods_json": bool(self.ue4ss_write_mods_json),
            "ue4ss_write_mods_txt": bool(self.ue4ss_write_mods_txt),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "UserPreferences":
        if not isinstance(data, dict):
            return cls()
        return cls(
            auto_check_updates=bool(data.get("auto_check_updates", True)),
            show_update_popups=bool(data.get("show_update_popups", False)),
            show_info_popups=bool(data.get("show_info_popups", False)),
            show_success_popups=bool(data.get("show_success_popups", False)),
            show_warning_popups=bool(data.get("show_warning_popups", False)),
            ue4ss_write_enabled_txt=bool(data.get("ue4ss_write_enabled_txt", True)),
            ue4ss_write_mods_json=bool(data.get("ue4ss_write_mods_json", False)),
            ue4ss_write_mods_txt=bool(data.get("ue4ss_write_mods_txt", False)),
        )

    def popup_enabled(self, kind: str) -> bool:
        normalized = kind.casefold()
        if normalized == "update":
            return self.show_update_popups
        if normalized == "success":
            return self.show_success_popups
        if normalized == "warning":
            return self.show_warning_popups
        return self.show_info_popups

    @property
    def popup_policy(self) -> str:
        return popup_policy_from_flags(
            update=self.show_update_popups,
            info=self.show_info_popups,
            success=self.show_success_popups,
            warning=self.show_warning_popups,
        )

    @property
    def popup_policy_label(self) -> str:
        return POPUP_POLICY_LABELS[self.popup_policy]

    def with_popup_policy(self, policy_text: str) -> "UserPreferences":
        policy = popup_policy_from_text(policy_text)
        if policy == POPUP_POLICY_CUSTOM:
            return self
        enabled = policy == POPUP_POLICY_ALL
        warning_enabled = policy in {POPUP_POLICY_ALL, POPUP_POLICY_WARNINGS_AND_CRITICAL}
        return replace(
            self,
            show_update_popups=enabled,
            show_info_popups=enabled,
            show_success_popups=enabled,
            show_warning_popups=warning_enabled,
        )

    def ue4ss_activation_policy(self) -> dict[str, bool]:
        return {
            "ue4ss_write_enabled_txt": self.ue4ss_write_enabled_txt,
            "ue4ss_write_mods_json": self.ue4ss_write_mods_json,
            "ue4ss_write_mods_txt": self.ue4ss_write_mods_txt,
        }

    @property
    def ue4ss_policy_text(self) -> str:
        return (
            f"enabled.txt={'on' if self.ue4ss_write_enabled_txt else 'off'}, "
            f"mods.json={'on' if self.ue4ss_write_mods_json else 'off'}, "
            f"mods.txt={'on' if self.ue4ss_write_mods_txt else 'off'}"
        )

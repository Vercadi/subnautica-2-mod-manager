from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATE_AVAILABLE = "Available"
STATE_ENABLED = "Enabled"
STATE_DISABLED = "Disabled"
STATE_PENDING_APPLY = "Pending Apply"
STATE_INSTALLED = "Installed"
STATE_WILL_REMOVE = "Will Remove"
STATE_NEEDS_REVIEW = "Needs Review"
STATE_BLOCKED = "Blocked"
STATE_ERROR = "Error"


@dataclass(frozen=True)
class SelectionActionState:
    enabled: bool
    reason: str = ""


def mod_display_state(mod: Any) -> str:
    """Return the user-facing state for a mod/list row.

    The UI passes light view objects here, so this intentionally uses getattr
    instead of requiring a concrete class.
    """
    if _truthy(getattr(mod, "error", "")):
        return STATE_ERROR
    if _truthy(getattr(mod, "review_policy_text", "")):
        return STATE_NEEDS_REVIEW

    deployment = str(getattr(mod, "deployment_status", "") or "").casefold()
    installed = bool(getattr(mod, "installed", False))
    in_profile = bool(getattr(mod, "in_active_profile", False))
    profile_enabled = bool(getattr(mod, "profile_enabled", False))
    state = str(getattr(mod, "state", "") or "")

    if installed and "remove" in deployment:
        return f"{STATE_INSTALLED}, {STATE_WILL_REMOVE}"
    if in_profile and profile_enabled:
        if not installed or _has_install_action(deployment):
            return f"{STATE_ENABLED}, {STATE_PENDING_APPLY}"
        return STATE_ENABLED
    if in_profile and not profile_enabled:
        if installed:
            return f"{STATE_DISABLED}, {STATE_PENDING_APPLY}"
        return STATE_DISABLED
    if installed:
        return STATE_INSTALLED
    if state == "library" or state.startswith("candidate"):
        return STATE_AVAILABLE
    return state.replace("_", " ").title() if state else STATE_AVAILABLE


def selection_action_states(
    mods: list[Any],
    *,
    active_profile_protected: bool = False,
    pending_change_count: int = 0,
    has_apply_callback: bool = True,
) -> dict[str, SelectionActionState]:
    """Compute main action availability for the current row selection."""
    selected = [mod for mod in mods if getattr(mod, "component_id", "")]
    any_selected = bool(selected)
    any_installed = any(bool(getattr(mod, "installed", False)) for mod in selected)
    any_review = any(_truthy(getattr(mod, "review_policy_text", "")) for mod in selected)
    enable_targets = [
        mod for mod in selected
        if _can_enable(mod, active_profile_protected=active_profile_protected)
    ]
    disable_targets = [
        mod for mod in selected
        if bool(getattr(mod, "in_active_profile", False))
        and bool(getattr(mod, "profile_enabled", False))
        and not active_profile_protected
    ]
    removable = [
        mod for mod in selected
        if not bool(getattr(mod, "installed", False))
    ]

    return {
        "Apply": SelectionActionState(
            bool(has_apply_callback and pending_change_count > 0),
            "" if pending_change_count > 0 else "No pending changes. Enable a mod first.",
        ),
        "Enable": SelectionActionState(
            bool(enable_targets),
            _selection_reason(any_selected, any_review, "No selected mods can be enabled."),
        ),
        "Disable": SelectionActionState(
            bool(disable_targets),
            "Vanilla cannot be edited." if active_profile_protected else _selection_reason(any_selected, False, "No selected enabled mods."),
        ),
        "Remove": SelectionActionState(
            bool(removable),
            "Installed mods need Uninstall." if any_installed and not removable else _selection_reason(any_selected, False, "Select available mods to remove."),
        ),
        "Uninstall": SelectionActionState(
            bool(any_installed),
            _selection_reason(any_selected, False, "Select installed mods to uninstall."),
        ),
        "Reset to Vanilla": SelectionActionState(True, ""),
    }


def _can_enable(mod: Any, *, active_profile_protected: bool) -> bool:
    if _truthy(getattr(mod, "review_policy_text", "")):
        return False
    state = str(getattr(mod, "state", "") or "")
    if state != "library":
        return False
    if bool(getattr(mod, "in_active_profile", False)):
        return not bool(getattr(mod, "profile_enabled", False)) and not active_profile_protected
    return True


def _has_install_action(deployment: str) -> bool:
    return any(token in deployment for token in ("install", "create", "overwrite"))


def _selection_reason(any_selected: bool, any_review: bool, fallback: str) -> str:
    if not any_selected:
        return "Select one or more mods first."
    if any_review:
        return "Needs review before install."
    return fallback


def _truthy(value: object) -> bool:
    return bool(str(value or "").strip())

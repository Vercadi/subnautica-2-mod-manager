from __future__ import annotations

from pathlib import PurePosixPath
from typing import Iterable

from ..models.archive_info import COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED, INSTALL_KIND_LOOSE_OVERLAY
from ..models.library import LibraryComponent
from ..models.review_policy import ReviewPolicy


LOOSE_OVERLAY_POLICY_ID = "loose_overlay_review_required"
LOOSE_OVERLAY_TITLE = "Review required: loose root overlay"
LOOSE_OVERLAY_SUMMARY = (
    "this source wants to place files outside the managed pak or UE4SS mod folders, "
    "often directly beside the game executable"
)
LOOSE_OVERLAY_BLOCKED_REASON = (
    "Automatic deployment is blocked because root DLL/config overlays can break game launch, "
    "conflict with other loaders, or leave files unmanaged."
)
LOOSE_OVERLAY_USER_ACTION = (
    "Keep it imported for reference, but leave it out of release profiles unless you manually review "
    "the mod author's install instructions and make your own backup."
)
LOOSE_OVERLAY_FUTURE_ACTION = (
    "A future explicit policy can support known-safe root overlays after target-specific handling is added."
)


def is_review_required_component(component_type: str, install_kind: str = "") -> bool:
    return component_type in {COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED} or install_kind == INSTALL_KIND_LOOSE_OVERLAY


def loose_overlay_policy(*, target_hints: Iterable[str] = ()) -> ReviewPolicy:
    return ReviewPolicy(
        policy_id=LOOSE_OVERLAY_POLICY_ID,
        title=LOOSE_OVERLAY_TITLE,
        summary=LOOSE_OVERLAY_SUMMARY,
        blocked_reason=LOOSE_OVERLAY_BLOCKED_REASON,
        user_action=LOOSE_OVERLAY_USER_ACTION,
        future_action=LOOSE_OVERLAY_FUTURE_ACTION,
        target_hints=_dedupe_hints(target_hints),
    )


def review_policy_for_component(component: LibraryComponent) -> ReviewPolicy | None:
    if not is_review_required_component(component.component_type, component.install_kind):
        return None
    return loose_overlay_policy(target_hints=(file.target_hint or file.source_path for file in component.files))


def review_policy_for_fields(
    component_type: str,
    install_kind: str = "",
    *,
    target_hints: Iterable[str] = (),
) -> ReviewPolicy | None:
    if not is_review_required_component(component_type, install_kind):
        return None
    return loose_overlay_policy(target_hints=target_hints)


def review_required_warning(*, target_hints: Iterable[str] = ()) -> str:
    policy = loose_overlay_policy(target_hints=target_hints)
    return "Loose overlay files require explicit review before deployment. " + policy.blocked_reason


def review_required_action_reason() -> str:
    return "review required: loose root overlay is blocked by release safety policy"


def _dedupe_hints(target_hints: Iterable[str]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for raw in target_hints:
        value = str(raw or "").replace("\\", "/").strip()
        if not value:
            continue
        # Keep hints short and path-like for UI labels.
        parts = PurePosixPath(value).parts
        value = str(PurePosixPath(*parts)) if parts else value
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        values.append(value)
    return values[:12]

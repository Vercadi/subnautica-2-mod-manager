from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from ..models.library import LibraryComponent


DuplicateKey = tuple[str, str, str, str, tuple[str, ...]]


@dataclass(frozen=True)
class DuplicateCleanupResult:
    removed_component_ids: list[str]
    protected_component_ids: list[str]

    @property
    def removed_count(self) -> int:
        return len(self.removed_component_ids)

    @property
    def protected_count(self) -> int:
        return len(self.protected_component_ids)

    @property
    def message(self) -> str:
        pieces: list[str] = []
        if self.removed_component_ids:
            pieces.append(f"replaced {len(self.removed_component_ids)} old uninstalled duplicate(s)")
        if self.protected_component_ids:
            pieces.append(f"kept {len(self.protected_component_ids)} installed duplicate(s)")
        return "; ".join(pieces)


def duplicate_key(component: LibraryComponent) -> DuplicateKey:
    return (
        _normalize_name(component.display_name),
        str(component.component_type or "").casefold(),
        str(component.install_kind or "").casefold(),
        _normalize_target_family(component.target_hint),
        tuple(sorted({str(file.role or "file").casefold() for file in component.files})),
    )


def duplicate_groups(components: list[LibraryComponent]) -> dict[DuplicateKey, list[LibraryComponent]]:
    grouped: dict[DuplicateKey, list[LibraryComponent]] = defaultdict(list)
    for component in components:
        key = duplicate_key(component)
        if key[0]:
            grouped[key].append(component)
    return {key: values for key, values in grouped.items() if len(values) > 1}


def duplicate_warning_text(count: int) -> str:
    return (
        f"Possible duplicate/update: {count} entries share this mod shape. "
        "Use Delete From List or Delete Old Versions to clean old uninstalled entries."
    )


def _normalize_name(value: str) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"\.[a-z0-9]{2,5}$", " ", text)
    text = re.sub(r"\bv?\d+(?:[._-]\d+){1,}\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens: list[str] = []
    for token in text.split():
        if token in {"v", "ver", "version", "build", "release", "ea", "early", "access"}:
            continue
        if token.isdigit():
            continue
        if re.fullmatch(r"[a-f0-9]{10,}", token):
            continue
        tokens.append(token)
    return "".join(tokens)


def _normalize_target_family(value: str) -> str:
    text = str(value or "").casefold().replace("\\", "/")
    text = re.sub(r"\bv?\d+(?:[._-]\d+){1,}\b", " ", text)
    text = re.sub(r"[^a-z0-9/~]+", " ", text)
    return " ".join(part for part in text.split() if not part.isdigit())

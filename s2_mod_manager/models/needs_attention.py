from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AttentionItem:
    title: str
    detail: str
    severity: str = "warning"

    @property
    def summary_text(self) -> str:
        return f"{self.title}: {self.detail}"


@dataclass(frozen=True)
class NeedsAttentionSummary:
    items: list[AttentionItem] = field(default_factory=list)

    @property
    def has_items(self) -> bool:
        return bool(self.items)

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def summary_text(self) -> str:
        if not self.items:
            return "Needs Attention: no actionable issues detected."
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.severity] = counts.get(item.severity, 0) + 1
        bits = ", ".join(f"{count} {severity}" for severity, count in sorted(counts.items()))
        return f"Needs Attention: {len(self.items)} item(s) ({bits})."

    def detail_text(self, *, limit: int = 8) -> str:
        if not self.items:
            return self.summary_text
        lines = [self.summary_text]
        lines.extend(f"- {item.summary_text}" for item in self.items[:limit])
        if len(self.items) > limit:
            lines.append(f"- ... {len(self.items) - limit} more")
        return "\n".join(lines)

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReviewPolicy:
    policy_id: str
    title: str
    summary: str
    blocked_reason: str
    user_action: str
    future_action: str
    target_hints: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        targets = ", ".join(self.target_hints) if self.target_hints else "targets listed in the preview"
        return (
            f"{self.title}: {self.summary} Targets: {targets}. "
            f"{self.blocked_reason} {self.user_action} {self.future_action}"
        )

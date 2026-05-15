from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ActivityRecord:
    action: str
    result: str
    target: str = ""
    details: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "action": self.action,
            "result": self.result,
            "target": self.target,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActivityRecord":
        return cls(
            created_at=str(data.get("created_at") or utc_now_iso()),
            action=str(data.get("action") or ""),
            result=str(data.get("result") or ""),
            target=str(data.get("target") or ""),
            details=str(data.get("details") or ""),
        )

    @property
    def summary_text(self) -> str:
        bits = [self.action, self.result]
        if self.target:
            bits.append(self.target)
        if self.details:
            bits.append(self.details)
        return " | ".join(bit for bit in bits if bit)

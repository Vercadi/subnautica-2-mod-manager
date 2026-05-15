from __future__ import annotations

from pathlib import Path

from ..models.activity import ActivityRecord
from ..utils.json_io import read_json, write_json


class ActivityLog:
    def __init__(self, data_dir: Path, *, limit: int = 200):
        self.path = Path(data_dir) / "activity_log.json"
        self.limit = max(1, int(limit))
        self._records = self.load()

    def load(self) -> list[ActivityRecord]:
        data = read_json(self.path)
        raw_records = data.get("records", [])
        if not isinstance(raw_records, list):
            return []
        records: list[ActivityRecord] = []
        for item in raw_records:
            if not isinstance(item, dict):
                continue
            try:
                records.append(ActivityRecord.from_dict(item))
            except Exception:
                continue
        return records[-self.limit :]

    def append(self, *, action: str, result: str, target: str = "", details: str = "") -> ActivityRecord:
        record = ActivityRecord(action=action, result=result, target=target, details=details)
        self._records.append(record)
        self._records = self._records[-self.limit :]
        self.save()
        return record

    def save(self) -> None:
        write_json(self.path, {"records": [record.to_dict() for record in self._records]})

    def list_records(self, *, limit: int | None = None) -> list[ActivityRecord]:
        if limit is None:
            return list(self._records)
        return list(self._records[-max(0, limit) :])

    @property
    def count(self) -> int:
        return len(self._records)

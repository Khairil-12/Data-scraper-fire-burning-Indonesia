"""Append-safe durable observation history."""

import json
from hashlib import sha256
from pathlib import Path
from typing import Iterator, Sequence

from .models import Hotspot


def _payload_checksum(hotspot: Hotspot) -> str:
    canonical = {
        "source": hotspot.source,
        "sensor": hotspot.sensor,
        "satellite": hotspot.satellite,
        "acq_date": hotspot.acq_date,
        "acq_time": hotspot.acq_time,
        "latitude": hotspot.latitude,
        "longitude": hotspot.longitude,
        "confidence": hotspot.confidence,
        "frp_mw": hotspot.frp_mw,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


class ObservationHistory:
    """Retain unique observations across refreshes."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._records: dict[str, dict[str, object]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    self._records[str(rec["id"])] = rec

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for rec in self._records.values():
                f.write(json.dumps(rec, separators=(",", ":")) + "\n")
        tmp.replace(self.path)

    def upsert(
        self,
        observations: Sequence[Hotspot],
        run_id: str = "run_default",
        seen_at_utc: str = "2026-10-20T00:00:00Z",
    ) -> dict[str, int]:
        inserted = 0
        already_seen = 0
        conflicts = 0

        for item in observations:
            checksum = _payload_checksum(item)
            if item.id not in self._records:
                self._records[item.id] = {
                    "id": item.id,
                    "first_seen_at_utc": seen_at_utc,
                    "last_seen_at_utc": seen_at_utc,
                    "first_run_id": run_id,
                    "last_run_id": run_id,
                    "observation_payload_sha256": checksum,
                    "source_identity": f"{item.source}|{item.sensor}|{item.satellite}",
                }
                inserted += 1
            else:
                existing = self._records[item.id]
                if existing.get("observation_payload_sha256") == checksum:
                    existing["last_seen_at_utc"] = seen_at_utc
                    existing["last_run_id"] = run_id
                    already_seen += 1
                else:
                    conflicts += 1

        self._save()
        return {"inserted": inserted, "already_seen": already_seen, "conflicts": conflicts}

    def read_all(self) -> Iterator[dict[str, object]]:
        yield from self._records.values()

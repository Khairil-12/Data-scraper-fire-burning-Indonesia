"""NASA FIRMS area CSV client."""

import csv
import hashlib
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path

import httpx

INDONESIA_AREA = "94.0,-11.5,142.5,6.5"
BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
REQUIRED_FIRMS_COLUMNS = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence"}
KNOWN_FIRMS_COLUMNS = REQUIRED_FIRMS_COLUMNS | {
    "bright_ti4", "bright_ti5", "scan", "track", "instrument", "version", "frp", "daynight"
}


def processing_level(sensor: str) -> str:
    if sensor.endswith("_NRT"):
        return "NRT"
    if sensor.endswith("_SP"):
        return "SP"
    raise ValueError(f"unknown FIRMS processing level for {sensor}")


def parse_backfill_sensors(sensors: list[str]) -> list[str]:
    for s in sensors:
        if not s.endswith("_SP"):
            raise ValueError(f"sensor {s} is not standard-processing; only _SP sensors allowed for backfill")
    return sensors


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class FirmsClient:
    """Fetch and privately preserve schema-validated FIRMS CSV responses."""

    def __init__(self, map_key: str, raw_dir: Path, *, transport: httpx.BaseTransport | None = None) -> None:
        if not map_key.strip():
            raise ValueError("FIRMS_MAP_KEY is required")
        self._map_key = map_key
        self._raw_dir = Path(raw_dir)
        self._transport = transport
        self.last_fetch_info: dict[str, object] | None = None

    def fetch(self, sensor: str, days: int, *, today: str | None = None) -> bytes:
        if not 1 <= days <= 5:
            raise ValueError("days must be between 1 and 5")
        level = processing_level(sensor)
        url = f"{BASE_URL}/{self._map_key}/{sensor}/{INDONESIA_AREA}/{days}"
        try:
            with httpx.Client(timeout=30, follow_redirects=True, transport=self._transport) as client:
                response = client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise RuntimeError(f"NASA FIRMS request failed: {error.__class__.__name__}") from error
        raw = response.content
        if not raw.strip():
            raise RuntimeError("NASA FIRMS returned an empty response")
        try:
            header = next(csv.reader(StringIO(raw.decode("utf-8-sig"))))
        except (UnicodeDecodeError, StopIteration, csv.Error) as error:
            raise RuntimeError("NASA FIRMS returned unreadable CSV") from error
        columns = {value.strip() for value in header if value.strip()}
        missing = sorted(REQUIRED_FIRMS_COLUMNS - columns)
        if missing:
            raise RuntimeError(f"missing required FIRMS columns: {', '.join(missing)}")
        stamp = today or date.today().isoformat()
        self._raw_dir.mkdir(parents=True, exist_ok=True)
        path = self._raw_dir / f"firms-{stamp}-{sensor}.csv"
        path.write_bytes(raw)
        self.last_fetch_info = {
            "sensor": sensor,
            "processing_level": level,
            "raw_file_path": str(path),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "source_url_redacted": f"{BASE_URL}/<redacted>/{sensor}/{INDONESIA_AREA}/{days}",
            "fetched_at_utc": _utc_now(),
            "row_count_including_header": raw.count(b"\n") + (0 if raw.endswith(b"\n") else 1),
            "required_columns": sorted(REQUIRED_FIRMS_COLUMNS),
            "unexpected_columns": sorted(columns - KNOWN_FIRMS_COLUMNS),
        }
        return raw

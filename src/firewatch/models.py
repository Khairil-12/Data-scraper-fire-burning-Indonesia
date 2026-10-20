"""Validated normalized satellite observations."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from hashlib import sha256

from .severity import classify_severity


def _parse_time(value: str) -> time:
    value = str(value).strip().zfill(4)
    if len(value) != 4 or not value.isdigit():
        raise ValueError("acq_time must be HHMM")
    return time(int(value[:2]), int(value[2:]))


@dataclass(frozen=True, slots=True)
class Hotspot:
    source: str
    sensor: str
    satellite: str
    acq_date: str
    acq_time: str
    latitude: float
    longitude: float
    confidence: str
    frp_mw: float | None = None
    bright_ti4_k: float | None = None
    bright_ti5_k: float | None = None
    scan_km: float | None = None
    track_km: float | None = None
    daynight: str | None = None
    version: str | None = None
    instrument: str | None = None
    province: str | None = None
    geography_match_status: str = "matched"
    distance_to_nearest_land_km: float | None = None
    land_cover_class: str | None = None
    land_cover_source: str | None = None
    land_cover_version: str | None = None
    land_cover_year: int | None = None
    land_cover_classified_at_utc: str | None = None
    dedupe_group_id: str | None = None
    processing_level: str = "NRT"
    raw: dict[str, str] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        if not self.source.strip() or not self.sensor.strip() or not self.satellite.strip():
            raise ValueError("source, sensor, and satellite are required")
        date.fromisoformat(self.acq_date)
        _parse_time(self.acq_time)

    @property
    def observed_at_utc(self) -> datetime:
        return datetime.combine(date.fromisoformat(self.acq_date), _parse_time(self.acq_time), timezone.utc)

    @property
    def id(self) -> str:
        value = "|".join((
            self.source, self.sensor, self.satellite, self.acq_date,
            str(self.acq_time).zfill(4), f"{self.latitude:.4f}", f"{self.longitude:.4f}",
        ))
        return f"firs_{sha256(value.encode()).hexdigest()[:20]}"

    @property
    def severity(self) -> str:
        return classify_severity(self.confidence, self.frp_mw)[0]

    @property
    def severity_reason(self) -> str:
        return classify_severity(self.confidence, self.frp_mw)[1]

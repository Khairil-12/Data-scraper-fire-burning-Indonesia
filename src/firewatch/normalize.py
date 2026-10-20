"""Normalize NASA FIRMS rows into validated satellite observations."""

from collections import Counter
from typing import Iterable

from .geography import classify_geography, is_in_indonesia
from .models import Hotspot


def _number(row: dict[str, str], key: str) -> float | None:
    value = (row.get(key) or "").strip()
    return float(value) if value else None


def normalize_firms_rows(
    rows: Iterable[dict[str, str]], sensor: str
) -> tuple[list[Hotspot], dict[str, int]]:
    """Validate, filter, and deduplicate FIRMS CSV rows."""
    from .firms import processing_level

    hotspots: list[Hotspot] = []
    rejected: Counter[str] = Counter()
    seen: set[str] = set()
    for row in rows:
        try:
            latitude = float(row["latitude"])
            longitude = float(row["longitude"])
            if not is_in_indonesia(latitude, longitude):
                rejected["outside_indonesia"] += 1
                continue
            geo = classify_geography(latitude, longitude)
            hotspot = Hotspot(
                source="NASA FIRMS", sensor=sensor, satellite=row["satellite"],
                acq_date=row["acq_date"], acq_time=row["acq_time"],
                latitude=latitude, longitude=longitude, confidence=row["confidence"],
                province=geo["province"] if geo["province"] != "unknown" else None,
                geography_match_status=str(geo["geography_match_status"]),
                distance_to_nearest_land_km=float(geo["distance_to_nearest_land_km"]),
                frp_mw=_number(row, "frp"), bright_ti4_k=_number(row, "bright_ti4"),
                bright_ti5_k=_number(row, "bright_ti5"),
                scan_km=_number(row, "scan"), track_km=_number(row, "track"),
                daynight=(row.get("daynight") or "").strip() or None,
                version=(row.get("version") or "").strip() or None,
                instrument=(row.get("instrument") or "").strip() or None,
                processing_level=processing_level(sensor),
                raw=dict(row),
            )
        except (KeyError, TypeError, ValueError):
            rejected["invalid"] += 1
            continue
        if hotspot.id in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(hotspot.id)
        hotspots.append(hotspot)
    return hotspots, dict(rejected)

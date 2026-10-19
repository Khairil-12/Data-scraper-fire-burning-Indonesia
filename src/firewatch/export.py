"""Public website and report exports."""

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .geography import province_metadata
from .models import Hotspot


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _record(item: Hotspot, generated_at: datetime) -> dict[str, object]:
    geography = province_metadata(item.province)
    return {
        "id": item.id,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "observed_at_utc": _timestamp(item.observed_at_utc),
        "last_source_report_at_utc": _timestamp(item.observed_at_utc),
        "sensor": item.sensor,
        "satellite": item.satellite,
        "confidence": item.confidence,
        "frp_mw": item.frp_mw,
        "bright_ti4_k": item.bright_ti4_k,
        "daynight": item.daynight,
        "province": item.province or "unknown",
        "province_group": geography["province_group"],
        "province_capital": geography["capital"],
        "classification": item.province or "unknown",
        "severity": item.severity,
        "severity_reason": item.severity_reason,
        "status": "satellite_detected",
        "source": item.source,
        "source_url": "https://firms.modaps.eosdis.nasa.gov/",
        "generated_at_utc": _timestamp(generated_at),
    }


def _atomic_write(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding=encoding, newline="")
    temporary.replace(path)


def write_public_exports(
    hotspots: Iterable[Hotspot], generated_at: datetime, output_dir: Path
) -> None:
    """Write latest GeoJSON, summary JSON, and Excel-compatible CSV."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records = [_record(item, generated_at) for item in hotspots]
    features = [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [record["longitude"], record["latitude"]]}, "properties": record}
        for record in records
    ]
    geojson = {"type": "FeatureCollection", "features": features}
    latest = max((record["last_source_report_at_utc"] for record in records), default=None)
    summary = {
        "generated_at_utc": _timestamp(generated_at),
        "last_source_report_at_utc": latest,
        "counts_by_province": dict(Counter(record["province"] or "unknown" for record in records)),
        "counts_by_sensor": dict(Counter(record["sensor"] for record in records)),
        "source": "NASA FIRMS",
        "source_url": "https://firms.modaps.eosdis.nasa.gov/",
        "caveat": "Satellite-derived estimate. Not confirmed fire perimeter, burned area, or official emergency status.",
    }
    _atomic_write(output_dir / "fire_points_latest.geojson", json.dumps(geojson, separators=(",", ":")))
    _atomic_write(output_dir / "fire_summary_latest.json", json.dumps(summary, separators=(",", ":")))
    csv_path = output_dir / "fire_points_latest.csv"
    temp = csv_path.with_suffix(".csv.tmp")
    fieldnames = list(records[0]) if records else ["id", "latitude", "longitude"]
    with temp.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(records)
    temp.replace(csv_path)

"""Quality report and degradation state evaluation."""

from collections import Counter
from datetime import datetime, timezone
from typing import Sequence

from .models import Hotspot


def _iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_quality_report(
    observations: Sequence[Hotspot],
    rejected: dict[str, int] | None = None,
    run_id: str = "run_default",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    rejected = rejected or {}
    gen_time = generated_at or datetime.now(timezone.utc)
    accepted_count = len(observations)
    rej_invalid = rejected.get("invalid", 0)
    rej_outside = rejected.get("outside_indonesia", 0)
    rej_dup = rejected.get("duplicate", 0)
    fetched_count = accepted_count + sum(rejected.values())

    unknown_prov_count = sum(1 for h in observations if not h.province or h.province == "unknown")
    low_conf_count = sum(1 for h in observations if str(h.confidence).lower() in ("l", "low"))
    coastal_count = sum(1 for h in observations if h.geography_match_status == "coastal_unknown")

    prov_counter = Counter(h.province or "unknown" for h in observations)
    sensor_counter = Counter(h.sensor for h in observations)
    level_counter = Counter(h.processing_level for h in observations)
    land_cover_counter = Counter(h.land_cover_class or "unknown" for h in observations)

    groups = {h.dedupe_group_id for h in observations if h.dedupe_group_id}
    unique_groups_count = len(groups) if groups else accepted_count
    linked_count = sum(1 for h in observations if h.dedupe_group_id and h.dedupe_group_id != h.id)

    unknown_percent = round(100.0 * unknown_prov_count / accepted_count, 2) if accepted_count else 0.0
    low_conf_percent = round(100.0 * low_conf_count / accepted_count, 2) if accepted_count else 0.0
    coastal_percent = round(100.0 * coastal_count / accepted_count, 2) if accepted_count else 0.0
    link_rate = round(100.0 * linked_count / accepted_count, 2) if accepted_count else 0.0

    newest_dt = max((h.observed_at_utc for h in observations), default=None)
    if not newest_dt:
        freshness = "unknown"
    else:
        age_hours = (gen_time - newest_dt).total_seconds() / 3600.0
        freshness = "current" if age_hours <= 8.0 else "stale"

    degradations = []
    if unknown_percent > 2.0:
        degradations.append("unknown_province_high")
    if not any(h.land_cover_class for h in observations):
        degradations.append("land_cover_degraded")

    refresh_status = "success" if not degradations else "partial"

    return {
        "run_id": run_id,
        "generated_at_utc": _iso(gen_time),
        "fetched_count": fetched_count,
        "accepted_count": accepted_count,
        "rejected_invalid_count": rej_invalid,
        "rejected_outside_indonesia_count": rej_outside,
        "duplicate_count": rej_dup,
        "unknown_province_count": unknown_prov_count,
        "low_confidence_count": low_conf_count,
        "counts_by_sensor": dict(sensor_counter),
        "counts_by_processing_level": dict(level_counter),
        "counts_by_province": dict(prov_counter),
        "counts_by_land_cover": dict(land_cover_counter),
        "raw_observation_count": accepted_count,
        "unique_cross_sensor_group_count": unique_groups_count,
        "unknown_province_percent": unknown_percent,
        "low_confidence_percent": low_conf_percent,
        "forest_peat_percent": 0.0,
        "water_coastal_unknown_percent": coastal_percent,
        "cross_sensor_link_rate": link_rate,
        "nrt_vs_sp_difference_count": 0,
        "newest_detection_at_utc": _iso(newest_dt),
        "last_source_report_at_utc": _iso(newest_dt),
        "freshness_status": freshness,
        "land_cover_status": "unclassified_pending_source_approval",
        "boundary_source": "indonesia-38-provinces.geojson",
        "boundary_version": "2022/2023",
        "refresh_status": refresh_status,
        "degradation_reasons": degradations,
    }

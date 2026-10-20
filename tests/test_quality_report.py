from datetime import datetime, timezone

from firewatch.models import Hotspot
from firewatch.quality_report import build_quality_report


def make_hotspot(idx: int, conf: str = "nominal", prov: str = "Kalimantan Tengah") -> Hotspot:
    return Hotspot(
        source="NASA FIRMS",
        sensor="VIIRS_SNPP_NRT",
        satellite="N",
        acq_date="2026-10-20",
        acq_time=f"{idx:02d}00",
        latitude=-2.0 - idx * 0.1,
        longitude=113.0 + idx * 0.1,
        confidence=conf,
        province=prov if prov != "unknown" else None,
        geography_match_status="province_match" if prov != "unknown" else "coastal_unknown",
    )


def test_quality_report_counts_every_required_category():
    observations = [
        make_hotspot(1, conf="high", prov="Kalimantan Tengah"),
        make_hotspot(2, conf="nominal", prov="Kalimantan Tengah"),
        make_hotspot(3, conf="low", prov="unknown"),
    ]
    report = build_quality_report(
        observations,
        rejected={"invalid": 2},
        run_id="run_test",
        generated_at=datetime.now(timezone.utc),
    )
    assert report["fetched_count"] == 5
    assert report["accepted_count"] == 3
    assert report["rejected_invalid_count"] == 2
    assert report["unknown_province_count"] == 1
    assert report["low_confidence_count"] == 1
    assert report["counts_by_province"] == {"Kalimantan Tengah": 2, "unknown": 1}
    assert "freshness_status" in report
    assert "unknown_province_percent" in report
    assert report["boundary_source"] == "indonesia-38-provinces.geojson"

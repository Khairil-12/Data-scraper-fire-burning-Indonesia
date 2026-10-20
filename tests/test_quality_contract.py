import json
from datetime import datetime, timezone

from firewatch.export import write_public_exports
from firewatch.models import Hotspot

REQUIRED_PUBLIC_KEYS = {
    "id", "latitude", "longitude", "observed_at_utc", "sensor", "satellite",
    "confidence", "frp_mw", "bright_ti4_k", "bright_ti5_k", "scan_km",
    "track_km", "daynight", "version", "instrument", "province",
    "province_group", "province_capital", "geography_match_status",
    "distance_to_nearest_land_km", "land_cover_class", "land_cover_source",
    "land_cover_version", "land_cover_year", "land_cover_classified_at_utc",
    "dedupe_group_id", "processing_level", "severity", "severity_method", "source",
}


def test_public_export_meets_data_quality_contract(tmp_path):
    hotspot = Hotspot(
        source="NASA FIRMS", sensor="VIIRS_SNPP_NRT", satellite="N",
        acq_date="2026-10-19", acq_time="0210", latitude=-2.6701,
        longitude=111.7182, confidence="n", frp_mw=42.8,
        province="Kalimantan Tengah",
    )
    write_public_exports([hotspot], datetime(2026, 10, 19, 3, tzinfo=timezone.utc), tmp_path)
    data = json.loads((tmp_path / "fire_points_latest.geojson").read_text())
    assert REQUIRED_PUBLIC_KEYS <= data["features"][0]["properties"].keys()

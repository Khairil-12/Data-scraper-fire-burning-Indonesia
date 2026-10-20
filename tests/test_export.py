import json
from datetime import datetime, timezone

from firewatch.export import write_public_exports
from firewatch.models import Hotspot


def test_public_exports_have_valid_geojson_summary_and_excel_csv(tmp_path):
    item = Hotspot(
        source="NASA FIRMS", sensor="VIIRS_SNPP_NRT", satellite="N",
        acq_date="2026-10-19", acq_time="0210", latitude=-2.6701,
        longitude=111.7182, confidence="nominal", frp_mw=42.8, province="Kalimantan Tengah",
    )
    write_public_exports([item], datetime(2026, 10, 19, 3, 0, tzinfo=timezone.utc), tmp_path)

    geojson = json.loads((tmp_path / "fire_points_latest.geojson").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "fire_summary_latest.json").read_text(encoding="utf-8"))
    csv_bytes = (tmp_path / "fire_points_latest.csv").read_bytes()

    assert geojson["type"] == "FeatureCollection"
    assert geojson["features"][0]["geometry"]["coordinates"] == [111.7182, -2.6701]
    assert geojson["features"][0]["properties"]["source"] == "NASA FIRMS"
    assert geojson["features"][0]["properties"]["province"] == "Kalimantan Tengah"
    assert geojson["features"][0]["properties"]["province_group"] == "Pulau Kalimantan"
    assert geojson["features"][0]["properties"]["province_capital"] == "Palangkaraya"
    assert summary["last_source_report_at_utc"] == "2026-10-19T02:10:00Z"
    assert summary["counts_by_province"] == {"Kalimantan Tengah": 1}
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    assert b";" in csv_bytes.splitlines()[0]

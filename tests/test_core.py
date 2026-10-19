from datetime import datetime, timezone

import pytest

from firewatch.models import Hotspot
from firewatch.normalize import normalize_firms_rows
from firewatch.severity import classify_severity


def test_hotspot_id_is_stable_for_normalized_coordinates():
    common = dict(
        source="NASA FIRMS",
        sensor="VIIRS_SNPP_NRT",
        satellite="N",
        acq_date="2026-10-19",
        acq_time="0210",
        confidence="nominal",
    )
    first = Hotspot(latitude=-2.67011, longitude=111.71821, **common)
    second = Hotspot(latitude=-2.67014, longitude=111.71824, **common)

    assert first.id == second.id
    assert first.id.startswith("firs_")


def test_hotspot_rejects_bad_coordinate():
    with pytest.raises(ValueError, match="latitude"):
        Hotspot(
            source="NASA FIRMS", sensor="VIIRS_SNPP_NRT", satellite="N",
            acq_date="2026-10-19", acq_time="0210", latitude=91,
            longitude=111.7, confidence="nominal",
        )


def test_normalize_discards_duplicate_and_non_indonesia_rows():
    rows = [
        {"latitude": "-2.6701", "longitude": "111.7182", "acq_date": "2026-10-19", "acq_time": "0210", "satellite": "N", "confidence": "nominal", "frp": "42.8", "bright_ti4": "342.5", "daynight": "D"},
        {"latitude": "-2.6701", "longitude": "111.7182", "acq_date": "2026-10-19", "acq_time": "0210", "satellite": "N", "confidence": "nominal", "frp": "42.8", "bright_ti4": "342.5", "daynight": "D"},
        {"latitude": "35.6762", "longitude": "139.6503", "acq_date": "2026-10-19", "acq_time": "0210", "satellite": "N", "confidence": "nominal"},
        {"latitude": "-2.0", "longitude": "140.0", "acq_date": "2026-10-19", "acq_time": "0210", "satellite": "N", "confidence": "nominal"},
    ]

    hotspots, rejected = normalize_firms_rows(rows, "VIIRS_SNPP_NRT")

    assert len(hotspots) == 1
    assert rejected == {"duplicate": 1, "outside_indonesia": 2}
    assert hotspots[0].observed_at_utc == datetime(2026, 10, 19, 2, 10, tzinfo=timezone.utc)
    assert hotspots[0].severity == "high"


@pytest.mark.parametrize(
    ("confidence", "frp", "expected"),
    [("low", 500, "low"), ("nominal", 24.99, "moderate"), ("nominal", 25, "high"), ("nominal", 100, "severe"), ("high", 25, "severe")],
)
def test_severity_rules(confidence, frp, expected):
    assert classify_severity(confidence, frp)[0] == expected

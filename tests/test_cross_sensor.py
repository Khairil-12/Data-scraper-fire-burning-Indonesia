import csv
from io import StringIO
from pathlib import Path

from firewatch.cross_sensor import link_cross_sensor_observations
from firewatch.models import Hotspot
from firewatch.normalize import normalize_firms_rows

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_cross_sensor_sample() -> list[Hotspot]:
    content = (FIXTURES_DIR / "firms_cross_sensor_sample.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(StringIO(content)))
    snpp_rows = [r for r in rows if r["satellite"] == "N"]
    noaa_rows = [r for r in rows if r["satellite"] == "1"]
    hotspots_snpp, _ = normalize_firms_rows(snpp_rows, "VIIRS_SNPP_NRT")
    hotspots_noaa, _ = normalize_firms_rows(noaa_rows, "VIIRS_NOAA20_NRT")
    return hotspots_snpp + hotspots_noaa


def test_pair_within_500m_and_30_minutes_gets_same_dedupe_group():
    items = load_cross_sensor_sample()
    pair = [h for h in items if abs(h.latitude - (-2.2)) < 0.01]
    grouped = link_cross_sensor_observations(pair)
    assert len(grouped) == 2
    assert len({item.dedupe_group_id for item in grouped}) == 1
    assert len({item.id for item in grouped}) == 2


def test_pair_outside_threshold_does_not_link():
    items = load_cross_sensor_sample()
    pair = [h for h in items if abs(h.latitude - (-6.2)) < 0.2]
    grouped = link_cross_sensor_observations(pair)
    assert len(grouped) == 2
    assert len({item.dedupe_group_id for item in grouped}) == 2

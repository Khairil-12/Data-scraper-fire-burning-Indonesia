import csv
from io import StringIO
from pathlib import Path

from firewatch.models import Hotspot
from firewatch.normalize import normalize_firms_rows
from firewatch.persistence import build_persistence_episodes

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def sample_observations() -> list[Hotspot]:
    content = (FIXTURES_DIR / "firms_persistence_sample.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(StringIO(content)))
    snpp_rows = [r for r in rows if r["satellite"] == "N"]
    noaa_rows = [r for r in rows if r["satellite"] == "1"]
    hotspots_snpp, _ = normalize_firms_rows(snpp_rows, "VIIRS_SNPP_NRT")
    hotspots_noaa, _ = normalize_firms_rows(noaa_rows, "VIIRS_NOAA20_NRT")
    return hotspots_snpp + hotspots_noaa


def test_repeated_nearby_detections_form_one_persistence_episode():
    episodes = build_persistence_episodes(sample_observations())
    # Sort by detection count descending
    episodes = sorted(episodes, key=lambda e: e.detection_count, reverse=True)
    episode = episodes[0]
    assert episode.detection_count == 3
    assert episode.first_detected_at_utc.isoformat() == "2026-10-19T00:00:00+00:00"
    assert episode.last_detected_at_utc.isoformat() == "2026-10-19T12:00:00+00:00"
    assert episode.active_duration_hours == 12.0


def test_spatially_separate_detection_starts_new_episode():
    episodes = build_persistence_episodes(sample_observations())
    assert len(episodes) == 2

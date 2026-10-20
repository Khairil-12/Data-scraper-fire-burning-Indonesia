from firewatch.history import ObservationHistory
from firewatch.models import Hotspot

FIXED_TIME = "2026-10-19T02:10:00Z"
FIXED_LATER = "2026-10-19T04:30:00Z"


def make_hotspot(**kwargs) -> Hotspot:
    defaults = {
        "source": "NASA FIRMS",
        "sensor": "VIIRS_SNPP_NRT",
        "satellite": "N",
        "acq_date": "2026-10-19",
        "acq_time": "0210",
        "latitude": -2.6701,
        "longitude": 111.7182,
        "confidence": "nominal",
        "frp_mw": 42.8,
        "province": "Kalimantan Tengah",
    }
    defaults.update(kwargs)
    return Hotspot(**defaults)


def test_same_observation_from_two_refreshes_is_stored_once(tmp_path):
    store = ObservationHistory(tmp_path / "data/private/observation_history.jsonl")
    first = store.upsert([make_hotspot()], run_id="run_1", seen_at_utc=FIXED_TIME)
    second = store.upsert([make_hotspot()], run_id="run_2", seen_at_utc=FIXED_LATER)
    assert first == {"inserted": 1, "already_seen": 0, "conflicts": 0}
    assert second == {"inserted": 0, "already_seen": 1, "conflicts": 0}
    assert len(list(store.read_all())) == 1


def test_newer_source_report_updates_seen_metadata_but_not_raw_identity(tmp_path):
    store = ObservationHistory(tmp_path / "data/private/observation_history.jsonl")
    original = make_hotspot()
    store.upsert([original], run_id="run_1", seen_at_utc=FIXED_TIME)
    store.upsert([original], run_id="run_2", seen_at_utc=FIXED_LATER)
    record = next(store.read_all())
    assert record["id"] == original.id
    assert record["first_seen_at_utc"] == FIXED_TIME
    assert record["last_seen_at_utc"] == FIXED_LATER

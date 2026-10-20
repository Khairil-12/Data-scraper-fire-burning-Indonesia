from pathlib import Path

import httpx
import pytest

from firewatch.firms import FirmsClient


CSV = b"latitude,longitude,acq_date,acq_time,satellite,confidence\n-2.6701,111.7182,2026-10-19,0210,N,nominal\n"


def test_fetch_uses_firms_area_api_and_saves_raw_response(tmp_path):
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=CSV)

    client = FirmsClient(
        "secret-map-key", tmp_path, transport=httpx.MockTransport(handler)
    )

    result = client.fetch("VIIRS_SNPP_NRT", 1, today="2026-10-19")

    assert result == CSV
    assert requests[0].url.path == "/api/area/csv/secret-map-key/VIIRS_SNPP_NRT/94.0,-11.5,142.5,6.5/1"
    assert list(tmp_path.glob("firms-2026-10-19-VIIRS_SNPP_NRT.csv"))


@pytest.mark.parametrize("days", [0, 6])
def test_fetch_rejects_unsupported_day_range(tmp_path, days):
    client = FirmsClient("key", tmp_path, transport=httpx.MockTransport(lambda _: httpx.Response(200)))

    with pytest.raises(ValueError, match="days"):
        client.fetch("VIIRS_SNPP_NRT", days)


def test_fetch_rejects_missing_required_firms_header(tmp_path):
    bad_csv = b"latitude,longitude,acq_date\n-2.0,113.0,2026-10-20\n"
    client = FirmsClient("secret-map-key", tmp_path, transport=httpx.MockTransport(lambda _: httpx.Response(200, content=bad_csv)))

    with pytest.raises(RuntimeError, match="missing required FIRMS columns: acq_time, confidence, satellite"):
        client.fetch("VIIRS_SNPP_NRT", 1)


def test_source_config_marks_nrt_and_standard_processing():
    from firewatch.firms import parse_backfill_sensors, processing_level
    assert processing_level("VIIRS_SNPP_NRT") == "NRT"
    assert processing_level("VIIRS_SNPP_SP") == "SP"

    with pytest.raises(ValueError, match="standard-processing"):
        parse_backfill_sensors(["VIIRS_SNPP_NRT"])


def test_fetch_raises_without_leaking_map_key(tmp_path):
    client = FirmsClient(
        "secret-map-key", tmp_path, transport=httpx.MockTransport(lambda _: httpx.Response(403, text="denied"))
    )

    with pytest.raises(RuntimeError) as error:
        client.fetch("VIIRS_SNPP_NRT", 1)

    assert "secret-map-key" not in str(error.value)

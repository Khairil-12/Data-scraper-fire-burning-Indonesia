import json

import httpx

from firewatch.cli import main


CSV = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
-2.6701,111.7182,342.5,0.4,0.4,2026-10-19,0210,N,nominal,2,300,42.8,D
"""


def test_refresh_writes_latest_public_outputs(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRMS_MAP_KEY", "test-key")

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CSV)

    result = main(
        [
            "refresh", "--days", "1", "--root", str(tmp_path),
            "--sensors", "VIIRS_SNPP_NRT", "--today", "2026-10-19",
        ],
        transport=httpx.MockTransport(handler),
    )

    assert result == 0
    summary = json.loads((tmp_path / "data/public/fire_summary_latest.json").read_text())
    manifest = json.loads((tmp_path / "data/private/run_manifest_latest.json").read_text())
    assert summary["counts_by_sensor"] == {"VIIRS_SNPP_NRT": 1}
    assert manifest["status"] == "success"
    assert manifest["accepted"] == 1

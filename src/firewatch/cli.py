"""Command-line refresh for Indonesia Fire Watch."""

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import httpx

from .export import write_public_exports
from .firms import FirmsClient
from .normalize import normalize_firms_rows


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _write_manifest(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def refresh(args: argparse.Namespace, *, transport: httpx.BaseTransport | None = None) -> int:
    key = os.getenv("FIRMS_MAP_KEY", "")
    if not key:
        raise RuntimeError("FIRMS_MAP_KEY is required")
    root = Path(args.root)
    raw_dir = root / "data/raw"
    private_dir = root / "data/private"
    public_dir = root / "data/public"
    started_at = _utc_now()
    client = FirmsClient(key, raw_dir, transport=transport)
    all_hotspots = []
    rejected: dict[str, int] = {}
    try:
        for sensor in args.sensors:
            raw = client.fetch(sensor, args.days, today=args.today)
            rows = csv.DictReader(StringIO(raw.decode("utf-8-sig")))
            hotspots, row_rejected = normalize_firms_rows(rows, sensor)
            all_hotspots.extend(hotspots)
            for reason, count in row_rejected.items():
                rejected[reason] = rejected.get(reason, 0) + count
        generated_at = _utc_now()
        write_public_exports(all_hotspots, generated_at, public_dir)
        latest = max((item.observed_at_utc for item in all_hotspots), default=None)
        _write_manifest(private_dir / "run_manifest_latest.json", {
            "status": "success",
            "started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
            "completed_at_utc": generated_at.isoformat().replace("+00:00", "Z"),
            "last_source_report_at_utc": latest.isoformat().replace("+00:00", "Z") if latest else None,
            "sensors": args.sensors,
            "accepted": len(all_hotspots),
            "rejected": rejected,
        })
    except Exception as error:
        _write_manifest(private_dir / "run_manifest_latest.json", {
            "status": "failed",
            "started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
            "error": error.__class__.__name__,
        })
        raise
    print(public_dir / "fire_points_latest.geojson")
    return 0


def main(argv: list[str] | None = None, *, transport: httpx.BaseTransport | None = None) -> int:
    parser = argparse.ArgumentParser(prog="firewatch")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("refresh")
    command.add_argument("--days", type=int, default=1)
    command.add_argument("--root", default=".")
    command.add_argument("--sensors", nargs="+", default=["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"])
    command.add_argument("--today", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    return refresh(args, transport=transport)


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line refresh for Indonesia Fire Watch."""

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import httpx

from .cross_sensor import link_cross_sensor_observations
from .export import write_public_exports
from .firms import FirmsClient, parse_backfill_sensors
from .history import ObservationHistory
from .normalize import normalize_firms_rows
from .quality_report import build_quality_report


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
    fetch_lineage: list[dict[str, object]] = []
    try:
        for sensor in args.sensors:
            raw = client.fetch(sensor, args.days, today=args.today)
            if client.last_fetch_info:
                fetch_lineage.append(client.last_fetch_info)
            rows = csv.DictReader(StringIO(raw.decode("utf-8-sig")))
            hotspots, row_rejected = normalize_firms_rows(rows, sensor)
            all_hotspots.extend(hotspots)
            for reason, count in row_rejected.items():
                rejected[reason] = rejected.get(reason, 0) + count
        all_hotspots = link_cross_sensor_observations(all_hotspots)
        history_store = ObservationHistory(private_dir / "observation_history.jsonl")
        run_id = f"run_{started_at.strftime('%Y%m%dT%H%M%SZ')}"
        history_stats = history_store.upsert(
            all_hotspots,
            run_id=run_id,
            seen_at_utc=started_at.isoformat().replace("+00:00", "Z"),
        )
        generated_at = _utc_now()
        quality_rep = build_quality_report(
            all_hotspots,
            rejected=rejected,
            run_id=run_id,
            generated_at=generated_at,
        )
        write_public_exports(all_hotspots, generated_at, public_dir, quality_report=quality_rep)
        latest = max((item.observed_at_utc for item in all_hotspots), default=None)
        total = len(all_hotspots) + sum(rejected.values())
        unknown_count = sum(1 for h in all_hotspots if h.geography_match_status != "province_match")
        _write_manifest(private_dir / "run_manifest_latest.json", {
            "status": "success",
            "run_id": run_id,
            "started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
            "completed_at_utc": generated_at.isoformat().replace("+00:00", "Z"),
            "last_source_report_at_utc": latest.isoformat().replace("+00:00", "Z") if latest else None,
            "sensors": args.sensors,
            "accepted": len(all_hotspots),
            "rejected": rejected,
            "historical_inserted_count": history_stats["inserted"],
            "historical_already_seen_count": history_stats["already_seen"],
            "history_conflict_count": history_stats["conflicts"],
            "quality": quality_rep,
            "fetch_lineage": fetch_lineage,
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


def backfill_standard(args: argparse.Namespace, *, transport: httpx.BaseTransport | None = None) -> int:
    key = os.getenv("FIRMS_MAP_KEY", "")
    if not key:
        raise RuntimeError("FIRMS_MAP_KEY is required")
    sensors = parse_backfill_sensors(args.sensors)
    root = Path(args.root)
    raw_dir = root / "data/raw"
    client = FirmsClient(key, raw_dir, transport=transport)
    for sensor in sensors:
        client.fetch(sensor, args.days)
    return 0


def main(argv: list[str] | None = None, *, transport: httpx.BaseTransport | None = None) -> int:
    parser = argparse.ArgumentParser(prog="firewatch")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("refresh")
    command.add_argument("--days", type=int, default=1)
    command.add_argument("--root", default=".")
    command.add_argument("--sensors", nargs="+", default=["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"])
    command.add_argument("--today", default=None, help=argparse.SUPPRESS)

    backfill = commands.add_parser("backfill-standard")
    backfill.add_argument("--from", dest="from_date", required=False)
    backfill.add_argument("--to", dest="to_date", required=False)
    backfill.add_argument("--days", type=int, default=1)
    backfill.add_argument("--root", default=".")
    backfill.add_argument("--sensors", nargs="+", default=["VIIRS_SNPP_SP", "VIIRS_NOAA20_SP"])

    args = parser.parse_args(argv)
    if args.command == "refresh":
        return refresh(args, transport=transport)
    if args.command == "backfill-standard":
        return backfill_standard(args, transport=transport)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

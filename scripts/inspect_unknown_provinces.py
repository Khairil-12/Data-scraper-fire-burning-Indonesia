"""Diagnose unknown province detections by calculating nearest boundary distance."""

import csv
import json
import sys
from pathlib import Path

from firewatch.geography import diagnose_unknown_province


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: inspect_unknown_provinces.py <geojson_in> <csv_out>")
        return 1
    geojson_path = Path(sys.argv[1])
    csv_path = Path(sys.argv[2])
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    unknown_rows = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        if props.get("province") == "unknown" or props.get("geography_match_status") != "province_match":
            lat = float(props["latitude"])
            lon = float(props["longitude"])
            diag = diagnose_unknown_province(lat, lon)
            unknown_rows.append({
                "id": props.get("id", ""),
                "latitude": lat,
                "longitude": lon,
                "nearest_province": diag["nearest_province"],
                "distance_to_boundary_km": diag["distance_to_boundary_km"],
                "observed_at_utc": props.get("observed_at_utc", ""),
                "sensor": props.get("sensor", ""),
            })

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "latitude", "longitude", "nearest_province",
        "distance_to_boundary_km", "observed_at_utc", "sensor",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(unknown_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

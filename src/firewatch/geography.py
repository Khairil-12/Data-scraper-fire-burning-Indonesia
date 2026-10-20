"""Versioned Indonesia boundary and province classification."""

import json
import math
from functools import lru_cache
from pathlib import Path

from shapely import make_valid
from shapely.geometry import Point, shape
from shapely.ops import nearest_points
from shapely.strtree import STRtree

REFERENCE_DIR = Path(__file__).resolve().parents[2] / "data/reference"
ADM0_PATH = REFERENCE_DIR / "indonesia-adm0.geojson"
BOUNDARY_PATH = ADM0_PATH if ADM0_PATH.exists() else REFERENCE_DIR / "geoBoundaries-IDN-ADM0_simplified.geojson"
# 2022/2023 Indonesia provincial boundary source: 38 provinces.
# Names intentionally remain official Indonesian names from PROVINSI.
PROVINCE_PATH = REFERENCE_DIR / "indonesia-38-provinces.geojson"

COASTAL_UNKNOWN_MAX_DISTANCE_KM = 5.0
OFFSHORE_UNKNOWN_MIN_DISTANCE_KM = 5.0

# Exact user-approved 38 province classification and provincial capitals.
PROVINCE_METADATA = {
    "Aceh": ("Pulau Sumatera", "Banda Aceh"), "Sumatera Utara": ("Pulau Sumatera", "Medan"), "Sumatera Barat": ("Pulau Sumatera", "Padang"), "Riau": ("Pulau Sumatera", "Pekanbaru"), "Kepulauan Riau": ("Pulau Sumatera", "Tanjung Pinang"), "Jambi": ("Pulau Sumatera", "Jambi"), "Bengkulu": ("Pulau Sumatera", "Bengkulu"), "Sumatera Selatan": ("Pulau Sumatera", "Palembang"), "Kepulauan Bangka Belitung": ("Pulau Sumatera", "Pangkal Pinang"), "Lampung": ("Pulau Sumatera", "Bandar Lampung"),
    "DKI Jakarta": ("Pulau Jawa", "Jakarta"), "Banten": ("Pulau Jawa", "Serang"), "Jawa Barat": ("Pulau Jawa", "Bandung"), "Jawa Tengah": ("Pulau Jawa", "Semarang"), "Daerah Istimewa Yogyakarta": ("Pulau Jawa", "Yogyakarta"), "Jawa Timur": ("Pulau Jawa", "Surabaya"),
    "Bali": ("Kepulauan Nusa Tenggara & Bali", "Denpasar"), "Nusa Tenggara Barat": ("Kepulauan Nusa Tenggara & Bali", "Mataram"), "Nusa Tenggara Timur": ("Kepulauan Nusa Tenggara & Bali", "Kupang"),
    "Kalimantan Barat": ("Pulau Kalimantan", "Pontianak"), "Kalimantan Tengah": ("Pulau Kalimantan", "Palangkaraya"), "Kalimantan Selatan": ("Pulau Kalimantan", "Banjarbaru"), "Kalimantan Timur": ("Pulau Kalimantan", "Samarinda"), "Kalimantan Utara": ("Pulau Kalimantan", "Tanjung Selor"),
    "Sulawesi Utara": ("Pulau Sulawesi", "Manado"), "Gorontalo": ("Pulau Sulawesi", "Gorontalo"), "Sulawesi Tengah": ("Pulau Sulawesi", "Palu"), "Sulawesi Barat": ("Pulau Sulawesi", "Mamuju"), "Sulawesi Selatan": ("Pulau Sulawesi", "Makassar"), "Sulawesi Tenggara": ("Pulau Sulawesi", "Kendari"),
    "Maluku": ("Kepulauan Maluku & Pulau Papua", "Ambon"), "Maluku Utara": ("Kepulauan Maluku & Pulau Papua", "Sofifi"), "Papua": ("Kepulauan Maluku & Pulau Papua", "Jayapura"), "Papua Barat": ("Kepulauan Maluku & Pulau Papua", "Manokwari"), "Papua Selatan": ("Kepulauan Maluku & Pulau Papua", "Merauke"), "Papua Tengah": ("Kepulauan Maluku & Pulau Papua", "Nabire"), "Papua Pegunungan": ("Kepulauan Maluku & Pulau Papua", "Jayawijaya"), "Papua Barat Daya": ("Kepulauan Maluku & Pulau Papua", "Sorong"),
}


def province_metadata(province: str | None) -> dict[str, str | None]:
    """Return user-approved group and capital for one of 38 provinces."""
    group, capital = PROVINCE_METADATA.get(province or "", ("unknown", None))
    return {"province_group": group, "capital": capital}


@lru_cache(maxsize=1)
def indonesia_boundary():
    data = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    geometries = [feature["geometry"] for feature in data["features"]]
    if len(geometries) != 1:
        raise ValueError("Indonesia boundary must contain exactly one feature")
    return shape(geometries[0])


@lru_cache(maxsize=1)
def province_index() -> tuple[STRtree, list[str]]:
    data = json.loads(PROVINCE_PATH.read_text(encoding="utf-8"))
    geometries = [shape(feature["geometry"]) for feature in data["features"]]
    names = [feature["properties"]["PROVINSI"] for feature in data["features"]]
    return STRtree(geometries), names


def is_in_indonesia(latitude: float, longitude: float) -> bool:
    return indonesia_boundary().covers(Point(longitude, latitude))


def province_for_coordinate(latitude: float, longitude: float) -> str | None:
    point = Point(longitude, latitude)
    tree, names = province_index()
    for index in tree.query(point, predicate="intersects"):
        return names[index]
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * radius_km * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))


@lru_cache(maxsize=1)
def province_features():
    data = json.loads(PROVINCE_PATH.read_text(encoding="utf-8"))
    return [(feature["properties"]["PROVINSI"], make_valid(shape(feature["geometry"]))) for feature in data["features"]]


def diagnose_unknown_province(latitude: float, longitude: float) -> dict[str, object]:
    point = Point(longitude, latitude)
    nearest_province = None
    min_dist_km = float("inf")
    for name, geom in province_features():
        p1, p2 = nearest_points(point, geom)
        dist = haversine_km(latitude, longitude, p2.y, p2.x)
        if dist < min_dist_km:
            min_dist_km = dist
            nearest_province = name
    return {
        "assigned_province": "unknown",
        "nearest_province": nearest_province or "unknown",
        "distance_to_boundary_km": round(min_dist_km, 4),
        "boundary_source": "indonesia-38-provinces.geojson",
        "boundary_version": "2022/2023",
    }


def province_boundary_coverage_errors() -> list[str]:
    adm0 = make_valid(indonesia_boundary())
    # 1 meter buffer in degrees at equator (~1 / 111320)
    buffered_adm0 = adm0.buffer(1.0 / 111320.0)
    uncovered = []
    for name, geom in province_features():
        diff = geom.difference(buffered_adm0)
        if not diff.is_empty and diff.area > 1e-9:
            uncovered.append(name)
    return uncovered


def _extract_coord(point_or_lat: object, longitude: float | None = None) -> tuple[float, float]:
    if isinstance(point_or_lat, (int, float)) and longitude is not None:
        return float(point_or_lat), float(longitude)
    if hasattr(point_or_lat, "y") and hasattr(point_or_lat, "x"):
        return float(point_or_lat.y), float(point_or_lat.x)
    if isinstance(point_or_lat, (tuple, list)) and len(point_or_lat) >= 2:
        return float(point_or_lat[0]), float(point_or_lat[1])
    raise ValueError(f"Invalid coordinate or point: {point_or_lat}")


def classify_unmatched_geography(point_or_lat: object, longitude: float | None = None) -> str:
    if isinstance(point_or_lat, (int, float)) and longitude is None:
        dist_km = float(point_or_lat)
    else:
        lat, lon = _extract_coord(point_or_lat, longitude)
        diagnostic = diagnose_unknown_province(lat, lon)
        dist_km = float(diagnostic["distance_to_boundary_km"])
    if dist_km <= COASTAL_UNKNOWN_MAX_DISTANCE_KM:
        return "coastal_unknown"
    return "offshore_unknown"


def classify_geography(point_or_lat: object, longitude: float | None = None) -> dict[str, object]:
    lat, lon = _extract_coord(point_or_lat, longitude)
    province = province_for_coordinate(lat, lon)
    if province:
        meta = province_metadata(province)
        return {
            "province": province,
            "province_group": meta["province_group"],
            "province_capital": meta["capital"],
            "geography_match_status": "province_match",
            "distance_to_nearest_land_km": 0.0,
        }
    diagnostic = diagnose_unknown_province(lat, lon)
    dist_km = float(diagnostic["distance_to_boundary_km"])
    status = classify_unmatched_geography(dist_km)
    return {
        "province": "unknown",
        "province_group": "unknown",
        "province_capital": None,
        "geography_match_status": status,
        "distance_to_nearest_land_km": dist_km,
    }


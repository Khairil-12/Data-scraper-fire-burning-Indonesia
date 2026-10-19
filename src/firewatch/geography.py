"""Versioned Indonesia boundary and province classification."""

import json
from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

REFERENCE_DIR = Path(__file__).resolve().parents[2] / "data/reference"
BOUNDARY_PATH = REFERENCE_DIR / "geoBoundaries-IDN-ADM0_simplified.geojson"
# 2022/2023 Indonesia provincial boundary source: 38 provinces.
# Names intentionally remain official Indonesian names from PROVINSI.
PROVINCE_PATH = REFERENCE_DIR / "indonesia-38-provinces.geojson"

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


from firewatch.geography import (
    PROVINCE_METADATA,
    diagnose_unknown_province,
    province_boundary_coverage_errors,
    province_for_coordinate,
    province_metadata,
)


def test_unknown_province_diagnostic_returns_distance_and_nearest_name():
    result = diagnose_unknown_province(latitude=-2.82823, longitude=122.17849)
    assert result["nearest_province"] == "Sulawesi Tengah"
    assert result["distance_to_boundary_km"] > 0
    assert result["assigned_province"] == "unknown"


def test_all_province_polygons_are_covered_by_indonesia_boundary():
    uncovered = province_boundary_coverage_errors()
    assert uncovered == []


def test_unmatched_province_point_near_land_is_coastal_unknown():
    from firewatch.geography import classify_unmatched_geography
    # (-2.82823, 122.17849) is ~0.003 km from boundary (near land)
    assert classify_unmatched_geography(-2.82823, 122.17849) == "coastal_unknown"


def test_unmatched_province_point_far_from_land_is_offshore_unknown():
    from firewatch.geography import classify_unmatched_geography
    # 50+ km offshore in Indian ocean
    assert classify_unmatched_geography(-10.0, 110.0) == "offshore_unknown"


def test_unmatched_point_is_never_assigned_to_nearest_province():
    from firewatch.geography import classify_geography
    geography = classify_geography(-2.82823, 122.17849)
    assert geography["province"] == "unknown"
    assert geography["province_group"] == "unknown"
    assert geography["province_capital"] is None
    assert geography["geography_match_status"] == "coastal_unknown"
    assert geography["distance_to_nearest_land_km"] > 0


def test_metadata_covers_exactly_all_38_boundary_provinces():
    assert len(PROVINCE_METADATA) == 38
    assert province_metadata("Kalimantan Tengah") == {"province_group": "Pulau Kalimantan", "capital": "Palangkaraya"}
    assert province_metadata("Papua Barat Daya") == {"province_group": "Kepulauan Maluku & Pulau Papua", "capital": "Sorong"}


def test_coordinates_classify_current_38_province_dataset():
    cases = [((-6.2, 106.8), "DKI Jakarta"), ((-0.9471, 100.4172), "Sumatera Barat"), ((-2.2, 113.9), "Kalimantan Tengah"), ((-3.8566, 119.9806), "Sulawesi Selatan"), ((-3.4931, 126.6718), "Maluku"), ((-8.65, 115.22), "Bali"), ((-6.8545, 139.9052), "Papua Selatan")]
    for (latitude, longitude), expected in cases:
        assert province_for_coordinate(latitude, longitude) == expected


def test_unknown_metadata_has_safe_fallback():
    assert province_metadata(None) == {"province_group": "unknown", "capital": None}

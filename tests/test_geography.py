from firewatch.geography import PROVINCE_METADATA, province_for_coordinate, province_metadata


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

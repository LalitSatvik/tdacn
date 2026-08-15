import pytest

from tdacn.segment.industry import sic_to_division


@pytest.mark.parametrize(
    "sic,expected",
    [
        ("7372", "Services"),  # prepackaged software
        ("6022", "Finance, Insurance, and Real Estate"),  # state commercial banks
        ("2834", "Manufacturing"),  # pharmaceutical preparations
        ("1311", "Mining"),  # crude petroleum and natural gas
        ("4911", "Transportation, Communications, Electric, Gas, and Sanitary Services"),
        ("0100", "Agriculture, Forestry, and Fishing"),
        ("9199", "Public Administration"),
    ],
)
def test_sic_to_division_maps_known_ranges(sic, expected):
    assert sic_to_division(sic) == expected


def test_sic_to_division_returns_unknown_for_unmapped_or_missing_codes():
    assert sic_to_division("") == "Unknown"
    assert sic_to_division(None) == "Unknown"
    assert sic_to_division("0000") == "Unknown"

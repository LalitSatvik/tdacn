"""Standard SIC division lookup (SEC's own coarse industry grouping) for
the industry segmentation dimension. `entities.industry_code` from the SEC
adapter is a raw 2-4 digit SIC code; this rolls it up to the ~10-way
division breakdown that keeps per-segment filer counts usable.
"""

from typing import Optional

# (low, high) inclusive ranges over the first two SIC digits -> division name.
_DIVISIONS = [
    (1, 9, "Agriculture, Forestry, and Fishing"),
    (10, 14, "Mining"),
    (15, 17, "Construction"),
    (20, 39, "Manufacturing"),
    (40, 49, "Transportation, Communications, Electric, Gas, and Sanitary Services"),
    (50, 51, "Wholesale Trade"),
    (52, 59, "Retail Trade"),
    (60, 67, "Finance, Insurance, and Real Estate"),
    (70, 89, "Services"),
    (91, 99, "Public Administration"),
]


def sic_to_division(sic: Optional[str]) -> str:
    if not sic:
        return "Unknown"
    try:
        prefix = int(str(sic)[:2])
    except ValueError:
        return "Unknown"

    for low, high, division in _DIVISIONS:
        if low <= prefix <= high:
            return division
    return "Unknown"

"""
Inspect geographic Chilean fixed-line phone observations from OpenStreetMap.

This script parses phone-tagged OSM features, extracts plausible Chilean
fixed-line area codes, and writes the accepted observations to an
inspection GeoJSON.

The output is NOT production GeoPedia data. It exists only so we can
inspect the geographic distribution of OSM phone observations before
constructing area-code polygons.

Input
-----
data/raw/countries/chile/osm/phones.geojson

Output
------
data/intermediate/countries/chile/inspection/osm-phone-code-points.geojson

Run with:

    python scripts/countries/chile/inspect/osm-phone-code-points.py
"""

import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "chile"
    / "osm"
    / "phones.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "inspection"
    / "osm-phone-code-points.geojson"
)


KNOWN_AREA_CODES = {
    "2",
    "32",
    "33",
    "34",
    "35",
    "41",
    "42",
    "43",
    "45",
    "51",
    "52",
    "53",
    "55",
    "57",
    "58",
    "61",
    "63",
    "64",
    "65",
    "67",
    "71",
    "72",
    "73",
    "75",
}


PHONE_PROPERTIES = (
    "phone",
    "contact:phone",
)


def load_geojson(
    path: Path,
) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def split_phone_values(
    value: str,
) -> list[str]:
    """
    Split fields containing multiple numbers.

    Semicolons are the standard OSM separator. Commas are also accepted.
    A slash is intentionally not used because it sometimes appears
    inside unusual phone formatting.
    """

    return [
        part.strip()
        for part in re.split(
            r"[;,]+",
            value,
        )
        if part.strip()
    ]


def digits_only(
    value: str,
) -> str:
    return re.sub(
        r"\D",
        "",
        value,
    )


def normalize_country_prefix(
    raw_phone: str,
) -> tuple[str, bool]:
    """
    Return digits after removing a Chilean country prefix.

    The boolean indicates whether an explicit Chilean country prefix
    was present.

    Accepted explicit prefixes:
        +56
        0056
    """

    stripped = raw_phone.strip()

    digits = digits_only(
        stripped
    )

    if not digits:
        return "", False

    if stripped.startswith("+"):
        if not digits.startswith("56"):
            return "", False

        return digits[2:], True

    if digits.startswith("0056"):
        return digits[4:], True

    # Some OSM values omit the + but explicitly contain 56.
    #
    # Require enough digits to make it plausible that 56 is actually
    # the country code rather than part of a local number.
    if (
        digits.startswith("56")
        and len(digits) >= 10
    ):
        return digits[2:], True

    return digits, False


def extract_area_code(
    raw_phone: str,
) -> tuple[
    str | None,
    str,
    str | None,
]:
    """
    Parse a possible Chilean fixed-line number.

    Returns:
        area_code
        classification
        normalized_digits

    We intentionally favor precision over recovering every possible
    historical/local-only number. Ambiguous numbers can be investigated
    separately rather than becoming incorrect Voronoi seeds.
    """

    (
        national_digits,
        explicit_chile_prefix,
    ) = normalize_country_prefix(
        raw_phone
    )

    if not national_digits:
        return (
            None,
            "invalid_or_foreign",
            None,
        )

    # Historical/domestic formatting may include a leading zero.
    if national_digits.startswith("0"):
        national_digits = (
            national_digits[1:]
        )

    if not national_digits:
        return (
            None,
            "unclassified",
            None,
        )

    # Chilean mobile numbers use 9 after +56.
    if (
        national_digits.startswith("9")
        and len(national_digits) >= 8
    ):
        return (
            None,
            "mobile",
            national_digits,
        )

    # Santiago:
    #
    # Modern format is:
    #   2 + 8 subscriber digits
    #
    # Older OSM entries may contain:
    #   2 + 7 subscriber digits
    #
    # Both are useful geographic evidence when the number explicitly
    # identifies code 2.
    if national_digits.startswith("2"):
        if len(national_digits) in {
            8,
            9,
        }:
            return (
                "2",
                "fixed",
                national_digits,
            )

    # Other geographic area codes are two digits.
    #
    # Chilean OSM data contains both modern and older subscriber-number
    # lengths, so accept 7 or 8 digits following the two-digit code.
    if len(national_digits) in {
        9,
        10,
    }:
        candidate = (
            national_digits[:2]
        )

        if candidate in KNOWN_AREA_CODES:
            return (
                candidate,
                "fixed",
                national_digits,
            )

    # For explicitly Chilean numbers, also accept an older compact
    # geographic representation with six subscriber digits.
    if (
        explicit_chile_prefix
        and len(national_digits) == 8
    ):
        candidate = (
            national_digits[:2]
        )

        if candidate in KNOWN_AREA_CODES:
            return (
                candidate,
                "fixed",
                national_digits,
            )

    return (
        None,
        "unclassified",
        national_digits,
    )


def get_point_coordinates(
    feature: dict,
) -> list[float] | None:
    geometry = feature.get(
        "geometry"
    )

    if not geometry:
        return None

    if geometry.get("type") != "Point":
        return None

    coordinates = geometry.get(
        "coordinates"
    )

    if (
        not isinstance(
            coordinates,
            list,
        )
        or len(coordinates) < 2
    ):
        return None

    return [
        coordinates[0],
        coordinates[1],
    ]


def create_output_feature(
    source_feature: dict,
    coordinates: list[float],
    raw_phone: str,
    phone_property: str,
    area_code: str,
    normalized_digits: str,
) -> dict:
    properties = source_feature.get(
        "properties",
        {}
    )

    return {
        "type": "Feature",
        "properties": {
            "area_code": area_code,
            "phone": raw_phone,
            "normalized_phone": normalized_digits,
            "phone_property": phone_property,
            "osm_id": properties.get(
                "@id"
            ),
            "name": properties.get(
                "name"
            ),
            "city": properties.get(
                "addr:city"
            ),
        },
        "geometry": {
            "type": "Point",
            "coordinates": coordinates,
        },
    }


def main() -> None:
    geojson = load_geojson(
        INPUT_PATH
    )

    source_features = geojson.get(
        "features",
        [],
    )

    classification_counts = Counter()
    area_code_counts = Counter()

    accepted_features = []

    rejected_samples = []

    for source_feature in source_features:
        coordinates = (
            get_point_coordinates(
                source_feature
            )
        )

        if coordinates is None:
            continue

        properties = source_feature.get(
            "properties",
            {},
        )

        for phone_property in PHONE_PROPERTIES:
            raw_value = properties.get(
                phone_property
            )

            if not isinstance(
                raw_value,
                str,
            ):
                continue

            for raw_phone in split_phone_values(
                raw_value
            ):
                (
                    area_code,
                    classification,
                    normalized_digits,
                ) = extract_area_code(
                    raw_phone
                )

                classification_counts[
                    classification
                ] += 1

                if (
                    classification == "fixed"
                    and area_code is not None
                    and normalized_digits is not None
                ):
                    area_code_counts[
                        area_code
                    ] += 1

                    accepted_features.append(
                        create_output_feature(
                            source_feature,
                            coordinates,
                            raw_phone,
                            phone_property,
                            area_code,
                            normalized_digits,
                        )
                    )

                elif (
                    classification
                    not in {
                        "mobile",
                    }
                    and len(
                        rejected_samples
                    )
                    < 40
                ):
                    rejected_samples.append(
                        (
                            raw_phone,
                            classification,
                            properties.get(
                                "name"
                            ),
                            properties.get(
                                "addr:city"
                            ),
                        )
                    )

    print()
    print("OSM PHONE POINT INSPECTION")
    print("=" * 55)

    print(
        f"Source features:       {len(source_features)}"
    )
    print(
        f"Accepted fixed points: {len(accepted_features)}"
    )

    print()
    print("CLASSIFICATION")
    print("=" * 55)

    for (
        classification,
        count,
    ) in classification_counts.most_common():
        print(
            f"{classification:<20} {count:>6}"
        )

    print()
    print("AREA CODE POINT COUNTS")
    print("=" * 55)

    for area_code in sorted(
        KNOWN_AREA_CODES,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        print(
            f"{area_code:>2} -> "
            f"{area_code_counts[area_code]:>5}"
        )

    missing_codes = sorted(
        KNOWN_AREA_CODES
        - set(area_code_counts),
        key=lambda value: (
            len(value),
            value,
        ),
    )

    print()
    print(
        f"Area codes represented: "
        f"{len(area_code_counts)} / "
        f"{len(KNOWN_AREA_CODES)}"
    )

    if missing_codes:
        print(
            "Missing area codes: "
            + ", ".join(
                missing_codes
            )
        )

    if rejected_samples:
        print()
        print("REJECTED / AMBIGUOUS SAMPLES")
        print("=" * 55)

        for (
            raw_phone,
            classification,
            name,
            city,
        ) in rejected_samples:
            print(
                f"{raw_phone}"
            )
            print(
                f"  classification: {classification}"
            )
            print(
                f"  name: {name}"
            )
            print(
                f"  city: {city}"
            )

    output_geojson = {
        "type": "FeatureCollection",
        "features": accepted_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output_geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_mb = (
        OUTPUT_PATH.stat().st_size
        / 1024
        / 1024
    )

    print()
    print(
        f"Output points: {len(accepted_features)}"
    )
    print(
        f"Output size:   {size_mb:.2f} MB"
    )
    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
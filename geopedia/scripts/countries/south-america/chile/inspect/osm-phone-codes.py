"""
Inspect Chilean phone numbers extracted from OpenStreetMap.

Reads phone-tagged OSM features exported from Overpass Turbo and attempts
to classify their phone numbers into known Chilean fixed-line area codes.

This is an inspection script only. It does not modify the source data or
generate GeoPedia runtime data.

Input
-----
data/raw/countries/chile/osm/phones.geojson

Run with:

    python scripts/countries/chile/inspect/osm-phone-codes.py
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


def load_geojson() -> dict:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"File not found: {INPUT_PATH}"
        )

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def split_phone_values(
    value: str,
) -> list[str]:
    """
    Split fields containing multiple phone numbers.

    Semicolons, commas, and forward slashes are common separators in
    OSM phone tags. We deliberately do not split on spaces or hyphens
    because those are commonly used inside individual phone numbers.
    """

    return [
        part.strip()
        for part in re.split(
            r"[;,/]+",
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


def extract_area_code(
    raw_phone: str,
) -> tuple[str | None, str]:
    """
    Attempt to extract a Chilean fixed-line area code.

    Returns:
        (area_code, classification)

    The parser is intentionally conservative. Numbers that cannot be
    interpreted confidently are retained as unclassified rather than
    guessed.
    """

    digits = digits_only(
        raw_phone
    )

    if not digits:
        return None, "empty"

    # Remove common international prefixes.
    #
    # +56...
    # 0056...
    # 0056...
    if digits.startswith("0056"):
        digits = digits[4:]
    elif digits.startswith("56"):
        digits = digits[2:]

    # Remove a domestic trunk zero if present.
    if digits.startswith("0"):
        digits = digits[1:]

    if not digits:
        return None, "empty"

    # Chilean mobile numbers begin with 9 after the country code.
    if digits.startswith("9"):
        return None, "mobile"

    # Santiago uses the one-digit geographic code 2.
    #
    # A complete Chilean geographic number using area code 2 should
    # contain 9 digits after removing +56:
    #
    # 2 + 8-digit subscriber number
    if (
        digits.startswith("2")
        and len(digits) == 9
    ):
        return "2", "fixed"

    # Other current geographic codes are two digits.
    if len(digits) >= 2:
        candidate = digits[:2]

        if candidate in KNOWN_AREA_CODES:
            return candidate, "fixed"

    return None, "unclassified"


def get_coordinates(
    feature: dict,
) -> tuple[float, float] | None:
    geometry = feature.get(
        "geometry"
    )

    if not geometry:
        return None

    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates"
    )

    if (
        geometry_type == "Point"
        and isinstance(coordinates, list)
        and len(coordinates) >= 2
    ):
        return (
            coordinates[0],
            coordinates[1],
        )

    return None


def main() -> None:
    geojson = load_geojson()

    features = geojson.get(
        "features",
        []
    )

    features_with_phone = 0
    features_with_coordinates = 0

    raw_phone_fields = 0
    individual_phone_values = 0

    area_code_counts = Counter()
    classification_counts = Counter()

    area_code_samples = {
        area_code: []
        for area_code in KNOWN_AREA_CODES
    }

    unclassified_samples = []
    mobile_samples = []

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        coordinate = get_coordinates(
            feature
        )

        if coordinate is not None:
            features_with_coordinates += 1

        feature_has_phone = False

        for property_name in PHONE_PROPERTIES:
            value = properties.get(
                property_name
            )

            if not isinstance(
                value,
                str,
            ):
                continue

            value = value.strip()

            if not value:
                continue

            feature_has_phone = True
            raw_phone_fields += 1

            phone_values = split_phone_values(
                value
            )

            for raw_phone in phone_values:
                individual_phone_values += 1

                (
                    area_code,
                    classification,
                ) = extract_area_code(
                    raw_phone
                )

                classification_counts[
                    classification
                ] += 1

                if area_code is not None:
                    area_code_counts[
                        area_code
                    ] += 1

                    if (
                        len(
                            area_code_samples[
                                area_code
                            ]
                        )
                        < 3
                    ):
                        area_code_samples[
                            area_code
                        ].append(
                            (
                                raw_phone,
                                properties.get(
                                    "name"
                                ),
                                properties.get(
                                    "addr:city"
                                ),
                                coordinate,
                            )
                        )

                elif (
                    classification
                    == "unclassified"
                    and len(
                        unclassified_samples
                    )
                    < 30
                ):
                    unclassified_samples.append(
                        (
                            raw_phone,
                            properties.get(
                                "name"
                            ),
                            properties.get(
                                "addr:city"
                            ),
                        )
                    )

                elif (
                    classification
                    == "mobile"
                    and len(
                        mobile_samples
                    )
                    < 10
                ):
                    mobile_samples.append(
                        (
                            raw_phone,
                            properties.get(
                                "name"
                            ),
                            properties.get(
                                "addr:city"
                            ),
                        )
                    )

        if feature_has_phone:
            features_with_phone += 1

    print()
    print("OSM PHONE DATA SUMMARY")
    print("=" * 50)

    print(
        f"GeoJSON features:           {len(features)}"
    )
    print(
        f"Features with phone tags:   {features_with_phone}"
    )
    print(
        f"Features with coordinates:  {features_with_coordinates}"
    )
    print(
        f"Raw phone fields:           {raw_phone_fields}"
    )
    print(
        f"Individual phone values:    {individual_phone_values}"
    )

    print()
    print("CLASSIFICATION")
    print("=" * 50)

    for classification, count in (
        classification_counts.most_common()
    ):
        print(
            f"{classification:<20} {count:>6}"
        )

    print()
    print("RECOGNIZED FIXED-LINE AREA CODES")
    print("=" * 50)

    total_fixed = sum(
        area_code_counts.values()
    )

    for area_code in sorted(
        KNOWN_AREA_CODES,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        count = area_code_counts[
            area_code
        ]

        percent = (
            count / total_fixed * 100
            if total_fixed
            else 0
        )

        print(
            f"{area_code:>2} -> "
            f"{count:>5} "
            f"({percent:5.1f}%)"
        )

    print()
    print(
        f"Total recognized fixed-line numbers: "
        f"{total_fixed}"
    )

    print()
    print("SAMPLES BY AREA CODE")
    print("=" * 50)

    for area_code in sorted(
        KNOWN_AREA_CODES,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        samples = area_code_samples[
            area_code
        ]

        if not samples:
            continue

        print()
        print(
            f"Area code {area_code}:"
        )

        for (
            raw_phone,
            name,
            city,
            coordinate,
        ) in samples:
            print(
                f"  {raw_phone}"
            )
            print(
                f"    name: {name}"
            )
            print(
                f"    city: {city}"
            )
            print(
                f"    coordinates: {coordinate}"
            )

    if unclassified_samples:
        print()
        print("UNCLASSIFIED SAMPLES")
        print("=" * 50)

        for (
            raw_phone,
            name,
            city,
        ) in unclassified_samples:
            print(
                f"  {raw_phone}"
            )
            print(
                f"    name: {name}"
            )
            print(
                f"    city: {city}"
            )

    if mobile_samples:
        print()
        print("MOBILE SAMPLES")
        print("=" * 50)

        for (
            raw_phone,
            name,
            city,
        ) in mobile_samples:
            print(
                f"  {raw_phone}"
            )
            print(
                f"    name: {name}"
            )
            print(
                f"    city: {city}"
            )


if __name__ == "__main__":
    main()
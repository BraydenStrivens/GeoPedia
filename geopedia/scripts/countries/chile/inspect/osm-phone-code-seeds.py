"""
Inspect candidate OSM phone-code seeds for Chile.

This is the final inspection before generating Voronoi area-code
polygons.

It looks for two major sources of unreliable geographic evidence:

1. A phone observation whose nearest neighboring observations strongly
   support another area code.
2. The same normalized phone number appearing at geographically distant
   locations, suggesting a centralized/company contact number rather
   than a geographically local fixed line.

This script DOES NOT remove observations and DOES NOT generate production
area-code geometry.

Input
-----
data/intermediate/countries/chile/inspection/
    osm-phone-code-points.geojson

Output
------
data/intermediate/countries/chile/inspection/
    osm-phone-code-seed-inspection.geojson

Run with:

    python scripts/countries/chile/inspect/osm-phone-code-seeds.py
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "inspection"
    / "osm-phone-code-points.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "inspection"
    / "osm-phone-code-seed-inspection.geojson"
)


NEIGHBOR_COUNT = 10

# If the same normalized number appears this far apart, treat that as
# evidence that it may be a centralized/non-local contact number.
DUPLICATE_DISTANCE_KM = 50.0

EARTH_RADIUS_KM = 6371.0088


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


def get_point(
    feature: dict,
) -> tuple[float, float]:
    geometry = feature.get(
        "geometry",
        {},
    )

    if geometry.get("type") != "Point":
        raise ValueError(
            "Expected Point geometry."
        )

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
        raise ValueError(
            "Point is missing coordinates."
        )

    return (
        float(coordinates[0]),
        float(coordinates[1]),
    )


def haversine_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    lon1_rad = math.radians(
        lon1
    )
    lat1_rad = math.radians(
        lat1
    )
    lon2_rad = math.radians(
        lon2
    )
    lat2_rad = math.radians(
        lat2
    )

    delta_lon = (
        lon2_rad - lon1_rad
    )

    delta_lat = (
        lat2_rad - lat1_rad
    )

    a = (
        math.sin(
            delta_lat / 2
        )
        ** 2
        + math.cos(
            lat1_rad
        )
        * math.cos(
            lat2_rad
        )
        * math.sin(
            delta_lon / 2
        )
        ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return (
        EARTH_RADIUS_KM * c
    )


def prepare_points(
    features: list[dict],
) -> list[dict]:
    points = []

    for index, feature in enumerate(
        features
    ):
        properties = feature.get(
            "properties",
            {},
        )

        lon, lat = get_point(
            feature
        )

        area_code = str(
            properties.get(
                "area_code",
                "",
            )
        )

        normalized_phone = str(
            properties.get(
                "normalized_phone",
                "",
            )
        )

        if not area_code:
            raise ValueError(
                f"Feature {index} is missing area_code."
            )

        if not normalized_phone:
            raise ValueError(
                f"Feature {index} is missing normalized_phone."
            )

        points.append(
            {
                "index": index,
                "feature": feature,
                "lon": lon,
                "lat": lat,
                "area_code": area_code,
                "normalized_phone": normalized_phone,
            }
        )

    return points


def inspect_duplicate_numbers(
    points: list[dict],
) -> dict[int, dict]:
    """
    Find normalized phone numbers appearing at multiple geographic
    locations.

    A duplicate is considered geographically dispersed if at least one
    pair of observations using that same normalized number is more than
    DUPLICATE_DISTANCE_KM apart.
    """

    by_phone = defaultdict(
        list
    )

    for point in points:
        by_phone[
            point[
                "normalized_phone"
            ]
        ].append(
            point
        )

    results = {}

    duplicate_groups = 0
    dispersed_groups = 0

    for (
        normalized_phone,
        group,
    ) in by_phone.items():
        if len(group) < 2:
            continue

        duplicate_groups += 1

        max_distance = 0.0

        for i in range(
            len(group)
        ):
            for j in range(
                i + 1,
                len(group),
            ):
                distance = haversine_km(
                    group[i]["lon"],
                    group[i]["lat"],
                    group[j]["lon"],
                    group[j]["lat"],
                )

                max_distance = max(
                    max_distance,
                    distance,
                )

        dispersed = (
            max_distance
            >= DUPLICATE_DISTANCE_KM
        )

        if dispersed:
            dispersed_groups += 1

        for point in group:
            results[
                point["index"]
            ] = {
                "duplicate_count": len(
                    group
                ),
                "duplicate_max_distance_km": (
                    max_distance
                ),
                "dispersed_duplicate": (
                    dispersed
                ),
            }

    print()
    print("DUPLICATE PHONE NUMBERS")
    print("=" * 70)

    print(
        f"Repeated-number groups:   "
        f"{duplicate_groups}"
    )

    print(
        f"Geographically dispersed: "
        f"{dispersed_groups}"
    )

    return results


def inspect_nearest_neighbors(
    points: list[dict],
) -> dict[int, dict]:
    results = {}

    total = len(
        points
    )

    for index, point in enumerate(
        points
    ):
        distances = []

        for other in points:
            if (
                point["index"]
                == other["index"]
            ):
                continue

            distance = haversine_km(
                point["lon"],
                point["lat"],
                other["lon"],
                other["lat"],
            )

            distances.append(
                (
                    distance,
                    other[
                        "area_code"
                    ],
                )
            )

        distances.sort(
            key=lambda item: item[0]
        )

        nearest = distances[
            :NEIGHBOR_COUNT
        ]

        counts = Counter(
            area_code
            for _, area_code
            in nearest
        )

        same_count = counts.get(
            point["area_code"],
            0,
        )

        other_count = (
            len(nearest)
            - same_count
        )

        dominant_code = None
        dominant_count = 0

        if counts:
            (
                dominant_code,
                dominant_count,
            ) = max(
                counts.items(),
                key=lambda item: (
                    item[1],
                    item[0],
                ),
            )

        nearest_distance = (
            nearest[0][0]
            if nearest
            else None
        )

        farthest_neighbor_distance = (
            nearest[-1][0]
            if nearest
            else None
        )

        nearest_same_distance = None

        nearest_other_distance = None
        nearest_other_code = None

        for (
            distance,
            area_code,
        ) in distances:
            if (
                area_code
                == point["area_code"]
            ):
                if (
                    nearest_same_distance
                    is None
                ):
                    nearest_same_distance = (
                        distance
                    )
            else:
                if (
                    nearest_other_distance
                    is None
                ):
                    nearest_other_distance = (
                        distance
                    )
                    nearest_other_code = (
                        area_code
                    )

            if (
                nearest_same_distance
                is not None
                and nearest_other_distance
                is not None
            ):
                break

        results[
            point["index"]
        ] = {
            "neighbor_counts": counts,
            "same_count": same_count,
            "other_count": other_count,
            "dominant_code": dominant_code,
            "dominant_count": dominant_count,
            "nearest_distance": nearest_distance,
            "neighbor_radius_km": (
                farthest_neighbor_distance
            ),
            "nearest_same_distance": (
                nearest_same_distance
            ),
            "nearest_other_distance": (
                nearest_other_distance
            ),
            "nearest_other_code": (
                nearest_other_code
            ),
        }

        if (
            (index + 1) % 250 == 0
            or index + 1 == total
        ):
            print(
                f"Analyzed "
                f"{index + 1}/{total} points..."
            )

    return results


def classify_seed(
    point: dict,
    neighbor_info: dict,
    duplicate_info: dict | None,
) -> tuple[str, int]:
    """
    Classify a candidate Voronoi seed.

    Severity:
        0 = looks geographically consistent
        1 = worth reviewing
        2 = suspicious
        3 = very strong exclusion candidate

    No observation is actually deleted here.
    """

    same_count = neighbor_info[
        "same_count"
    ]

    dominant_code = neighbor_info[
        "dominant_code"
    ]

    dominant_count = neighbor_info[
        "dominant_count"
    ]

    dispersed_duplicate = (
        duplicate_info is not None
        and duplicate_info[
            "dispersed_duplicate"
        ]
    )

    # Strongest case:
    #
    # None of the ten nearest observations use this point's code,
    # another code occupies at least 8/10 neighbors, AND the phone
    # number itself occurs at geographically dispersed locations.
    if (
        same_count == 0
        and dominant_code
        != point["area_code"]
        and dominant_count >= 8
        and dispersed_duplicate
    ):
        return (
            "strong_nonlocal_candidate",
            3,
        )

    # No nearby support at all and overwhelming support for another
    # code.
    if (
        same_count == 0
        and dominant_code
        != point["area_code"]
        and dominant_count >= 9
    ):
        return (
            "isolated_code_candidate",
            3,
        )

    # A geographically dispersed repeated number is suspicious even
    # when its immediate neighborhood is somewhat mixed.
    if (
        dispersed_duplicate
        and same_count <= 2
    ):
        return (
            "dispersed_number_candidate",
            2,
        )

    # Strong nearest-neighbor disagreement.
    if (
        same_count <= 1
        and dominant_code
        != point["area_code"]
        and dominant_count >= 7
    ):
        return (
            "neighbor_conflict",
            2,
        )

    # Moderate disagreement. This can easily be a real boundary, so
    # treat it only as something worth reviewing.
    if (
        same_count <= 3
        and dominant_code
        != point["area_code"]
        and dominant_count >= 6
    ):
        return (
            "boundary_or_conflict",
            1,
        )

    return (
        "consistent",
        0,
    )


def format_counts(
    counts: Counter,
) -> str:
    ordered = sorted(
        counts.items(),
        key=lambda item: (
            -item[1],
            len(item[0]),
            item[0],
        ),
    )

    return ", ".join(
        f"{area_code}:{count}"
        for area_code, count
        in ordered
    )


def rounded_distance(
    value: float | None,
) -> float | None:
    if value is None:
        return None

    return round(
        value,
        3,
    )


def create_inspection_feature(
    point: dict,
    neighbor_info: dict,
    duplicate_info: dict | None,
    classification: str,
    severity: int,
) -> dict:
    source_properties = dict(
        point[
            "feature"
        ].get(
            "properties",
            {},
        )
    )

    source_properties[
        "seed_class"
    ] = classification

    source_properties[
        "seed_severity"
    ] = severity

    source_properties[
        "nearest_10"
    ] = format_counts(
        neighbor_info[
            "neighbor_counts"
        ]
    )

    source_properties[
        "same_in_nearest_10"
    ] = neighbor_info[
        "same_count"
    ]

    source_properties[
        "dominant_nearby_code"
    ] = neighbor_info[
        "dominant_code"
    ]

    source_properties[
        "dominant_nearby_count"
    ] = neighbor_info[
        "dominant_count"
    ]

    source_properties[
        "nearest_point_km"
    ] = rounded_distance(
        neighbor_info[
            "nearest_distance"
        ]
    )

    source_properties[
        "nearest_10_radius_km"
    ] = rounded_distance(
        neighbor_info[
            "neighbor_radius_km"
        ]
    )

    source_properties[
        "nearest_same_km"
    ] = rounded_distance(
        neighbor_info[
            "nearest_same_distance"
        ]
    )

    source_properties[
        "nearest_other_km"
    ] = rounded_distance(
        neighbor_info[
            "nearest_other_distance"
        ]
    )

    source_properties[
        "nearest_other_code"
    ] = neighbor_info[
        "nearest_other_code"
    ]

    if duplicate_info is None:
        source_properties[
            "duplicate_count"
        ] = 1

        source_properties[
            "duplicate_max_distance_km"
        ] = 0.0

        source_properties[
            "dispersed_duplicate"
        ] = False

    else:
        source_properties[
            "duplicate_count"
        ] = duplicate_info[
            "duplicate_count"
        ]

        source_properties[
            "duplicate_max_distance_km"
        ] = round(
            duplicate_info[
                "duplicate_max_distance_km"
            ],
            3,
        )

        source_properties[
            "dispersed_duplicate"
        ] = duplicate_info[
            "dispersed_duplicate"
        ]

    return {
        "type": "Feature",
        "properties": (
            source_properties
        ),
        "geometry": point[
            "feature"
        ][
            "geometry"
        ],
    }


def print_classification_summary(
    classifications: list[
        tuple[
            dict,
            dict,
            dict | None,
            str,
            int,
        ]
    ],
) -> None:
    counts = Counter(
        classification
        for (
            _,
            _,
            _,
            classification,
            _,
        ) in classifications
    )

    print()
    print("SEED CLASSIFICATION")
    print("=" * 70)

    for (
        classification,
        count,
    ) in counts.most_common():
        print(
            f"{classification:<30} "
            f"{count:>5}"
        )


def print_by_area_code(
    classifications: list[
        tuple[
            dict,
            dict,
            dict | None,
            str,
            int,
        ]
    ],
) -> None:
    by_code = defaultdict(
        Counter
    )

    for (
        point,
        _,
        _,
        classification,
        severity,
    ) in classifications:
        by_code[
            point["area_code"]
        ][
            "total"
        ] += 1

        if severity == 0:
            by_code[
                point["area_code"]
            ][
                "consistent"
            ] += 1

        elif severity == 1:
            by_code[
                point["area_code"]
            ][
                "review"
            ] += 1

        elif severity == 2:
            by_code[
                point["area_code"]
            ][
                "suspicious"
            ] += 1

        elif severity == 3:
            by_code[
                point["area_code"]
            ][
                "strong"
            ] += 1

    print()
    print("SEED STATUS BY AREA CODE")
    print("=" * 70)

    for area_code in sorted(
        by_code,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        counts = by_code[
            area_code
        ]

        print(
            f"{area_code:>2} -> "
            f"total {counts['total']:>4} | "
            f"ok {counts['consistent']:>4} | "
            f"review {counts['review']:>3} | "
            f"suspicious {counts['suspicious']:>3} | "
            f"strong {counts['strong']:>3}"
        )


def print_top_candidates(
    classifications: list[
        tuple[
            dict,
            dict,
            dict | None,
            str,
            int,
        ]
    ],
) -> None:
    candidates = [
        item
        for item in classifications
        if item[4] >= 2
    ]

    candidates.sort(
        key=lambda item: (
            -item[4],
            item[1][
                "same_count"
            ],
            -item[1][
                "dominant_count"
            ],
        )
    )

    print()
    print("TOP EXCLUSION CANDIDATES")
    print("=" * 70)

    if not candidates:
        print(
            "No severity 2-3 candidates."
        )
        return

    for (
        point,
        neighbor_info,
        duplicate_info,
        classification,
        severity,
    ) in candidates[:75]:
        properties = point[
            "feature"
        ].get(
            "properties",
            {},
        )

        print()
        print(
            f"[{severity}] "
            f"{classification}"
        )

        print(
            f"  code:  "
            f"{point['area_code']}"
        )

        print(
            f"  phone: "
            f"{properties.get('phone')}"
        )

        print(
            f"  name:  "
            f"{properties.get('name')}"
        )

        print(
            f"  city:  "
            f"{properties.get('city')}"
        )

        print(
            "  coordinates: "
            f"({point['lon']}, "
            f"{point['lat']})"
        )

        print(
            "  nearest 10: "
            f"{format_counts(neighbor_info['neighbor_counts'])}"
        )

        print(
            "  nearest-10 radius: "
            f"{neighbor_info['neighbor_radius_km']:.2f} km"
        )

        if duplicate_info is not None:
            print(
                "  duplicate count: "
                f"{duplicate_info['duplicate_count']}"
            )

            print(
                "  duplicate max distance: "
                f"{duplicate_info['duplicate_max_distance_km']:.2f} km"
            )


def main() -> None:
    geojson = load_geojson(
        INPUT_PATH
    )

    features = geojson.get(
        "features",
        [],
    )

    points = prepare_points(
        features
    )

    print()
    print(
        "OSM PHONE CODE SEED INSPECTION"
    )
    print("=" * 70)

    print(
        f"Input points: "
        f"{len(points)}"
    )

    duplicate_results = (
        inspect_duplicate_numbers(
            points
        )
    )

    print()
    print("NEAREST-NEIGHBOR ANALYSIS")
    print("=" * 70)

    neighbor_results = (
        inspect_nearest_neighbors(
            points
        )
    )

    classifications = []

    output_features = []

    for point in points:
        neighbor_info = (
            neighbor_results[
                point["index"]
            ]
        )

        duplicate_info = (
            duplicate_results.get(
                point["index"]
            )
        )

        (
            classification,
            severity,
        ) = classify_seed(
            point,
            neighbor_info,
            duplicate_info,
        )

        classifications.append(
            (
                point,
                neighbor_info,
                duplicate_info,
                classification,
                severity,
            )
        )

        output_features.append(
            create_inspection_feature(
                point,
                neighbor_info,
                duplicate_info,
                classification,
                severity,
            )
        )

    print_classification_summary(
        classifications
    )

    print_by_area_code(
        classifications
    )

    print_top_candidates(
        classifications
    )

    output_geojson = {
        "type": "FeatureCollection",
        "features": output_features,
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

    severity_counts = Counter(
        severity
        for (
            _,
            _,
            _,
            _,
            severity,
        ) in classifications
    )

    print()
    print("SUMMARY")
    print("=" * 70)

    print(
        f"Severity 0: "
        f"{severity_counts[0]}"
    )

    print(
        f"Severity 1: "
        f"{severity_counts[1]}"
    )

    print(
        f"Severity 2: "
        f"{severity_counts[2]}"
    )

    print(
        f"Severity 3: "
        f"{severity_counts[3]}"
    )

    print()
    print(
        f"Output points: "
        f"{len(output_features)}"
    )

    print(
        f"Output size:   "
        f"{size_mb:.2f} MB"
    )

    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
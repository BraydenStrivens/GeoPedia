"""
Inspect spatial conflicts and possible outliers among Chilean OSM
fixed-line area-code observations.

This script does NOT remove observations or generate area-code polygons.
It examines the accepted OSM phone-code points and identifies observations
whose area code disagrees with nearby observations.

Input
-----
data/intermediate/countries/chile/inspection/
    osm-phone-code-points.geojson

Outputs
-------
data/intermediate/countries/chile/inspection/
    osm-phone-code-outliers.geojson

The output contains only observations flagged as potentially suspicious.
Each feature retains its original phone information plus neighborhood
statistics.

Run with:

    python scripts/countries/chile/inspect/osm-phone-code-outliers.py
"""

import json
import math
from collections import Counter
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
    / "osm-phone-code-outliers.geojson"
)


RADII_KM = (
    5,
    15,
    50,
)

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


def get_point(
    feature: dict,
) -> tuple[
    float,
    float,
]:
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


def format_counts(
    counts: Counter,
) -> str:
    if not counts:
        return "none"

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
        for area_code, count in ordered
    )


def calculate_neighborhoods(
    features: list[dict],
) -> list[dict]:
    points = []

    for feature in features:
        lon, lat = get_point(
            feature
        )

        area_code = str(
            feature.get(
                "properties",
                {},
            ).get(
                "area_code",
                "",
            )
        )

        if not area_code:
            raise ValueError(
                "Feature is missing area_code."
            )

        points.append(
            {
                "feature": feature,
                "lon": lon,
                "lat": lat,
                "area_code": area_code,
            }
        )

    results = []

    total = len(points)

    for index, point in enumerate(
        points
    ):
        neighborhood_counts = {
            radius: Counter()
            for radius in RADII_KM
        }

        neighborhood_totals = {
            radius: 0
            for radius in RADII_KM
        }

        nearest_same_distance = None
        nearest_other_distance = None
        nearest_other_code = None

        for other_index, other in enumerate(
            points
        ):
            if index == other_index:
                continue

            distance = haversine_km(
                point["lon"],
                point["lat"],
                other["lon"],
                other["lat"],
            )

            if (
                other["area_code"]
                == point["area_code"]
            ):
                if (
                    nearest_same_distance
                    is None
                    or distance
                    < nearest_same_distance
                ):
                    nearest_same_distance = (
                        distance
                    )
            else:
                if (
                    nearest_other_distance
                    is None
                    or distance
                    < nearest_other_distance
                ):
                    nearest_other_distance = (
                        distance
                    )
                    nearest_other_code = (
                        other["area_code"]
                    )

            for radius in RADII_KM:
                if distance <= radius:
                    neighborhood_counts[
                        radius
                    ][
                        other["area_code"]
                    ] += 1

                    neighborhood_totals[
                        radius
                    ] += 1

        radius_stats = {}

        for radius in RADII_KM:
            counts = neighborhood_counts[
                radius
            ]

            total_neighbors = (
                neighborhood_totals[
                    radius
                ]
            )

            same_count = counts.get(
                point["area_code"],
                0,
            )

            other_count = (
                total_neighbors
                - same_count
            )

            same_ratio = (
                same_count
                / total_neighbors
                if total_neighbors
                else None
            )

            dominant_code = None
            dominant_count = 0

            if counts:
                (
                    dominant_code,
                    dominant_count,
                ) = max(
                    counts.items(),
                    key=lambda item: item[1],
                )

            radius_stats[
                radius
            ] = {
                "counts": counts,
                "total": total_neighbors,
                "same": same_count,
                "other": other_count,
                "same_ratio": same_ratio,
                "dominant_code": dominant_code,
                "dominant_count": dominant_count,
            }

        results.append(
            {
                **point,
                "radius_stats": radius_stats,
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
        )

        if (
            (index + 1) % 250 == 0
            or index + 1 == total
        ):
            print(
                f"Analyzed "
                f"{index + 1}/{total} points..."
            )

    return results


def classify_point(
    result: dict,
) -> tuple[
    str,
    int,
]:
    """
    Classify how suspicious a point looks.

    This does NOT decide whether the point is wrong.

    Severity:
        3 = strong isolated conflict
        2 = local conflict
        1 = mixed/boundary candidate
        0 = no notable conflict
    """

    area_code = result[
        "area_code"
    ]

    stats_5 = result[
        "radius_stats"
    ][5]

    stats_15 = result[
        "radius_stats"
    ][15]

    stats_50 = result[
        "radius_stats"
    ][50]

    # Strong case:
    #
    # At least five nearby observations within 15 km,
    # none use this point's code, and another code is
    # clearly present.
    if (
        stats_15["total"] >= 5
        and stats_15["same"] == 0
        and stats_15["other"] >= 5
    ):
        return (
            "isolated_conflict",
            3,
        )

    # Strongly outnumbered at very short range.
    if (
        stats_5["total"] >= 5
        and stats_5["same_ratio"]
        is not None
        and stats_5["same_ratio"] <= 0.20
    ):
        return (
            "local_conflict",
            2,
        )

    # Outnumbered over a slightly larger local area.
    if (
        stats_15["total"] >= 8
        and stats_15["same_ratio"]
        is not None
        and stats_15["same_ratio"] <= 0.25
    ):
        return (
            "local_conflict",
            2,
        )

    # Mixed neighborhoods are interesting because they
    # may represent a real area-code transition.
    if (
        stats_15["same"] >= 2
        and stats_15["other"] >= 2
    ):
        return (
            "mixed_boundary_candidate",
            1,
        )

    # In sparse areas, use 50 km only as a weak signal.
    if (
        stats_50["total"] >= 5
        and stats_50["same"] == 0
        and stats_50["other"] >= 5
    ):
        return (
            "sparse_conflict",
            1,
        )

    return (
        "normal",
        0,
    )


def create_outlier_feature(
    result: dict,
    classification: str,
    severity: int,
) -> dict:
    source_properties = (
        result[
            "feature"
        ].get(
            "properties",
            {},
        )
    )

    properties = dict(
        source_properties
    )

    properties[
        "inspection_class"
    ] = classification

    properties[
        "inspection_severity"
    ] = severity

    nearest_same = result[
        "nearest_same_distance"
    ]

    nearest_other = result[
        "nearest_other_distance"
    ]

    properties[
        "nearest_same_km"
    ] = (
        round(
            nearest_same,
            3,
        )
        if nearest_same is not None
        else None
    )

    properties[
        "nearest_other_km"
    ] = (
        round(
            nearest_other,
            3,
        )
        if nearest_other is not None
        else None
    )

    properties[
        "nearest_other_code"
    ] = result[
        "nearest_other_code"
    ]

    for radius in RADII_KM:
        stats = result[
            "radius_stats"
        ][radius]

        properties[
            f"neighbors_{radius}km"
        ] = stats[
            "total"
        ]

        properties[
            f"same_{radius}km"
        ] = stats[
            "same"
        ]

        properties[
            f"other_{radius}km"
        ] = stats[
            "other"
        ]

        properties[
            f"codes_{radius}km"
        ] = format_counts(
            stats[
                "counts"
            ]
        )

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": result[
            "feature"
        ][
            "geometry"
        ],
    }


def print_top_conflicts(
    classified_results: list[
        tuple[
            dict,
            str,
            int,
        ]
    ],
) -> None:
    suspicious = [
        item
        for item in classified_results
        if item[2] >= 2
    ]

    suspicious.sort(
        key=lambda item: (
            -item[2],
            (
                item[0][
                    "nearest_other_distance"
                ]
                if item[0][
                    "nearest_other_distance"
                ]
                is not None
                else float("inf")
            ),
        )
    )

    print()
    print("TOP CONFLICTS")
    print("=" * 70)

    if not suspicious:
        print(
            "No severity 2-3 conflicts found."
        )
        return

    for (
        result,
        classification,
        severity,
    ) in suspicious[:50]:
        properties = (
            result[
                "feature"
            ].get(
                "properties",
                {},
            )
        )

        print()
        print(
            f"[{severity}] "
            f"{classification}"
        )

        print(
            f"  code:  "
            f"{result['area_code']}"
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
            f"({result['lon']}, "
            f"{result['lat']})"
        )

        for radius in RADII_KM:
            stats = result[
                "radius_stats"
            ][radius]

            print(
                f"  {radius:>2} km: "
                f"{format_counts(stats['counts'])}"
            )


def main() -> None:
    geojson = load_geojson(
        INPUT_PATH
    )

    features = geojson.get(
        "features",
        [],
    )

    print()
    print(
        "OSM PHONE CODE OUTLIER INSPECTION"
    )
    print("=" * 70)

    print(
        f"Input points: {len(features)}"
    )

    results = calculate_neighborhoods(
        features
    )

    classification_counts = (
        Counter()
    )

    classification_by_code = {}

    classified_results = []

    output_features = []

    for result in results:
        (
            classification,
            severity,
        ) = classify_point(
            result
        )

        classification_counts[
            classification
        ] += 1

        area_code = result[
            "area_code"
        ]

        if (
            area_code
            not in classification_by_code
        ):
            classification_by_code[
                area_code
            ] = Counter()

        classification_by_code[
            area_code
        ][
            classification
        ] += 1

        classified_results.append(
            (
                result,
                classification,
                severity,
            )
        )

        if severity > 0:
            output_features.append(
                create_outlier_feature(
                    result,
                    classification,
                    severity,
                )
            )

    print()
    print("CLASSIFICATION SUMMARY")
    print("=" * 70)

    for (
        classification,
        count,
    ) in (
        classification_counts
        .most_common()
    ):
        print(
            f"{classification:<28} "
            f"{count:>5}"
        )

    print()
    print("CONFLICTS BY AREA CODE")
    print("=" * 70)

    for area_code in sorted(
        classification_by_code,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        counts = (
            classification_by_code[
                area_code
            ]
        )

        suspicious_count = (
            counts[
                "isolated_conflict"
            ]
            + counts[
                "local_conflict"
            ]
            + counts[
                "sparse_conflict"
            ]
        )

        mixed_count = counts[
            "mixed_boundary_candidate"
        ]

        total = sum(
            counts.values()
        )

        print(
            f"{area_code:>2} -> "
            f"total {total:>4} | "
            f"conflicts {suspicious_count:>3} | "
            f"mixed {mixed_count:>3}"
        )

    print_top_conflicts(
        classified_results
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

    print()
    print(
        f"Flagged points: "
        f"{len(output_features)}"
    )
    print(
        f"Output size:    "
        f"{size_mb:.2f} MB"
    )
    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
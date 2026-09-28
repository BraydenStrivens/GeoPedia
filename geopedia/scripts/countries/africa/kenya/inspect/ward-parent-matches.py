"""
Inspect spatial matching between Kenya's ADM3 wards and ADM2 sub-counties.

For every ward whose representative point is not covered by exactly one
sub-county, report the direct matches and rank nearby sub-counties by the
fraction of the ward's area they overlap.

This script does not modify any data.
"""

import json
from pathlib import Path

from shapely.geometry import shape


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "kenya"
)

SUB_COUNTIES_PATH = (
    RAW_DIR
    / "geoBoundaries-KEN-ADM2.geojson"
)

WARDS_PATH = (
    RAW_DIR
    / "geoBoundaries-KEN-ADM3.geojson"
)


def load_features(path: Path) -> list[dict]:
    """Load features from a GeoJSON FeatureCollection."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data["features"]


def main() -> None:
    """Inspect all ambiguous or failed ward-to-sub-county matches."""
    print("Inspecting Kenya ward parent matches...")
    print()

    sub_county_features = load_features(
        SUB_COUNTIES_PATH
    )

    ward_features = load_features(
        WARDS_PATH
    )

    sub_counties = [
        {
            "name": feature["properties"]["shapeName"],
            "id": feature["properties"]["shapeID"],
            "geometry": shape(feature["geometry"]),
        }
        for feature in sub_county_features
    ]

    failures = []

    for ward_feature in ward_features:
        ward_name = ward_feature["properties"]["shapeName"]
        ward_id = ward_feature["properties"]["shapeID"]
        ward_geometry = shape(
            ward_feature["geometry"]
        )

        point = ward_geometry.representative_point()

        direct_matches = [
            sub_county
            for sub_county in sub_counties
            if sub_county["geometry"].covers(point)
        ]

        if len(direct_matches) == 1:
            continue

        overlaps = []

        for sub_county in sub_counties:
            if not ward_geometry.intersects(
                sub_county["geometry"]
            ):
                continue

            intersection = ward_geometry.intersection(
                sub_county["geometry"]
            )

            if intersection.is_empty:
                continue

            overlap_area = intersection.area

            if overlap_area <= 0:
                continue

            overlap_fraction = (
                overlap_area / ward_geometry.area
                if ward_geometry.area > 0
                else 0
            )

            overlaps.append(
                {
                    "name": sub_county["name"],
                    "id": sub_county["id"],
                    "fraction": overlap_fraction,
                }
            )

        overlaps.sort(
            key=lambda item: item["fraction"],
            reverse=True,
        )

        failures.append(
            {
                "ward": ward_name,
                "ward_id": ward_id,
                "direct_matches": direct_matches,
                "overlaps": overlaps[:5],
            }
        )

    print(
        f"Total wards: {len(ward_features)}"
    )
    print(
        f"Representative-point failures: {len(failures)}"
    )
    print()

    for failure in failures:
        print(
            f"=== {failure['ward']} ==="
        )
        print(
            f"Ward ID: {failure['ward_id']}"
        )

        direct_names = [
            item["name"]
            for item in failure["direct_matches"]
        ]

        print(
            f"Representative-point matches: "
            f"{direct_names}"
        )

        print("Largest overlaps:")

        for overlap in failure["overlaps"]:
            print(
                f"  {overlap['name']} | "
                f"{overlap['fraction']:.2%} | "
                f"{overlap['id']}"
            )

        print()


if __name__ == "__main__":
    main()
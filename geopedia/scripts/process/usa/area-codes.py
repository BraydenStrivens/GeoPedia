"""
Processes raw US telephone area-code GeoJSON for use by GeoPedia.

The source ArcGIS dataset contains one feature per area code. Overlay area
codes therefore appear as multiple features with identical geometry.

This script groups features that share identical geometry into one
geographic feature while preserving every area code assigned to that
region.

Example:

    201 + geometry A
    551 + geometry A

becomes:

    {
        "id": "201-551",
        "properties": {
            "id": "201-551",
            "area_codes": ["201", "551"],
            "states": ["NJ"]
        },
        "geometry": geometry A
    }

The resulting GeoJSON contains one clickable feature per unique geographic
area while still allowing each area code to remain a separate quiz answer.
"""

import json
from collections import defaultdict
from pathlib import Path
from shapely.geometry import mapping, shape


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FILE = Path("data/raw/us-area-codes.geojson")

OUTPUT_FILE = Path(
    "public/data/us-area-codes.geojson"
)

SIMPLIFY_TOLERANCE = 0.01


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def geometry_key(geometry):
    """
    Creates a consistent string representation of a geometry.

    Features with identical geometry will produce identical keys and can
    therefore be grouped together.
    """
    return json.dumps(
        geometry,
        sort_keys=True,
        separators=(",", ":"),
    )


def area_code_sort_key(area_code):
    """
    Sorts normal three-digit area codes numerically.
    """
    try:
        return int(area_code)
    except ValueError:
        return area_code


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def main():
    if not INPUT_FILE.exists():
        print(
            f"ERROR: Input file not found: {INPUT_FILE}"
        )
        return

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw_geojson = json.load(file)

    raw_features = raw_geojson.get(
        "features",
        [],
    )

    print(
        f"Raw features: {len(raw_features)}"
    )
    
    # Group all features that have identical geometry.
    grouped_features = defaultdict(list)

    for feature in raw_features:
        geometry = feature.get("geometry")
        properties = feature.get(
            "properties",
            {},
        )

        if not geometry:
            continue

        area_code = properties.get("AREA_CODE")

        if area_code is None:
            continue

        key = geometry_key(geometry)

        grouped_features[key].append(feature)

    processed_features = []

    for features in grouped_features.values():
        # All features in this group have identical geometry,
        # so only one copy needs to be kept.
        geometry = features[0]["geometry"]

        simplified_geometry = shape(
            geometry
        ).simplify(
            SIMPLIFY_TOLERANCE,
            preserve_topology=True,
        )

        geometry = mapping(
            simplified_geometry
        )

        area_codes = sorted(
            {
                str(
                    feature["properties"][
                        "AREA_CODE"
                    ]
                )
                for feature in features
            },
            key=area_code_sort_key,
        )

        states = sorted(
            {
                str(
                    feature["properties"]["STATE"]
                )
                for feature in features
                if feature["properties"].get(
                    "STATE"
                )
            }
        )

        # A stable region ID based on all area codes sharing
        # this geography.
        region_id = "-".join(area_codes)

        processed_feature = {
            "type": "Feature",
            "id": region_id,
            "properties": {
                "id": region_id,
                "area_codes": area_codes,
                "states": states,
            },
            "geometry": geometry,
        }

        processed_features.append(
            processed_feature
        )

    # Sort the output by the first area code so the file is
    # deterministic and easier to inspect.
    processed_features.sort(
        key=lambda feature: area_code_sort_key(
            feature["properties"][
                "area_codes"
            ][0]
        )
    )

    processed_geojson = {
        "type": "FeatureCollection",
        "features": processed_features,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            processed_geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    total_area_codes = sum(
        len(
            feature["properties"][
                "area_codes"
            ]
        )
        for feature in processed_features
    )

    overlay_regions = [
        feature
        for feature in processed_features
        if len(
            feature["properties"][
                "area_codes"
            ]
        )
        > 1
    ]

    print()
    print(
        f"Processed regions: "
        f"{len(processed_features)}"
    )

    print(
        f"Total area codes:   "
        f"{total_area_codes}"
    )

    print(
        f"Overlay regions:    "
        f"{len(overlay_regions)}"
    )

    print()
    print(
        f"Output: {OUTPUT_FILE}"
    )

    print()
    print("Sample overlay regions:")

    for feature in overlay_regions[:10]:
        properties = feature["properties"]

        print(
            "  "
            + " / ".join(
                properties["area_codes"]
            )
            + " | "
            + ", ".join(
                properties["states"]
            )
        )


if __name__ == "__main__":
    main()
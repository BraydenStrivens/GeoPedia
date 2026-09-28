"""Extract Puerto Rico's municipalities from GeoPedia's U.S. counties GeoJSON.

Puerto Rico's 78 municipios are treated as county-equivalent entities by the
U.S. Census Bureau and are already included in GeoPedia's processed U.S.
counties dataset. This script extracts those features into a dedicated runtime
GeoJSON for Puerto Rico.

Output properties:
    municipality_id: Five-digit Census GEOID.
    name: Municipality name.
"""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "usa"
    / "geojson"
    / "counties.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "municipalities.geojson"
)

EXPECTED_MUNICIPALITY_COUNT = 78
PUERTO_RICO_STATE_CODE = "PR"
PUERTO_RICO_GEOID_PREFIX = "72"


def main() -> None:
    """Extract and validate Puerto Rico's 78 municipalities."""
    print(f"Reading {SOURCE_PATH}")

    with SOURCE_PATH.open("r", encoding="utf-8") as file:
        source = json.load(file)

    source_features = source.get("features")

    if not isinstance(source_features, list):
        raise ValueError("Source GeoJSON does not contain a valid features array.")

    puerto_rico_features = [
        feature
        for feature in source_features
        if feature.get("properties", {}).get("state") == PUERTO_RICO_STATE_CODE
    ]

    print(f"Puerto Rico features found: {len(puerto_rico_features)}")

    if len(puerto_rico_features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            "Expected "
            f"{EXPECTED_MUNICIPALITY_COUNT} Puerto Rico municipalities, "
            f"found {len(puerto_rico_features)}."
        )

    output_features = []

    for feature in puerto_rico_features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry")

        geoid = properties.get("geoid")
        name = properties.get("name")

        if not isinstance(geoid, str) or not geoid:
            raise ValueError(f"Feature has an invalid GEOID: {properties}")

        if not geoid.startswith(PUERTO_RICO_GEOID_PREFIX):
            raise ValueError(
                f"Puerto Rico municipality GEOID does not start with "
                f"{PUERTO_RICO_GEOID_PREFIX}: {geoid}"
            )

        if len(geoid) != 5 or not geoid.isdigit():
            raise ValueError(f"Invalid municipality GEOID format: {geoid}")

        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Municipality {geoid} has an invalid name.")

        if geometry is None:
            raise ValueError(f"Municipality {geoid} has no geometry.")

        geometry_type = geometry.get("type")

        if geometry_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(
                f"Municipality {geoid} has unsupported geometry type: "
                f"{geometry_type}"
            )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "municipality_id": geoid,
                    "name": name.strip(),
                },
                "geometry": geometry,
            }
        )

    output_features.sort(
        key=lambda feature: feature["properties"]["municipality_id"]
    )

    municipality_ids = [
        feature["properties"]["municipality_id"]
        for feature in output_features
    ]
    municipality_names = [
        feature["properties"]["name"]
        for feature in output_features
    ]

    if len(set(municipality_ids)) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError("Municipality IDs are not unique.")

    if len(set(municipality_names)) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError("Municipality names are not unique.")

    output = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print()
    print("Municipalities:")
    for feature in output_features:
        properties = feature["properties"]
        print(
            f"  {properties['municipality_id']}  "
            f"{properties['name']}"
        )

    print()
    print(f"Features written: {len(output_features)}")
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


if __name__ == "__main__":
    main()
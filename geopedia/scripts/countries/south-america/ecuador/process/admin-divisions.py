from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import mapping


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "ecuador"
    / "ecu_adm_2024"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ecuador"
    / "admin"
)


# ---------------------------------------------------------------------------
# Administrative-level configuration
# ---------------------------------------------------------------------------

LEVELS = {
    1: {
        "source": "ecu_adm_adm1_2024.shp",
        "output": "provinces.geojson",
        "expected_count": 24,
        "properties": {
            "ADM1_PCODE": "province_id",
            "ADM1_ES": "province",
        },
    },
    2: {
        "source": "ecu_adm_adm2_2024.shp",
        "output": "cantons.geojson",
        "expected_count": 221,
        "properties": {
            "ADM2_PCODE": "canton_id",
            "ADM2_ES": "canton",
            "ADM1_PCODE": "province_id",
            "ADM1_ES": "province",
        },
    },
    3: {
        "source": "ecu_adm_adm3_2024.shp",
        "output": "parishes.geojson",
        "expected_count": 1_042,
        "properties": {
            "ADM3_PCODE": "parish_id",
            "ADM3_ES": "parish",
            "ADM2_PCODE": "canton_id",
            "ADM2_ES": "canton",
            "ADM1_PCODE": "province_id",
            "ADM1_ES": "province",
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_string(
    value: Any,
    property_name: str,
    feature_index: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"Feature {feature_index} property "
            f"{property_name!r} is not a string."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"Feature {feature_index} property "
            f"{property_name!r} is empty."
        )

    return value


def validate_geometry(
    geometry: Any,
    feature_id: str,
) -> None:
    if geometry is None:
        raise ValueError(
            f"Feature {feature_id} has no geometry."
        )

    if geometry.is_empty:
        raise ValueError(
            f"Feature {feature_id} has empty geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"Feature {feature_id} has unexpected "
            f"geometry type {geometry.geom_type!r}."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Feature {feature_id} has invalid geometry."
        )


def serialize_geojson(
    data: dict[str, Any],
) -> bytes:
    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def process_level(
    level: int,
    config: dict[str, Any],
) -> None:
    source_path = (
        SOURCE_DIR
        / config["source"]
    )

    output_path = (
        OUTPUT_DIR
        / config["output"]
    )

    print()
    print(f"===== ADM{level} =====")
    print(f"Loading {source_path.name}...")

    data = gpd.read_file(
        source_path
    )

    expected_count = config[
        "expected_count"
    ]

    if len(data) != expected_count:
        raise ValueError(
            f"ADM{level} expected "
            f"{expected_count:,} features, "
            f"got {len(data):,}."
        )

    if data.crs is None:
        raise ValueError(
            f"ADM{level} has no CRS."
        )

    if data.crs.to_epsg() != 4326:
        print(
            f"Reprojecting ADM{level} "
            f"from {data.crs} to EPSG:4326..."
        )

        data = data.to_crs(
            "EPSG:4326"
        )

    property_mapping = config[
        "properties"
    ]

    missing_columns = [
        source_property
        for source_property
        in property_mapping
        if source_property
        not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"ADM{level} is missing columns: "
            f"{missing_columns}"
        )

    features: list[
        dict[str, Any]
    ] = []

    seen_ids: set[str] = set()

    geometry_type_counts: dict[
        str,
        int,
    ] = {}

    for index, row in data.iterrows():
        properties: dict[
            str,
            str,
        ] = {}

        for (
            source_property,
            runtime_property,
        ) in property_mapping.items():
            properties[
                runtime_property
            ] = clean_string(
                row[source_property],
                source_property,
                int(index),
            )

        id_property = next(
            runtime_property
            for runtime_property
            in property_mapping.values()
            if runtime_property.endswith(
                "_id"
            )
        )

        feature_id = properties[
            id_property
        ]

        if feature_id in seen_ids:
            raise ValueError(
                f"ADM{level} has duplicate ID "
                f"{feature_id!r}."
            )

        seen_ids.add(
            feature_id
        )

        geometry = row.geometry

        validate_geometry(
            geometry,
            feature_id,
        )

        geometry_type_counts[
            geometry.geom_type
        ] = (
            geometry_type_counts.get(
                geometry.geom_type,
                0,
            )
            + 1
        )

        features.append(
            {
                "type": "Feature",
                "id": feature_id,
                "properties": properties,
                "geometry": mapping(
                    geometry
                ),
            }
        )

    if len(features) != expected_count:
        raise ValueError(
            f"ADM{level} output feature "
            "count changed during processing."
        )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    serialized = serialize_geojson(
        feature_collection
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_bytes(
        serialized
    )

    print(
        f"Features:       {len(features):,}"
    )

    print(
        f"Geometry types: {geometry_type_counts}"
    )

    print(
        f"File size:      "
        f"{len(serialized):,} bytes "
        f"({len(serialized) / 1_000_000:.3f} MB)"
    )

    print(
        f"Output:         {output_path}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Processing Ecuador administrative divisions..."
    )

    for level, config in LEVELS.items():
        process_level(
            level,
            config,
        )

    print()
    print(
        "Finished Ecuador ADM1-ADM3 processing."
    )


if __name__ == "__main__":
    main()
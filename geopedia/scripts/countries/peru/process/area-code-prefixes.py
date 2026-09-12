"""
Generates Peru's 1-digit geographic telephone area-code prefix regions.

The six prefix regions are created by dissolving Peru's first-level
administrative regions according to the first digit of their geographic
fixed-line telephone area code.

Input:
    data/intermediate/countries/peru/admin/regions.geojson

Outputs:
    data/intermediate/countries/peru/area-codes/prefixes.geojson
    public/data/countries/peru/geojson/area-code-prefixes.geojson
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

INPUT_PATH = Path(
    "data/intermediate/countries/peru/admin/regions.geojson"
)

INTERMEDIATE_OUTPUT_PATH = Path(
    "data/intermediate/countries/peru/area-codes/prefixes.geojson"
)

RUNTIME_OUTPUT_PATH = Path(
    "public/data/countries/peru/geojson/area-code-prefixes.geojson"
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXPECTED_REGION_COUNT = 25
EXPECTED_PREFIX_COUNT = 6

RUNTIME_SIMPLIFICATION_TOLERANCE = 0.01


PREFIX_BY_REGION_ID = {
    "PE01": "4",  # Amazonas
    "PE02": "4",  # Ancash
    "PE03": "8",  # Apurimac
    "PE04": "5",  # Arequipa
    "PE05": "6",  # Ayacucho
    "PE06": "7",  # Cajamarca
    "PE07": "1",  # Callao
    "PE08": "8",  # Cusco
    "PE09": "6",  # Huancavelica
    "PE10": "6",  # Huánuco
    "PE11": "5",  # Ica
    "PE12": "6",  # Junín
    "PE13": "4",  # La Libertad
    "PE14": "7",  # Lambayeque
    "PE15": "1",  # Lima
    "PE16": "6",  # Loreto
    "PE17": "8",  # Madre de Dios
    "PE18": "5",  # Moquegua
    "PE19": "6",  # Pasco
    "PE20": "7",  # Piura
    "PE21": "5",  # Puno
    "PE22": "4",  # San Martín
    "PE23": "5",  # Tacna
    "PE24": "7",  # Tumbes
    "PE25": "6",  # Ucayali
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def write_geojson(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def require_string(
    properties: dict[str, Any],
    key: str,
) -> str:
    value = properties.get(key)

    if not isinstance(value, str):
        raise ValueError(
            f'Missing string property "{key}".'
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f'Empty string property "{key}".'
        )

    return value


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def create_prefix_features(
    region_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    geometries_by_prefix: dict[str, list[Any]] = {}
    region_ids_by_prefix: dict[str, list[str]] = {}

    seen_region_ids: set[str] = set()

    for feature in region_features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "Region feature has invalid properties."
            )

        region_id = require_string(
            properties,
            "region_id",
        )

        if region_id in seen_region_ids:
            raise ValueError(
                f"Duplicate region ID: {region_id}"
            )

        seen_region_ids.add(
            region_id
        )

        prefix = PREFIX_BY_REGION_ID.get(
            region_id
        )

        if prefix is None:
            raise ValueError(
                f"No area-code prefix configured for {region_id}."
            )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            geometry_data,
            dict,
        ):
            raise ValueError(
                f"{region_id} has invalid geometry."
            )

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            raise ValueError(
                f"{region_id} has empty geometry."
            )

        geometries_by_prefix.setdefault(
            prefix,
            [],
        ).append(
            geometry
        )

        region_ids_by_prefix.setdefault(
            prefix,
            [],
        ).append(
            region_id
        )

    expected_region_ids = set(
        PREFIX_BY_REGION_ID
    )

    if seen_region_ids != expected_region_ids:
        missing = sorted(
            expected_region_ids - seen_region_ids
        )

        extra = sorted(
            seen_region_ids - expected_region_ids
        )

        raise ValueError(
            "Region IDs do not match prefix configuration. "
            f"Missing: {missing}; Extra: {extra}"
        )

    prefix_features: list[
        dict[str, Any]
    ] = []

    for prefix in sorted(
        geometries_by_prefix,
        key=int,
    ):
        merged_geometry = unary_union(
            geometries_by_prefix[prefix]
        )

        if merged_geometry.is_empty:
            raise ValueError(
                f"Prefix {prefix} produced empty geometry."
            )

        if not merged_geometry.is_valid:
            merged_geometry = (
                merged_geometry.buffer(0)
            )

        if (
            merged_geometry.is_empty
            or not merged_geometry.is_valid
        ):
            raise ValueError(
                f"Prefix {prefix} produced invalid geometry."
            )

        prefix_features.append(
            {
                "type": "Feature",
                "properties": {
                    "area_code_prefix": prefix,
                    "region_ids": sorted(
                        region_ids_by_prefix[
                            prefix
                        ]
                    ),
                },
                "geometry": mapping(
                    merged_geometry
                ),
            }
        )

    return prefix_features


def create_runtime_features(
    features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime_features: list[
        dict[str, Any]
    ] = []

    for feature in features:
        geometry = shape(
            feature["geometry"]
        )

        simplified = geometry.simplify(
            RUNTIME_SIMPLIFICATION_TOLERANCE,
            preserve_topology=True,
        )

        if simplified.is_empty:
            raise ValueError(
                "Simplification produced empty geometry."
            )

        if not simplified.is_valid:
            simplified = simplified.buffer(
                0
            )

        if (
            simplified.is_empty
            or not simplified.is_valid
        ):
            raise ValueError(
                "Unable to repair simplified geometry."
            )

        runtime_features.append(
            {
                "type": "Feature",
                "properties": feature[
                    "properties"
                ],
                "geometry": mapping(
                    simplified
                ),
            }
        )

    return runtime_features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Generating Peru 1-digit area-code prefix regions...\n"
    )

    data = load_geojson(
        INPUT_PATH
    )

    region_features = data[
        "features"
    ]

    if (
        len(region_features)
        != EXPECTED_REGION_COUNT
    ):
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} regions "
            f"but found {len(region_features)}."
        )

    prefix_features = (
        create_prefix_features(
            region_features
        )
    )

    if (
        len(prefix_features)
        != EXPECTED_PREFIX_COUNT
    ):
        raise ValueError(
            f"Expected {EXPECTED_PREFIX_COUNT} prefixes "
            f"but generated {len(prefix_features)}."
        )

    write_geojson(
        INTERMEDIATE_OUTPUT_PATH,
        prefix_features,
    )

    runtime_features = (
        create_runtime_features(
            prefix_features
        )
    )

    write_geojson(
        RUNTIME_OUTPUT_PATH,
        runtime_features,
    )

    intermediate_size = (
        INTERMEDIATE_OUTPUT_PATH
        .stat()
        .st_size
    )

    runtime_size = (
        RUNTIME_OUTPUT_PATH
        .stat()
        .st_size
    )

    print(
        f"Prefixes:      {len(prefix_features)}"
    )

    print(
        "Prefix values: "
        + ", ".join(
            feature["properties"][
                "area_code_prefix"
            ]
            for feature in prefix_features
        )
    )

    print(
        f"Intermediate:  {intermediate_size:,} bytes "
        f"({intermediate_size / 1_000_000:.3f} MB)"
    )

    print(
        f"Runtime:       {runtime_size:,} bytes "
        f"({runtime_size / 1_000_000:.3f} MB)"
    )

    print(
        f"Output:        {RUNTIME_OUTPUT_PATH}"
    )

    print(
        "\nPeru area-code prefix generation complete."
    )


if __name__ == "__main__":
    main()
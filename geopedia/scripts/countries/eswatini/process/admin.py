"""
Process raw Eswatini administrative boundaries for GeoPedia.

Source files:

    data/raw/countries/eswatini/
        geoBoundaries-SWZ-ADM1.geojson
        geoBoundaries-SWZ-ADM2.geojson

The ADM1 dataset contains Eswatini's 4 regions.

The ADM2 dataset contains 53 tinkhundla but does not include each
inkhundla's parent region. This script derives that relationship spatially
from the ADM1 region boundaries.

The source prefix "Inkhundla " is removed from ADM2 names.

Canonical output properties:

Regions:
    region_id
    region

Tinkhundla:
    inkhundla_id
    inkhundla
    region

Outputs:

    data/intermediate/countries/eswatini/admin/
        regions.geojson
        tinkhundla.geojson

Run from the GeoPedia project root:

    python scripts/countries/eswatini/process/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.strtree import STRtree


RAW_DIR = Path(
    "data/raw/countries/eswatini"
)

OUTPUT_DIR = Path(
    "public/data/countries/eswatini/geojson"
)

REGIONS_INPUT = (
    RAW_DIR
    / "geoBoundaries-SWZ-ADM1.geojson"
)

TINKHUNDLA_INPUT = (
    RAW_DIR
    / "geoBoundaries-SWZ-ADM2.geojson"
)

REGIONS_OUTPUT = (
    OUTPUT_DIR
    / "regions.geojson"
)

TINKHUNDLA_OUTPUT = (
    OUTPUT_DIR
    / "tinkhundla.geojson"
)


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if (
        data.get("type")
        != "FeatureCollection"
    ):
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def clean_inkhundla_name(
    name: str,
) -> str:
    """Remove geoBoundaries' redundant 'Inkhundla ' name prefix."""
    prefix = "Inkhundla "

    if name.startswith(
        prefix
    ):
        return name[
            len(prefix):
        ]

    return name


def validate_geometry(
    geometry_data: dict[str, Any],
    label: str,
):
    """Create and validate a polygonal Shapely geometry."""
    geometry = shape(
        geometry_data
    )

    if geometry.is_empty:
        raise ValueError(
            f"{label} has empty geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{label} has unexpected geometry type "
            f"{geometry.geom_type}."
        )

    if not geometry.is_valid:
        repaired = geometry.buffer(
            0
        )

        if (
            repaired.is_empty
            or repaired.geom_type
            not in {
                "Polygon",
                "MultiPolygon",
            }
            or not repaired.is_valid
        ):
            raise ValueError(
                f"{label} has invalid geometry "
                "that could not be repaired."
            )

        geometry = repaired

    return geometry


def process_regions(
    data: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[Any],
    list[str],
]:
    """Normalize Eswatini's region features."""
    output_features: list[
        dict[str, Any]
    ] = []

    geometries: list[Any] = []
    names: list[str] = []

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for feature in data[
        "features"
    ]:
        properties = feature.get(
            "properties",
            {},
        )

        region_id = properties.get(
            "shapeID"
        )

        region = properties.get(
            "shapeName"
        )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            region_id,
            str,
        ) or not region_id:
            raise ValueError(
                "Region feature is missing shapeID."
            )

        if not isinstance(
            region,
            str,
        ) or not region:
            raise ValueError(
                f"Region {region_id} is missing shapeName."
            )

        if geometry_data is None:
            raise ValueError(
                f"Region {region} has no geometry."
            )

        if region_id in seen_ids:
            raise ValueError(
                f"Duplicate region ID: {region_id}"
            )

        if region in seen_names:
            raise ValueError(
                f"Duplicate region name: {region}"
            )

        geometry = validate_geometry(
            geometry_data,
            f"Region {region}",
        )

        seen_ids.add(
            region_id
        )

        seen_names.add(
            region
        )

        geometries.append(
            geometry
        )

        names.append(
            region
        )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "region_id": region_id,
                    "region": region,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    return (
        output_features,
        geometries,
        names,
    )


def find_parent_region(
    inkhundla_geometry,
    region_geometries: list[Any],
    region_names: list[str],
    region_tree: STRtree,
) -> str:
    """
    Assign an inkhundla to the region containing the largest portion of it.

    A representative point is attempted first. If source boundary
    discrepancies make that inconclusive, the region with the greatest
    polygon overlap is used.
    """
    representative_point = (
        inkhundla_geometry.representative_point()
    )

    candidate_indices = region_tree.query(
        representative_point
    )

    containing_indices = [
        int(index)
        for index in candidate_indices
        if region_geometries[
            int(index)
        ].covers(
            representative_point
        )
    ]

    if len(
        containing_indices
    ) == 1:
        return region_names[
            containing_indices[0]
        ]

    candidate_indices = region_tree.query(
        inkhundla_geometry
    )

    best_index: int | None = None
    best_area = 0.0

    for raw_index in candidate_indices:
        index = int(
            raw_index
        )

        intersection = (
            inkhundla_geometry.intersection(
                region_geometries[index]
            )
        )

        area = intersection.area

        if area > best_area:
            best_area = area
            best_index = index

    if (
        best_index is None
        or best_area <= 0
    ):
        raise ValueError(
            "Could not spatially assign an inkhundla "
            "to a region."
        )

    return region_names[
        best_index
    ]


def process_tinkhundla(
    data: dict[str, Any],
    region_geometries: list[Any],
    region_names: list[str],
) -> list[dict[str, Any]]:
    """Normalize tinkhundla and derive their parent regions."""
    region_tree = STRtree(
        region_geometries
    )

    output_features: list[
        dict[str, Any]
    ] = []

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    region_counts = {
        region: 0
        for region in region_names
    }

    for feature in data[
        "features"
    ]:
        properties = feature.get(
            "properties",
            {},
        )

        inkhundla_id = properties.get(
            "shapeID"
        )

        source_name = properties.get(
            "shapeName"
        )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            inkhundla_id,
            str,
        ) or not inkhundla_id:
            raise ValueError(
                "Inkhundla feature is missing shapeID."
            )

        if not isinstance(
            source_name,
            str,
        ) or not source_name:
            raise ValueError(
                f"Inkhundla {inkhundla_id} "
                "is missing shapeName."
            )

        if geometry_data is None:
            raise ValueError(
                f"Inkhundla {source_name} has no geometry."
            )

        inkhundla = clean_inkhundla_name(
            source_name
        )

        if inkhundla_id in seen_ids:
            raise ValueError(
                f"Duplicate inkhundla ID: {inkhundla_id}"
            )

        if inkhundla in seen_names:
            raise ValueError(
                f"Duplicate inkhundla name: {inkhundla}"
            )

        geometry = validate_geometry(
            geometry_data,
            f"Inkhundla {inkhundla}",
        )

        region = find_parent_region(
            geometry,
            region_geometries,
            region_names,
            region_tree,
        )

        seen_ids.add(
            inkhundla_id
        )

        seen_names.add(
            inkhundla
        )

        region_counts[
            region
        ] += 1

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "inkhundla_id": inkhundla_id,
                    "inkhundla": inkhundla,
                    "region": region,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    print()
    print(
        "Tinkhundla by region"
    )
    print(
        "--------------------"
    )

    for region in sorted(
        region_counts
    ):
        print(
            f"{region}: "
            f"{region_counts[region]}"
        )

    return output_features


def write_geojson(
    path: Path,
    features: list[
        dict[str, Any]
    ],
) -> None:
    """Write a compact GeoJSON FeatureCollection."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    size_mb = (
        path.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"Wrote {path} "
        f"({size_mb:.2f} MB)"
    )


def main() -> None:
    """Process Eswatini's regions and tinkhundla."""
    print(
        f"Reading {REGIONS_INPUT}..."
    )

    region_data = load_geojson(
        REGIONS_INPUT
    )

    print(
        f"Region source features: "
        f"{len(region_data['features']):,}"
    )

    (
        region_features,
        region_geometries,
        region_names,
    ) = process_regions(
        region_data
    )

    print(
        f"Processed regions: "
        f"{len(region_features):,}"
    )

    print()
    print(
        f"Reading {TINKHUNDLA_INPUT}..."
    )

    tinkhundla_data = load_geojson(
        TINKHUNDLA_INPUT
    )

    print(
        f"Tinkhundla source features: "
        f"{len(tinkhundla_data['features']):,}"
    )

    tinkhundla_features = process_tinkhundla(
        tinkhundla_data,
        region_geometries,
        region_names,
    )

    print(
        f"Processed tinkhundla: "
        f"{len(tinkhundla_features):,}"
    )

    print()

    write_geojson(
        REGIONS_OUTPUT,
        region_features,
    )

    write_geojson(
        TINKHUNDLA_OUTPUT,
        tinkhundla_features,
    )

    print()
    print(
        "Done."
    )


if __name__ == "__main__":
    main()
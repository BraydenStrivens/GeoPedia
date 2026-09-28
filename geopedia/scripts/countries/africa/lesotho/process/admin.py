"""
Process raw Lesotho administrative boundaries for GeoPedia.

Source files:

    data/raw/countries/lesotho/
        geoBoundaries-LSO-ADM1.geojson
        geoBoundaries-LSO-ADM2.geojson

The geoBoundaries ADM1 dataset contains Lesotho's 10 districts.

The ADM2 dataset contains 78 constituencies but does not include the parent
district for each constituency. This script derives that relationship
spatially from the ADM1 district boundaries.

Canonical output properties:

Districts:
    district_id
    district

Constituencies:
    constituency_id
    constituency
    district

District names have the source suffix " District" removed.

Outputs:

    data/intermediate/countries/lesotho/admin/
        districts.geojson
        constituencies.geojson

Run from the GeoPedia project root:

    python scripts/countries/lesotho/process/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.strtree import STRtree


RAW_DIR = Path(
    "data/raw/countries/lesotho"
)

OUTPUT_DIR = Path(
    "data/intermediate/countries/lesotho/admin"
)

DISTRICTS_INPUT = (
    RAW_DIR
    / "geoBoundaries-LSO-ADM1.geojson"
)

CONSTITUENCIES_INPUT = (
    RAW_DIR
    / "geoBoundaries-LSO-ADM2.geojson"
)

DISTRICTS_OUTPUT = (
    OUTPUT_DIR
    / "districts.geojson"
)

CONSTITUENCIES_OUTPUT = (
    OUTPUT_DIR
    / "constituencies.geojson"
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


def clean_district_name(
    name: str,
) -> str:
    """Remove geoBoundaries' trailing ' District' suffix."""
    suffix = " District"

    if name.endswith(
        suffix
    ):
        return name[
            :-len(suffix)
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


def process_districts(
    data: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[Any],
    list[str],
]:
    """
    Normalize district features and prepare their geometries for spatial
    constituency assignment.
    """
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

        source_id = properties.get(
            "shapeID"
        )

        source_name = properties.get(
            "shapeName"
        )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            source_id,
            str,
        ):
            raise ValueError(
                "District feature is missing shapeID."
            )

        if not isinstance(
            source_name,
            str,
        ):
            raise ValueError(
                f"District {source_id} is missing shapeName."
            )

        if geometry_data is None:
            raise ValueError(
                f"District {source_name} has no geometry."
            )

        district = clean_district_name(
            source_name
        )

        if source_id in seen_ids:
            raise ValueError(
                f"Duplicate district ID: {source_id}"
            )

        if district in seen_names:
            raise ValueError(
                f"Duplicate district name: {district}"
            )

        geometry = validate_geometry(
            geometry_data,
            f"District {district}",
        )

        seen_ids.add(
            source_id
        )

        seen_names.add(
            district
        )

        geometries.append(
            geometry
        )

        names.append(
            district
        )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "district_id": source_id,
                    "district": district,
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


def find_parent_district(
    constituency_geometry,
    district_geometries: list[Any],
    district_names: list[str],
    district_tree: STRtree,
) -> str:
    """
    Assign a constituency to the district containing the largest portion of
    its geometry.

    A representative point is tried first because constituencies should be
    nested inside districts. If boundary discrepancies prevent a direct
    point match, intersecting district polygons are compared by overlap area.
    """
    representative_point = (
        constituency_geometry.representative_point()
    )

    candidate_indices = (
        district_tree.query(
            representative_point
        )
    )

    containing_indices = [
        int(index)
        for index in candidate_indices
        if district_geometries[
            int(index)
        ].covers(
            representative_point
        )
    ]

    if (
        len(
            containing_indices
        )
        == 1
    ):
        return district_names[
            containing_indices[
                0
            ]
        ]

    candidate_indices = (
        district_tree.query(
            constituency_geometry
        )
    )

    best_index: int | None = None
    best_area = 0.0

    for raw_index in candidate_indices:
        index = int(
            raw_index
        )

        district_geometry = (
            district_geometries[
                index
            ]
        )

        intersection = (
            constituency_geometry.intersection(
                district_geometry
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
            "Could not spatially assign constituency "
            "to a district."
        )

    return district_names[
        best_index
    ]


def process_constituencies(
    data: dict[str, Any],
    district_geometries: list[Any],
    district_names: list[str],
) -> list[dict[str, Any]]:
    """Normalize constituencies and derive their parent districts."""
    district_tree = STRtree(
        district_geometries
    )

    output_features: list[
        dict[str, Any]
    ] = []

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    district_counts: dict[
        str,
        int,
    ] = {
        district: 0
        for district in district_names
    }

    for feature in data[
        "features"
    ]:
        properties = feature.get(
            "properties",
            {},
        )

        source_id = properties.get(
            "shapeID"
        )

        constituency = properties.get(
            "shapeName"
        )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            source_id,
            str,
        ):
            raise ValueError(
                "Constituency feature is missing shapeID."
            )

        if not isinstance(
            constituency,
            str,
        ):
            raise ValueError(
                f"Constituency {source_id} is missing shapeName."
            )

        if geometry_data is None:
            raise ValueError(
                f"Constituency {constituency} has no geometry."
            )

        if source_id in seen_ids:
            raise ValueError(
                f"Duplicate constituency ID: {source_id}"
            )

        if constituency in seen_names:
            raise ValueError(
                f"Duplicate constituency name: {constituency}"
            )

        geometry = validate_geometry(
            geometry_data,
            f"Constituency {constituency}",
        )

        district = find_parent_district(
            geometry,
            district_geometries,
            district_names,
            district_tree,
        )

        seen_ids.add(
            source_id
        )

        seen_names.add(
            constituency
        )

        district_counts[
            district
        ] += 1

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "constituency_id": source_id,
                    "constituency": constituency,
                    "district": district,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    print()
    print(
        "Constituencies by district"
    )
    print(
        "--------------------------"
    )

    for district in sorted(
        district_counts
    ):
        print(
            f"{district}: "
            f"{district_counts[district]}"
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
    """Process Lesotho districts and constituencies."""
    print(
        f"Reading {DISTRICTS_INPUT}..."
    )

    district_data = load_geojson(
        DISTRICTS_INPUT
    )

    print(
        f"District source features: "
        f"{len(district_data['features']):,}"
    )

    (
        district_features,
        district_geometries,
        district_names,
    ) = process_districts(
        district_data
    )

    print(
        f"Processed districts: "
        f"{len(district_features):,}"
    )

    print()
    print(
        f"Reading {CONSTITUENCIES_INPUT}..."
    )

    constituency_data = (
        load_geojson(
            CONSTITUENCIES_INPUT
        )
    )

    print(
        f"Constituency source features: "
        f"{len(constituency_data['features']):,}"
    )

    constituency_features = (
        process_constituencies(
            constituency_data,
            district_geometries,
            district_names,
        )
    )

    print(
        f"Processed constituencies: "
        f"{len(constituency_features):,}"
    )

    print()

    write_geojson(
        DISTRICTS_OUTPUT,
        district_features,
    )

    write_geojson(
        CONSTITUENCIES_OUTPUT,
        constituency_features,
    )

    print()
    print(
        "Done."
    )


if __name__ == "__main__":
    main()
"""
Generate Chile 1-digit postal-prefix GeoJSON from the canonical region data.

Chile's first postal-code digit divides the country into broad geographic
zones. Prefixes 7, 8, and 9 all apply to the Metropolitan Region for the
purposes of GeoPedia's quiz, so they share a single geographic feature.

Input
-----
data/intermediate/countries/chile/admin/regions.geojson

Output
------
data/intermediate/countries/chile/postal-prefixes.geojson

Run with:

    python scripts/countries/chile/process/postal-prefixes.py
"""

import json
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "chile"
    / "geojson"
    / "regions.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "chile"
    / "geojson"
    / "postal-prefixes.geojson"
)


# Each entry represents one geographic feature.
#
# Prefixes 7, 8, and 9 share the Metropolitan Region, so they are represented
# by one feature with the ID "7/8/9".
POSTAL_PREFIX_REGIONS = {
    "1": [
        "CL15",  # Arica y Parinacota
        "CL01",  # Tarapacá
        "CL02",  # Antofagasta
        "CL03",  # Atacama
        "CL04",  # Coquimbo
    ],
    "2": [
        "CL05",  # Valparaíso
    ],
    "3": [
        "CL06",  # O'Higgins
        "CL07",  # Maule
        "CL16",  # Ñuble
    ],
    "4": [
        "CL08",  # Bío-Bío
        "CL09",  # La Araucanía
    ],
    "5": [
        "CL14",  # Los Ríos
        "CL10",  # Los Lagos
    ],
    "6": [
        "CL11",  # Aysén
        "CL12",  # Magallanes
    ],
    "7/8/9": [
        "CL13",  # Metropolitana de Santiago
    ],
}


POSTAL_PREFIX_ANSWERS = {
    "1": ["1"],
    "2": ["2"],
    "3": ["3"],
    "4": ["4"],
    "5": ["5"],
    "6": ["6"],
    "7/8/9": ["7", "8", "9"],
}


EXPECTED_REGIONS = 16
EXPECTED_FEATURES = 7
EXPECTED_ANSWERS = 9


def load_geojson(
    path: Path,
) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_region_index(
    geojson: dict,
) -> dict:
    features = geojson.get(
        "features",
        [],
    )

    if len(features) != EXPECTED_REGIONS:
        raise ValueError(
            f"Expected {EXPECTED_REGIONS} regions, "
            f"found {len(features)}."
        )

    region_index = {}

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        region_id = properties.get(
            "region_id"
        )

        if not region_id:
            raise ValueError(
                "Region feature is missing region_id."
            )

        if region_id in region_index:
            raise ValueError(
                f"Duplicate region_id: {region_id}"
            )

        geometry = feature.get(
            "geometry"
        )

        if geometry is None:
            raise ValueError(
                f"Region {region_id} has no geometry."
            )

        region_index[region_id] = {
            "name": properties.get(
                "region"
            ),
            "geometry": shape(
                geometry
            ),
        }

    return region_index


def validate_region_mapping(
    region_index: dict,
) -> None:
    assigned_regions = []

    for region_ids in (
        POSTAL_PREFIX_REGIONS.values()
    ):
        for region_id in region_ids:
            if region_id not in region_index:
                raise ValueError(
                    "Postal-prefix mapping references "
                    f"unknown region_id: {region_id}"
                )

            assigned_regions.append(
                region_id
            )

    duplicates = {
        region_id
        for region_id in assigned_regions
        if assigned_regions.count(
            region_id
        ) > 1
    }

    if duplicates:
        raise ValueError(
            "Regions assigned to multiple postal "
            f"features: {sorted(duplicates)}"
        )

    source_regions = set(
        region_index.keys()
    )

    mapped_regions = set(
        assigned_regions
    )

    missing = (
        source_regions - mapped_regions
    )

    extra = (
        mapped_regions - source_regions
    )

    if missing:
        raise ValueError(
            "Regions missing from postal-prefix "
            f"mapping: {sorted(missing)}"
        )

    if extra:
        raise ValueError(
            "Unknown mapped regions: "
            f"{sorted(extra)}"
        )


def create_feature(
    postal_prefix_id: str,
    region_ids: list[str],
    region_index: dict,
) -> dict:
    geometries = [
        region_index[region_id]["geometry"]
        for region_id in region_ids
    ]

    dissolved_geometry = unary_union(
        geometries
    )

    if dissolved_geometry.is_empty:
        raise ValueError(
            "Dissolved geometry is empty for "
            f"postal prefix {postal_prefix_id}."
        )

    if not dissolved_geometry.is_valid:
        raise ValueError(
            "Dissolved geometry is invalid for "
            f"postal prefix {postal_prefix_id}."
        )

    answers = POSTAL_PREFIX_ANSWERS[
        postal_prefix_id
    ]

    return {
        "type": "Feature",
        "properties": {
            "postal_prefix_id": postal_prefix_id,
            "postal_prefixes": answers,
            "postal_prefix": " / ".join(
                answers
            ),
        },
        "geometry": mapping(
            dissolved_geometry
        ),
    }


def validate_output(
    features: list[dict],
) -> None:
    if len(features) != EXPECTED_FEATURES:
        raise ValueError(
            f"Expected {EXPECTED_FEATURES} output "
            f"features, found {len(features)}."
        )

    answer_count = sum(
        len(
            feature["properties"][
                "postal_prefixes"
            ]
        )
        for feature in features
    )

    if answer_count != EXPECTED_ANSWERS:
        raise ValueError(
            f"Expected {EXPECTED_ANSWERS} answers, "
            f"found {answer_count}."
        )

    feature_ids = [
        feature["properties"][
            "postal_prefix_id"
        ]
        for feature in features
    ]

    if len(feature_ids) != len(
        set(feature_ids)
    ):
        raise ValueError(
            "Duplicate postal_prefix_id values "
            "in output."
        )


def write_geojson(
    features: list[dict],
    path: Path,
) -> None:
    output = {
        "type": "FeatureCollection",
        "features": features,
    }

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def main() -> None:
    print(
        "Generating Chile 1-digit postal-prefix "
        "GeoJSON..."
    )

    source = load_geojson(
        INPUT_PATH
    )

    region_index = build_region_index(
        source
    )

    validate_region_mapping(
        region_index
    )

    features = []

    for (
        postal_prefix_id,
        region_ids,
    ) in POSTAL_PREFIX_REGIONS.items():
        feature = create_feature(
            postal_prefix_id,
            region_ids,
            region_index,
        )

        features.append(
            feature
        )

    validate_output(
        features
    )

    write_geojson(
        features,
        OUTPUT_PATH,
    )

    answer_count = sum(
        len(
            feature["properties"][
                "postal_prefixes"
            ]
        )
        for feature in features
    )

    size_mb = (
        OUTPUT_PATH.stat().st_size
        / 1024
        / 1024
    )

    print()
    print(
        f"Features: {len(features)}"
    )
    print(
        f"Answers:  {answer_count}"
    )
    print(
        f"Size:     {size_mb:.2f} MB"
    )
    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
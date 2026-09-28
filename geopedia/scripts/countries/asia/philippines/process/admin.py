"""
Process Philippines administrative boundaries for GeoPedia.

This script converts the raw Philippines administrative GeoJSON datasets into
clean, canonical intermediate GeoJSON used by GeoPedia.

Raw inputs
----------
    data/raw/countries/philippines/phl_admin_boundaries/
        phl_admin1.geojson
        phl_admin2.geojson
        phl_admin3.geojson
        phl_admin4.geojson

Intermediate outputs
--------------------
    data/intermediate/countries/philippines/
        regions.geojson
        provinces.geojson
        municipalities-cities.geojson
        barangays.geojson

Canonicalization
----------------
Region names are normalized so numbered source labels such as:

    Region I (Ilocos Region)

become:

    Ilocos Region

This normalization is applied at every administrative level so lower-level
grouping properties use the same canonical region names as the region quiz.

Several province-level source names are also normalized:

    City of Isabela (not a province)
        -> City of Isabela

    Davao de Oro (Compostela Valley)
        -> Davao de Oro

    Cotabato (North Cotabato)
        -> Cotabato

Metropolitan Manila
-------------------
The source contains four province-level Metropolitan Manila districts:

    PH13039  Metropolitan Manila First District
    PH13074  Metropolitan Manila Second District
    PH13075  Metropolitan Manila Third District
    PH13076  Metropolitan Manila Fourth District

Their geometries are unioned into one GeoPedia province-level feature:

    province_id = PH13039
    province    = Metropolitan Manila
    region_id   = PH13
    region      = National Capital Region (NCR)

Admin 3 and Admin 4 features belonging to any of the four source districts are
remapped to PH13039 / Metropolitan Manila.

Cotabato
--------
The source contains:

    PH12047  Cotabato (North Cotabato)
    PH19099  Special Geographic Area

GeoPedia treats the Special Geographic Area as part of Cotabato for this quiz.
Its geometry is unioned with Cotabato and the resulting feature uses:

    province_id = PH12047
    province    = Cotabato
    region_id   = PH12
    region      = Soccsksargen

Admin 3 and Admin 4 descendants of PH19099 are consequently reassigned to
Cotabato and Soccsksargen.

Feature counts
--------------
The raw Admin 2 dataset contains 88 features.

Merging four Metropolitan Manila districts into one removes three features.
Merging Special Geographic Area into Cotabato removes one more.

The processed Admin 2 dataset therefore contains 84 features.

Admin 1, Admin 3, and Admin 4 retain their original feature counts:

    Admin 1:       17
    Admin 2:       84
    Admin 3:    1,642
    Admin 4:   42,048

Geometry
--------
Merged province geometries are combined using Shapely unary_union so internal
boundaries between merged source features are removed.

No simplification is performed here. Simplification and publication are handled
separately by:

    scripts/countries/philippines/process/simplify-admin.py

Requirements
------------
    pip install ijson shapely

Run from the GeoPedia project root:

    python scripts/countries/philippines/process/admin.py
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import ijson
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "philippines"
    / "phl_admin_boundaries"
)

INTERMEDIATE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "philippines"
)


# ---------------------------------------------------------------------------
# Expected feature counts
# ---------------------------------------------------------------------------

EXPECTED_REGION_COUNT = 17

RAW_PROVINCE_COUNT = 88
EXPECTED_PROVINCE_COUNT = 84

EXPECTED_MUNICIPALITY_CITY_COUNT = 1_642
EXPECTED_BARANGAY_COUNT = 42_048


# ---------------------------------------------------------------------------
# Region normalization
# ---------------------------------------------------------------------------

REGION_NAME_OVERRIDES = {
    "Region I (Ilocos Region)": "Ilocos Region",
    "Region II (Cagayan Valley)": "Cagayan Valley",
    "Region III (Central Luzon)": "Central Luzon",
    "Region IV-A (Calabarzon)": "Calabarzon",
    "Region V (Bicol Region)": "Bicol Region",
    "Region VI (Western Visayas)": "Western Visayas",
    "Region VII (Central Visayas)": "Central Visayas",
    "Region VIII (Eastern Visayas)": "Eastern Visayas",
    "Region IX (Zamboanga Peninsula)": "Zamboanga Peninsula",
    "Region X (Northern Mindanao)": "Northern Mindanao",
    "Region XI (Davao Region)": "Davao Region",
    "Region XII (Soccsksargen)": "Soccsksargen",
    "Region XIII (Caraga)": "Caraga",
}


# ---------------------------------------------------------------------------
# Province normalization
# ---------------------------------------------------------------------------

PROVINCE_NAME_OVERRIDES = {
    "City of Isabela (not a province)": "City of Isabela",
    "Davao de Oro (Compostela Valley)": "Davao de Oro",
    "Cotabato (North Cotabato)": "Cotabato",
}


# ---------------------------------------------------------------------------
# Metropolitan Manila merge
# ---------------------------------------------------------------------------

METROPOLITAN_MANILA_CANONICAL_ID = "PH13039"
METROPOLITAN_MANILA_NAME = "Metropolitan Manila"

METROPOLITAN_MANILA_SOURCE_IDS = {
    "PH13039",
    "PH13074",
    "PH13075",
    "PH13076",
}

METROPOLITAN_MANILA_REGION_ID = "PH13"
METROPOLITAN_MANILA_REGION_NAME = "National Capital Region (NCR)"


# ---------------------------------------------------------------------------
# Cotabato merge
# ---------------------------------------------------------------------------

COTABATO_CANONICAL_ID = "PH12047"
COTABATO_NAME = "Cotabato"

SPECIAL_GEOGRAPHIC_AREA_ID = "PH19099"

COTABATO_REGION_ID = "PH12"
COTABATO_REGION_NAME = "Soccsksargen"


# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdminDataset:
    """Configuration for one Philippines administrative source dataset."""

    level: int
    label: str
    raw_filename: str
    output_filename: str
    expected_output_count: int

    output_id_property: str
    output_name_property: str

    parent_levels: tuple[int, ...]


DATASETS = (
    AdminDataset(
        level=1,
        label="Regions",
        raw_filename="phl_admin1.geojson",
        output_filename="regions.geojson",
        expected_output_count=EXPECTED_REGION_COUNT,
        output_id_property="region_id",
        output_name_property="region",
        parent_levels=(),
    ),
    AdminDataset(
        level=2,
        label="Provinces / Province-Level Units",
        raw_filename="phl_admin2.geojson",
        output_filename="provinces.geojson",
        expected_output_count=EXPECTED_PROVINCE_COUNT,
        output_id_property="province_id",
        output_name_property="province",
        parent_levels=(1,),
    ),
    AdminDataset(
        level=3,
        label="Municipalities / Cities",
        raw_filename="phl_admin3.geojson",
        output_filename="municipalities-cities.geojson",
        expected_output_count=EXPECTED_MUNICIPALITY_CITY_COUNT,
        output_id_property="municipality_city_id",
        output_name_property="municipality_city",
        parent_levels=(1, 2),
    ),
    AdminDataset(
        level=4,
        label="Barangays",
        raw_filename="phl_admin4.geojson",
        output_filename="barangays.geojson",
        expected_output_count=EXPECTED_BARANGAY_COUNT,
        output_id_property="barangay_id",
        output_name_property="barangay",
        parent_levels=(1, 2, 3),
    ),
)


LEVEL_OUTPUT_PROPERTIES = {
    1: (
        "region_id",
        "region",
    ),
    2: (
        "province_id",
        "province",
    ),
    3: (
        "municipality_city_id",
        "municipality_city",
    ),
    4: (
        "barangay_id",
        "barangay",
    ),
}


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------


def require_string(
    value: Any,
    *,
    property_name: str,
    dataset_label: str,
    feature_number: int,
) -> str:
    """Validate and return a required non-empty string."""

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{dataset_label}: feature {feature_number:,} has a non-string "
            f"{property_name!r}."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{dataset_label}: feature {feature_number:,} has a blank "
            f"{property_name!r}."
        )

    return value


def normalize_region_name(
    name: str,
) -> str:
    """Return GeoPedia's canonical name for a Philippines region."""

    return REGION_NAME_OVERRIDES.get(
        name,
        name,
    )


def normalize_province_name(
    name: str,
) -> str:
    """Return GeoPedia's canonical name for a province-level unit."""

    return PROVINCE_NAME_OVERRIDES.get(
        name,
        name,
    )


# ---------------------------------------------------------------------------
# Hierarchy normalization
# ---------------------------------------------------------------------------


def normalize_region(
    region_id: str,
    region_name: str,
) -> tuple[str, str]:
    """Normalize a region ID/name pair."""

    return (
        region_id,
        normalize_region_name(
            region_name
        ),
    )


def normalize_province_hierarchy(
    *,
    province_id: str,
    province_name: str,
    region_id: str,
    region_name: str,
) -> tuple[
    str,
    str,
    str,
    str,
]:
    """
    Normalize a province and its region hierarchy.

    This handles:
    - Metropolitan Manila district consolidation.
    - Special Geographic Area reassignment to Cotabato.
    - Province label normalization.
    - Region label normalization.
    """

    region_id, region_name = normalize_region(
        region_id,
        region_name,
    )

    if province_id in METROPOLITAN_MANILA_SOURCE_IDS:
        return (
            METROPOLITAN_MANILA_CANONICAL_ID,
            METROPOLITAN_MANILA_NAME,
            METROPOLITAN_MANILA_REGION_ID,
            METROPOLITAN_MANILA_REGION_NAME,
        )

    if province_id == SPECIAL_GEOGRAPHIC_AREA_ID:
        return (
            COTABATO_CANONICAL_ID,
            COTABATO_NAME,
            COTABATO_REGION_ID,
            COTABATO_REGION_NAME,
        )

    if province_id == COTABATO_CANONICAL_ID:
        return (
            COTABATO_CANONICAL_ID,
            COTABATO_NAME,
            COTABATO_REGION_ID,
            COTABATO_REGION_NAME,
        )

    return (
        province_id,
        normalize_province_name(
            province_name
        ),
        region_id,
        region_name,
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def parse_geometry(
    geometry_data: Any,
    *,
    dataset_label: str,
    feature_number: int,
    feature_id: str,
) -> BaseGeometry:
    """Parse and validate a polygonal GeoJSON geometry."""

    if not isinstance(
        geometry_data,
        dict,
    ):
        raise ValueError(
            f"{dataset_label}: feature {feature_number:,} ({feature_id}) "
            "has missing or malformed geometry."
        )

    try:
        geometry = shape(
            geometry_data
        )

    except Exception as error:
        raise ValueError(
            f"{dataset_label}: feature {feature_number:,} ({feature_id}) "
            "could not be parsed by Shapely."
        ) from error

    if geometry.is_empty:
        raise ValueError(
            f"{dataset_label}: feature {feature_number:,} ({feature_id}) "
            "has empty geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{dataset_label}: feature {feature_number:,} ({feature_id}) "
            f"has unexpected geometry type {geometry.geom_type!r}."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{dataset_label}: feature {feature_number:,} ({feature_id}) "
            "has invalid geometry."
        )

    return geometry


def merge_geometries(
    geometries: list[BaseGeometry],
    *,
    label: str,
) -> BaseGeometry:
    """Union a collection of polygonal geometries."""

    if not geometries:
        raise ValueError(
            f"No geometries were collected for {label}."
        )

    merged = unary_union(
        geometries
    )

    if merged.is_empty:
        raise ValueError(
            f"The merged geometry for {label} is empty."
        )

    if merged.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"The merged geometry for {label} has unexpected geometry type "
            f"{merged.geom_type!r}."
        )

    if not merged.is_valid:
        raise ValueError(
            f"The merged geometry for {label} is invalid."
        )

    return merged


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def make_feature(
    *,
    properties: dict[str, str],
    geometry: BaseGeometry,
) -> dict[str, Any]:
    """Create a GeoJSON Feature."""

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": mapping(
            geometry
        ),
    }


def write_feature_collection(
    path: Path,
    features: list[dict[str, Any]],
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


def file_size_mb(
    path: Path,
) -> float:
    """Return file size in MiB."""

    return (
        path.stat().st_size
        / (1024 * 1024)
    )


# ---------------------------------------------------------------------------
# Region processing
# ---------------------------------------------------------------------------


def process_regions(
    dataset: AdminDataset,
) -> list[dict[str, Any]]:
    """Process Admin 1 regions."""

    input_path = (
        RAW_DIRECTORY
        / dataset.raw_filename
    )

    features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    with input_path.open(
        "rb",
    ) as input_file:
        source_features = ijson.items(
            input_file,
            "features.item",
            use_float=True,
        )

        for feature_number, feature in enumerate(
            source_features,
            start=1,
        ):
            properties = feature.get(
                "properties"
            )

            if not isinstance(
                properties,
                dict,
            ):
                raise ValueError(
                    f"{dataset.label}: feature {feature_number:,} has "
                    "malformed properties."
                )

            region_id = require_string(
                properties.get(
                    "adm1_pcode"
                ),
                property_name="adm1_pcode",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            region_name = require_string(
                properties.get(
                    "adm1_name"
                ),
                property_name="adm1_name",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            region_name = normalize_region_name(
                region_name
            )

            if region_id in seen_ids:
                raise ValueError(
                    f"{dataset.label}: duplicate region ID {region_id!r}."
                )

            seen_ids.add(
                region_id
            )

            geometry = parse_geometry(
                feature.get(
                    "geometry"
                ),
                dataset_label=dataset.label,
                feature_number=feature_number,
                feature_id=region_id,
            )

            features.append(
                make_feature(
                    properties={
                        "region_id": region_id,
                        "region": region_name,
                    },
                    geometry=geometry,
                )
            )

    if len(
        features
    ) != dataset.expected_output_count:
        raise ValueError(
            f"{dataset.label}: expected {dataset.expected_output_count:,} "
            f"features but produced {len(features):,}."
        )

    return features


# ---------------------------------------------------------------------------
# Province processing
# ---------------------------------------------------------------------------


def process_provinces(
    dataset: AdminDataset,
) -> list[dict[str, Any]]:
    """Process Admin 2 and perform the required province geometry merges."""

    input_path = (
        RAW_DIRECTORY
        / dataset.raw_filename
    )

    ordinary_features: list[dict[str, Any]] = []

    seen_source_ids: set[str] = set()

    manila_geometries: list[BaseGeometry] = []
    cotabato_geometries: list[BaseGeometry] = []

    with input_path.open(
        "rb",
    ) as input_file:
        source_features = ijson.items(
            input_file,
            "features.item",
            use_float=True,
        )

        for feature_number, feature in enumerate(
            source_features,
            start=1,
        ):
            properties = feature.get(
                "properties"
            )

            if not isinstance(
                properties,
                dict,
            ):
                raise ValueError(
                    f"{dataset.label}: feature {feature_number:,} has "
                    "malformed properties."
                )

            province_id = require_string(
                properties.get(
                    "adm2_pcode"
                ),
                property_name="adm2_pcode",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            province_name = require_string(
                properties.get(
                    "adm2_name"
                ),
                property_name="adm2_name",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            region_id = require_string(
                properties.get(
                    "adm1_pcode"
                ),
                property_name="adm1_pcode",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            region_name = require_string(
                properties.get(
                    "adm1_name"
                ),
                property_name="adm1_name",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            if province_id in seen_source_ids:
                raise ValueError(
                    f"{dataset.label}: duplicate source province ID "
                    f"{province_id!r}."
                )

            seen_source_ids.add(
                province_id
            )

            geometry = parse_geometry(
                feature.get(
                    "geometry"
                ),
                dataset_label=dataset.label,
                feature_number=feature_number,
                feature_id=province_id,
            )

            if province_id in METROPOLITAN_MANILA_SOURCE_IDS:
                manila_geometries.append(
                    geometry
                )
                continue

            if province_id in {
                COTABATO_CANONICAL_ID,
                SPECIAL_GEOGRAPHIC_AREA_ID,
            }:
                cotabato_geometries.append(
                    geometry
                )
                continue

            (
                province_id,
                province_name,
                region_id,
                region_name,
            ) = normalize_province_hierarchy(
                province_id=province_id,
                province_name=province_name,
                region_id=region_id,
                region_name=region_name,
            )

            ordinary_features.append(
                make_feature(
                    properties={
                        "province_id": province_id,
                        "province": province_name,
                        "region_id": region_id,
                        "region": region_name,
                    },
                    geometry=geometry,
                )
            )

    if len(
        seen_source_ids
    ) != RAW_PROVINCE_COUNT:
        raise ValueError(
            f"{dataset.label}: expected {RAW_PROVINCE_COUNT:,} source "
            f"features but found {len(seen_source_ids):,}."
        )

    if len(
        manila_geometries
    ) != len(
        METROPOLITAN_MANILA_SOURCE_IDS
    ):
        raise ValueError(
            "Metropolitan Manila merge did not collect all four source "
            f"features. Found {len(manila_geometries):,}."
        )

    if len(
        cotabato_geometries
    ) != 2:
        raise ValueError(
            "Cotabato merge expected Cotabato and Special Geographic Area "
            f"geometries but collected {len(cotabato_geometries):,}."
        )

    manila_geometry = merge_geometries(
        manila_geometries,
        label="Metropolitan Manila",
    )

    cotabato_geometry = merge_geometries(
        cotabato_geometries,
        label="Cotabato",
    )

    ordinary_features.append(
        make_feature(
            properties={
                "province_id": METROPOLITAN_MANILA_CANONICAL_ID,
                "province": METROPOLITAN_MANILA_NAME,
                "region_id": METROPOLITAN_MANILA_REGION_ID,
                "region": METROPOLITAN_MANILA_REGION_NAME,
            },
            geometry=manila_geometry,
        )
    )

    ordinary_features.append(
        make_feature(
            properties={
                "province_id": COTABATO_CANONICAL_ID,
                "province": COTABATO_NAME,
                "region_id": COTABATO_REGION_ID,
                "region": COTABATO_REGION_NAME,
            },
            geometry=cotabato_geometry,
        )
    )

    if len(
        ordinary_features
    ) != dataset.expected_output_count:
        raise ValueError(
            f"{dataset.label}: expected {dataset.expected_output_count:,} "
            f"processed features but produced {len(ordinary_features):,}."
        )

    output_ids = [
        feature[
            "properties"
        ][
            "province_id"
        ]
        for feature in ordinary_features
    ]

    if len(
        output_ids
    ) != len(
        set(
            output_ids
        )
    ):
        raise ValueError(
            f"{dataset.label}: duplicate province IDs remain after merging."
        )

    return ordinary_features


# ---------------------------------------------------------------------------
# Admin 3 / Admin 4 processing
# ---------------------------------------------------------------------------


def process_lower_level(
    dataset: AdminDataset,
) -> list[dict[str, Any]]:
    """
    Process Admin 3 or Admin 4.

    Province and region parent properties are canonicalized so grouping values
    exactly match the processed province and region datasets.
    """

    input_path = (
        RAW_DIRECTORY
        / dataset.raw_filename
    )

    features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    own_id_property = (
        f"adm{dataset.level}_pcode"
    )

    own_name_property = (
        f"adm{dataset.level}_name"
    )

    output_id_property = (
        dataset.output_id_property
    )

    output_name_property = (
        dataset.output_name_property
    )

    with input_path.open(
        "rb",
    ) as input_file:
        source_features = ijson.items(
            input_file,
            "features.item",
            use_float=True,
        )

        for feature_number, feature in enumerate(
            source_features,
            start=1,
        ):
            properties = feature.get(
                "properties"
            )

            if not isinstance(
                properties,
                dict,
            ):
                raise ValueError(
                    f"{dataset.label}: feature {feature_number:,} has "
                    "malformed properties."
                )

            own_id = require_string(
                properties.get(
                    own_id_property
                ),
                property_name=own_id_property,
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            own_name = require_string(
                properties.get(
                    own_name_property
                ),
                property_name=own_name_property,
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            if own_id in seen_ids:
                raise ValueError(
                    f"{dataset.label}: duplicate feature ID {own_id!r}."
                )

            seen_ids.add(
                own_id
            )

            region_id = require_string(
                properties.get(
                    "adm1_pcode"
                ),
                property_name="adm1_pcode",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            region_name = require_string(
                properties.get(
                    "adm1_name"
                ),
                property_name="adm1_name",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            province_id = require_string(
                properties.get(
                    "adm2_pcode"
                ),
                property_name="adm2_pcode",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            province_name = require_string(
                properties.get(
                    "adm2_name"
                ),
                property_name="adm2_name",
                dataset_label=dataset.label,
                feature_number=feature_number,
            )

            (
                province_id,
                province_name,
                region_id,
                region_name,
            ) = normalize_province_hierarchy(
                province_id=province_id,
                province_name=province_name,
                region_id=region_id,
                region_name=region_name,
            )

            output_properties: dict[str, str] = {
                output_id_property: own_id,
                output_name_property: own_name,
                "province_id": province_id,
                "province": province_name,
                "region_id": region_id,
                "region": region_name,
            }

            if dataset.level == 4:
                municipality_city_id = require_string(
                    properties.get(
                        "adm3_pcode"
                    ),
                    property_name="adm3_pcode",
                    dataset_label=dataset.label,
                    feature_number=feature_number,
                )

                municipality_city_name = require_string(
                    properties.get(
                        "adm3_name"
                    ),
                    property_name="adm3_name",
                    dataset_label=dataset.label,
                    feature_number=feature_number,
                )

                output_properties[
                    "municipality_city_id"
                ] = municipality_city_id

                output_properties[
                    "municipality_city"
                ] = municipality_city_name

            geometry = parse_geometry(
                feature.get(
                    "geometry"
                ),
                dataset_label=dataset.label,
                feature_number=feature_number,
                feature_id=own_id,
            )

            features.append(
                make_feature(
                    properties=output_properties,
                    geometry=geometry,
                )
            )

    if len(
        features
    ) != dataset.expected_output_count:
        raise ValueError(
            f"{dataset.label}: expected {dataset.expected_output_count:,} "
            f"features but produced {len(features):,}."
        )

    return features


# ---------------------------------------------------------------------------
# Dataset dispatch
# ---------------------------------------------------------------------------


def process_dataset(
    dataset: AdminDataset,
) -> list[dict[str, Any]]:
    """Process one administrative level."""

    if dataset.level == 1:
        return process_regions(
            dataset
        )

    if dataset.level == 2:
        return process_provinces(
            dataset
        )

    return process_lower_level(
        dataset
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Processing Philippines administrative boundaries..."
    )
    print()

    results: list[
        tuple[
            AdminDataset,
            Path,
            int,
            float,
        ]
    ] = []

    for dataset in DATASETS:
        print(
            f"Processing {dataset.label}..."
        )

        input_path = (
            RAW_DIRECTORY
            / dataset.raw_filename
        )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Raw dataset not found:\n{input_path}"
            )

        features = process_dataset(
            dataset
        )

        output_path = (
            INTERMEDIATE_DIRECTORY
            / dataset.output_filename
        )

        write_feature_collection(
            output_path,
            features,
        )

        size_mb = file_size_mb(
            output_path
        )

        results.append(
            (
                dataset,
                output_path,
                len(
                    features
                ),
                size_mb,
            )
        )

        print(
            f"  Features: {len(features):,}"
        )
        print(
            f"  Size:     {size_mb:.1f} MB"
        )
        print(
            f"  Output:   {output_path.relative_to(PROJECT_ROOT)}"
        )

        if dataset.level == 2:
            print(
                "  Merged:   4 Metropolitan Manila districts -> "
                "Metropolitan Manila"
            )
            print(
                "  Merged:   Special Geographic Area -> Cotabato"
            )

        print()

    print(
        "=" * 78
    )
    print(
        "Philippines administrative processing complete."
    )
    print(
        "=" * 78
    )
    print()
    print(
        "Intermediate datasets:"
    )

    for (
        dataset,
        _,
        feature_count,
        size_mb,
    ) in results:
        print(
            f"  {dataset.label}: {feature_count:,} features, "
            f"{size_mb:.1f} MB"
        )

    print()
    print(
        "Canonical hierarchy:"
    )
    print(
        "  Metropolitan Manila -> National Capital Region (NCR)"
    )
    print(
        "  Cotabato -> Soccsksargen"
    )
    print()
    print(
        "Geometry has not been simplified or published."
    )


if __name__ == "__main__":
    main()
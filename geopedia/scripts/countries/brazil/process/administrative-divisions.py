"""
Process Brazil IBGE administrative boundary data for GeoPedia.

Outputs:
- Brazil's 5 official geographic regions.
- Brazil's 27 federative units (26 states plus the Federal District).
- Brazil's 5,573 municipalities from the 2025 IBGE territorial mesh.

IBGE provides authoritative identifiers and parent relationships directly in
the source data, so no spatial inference is required to determine which region
a state belongs to or which state a municipality belongs to.

Runtime identifiers:
- Regions use IBGE `CD_REGIAO`.
- States use IBGE `CD_UF`.
- Municipalities use IBGE `CD_MUN`.

All output geometry is converted from SIRGAS 2000 (EPSG:4674) to WGS 84
(EPSG:4326) for GeoJSON runtime use.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import geopandas as gpd
from shapely import coverage_simplify, set_precision
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
)
from shapely.geometry.base import BaseGeometry


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "brazil"
    / "ibge"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
)

REGIONS_PATH = (
    RAW_DIR
    / "BR_Regioes_2025"
    / "BR_Regioes_2025.shp"
)

STATES_PATH = (
    RAW_DIR
    / "BR_UF_2025"
    / "BR_UF_2025.shp"
)

MUNICIPALITIES_PATH = (
    RAW_DIR
    / "BR_Municipios_2025"
    / "BR_Municipios_2025.shp"
)

REGIONS_OUTPUT_PATH = OUTPUT_DIR / "regions.geojson"
STATES_OUTPUT_PATH = OUTPUT_DIR / "states.geojson"
MUNICIPALITIES_OUTPUT_PATH = OUTPUT_DIR / "municipalities.geojson"

EXPECTED_REGION_COUNT = 5
EXPECTED_STATE_COUNT = 27
EXPECTED_MUNICIPALITY_COUNT = 5573

OUTPUT_CRS = "EPSG:4326"

OUTPUT_PRECISION_GRID_SIZE = 0.00001

# Regions cover very large areas, so a slightly stronger tolerance is
# appropriate while still retaining recognizable boundaries.
REGION_SIMPLIFY_TOLERANCE = 0.02

# Roughly 110 meters in latitude.
STATE_SIMPLIFY_TOLERANCE = 0.02

# Municipalities are much smaller, so a more conservative tolerance retains
# useful local boundary detail.
MUNICIPALITY_SIMPLIFY_TOLERANCE = 0.005

REGION_REQUIRED_COLUMNS = {
    "CD_REGIAO",
    "NM_REGIAO",
    "SIGLA_RG",
    "geometry",
}

STATE_REQUIRED_COLUMNS = {
    "CD_UF",
    "NM_UF",
    "SIGLA_UF",
    "CD_REGIAO",
    "geometry",
}

MUNICIPALITY_REQUIRED_COLUMNS = {
    "CD_MUN",
    "NM_MUN",
    "CD_UF",
    "geometry",
}


def count_coordinates(geometry: BaseGeometry) -> int:
    """Count coordinate pairs contained in a polygonal geometry."""
    if geometry is None or geometry.is_empty:
        return 0

    if isinstance(geometry, Polygon):
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if isinstance(geometry, MultiPolygon):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    if isinstance(geometry, GeometryCollection):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    return 0


def validate_required_columns(
    gdf: gpd.GeoDataFrame,
    required_columns: set[str],
    label: str,
) -> None:
    """Validate that an IBGE dataset contains all required source fields."""
    missing_columns = required_columns - set(gdf.columns)

    if missing_columns:
        raise ValueError(
            f"{label} dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def validate_geometry(
    gdf: gpd.GeoDataFrame,
    label: str,
) -> None:
    """Validate that a GeoDataFrame contains usable polygon geometry."""
    if gdf.crs is None:
        raise ValueError(
            f"{label} dataset has no CRS."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            f"{label} dataset contains null geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            f"{label} dataset contains empty geometries."
        )

    invalid_count = int(
        (~gdf.geometry.is_valid).sum()
    )

    if invalid_count:
        raise ValueError(
            f"{label} dataset contains "
            f"{invalid_count} invalid geometries."
        )

    unexpected_geometry_types = sorted(
        set(gdf.geometry.geom_type)
        - {"Polygon", "MultiPolygon"}
    )

    if unexpected_geometry_types:
        raise ValueError(
            f"{label} dataset contains unexpected geometry types: "
            f"{unexpected_geometry_types}"
        )


def simplify_geometries(
    gdf: gpd.GeoDataFrame,
    tolerance: float,
    label: str,
) -> gpd.GeoDataFrame:
    """
    Simplify a polygon coverage and reduce coordinate precision.

    Coverage simplification preserves shared administrative boundaries while
    reducing geometry complexity. Coordinate precision is then snapped to a small
    grid to avoid storing unnecessary decimal precision in runtime GeoJSON.
    """
    result = gdf.copy()

    coordinates_before = sum(
        count_coordinates(geometry)
        for geometry in result.geometry
    )

    simplified_geometries = coverage_simplify(
        result.geometry.to_numpy(),
        tolerance=tolerance,
        simplify_boundary=True,
    )

    result.geometry = simplified_geometries
    
    result.geometry = set_precision(
        result.geometry.to_numpy(),
        grid_size=OUTPUT_PRECISION_GRID_SIZE,
    )

    coordinates_after = sum(
        count_coordinates(geometry)
        for geometry in result.geometry
    )

    print(
        f"{label} coordinates before simplification: "
        f"{coordinates_before:,}"
    )
    print(
        f"{label} coordinates after simplification:  "
        f"{coordinates_after:,}"
    )

    if coordinates_before:
        reduction = (
            1 - coordinates_after / coordinates_before
        ) * 100

        print(
            f"{label} coordinate reduction: "
            f"{reduction:.1f}%"
        )

    validate_geometry(
        result,
        f"{label} after simplification",
    )

    return result

def clean_display_name(value: object) -> str:
    """
    Clean a source-provided geographic name for display.

    Repeated whitespace is collapsed while preserving IBGE capitalization,
    accents, punctuation, and spelling.
    """
    if value is None:
        raise ValueError(
            "Expected geographic name, found None."
        )

    result = " ".join(str(value).split())

    if not result:
        raise ValueError(
            "Expected non-empty geographic name."
        )

    return result


def normalize_numeric_code(
    value: object,
    field_name: str,
    expected_length: int,
) -> str:
    """
    Normalize and validate an IBGE numeric identifier.

    Shapefile readers normally return these codes as strings, but the helper
    tolerates numeric representations such as `35.0` while ensuring the final
    runtime value contains exactly the expected number of digits.
    """
    if value is None:
        raise ValueError(
            f"{field_name} cannot be None."
        )

    result = str(value).strip()

    if result.endswith(".0") and result[:-2].isdigit():
        result = result[:-2]

    if not re.fullmatch(
        rf"\d{{{expected_length}}}",
        result,
    ):
        raise ValueError(
            f"Unexpected {field_name} value: {value!r}. "
            f"Expected exactly {expected_length} digits."
        )

    return result


def normalize_abbreviation(
    value: object,
    field_name: str,
    allowed_lengths: set[int],
) -> str:
    """Normalize and validate an IBGE region or state abbreviation."""
    if value is None:
        raise ValueError(
            f"{field_name} cannot be None."
        )

    result = str(value).strip().upper()

    if len(result) not in allowed_lengths:
        raise ValueError(
            f"Unexpected {field_name} value: {value!r}."
        )

    if not result.isalpha():
        raise ValueError(
            f"Unexpected {field_name} value: {value!r}."
        )

    return result


def prepare_dataset(
    gdf: gpd.GeoDataFrame,
    required_columns: set[str],
    expected_count: int,
    tolerance: float,
    label: str,
) -> gpd.GeoDataFrame:
    """
    Validate, reproject, and simplify one IBGE administrative dataset.
    """
    validate_required_columns(
        gdf,
        required_columns,
        label,
    )

    if len(gdf) != expected_count:
        raise ValueError(
            f"Expected {expected_count:,} {label.lower()} features, "
            f"found {len(gdf):,}."
        )

    validate_geometry(
        gdf,
        label,
    )

    if gdf.crs.to_string() != OUTPUT_CRS:
        print(
            f"Reprojecting {label.lower()} from "
            f"{gdf.crs} to {OUTPUT_CRS}..."
        )

        gdf = gdf.to_crs(OUTPUT_CRS)

    print(
        f"Simplifying {label.lower()} geometries..."
    )

    return simplify_geometries(
        gdf,
        tolerance,
        label,
    )


def build_region_features(
    regions: gpd.GeoDataFrame,
) -> list[dict]:
    """Create cleaned Brazil region GeoJSON features."""
    features = []

    seen_ids: set[str] = set()
    seen_abbreviations: set[str] = set()

    for _, row in regions.iterrows():
        region_id = normalize_numeric_code(
            row["CD_REGIAO"],
            "CD_REGIAO",
            1,
        )

        name = clean_display_name(
            row["NM_REGIAO"]
        )

        abbreviation = normalize_abbreviation(
            row["SIGLA_RG"],
            "SIGLA_RG",
            {1, 2},
        )

        if region_id in seen_ids:
            raise ValueError(
                f"Duplicate region ID: {region_id!r}."
            )

        if abbreviation in seen_abbreviations:
            raise ValueError(
                f"Duplicate region abbreviation: "
                f"{abbreviation!r}."
            )

        seen_ids.add(region_id)
        seen_abbreviations.add(abbreviation)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": region_id,
                    "name": name,
                    "abbreviation": abbreviation,
                },
                "geometry": mapping(row.geometry),
            }
        )

    features.sort(
        key=lambda feature: int(
            feature["properties"]["id"]
        )
    )

    if len(features) != EXPECTED_REGION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} region features, "
            f"found {len(features)}."
        )

    return features


def build_state_features(
    states: gpd.GeoDataFrame,
    region_ids: set[str],
) -> list[dict]:
    """Create cleaned Brazil state GeoJSON features."""
    features = []

    seen_ids: set[str] = set()
    seen_abbreviations: set[str] = set()

    for _, row in states.iterrows():
        state_id = normalize_numeric_code(
            row["CD_UF"],
            "CD_UF",
            2,
        )

        name = clean_display_name(
            row["NM_UF"]
        )

        abbreviation = normalize_abbreviation(
            row["SIGLA_UF"],
            "SIGLA_UF",
            {2},
        )

        region_id = normalize_numeric_code(
            row["CD_REGIAO"],
            "CD_REGIAO",
            1,
        )

        if region_id not in region_ids:
            raise ValueError(
                f"State {name!r} references unknown "
                f"region ID {region_id!r}."
            )

        if state_id in seen_ids:
            raise ValueError(
                f"Duplicate state ID: {state_id!r}."
            )

        if abbreviation in seen_abbreviations:
            raise ValueError(
                f"Duplicate state abbreviation: "
                f"{abbreviation!r}."
            )

        seen_ids.add(state_id)
        seen_abbreviations.add(abbreviation)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": state_id,
                    "name": name,
                    "abbreviation": abbreviation,
                    "region_id": region_id,
                },
                "geometry": mapping(row.geometry),
            }
        )

    features.sort(
        key=lambda feature: int(
            feature["properties"]["id"]
        )
    )

    if len(features) != EXPECTED_STATE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_STATE_COUNT} state features, "
            f"found {len(features)}."
        )

    return features


def build_municipality_features(
    municipalities: gpd.GeoDataFrame,
    state_ids: set[str],
) -> list[dict]:
    """Create cleaned Brazil municipality GeoJSON features."""
    features = []

    seen_ids: set[str] = set()

    for _, row in municipalities.iterrows():
        municipality_id = normalize_numeric_code(
            row["CD_MUN"],
            "CD_MUN",
            7,
        )

        name = clean_display_name(
            row["NM_MUN"]
        )

        state_id = normalize_numeric_code(
            row["CD_UF"],
            "CD_UF",
            2,
        )

        if state_id not in state_ids:
            raise ValueError(
                f"Municipality {name!r} references unknown "
                f"state ID {state_id!r}."
            )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: "
                f"{municipality_id!r}."
            )

        seen_ids.add(municipality_id)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": municipality_id,
                    "name": name,
                    "state_id": state_id,
                },
                "geometry": mapping(row.geometry),
            }
        )

    features.sort(
        key=lambda feature: int(
            feature["properties"]["id"]
        )
    )

    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT:,} "
            f"municipality features, found {len(features):,}."
        )

    return features


def validate_hierarchy(
    region_features: list[dict],
    state_features: list[dict],
    municipality_features: list[dict],
) -> None:
    """Validate the generated region-state-municipality hierarchy."""
    region_ids = {
        feature["properties"]["id"]
        for feature in region_features
    }

    state_ids = {
        feature["properties"]["id"]
        for feature in state_features
    }

    referenced_region_ids = {
        feature["properties"]["region_id"]
        for feature in state_features
    }

    referenced_state_ids = {
        feature["properties"]["state_id"]
        for feature in municipality_features
    }

    unknown_region_ids = (
        referenced_region_ids - region_ids
    )

    if unknown_region_ids:
        raise ValueError(
            "States reference unknown region IDs: "
            f"{sorted(unknown_region_ids)}"
        )

    regions_without_states = (
        region_ids - referenced_region_ids
    )

    if regions_without_states:
        raise ValueError(
            "Regions have no state features: "
            f"{sorted(regions_without_states)}"
        )

    unknown_state_ids = (
        referenced_state_ids - state_ids
    )

    if unknown_state_ids:
        raise ValueError(
            "Municipalities reference unknown state IDs: "
            f"{sorted(unknown_state_ids)}"
        )

    states_without_municipalities = (
        state_ids - referenced_state_ids
    )

    if states_without_municipalities:
        raise ValueError(
            "States have no municipality features: "
            f"{sorted(states_without_municipalities)}"
        )


def write_feature_collection(
    path: Path,
    features: list[dict],
) -> None:
    """Write a compact UTF-8 GeoJSON FeatureCollection."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    """Process and validate Brazil's 2025 IBGE administrative datasets."""
    print("Loading IBGE datasets...")

    regions = gpd.read_file(
        REGIONS_PATH
    )

    states = gpd.read_file(
        STATES_PATH
    )

    municipalities = gpd.read_file(
        MUNICIPALITIES_PATH
    )

    print()
    print("Preparing regions...")

    regions = prepare_dataset(
        regions,
        REGION_REQUIRED_COLUMNS,
        EXPECTED_REGION_COUNT,
        REGION_SIMPLIFY_TOLERANCE,
        "Region",
    )

    print()
    print("Preparing states...")

    states = prepare_dataset(
        states,
        STATE_REQUIRED_COLUMNS,
        EXPECTED_STATE_COUNT,
        STATE_SIMPLIFY_TOLERANCE,
        "State",
    )

    print()
    print("Preparing municipalities...")

    municipalities = prepare_dataset(
        municipalities,
        MUNICIPALITY_REQUIRED_COLUMNS,
        EXPECTED_MUNICIPALITY_COUNT,
        MUNICIPALITY_SIMPLIFY_TOLERANCE,
        "Municipality",
    )

    print()
    print("Building regions...")

    region_features = build_region_features(
        regions
    )

    region_ids = {
        feature["properties"]["id"]
        for feature in region_features
    }

    print("Building states...")

    state_features = build_state_features(
        states,
        region_ids,
    )

    state_ids = {
        feature["properties"]["id"]
        for feature in state_features
    }

    print("Building municipalities...")

    municipality_features = (
        build_municipality_features(
            municipalities,
            state_ids,
        )
    )

    print("Validating hierarchy...")

    validate_hierarchy(
        region_features,
        state_features,
        municipality_features,
    )

    print("Writing GeoJSON...")

    write_feature_collection(
        REGIONS_OUTPUT_PATH,
        region_features,
    )

    write_feature_collection(
        STATES_OUTPUT_PATH,
        state_features,
    )

    write_feature_collection(
        MUNICIPALITIES_OUTPUT_PATH,
        municipality_features,
    )

    print()
    print("Brazil administrative processing complete.")
    print(
        f"Regions:        "
        f"{len(region_features):,}"
    )
    print(
        f"States:         "
        f"{len(state_features):,}"
    )
    print(
        f"Municipalities: "
        f"{len(municipality_features):,}"
    )
    print()
    print(
        f"Regions output:        "
        f"{REGIONS_OUTPUT_PATH}"
    )
    print(
        f"States output:         "
        f"{STATES_OUTPUT_PATH}"
    )
    print(
        f"Municipalities output: "
        f"{MUNICIPALITIES_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
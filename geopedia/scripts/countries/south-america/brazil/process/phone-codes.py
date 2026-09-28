"""
Process Brazil telephone area-code boundaries for GeoPedia.

Outputs:
- 67 two-digit DDD regions.
- 9 one-digit DDD regions derived from the first digit of each two-digit code.

The source file stores area codes in the `description` field as numeric values
such as `11.0`. These are normalized to two-character strings such as `"11"`.

The one-digit dataset is derived by dissolving all two-digit regions sharing
the same leading digit.

Runtime properties:
- Two-digit:
    {
        "id": "11",
        "phone_code": "11",
        "phone_code_1_digit": "1"
    }

- One-digit:
    {
        "id": "1",
        "phone_code": "1"
    }
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
from shapely import coverage_simplify, get_num_coordinates, set_precision
from shapely.geometry import mapping
from shapely.ops import unary_union


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "brazil"
    / "brazil_phone_area_codes.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
)

TWO_DIGIT_OUTPUT_PATH = (
    OUTPUT_DIR
    / "phone-codes-2-digit.geojson"
)

ONE_DIGIT_OUTPUT_PATH = (
    OUTPUT_DIR
    / "phone-codes-1-digit.geojson"
)

EXPECTED_TWO_DIGIT_CODE_COUNT = 67
EXPECTED_ONE_DIGIT_CODE_COUNT = 9

OUTPUT_CRS = "EPSG:4326"

# These regions are relatively large, so they can tolerate substantial
# simplification while remaining recognizable at quiz-map scales.
TWO_DIGIT_SIMPLIFY_TOLERANCE = 0.01
ONE_DIGIT_SIMPLIFY_TOLERANCE = 0.02

# Avoid storing unnecessary floating-point precision in runtime GeoJSON.
OUTPUT_PRECISION_GRID_SIZE = 0.00001


def normalize_phone_code(value: object) -> str:
    """
    Normalize a source DDD value into a two-digit string.

    The raw data stores values such as `11.0`. Every valid Brazil geographic
    DDD in this dataset must normalize to an integer between 10 and 99.
    """
    if value is None:
        raise ValueError(
            "Phone-code description cannot be None."
        )

    if isinstance(value, bool):
        raise ValueError(
            f"Unexpected phone-code value: {value!r}."
        )

    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Unexpected phone-code value: {value!r}."
        ) from error

    if not math.isfinite(numeric_value):
        raise ValueError(
            f"Phone-code value must be finite: {value!r}."
        )

    integer_value = int(numeric_value)

    if numeric_value != integer_value:
        raise ValueError(
            f"Phone-code value is not an integer: {value!r}."
        )

    if not 10 <= integer_value <= 99:
        raise ValueError(
            f"Phone-code value is outside the expected range: "
            f"{value!r}."
        )

    return f"{integer_value:02d}"


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

    unexpected_types = sorted(
        set(gdf.geometry.geom_type)
        - {"Polygon", "MultiPolygon"}
    )

    if unexpected_types:
        raise ValueError(
            f"{label} dataset contains unexpected geometry types: "
            f"{unexpected_types}"
        )


def simplify_coverage(
    gdf: gpd.GeoDataFrame,
    tolerance: float,
    label: str,
) -> gpd.GeoDataFrame:
    """
    Simplify a polygon coverage while preserving shared boundaries.

    Coverage simplification is used so neighboring phone-code regions remain
    aligned instead of developing gaps or slivers after simplification.
    """
    result = gdf.copy()

    coordinates_before = sum(
        get_num_coordinates(geometry)
        for geometry in result.geometry
    )

    simplified_geometries = coverage_simplify(
        result.geometry.to_numpy(),
        tolerance=tolerance,
        simplify_boundary=True,
    )

    result.geometry = set_precision(
        simplified_geometries,
        grid_size=OUTPUT_PRECISION_GRID_SIZE,
    )

    coordinates_after = sum(
        get_num_coordinates(geometry)
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


def load_two_digit_regions() -> gpd.GeoDataFrame:
    """Load, validate, and normalize the raw two-digit DDD dataset."""
    print("Loading raw phone-code dataset...")

    gdf = gpd.read_file(
        RAW_PATH
    )

    if "description" not in gdf.columns:
        raise ValueError(
            "Raw phone-code dataset is missing "
            "the `description` field."
        )

    if len(gdf) != EXPECTED_TWO_DIGIT_CODE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_TWO_DIGIT_CODE_COUNT} "
            f"two-digit phone-code features, found {len(gdf)}."
        )

    validate_geometry(
        gdf,
        "Raw two-digit phone-code",
    )

    if gdf.crs.to_string() != OUTPUT_CRS:
        print(
            f"Reprojecting phone-code data from "
            f"{gdf.crs} to {OUTPUT_CRS}..."
        )

        gdf = gdf.to_crs(
            OUTPUT_CRS
        )

    result = gdf[
        [
            "description",
            "geometry",
        ]
    ].copy()

    result["phone_code"] = (
        result["description"]
        .map(normalize_phone_code)
    )

    result["phone_code_1_digit"] = (
        result["phone_code"]
        .str[0]
    )

    if result["phone_code"].nunique() != EXPECTED_TWO_DIGIT_CODE_COUNT:
        raise ValueError(
            "Two-digit phone-code values are not unique after normalization."
        )

    expected_one_digit_codes = {
        str(value)
        for value in range(1, 10)
    }

    actual_one_digit_codes = set(
        result["phone_code_1_digit"]
    )

    if actual_one_digit_codes != expected_one_digit_codes:
        raise ValueError(
            "Unexpected one-digit phone-code set. "
            f"Expected {sorted(expected_one_digit_codes)}, "
            f"found {sorted(actual_one_digit_codes)}."
        )

    result = result.drop(
        columns=["description"]
    )

    result = result.sort_values(
        "phone_code"
    ).reset_index(
        drop=True
    )

    return result


def build_one_digit_regions(
    two_digit_regions: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Dissolve two-digit DDD regions into nine one-digit phone-code regions.
    """
    records = []

    for phone_code, group in two_digit_regions.groupby(
        "phone_code_1_digit",
        sort=True,
    ):
        geometry = unary_union(
            group.geometry.tolist()
        )

        records.append(
            {
                "phone_code": phone_code,
                "geometry": geometry,
            }
        )

    result = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=two_digit_regions.crs,
    )

    if len(result) != EXPECTED_ONE_DIGIT_CODE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ONE_DIGIT_CODE_COUNT} "
            f"one-digit phone-code regions, found {len(result)}."
        )

    if result["phone_code"].nunique() != EXPECTED_ONE_DIGIT_CODE_COUNT:
        raise ValueError(
            "One-digit phone-code values are not unique."
        )

    validate_geometry(
        result,
        "One-digit phone-code",
    )

    return result


def build_two_digit_features(
    gdf: gpd.GeoDataFrame,
) -> list[dict]:
    """Create GeoJSON features for the 67 two-digit DDD regions."""
    features = []

    for _, row in gdf.iterrows():
        phone_code = row["phone_code"]

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": phone_code,
                    "phone_code": phone_code,
                    "phone_code_1_digit": row[
                        "phone_code_1_digit"
                    ],
                },
                "geometry": mapping(
                    row.geometry
                ),
            }
        )

    return features


def build_one_digit_features(
    gdf: gpd.GeoDataFrame,
) -> list[dict]:
    """Create GeoJSON features for the nine one-digit DDD regions."""
    features = []

    for _, row in gdf.iterrows():
        phone_code = row["phone_code"]

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": phone_code,
                    "phone_code": phone_code,
                },
                "geometry": mapping(
                    row.geometry
                ),
            }
        )

    return features


def write_feature_collection(
    path: Path,
    features: list[dict],
) -> None:
    """Write a compact UTF-8 GeoJSON FeatureCollection."""
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
            separators=(",", ":"),
        )


def main() -> None:
    """Process Brazil's two-digit and one-digit telephone area-code datasets."""
    two_digit_regions = (
        load_two_digit_regions()
    )

    print()
    print("Simplifying two-digit phone-code regions...")

    two_digit_regions = simplify_coverage(
        two_digit_regions,
        TWO_DIGIT_SIMPLIFY_TOLERANCE,
        "Two-digit phone-code",
    )

    print()
    print("Building one-digit phone-code regions...")

    one_digit_regions = build_one_digit_regions(
        two_digit_regions
    )

    print()
    print("Simplifying one-digit phone-code regions...")

    one_digit_regions = simplify_coverage(
        one_digit_regions,
        ONE_DIGIT_SIMPLIFY_TOLERANCE,
        "One-digit phone-code",
    )

    two_digit_features = build_two_digit_features(
        two_digit_regions
    )

    one_digit_features = build_one_digit_features(
        one_digit_regions
    )

    print()
    print("Writing GeoJSON...")

    write_feature_collection(
        TWO_DIGIT_OUTPUT_PATH,
        two_digit_features,
    )

    write_feature_collection(
        ONE_DIGIT_OUTPUT_PATH,
        one_digit_features,
    )

    print()
    print("Brazil phone-code processing complete.")
    print(
        f"Two-digit regions: "
        f"{len(two_digit_features)}"
    )
    print(
        f"One-digit regions: "
        f"{len(one_digit_features)}"
    )
    print()
    print(
        f"Two-digit output: "
        f"{TWO_DIGIT_OUTPUT_PATH}"
    )
    print(
        f"One-digit output: "
        f"{ONE_DIGIT_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
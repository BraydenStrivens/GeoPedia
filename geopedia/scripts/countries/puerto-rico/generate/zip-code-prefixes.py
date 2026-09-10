"""Generate Puerto Rico's 3-digit ZIP-prefix GeoJSON for GeoPedia.

This generator derives three quiz regions from GeoPedia's processed Puerto
Rico ZIP-code dataset by dissolving all 5-digit ZCTA geometries that share
the same 3-digit prefix.

The generated regions are:

    006
    007
    009

Input:
    public/data/countries/puerto-rico/geojson/zip-codes.geojson

Output:
    public/data/countries/puerto-rico/geojson/zip-code-prefixes.geojson

The source ZIP-code geometry has already been validated and normalized by
process/zip-codes.py, so this script operates only on GeoPedia's processed
runtime data.
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "zip-codes.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "zip-code-prefixes.geojson"
)

EXPECTED_ZCTA_COUNT = 132

EXPECTED_PREFIXES = {
    "006",
    "007",
    "009",
}


def load_zip_codes() -> gpd.GeoDataFrame:
    """Load and validate Puerto Rico's processed ZIP-code dataset."""
    print("Reading ZIP codes from:")
    print(INPUT_PATH)
    print()

    zip_codes = gpd.read_file(
        INPUT_PATH
    )

    if zip_codes.empty:
        raise ValueError(
            "Puerto Rico ZIP-code dataset is empty."
        )

    if zip_codes.crs is None:
        raise ValueError(
            "Puerto Rico ZIP-code dataset has no CRS."
        )

    if len(zip_codes) != EXPECTED_ZCTA_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ZCTA_COUNT} ZIP-code features, "
            f"found {len(zip_codes)}."
        )

    required_columns = {
        "zip_code",
        "prefix_3",
        "geometry",
    }

    missing_columns = (
        required_columns - set(zip_codes.columns)
    )

    if missing_columns:
        raise ValueError(
            "ZIP-code dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    zip_codes["zip_code"] = (
        zip_codes["zip_code"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    zip_codes["prefix_3"] = (
        zip_codes["prefix_3"]
        .astype(str)
        .str.strip()
        .str.zfill(3)
    )

    prefixes = set(
        zip_codes["prefix_3"].unique()
    )

    if prefixes != EXPECTED_PREFIXES:
        raise ValueError(
            "Unexpected 3-digit ZIP prefixes. "
            f"Expected {sorted(EXPECTED_PREFIXES)}, "
            f"found {sorted(prefixes)}."
        )

    invalid_geometries = zip_codes[
        zip_codes.geometry.isna()
        | zip_codes.geometry.is_empty
        | ~zip_codes.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        invalid_codes = (
            invalid_geometries["zip_code"]
            .tolist()
        )

        raise ValueError(
            "Invalid ZIP-code geometry found for: "
            f"{invalid_codes}"
        )

    print(f"ZIP-code features: {len(zip_codes)}")
    print(
        "3-digit prefixes: "
        f"{', '.join(sorted(prefixes))}"
    )
    print()

    return zip_codes


def dissolve_prefixes(
    zip_codes: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve individual ZCTA polygons into 3-digit prefix regions."""
    print("Dissolving ZIP codes by 3-digit prefix...")
    print()

    prefixes = (
        zip_codes[
            [
                "prefix_3",
                "geometry",
            ]
        ]
        .dissolve(
            by="prefix_3",
            as_index=False,
        )
    )

    prefixes = prefixes[
        [
            "prefix_3",
            "geometry",
        ]
    ].copy()

    prefixes = prefixes.sort_values(
        "prefix_3"
    ).reset_index(
        drop=True
    )

    return prefixes


def validate_prefixes(
    prefixes: gpd.GeoDataFrame,
) -> None:
    """Validate the generated 3-digit ZIP-prefix regions."""
    if len(prefixes) != len(EXPECTED_PREFIXES):
        raise ValueError(
            f"Expected {len(EXPECTED_PREFIXES)} prefix features, "
            f"found {len(prefixes)}."
        )

    actual_prefixes = set(
        prefixes["prefix_3"].unique()
    )

    if actual_prefixes != EXPECTED_PREFIXES:
        raise ValueError(
            "Generated prefix set does not match expected prefixes. "
            f"Expected {sorted(EXPECTED_PREFIXES)}, "
            f"found {sorted(actual_prefixes)}."
        )

    if prefixes["prefix_3"].duplicated().any():
        duplicates = sorted(
            prefixes.loc[
                prefixes["prefix_3"].duplicated(
                    keep=False
                ),
                "prefix_3",
            ].unique()
        )

        raise ValueError(
            f"Duplicate generated prefixes found: {duplicates}"
        )

    invalid_geometries = prefixes[
        prefixes.geometry.isna()
        | prefixes.geometry.is_empty
        | ~prefixes.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        invalid_prefixes = (
            invalid_geometries["prefix_3"]
            .tolist()
        )

        raise ValueError(
            "Invalid generated geometry found for prefixes: "
            f"{invalid_prefixes}"
        )

    invalid_geometry_types = prefixes[
        ~prefixes.geometry.geom_type.isin(
            [
                "Polygon",
                "MultiPolygon",
            ]
        )
    ]

    if len(invalid_geometry_types) > 0:
        rows = [
            (
                row["prefix_3"],
                row.geometry.geom_type,
            )
            for _, row in invalid_geometry_types.iterrows()
        ]

        raise ValueError(
            "Unexpected generated geometry types: "
            f"{rows}"
        )

    if str(prefixes.crs).upper() != "EPSG:4326":
        raise ValueError(
            f"Expected output CRS EPSG:4326, found {prefixes.crs}."
        )


def write_geojson(
    prefixes: gpd.GeoDataFrame,
) -> int:
    """Write compact UTF-8 GeoJSON and return its byte size."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        prefixes.to_json(
            drop_id=True,
        )
    )

    content = json.dumps(
        geojson,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )

    return len(
        content.encode("utf-8")
    )


def print_summary(
    prefixes: gpd.GeoDataFrame,
    output_size: int,
) -> None:
    """Print a concise generation summary."""
    print("Puerto Rico ZIP-code prefixes generated successfully.")
    print(f"Features written: {len(prefixes)}")
    print()

    for _, row in prefixes.iterrows():
        print(
            f"  {row['prefix_3']}: "
            f"{row.geometry.geom_type}"
        )

    print()
    print(
        f"Output size: "
        f"{output_size / 1024:.2f} KB "
        f"({output_size:,} bytes)"
    )
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


def main() -> None:
    """Generate Puerto Rico's 3-digit ZIP-prefix regions."""
    zip_codes = load_zip_codes()

    prefixes = dissolve_prefixes(
        zip_codes
    )

    validate_prefixes(
        prefixes
    )

    output_size = write_geojson(
        prefixes
    )

    print_summary(
        prefixes,
        output_size,
    )


if __name__ == "__main__":
    main()
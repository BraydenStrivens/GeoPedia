"""Process Dominican Republic municipalities for GeoPedia.

Reads the raw ADM3 administrative-boundary GeoJSON sourced from the Dominican
Republic Oficina Nacional de Estadística (ONE) through OCHA/HDX and produces
a simplified runtime GeoJSON containing the country's 155 municipalities.

Processing:
- Validates the expected source schema and feature count.
- Normalizes ONE pcodes such as DO010101 to municipality IDs such as 010101.
- Normalizes ADM2 pcodes such as DO0101 to province IDs such as 0101.
- Normalizes ADM1 pcodes such as DO01 to region IDs such as 01.
- Removes the "Municipio " administrative prefix from municipality names.
- Validates ADM3 -> ADM2 -> ADM1 hierarchy consistency.
- Repairs invalid geometry when necessary.
- Projects geometry to UTM zone 19N for metric simplification.
- Simplifies geometry while preserving topology.
- Converts the result back to WGS84.
- Rounds coordinates to six decimal places.
- Retains only properties required by GeoPedia.
- Performs final validation before writing the output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "dominican-republic"
    / "dom_admin_boundaries.geojson"
    / "dom_admin3.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "dominican-republic"
    / "geojson"
    / "municipalities.geojson"
)

EXPECTED_FEATURE_COUNT = 155
EXPECTED_SOURCE_CRS = "EPSG:4326"

PROCESSING_CRS = "EPSG:32619"

SIMPLIFY_TOLERANCE_METERS = 100.0
COORDINATE_PRECISION = 6

REQUIRED_SOURCE_COLUMNS = {
    "adm3_name",
    "adm3_pcode",
    "adm2_name",
    "adm2_pcode",
    "adm1_name",
    "adm1_pcode",
    "adm0_pcode",
    "valid_on",
    "version",
    "lang",
    "geometry",
}

EXPECTED_REGION_IDS = {
    f"{number:02d}"
    for number in range(1, 11)
}


def load_source() -> gpd.GeoDataFrame:
    """Load and validate the raw ADM3 source dataset."""
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Source file does not exist: {SOURCE_PATH}")

    gdf = gpd.read_file(SOURCE_PATH)

    if len(gdf) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected ADM3 feature count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(gdf)}."
        )

    missing_columns = REQUIRED_SOURCE_COLUMNS - set(gdf.columns)

    if missing_columns:
        raise ValueError(
            "Source dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if gdf.crs is None:
        raise ValueError("Source dataset has no CRS.")

    if gdf.crs.to_string() != EXPECTED_SOURCE_CRS:
        raise ValueError(
            f"Expected source CRS {EXPECTED_SOURCE_CRS}, "
            f"found {gdf.crs.to_string()}."
        )

    if gdf.geometry.isna().any():
        raise ValueError("Source dataset contains missing geometry.")

    if gdf.geometry.is_empty.any():
        raise ValueError("Source dataset contains empty geometry.")

    for column in (
        "adm3_name",
        "adm3_pcode",
        "adm2_name",
        "adm2_pcode",
        "adm1_name",
        "adm1_pcode",
    ):
        if gdf[column].isna().any():
            raise ValueError(f"Source column {column!r} contains null values.")

        if gdf[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"Source column {column!r} contains blank values.")

    if gdf["adm3_pcode"].duplicated().any():
        duplicates = sorted(
            gdf.loc[gdf["adm3_pcode"].duplicated(False), "adm3_pcode"]
            .astype(str)
            .unique()
        )
        raise ValueError(f"Duplicate ADM3 pcodes found: {duplicates}")

    expected_metadata = {
        "adm0_pcode": {"DO"},
        "valid_on": {"2021-06-29"},
        "version": {"v01"},
        "lang": {"es"},
    }

    for column, expected_values in expected_metadata.items():
        actual_values = set(gdf[column].dropna().astype(str))

        if actual_values != expected_values:
            raise ValueError(
                f"Unexpected values for {column!r}: "
                f"expected {sorted(expected_values)}, "
                f"found {sorted(actual_values)}."
            )

    validate_source_hierarchy(gdf)

    return gdf


def normalize_region_id(pcode: str) -> str:
    """Convert an ONE ADM1 pcode such as DO01 to runtime ID 01."""
    pcode = pcode.strip()

    if not pcode.startswith("DO"):
        raise ValueError(f"Unexpected ADM1 pcode: {pcode!r}")

    region_id = pcode[2:]

    if len(region_id) != 2 or not region_id.isdigit():
        raise ValueError(f"Unexpected ADM1 pcode format: {pcode!r}")

    return region_id


def normalize_province_id(pcode: str) -> str:
    """Convert an ONE ADM2 pcode such as DO0101 to runtime ID 0101."""
    pcode = pcode.strip()

    if not pcode.startswith("DO"):
        raise ValueError(f"Unexpected ADM2 pcode: {pcode!r}")

    province_id = pcode[2:]

    if len(province_id) != 4 or not province_id.isdigit():
        raise ValueError(f"Unexpected ADM2 pcode format: {pcode!r}")

    return province_id


def normalize_municipality_id(pcode: str) -> str:
    """Convert an ONE ADM3 pcode such as DO010101 to runtime ID 010101."""
    pcode = pcode.strip()

    if not pcode.startswith("DO"):
        raise ValueError(f"Unexpected ADM3 pcode: {pcode!r}")

    municipality_id = pcode[2:]

    if len(municipality_id) != 6 or not municipality_id.isdigit():
        raise ValueError(f"Unexpected ADM3 pcode format: {pcode!r}")

    return municipality_id


def normalize_municipality_name(name: str) -> str:
    """Remove the source's administrative prefix from a municipality name."""
    name = name.strip()
    prefix = "Municipio "

    if not name.startswith(prefix):
        raise ValueError(
            f"ADM3 name does not start with {prefix!r}: {name!r}"
        )

    display_name = name[len(prefix) :].strip()

    if not display_name:
        raise ValueError(
            f"ADM3 name is empty after removing its prefix: {name!r}"
        )

    return display_name


def validate_source_hierarchy(gdf: gpd.GeoDataFrame) -> None:
    """Validate that ADM3, ADM2, and ADM1 pcodes encode the same hierarchy."""
    for _, row in gdf.iterrows():
        municipality_id = normalize_municipality_id(
            str(row["adm3_pcode"])
        )
        province_id = normalize_province_id(
            str(row["adm2_pcode"])
        )
        region_id = normalize_region_id(
            str(row["adm1_pcode"])
        )

        if municipality_id[:4] != province_id:
            raise ValueError(
                "ADM3 hierarchy mismatch: "
                f"{row['adm3_pcode']} belongs to {row['adm2_pcode']}, "
                f"but normalized IDs are "
                f"{municipality_id!r} and {province_id!r}."
            )

        if province_id[:2] != region_id:
            raise ValueError(
                "ADM2 hierarchy mismatch on ADM3 feature: "
                f"{row['adm2_pcode']} belongs to {row['adm1_pcode']}, "
                f"but normalized IDs are "
                f"{province_id!r} and {region_id!r}."
            )

        if region_id not in EXPECTED_REGION_IDS:
            raise ValueError(
                f"Unexpected ADM1 region ID on ADM3 feature: {region_id!r}"
            )


def repair_invalid_geometry(
    gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, int]:
    """Repair invalid source geometries and return the repair count."""
    invalid_mask = ~gdf.geometry.is_valid
    repair_count = int(invalid_mask.sum())

    if repair_count:
        gdf = gdf.copy()
        gdf.loc[invalid_mask, "geometry"] = (
            gdf.loc[invalid_mask, "geometry"].make_valid()
        )

    if (~gdf.geometry.is_valid).any():
        raise ValueError("Invalid geometry remains after repair.")

    if gdf.geometry.is_empty.any():
        raise ValueError("Geometry repair produced empty geometry.")

    return gdf, repair_count


def simplify_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Simplify geometry in a metric projected CRS."""
    projected = gdf.to_crs(PROCESSING_CRS)

    projected["geometry"] = projected.geometry.simplify(
        SIMPLIFY_TOLERANCE_METERS,
        preserve_topology=True,
    )

    simplified = projected.to_crs(EXPECTED_SOURCE_CRS)

    if simplified.geometry.is_empty.any():
        raise ValueError("Simplification produced empty geometry.")

    if (~simplified.geometry.is_valid).any():
        raise ValueError("Simplification produced invalid geometry.")

    return simplified


def round_coordinates(
    geometry: dict[str, Any],
    precision: int,
) -> dict[str, Any]:
    """Round all coordinates in a GeoJSON geometry recursively."""

    def round_value(value: Any) -> Any:
        if isinstance(value, list):
            return [round_value(item) for item in value]

        if isinstance(value, float):
            return round(value, precision)

        return value

    return {
        **geometry,
        "coordinates": round_value(geometry["coordinates"]),
    }


def build_output_features(
    gdf: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:
    """Build minimal GeoJSON features for the GeoPedia runtime."""
    features: list[dict[str, Any]] = []

    for _, row in gdf.iterrows():
        geometry = row.geometry.__geo_interface__

        municipality_id = normalize_municipality_id(
            str(row["adm3_pcode"])
        )
        province_id = normalize_province_id(
            str(row["adm2_pcode"])
        )
        region_id = normalize_region_id(
            str(row["adm1_pcode"])
        )

        feature = {
            "type": "Feature",
            "properties": {
                "municipality_id": municipality_id,
                "name": normalize_municipality_name(
                    str(row["adm3_name"])
                ),
                "province_id": province_id,
                "region_id": region_id,
            },
            "geometry": round_coordinates(
                dict(geometry),
                COORDINATE_PRECISION,
            ),
        }

        features.append(feature)

    features.sort(
        key=lambda feature: feature["properties"]["municipality_id"]
    )

    return features


def validate_output(features: list[dict[str, Any]]) -> None:
    """Validate the final runtime features before writing them."""
    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected output feature count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(features)}."
        )

    municipality_ids = [
        feature["properties"]["municipality_id"]
        for feature in features
    ]

    names = [
        feature["properties"]["name"]
        for feature in features
    ]

    if len(set(municipality_ids)) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Output municipality IDs are not unique.")

    if len(set(names)) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Output municipality names are not unique.")

    allowed_geometry_types = {"Polygon", "MultiPolygon"}

    for feature in features:
        properties = feature.get("properties", {})

        if set(properties) != {
            "municipality_id",
            "name",
            "province_id",
            "region_id",
        }:
            raise ValueError(
                "Output feature contains unexpected properties: "
                f"{sorted(properties)}"
            )

        municipality_id = properties["municipality_id"]
        province_id = properties["province_id"]
        region_id = properties["region_id"]

        if (
            not isinstance(municipality_id, str)
            or len(municipality_id) != 6
            or not municipality_id.isdigit()
        ):
            raise ValueError(
                f"Invalid output municipality ID: {municipality_id!r}"
            )

        if (
            not isinstance(province_id, str)
            or len(province_id) != 4
            or not province_id.isdigit()
        ):
            raise ValueError(
                f"Invalid output province ID: {province_id!r}"
            )

        if region_id not in EXPECTED_REGION_IDS:
            raise ValueError(
                f"Invalid output region ID: {region_id!r}"
            )

        if municipality_id[:4] != province_id:
            raise ValueError(
                "Output hierarchy mismatch: "
                f"municipality {municipality_id!r} has "
                f"province {province_id!r}."
            )

        if province_id[:2] != region_id:
            raise ValueError(
                "Output hierarchy mismatch: "
                f"province {province_id!r} has region {region_id!r}."
            )

        geometry = feature.get("geometry")

        if not isinstance(geometry, dict):
            raise ValueError("Output feature has invalid geometry.")

        geometry_type = geometry.get("type")

        if geometry_type not in allowed_geometry_types:
            raise ValueError(
                f"Unexpected output geometry type: {geometry_type!r}"
            )


def write_output(features: list[dict[str, Any]]) -> None:
    """Write the validated runtime GeoJSON."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            feature_collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    """Process the Dominican Republic ADM3 municipalities."""
    print("Processing Dominican Republic municipalities")
    print(f"Source: {SOURCE_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    source_size = SOURCE_PATH.stat().st_size

    gdf = load_source()

    print(f"Loaded features: {len(gdf)}")
    print(f"Source CRS: {gdf.crs}")

    gdf, repair_count = repair_invalid_geometry(gdf)

    print(f"Invalid geometries repaired: {repair_count}")

    gdf = simplify_geometry(gdf)

    features = build_output_features(gdf)
    validate_output(features)
    write_output(features)

    output_size = OUTPUT_PATH.stat().st_size

    print()
    print("Output municipalities:")

    for feature in features:
        properties = feature["properties"]

        print(
            f"  {properties['municipality_id']}: "
            f"{properties['name']} "
            f"(province {properties['province_id']}, "
            f"region {properties['region_id']})"
        )

    print()
    print(f"Features written: {len(features)}")
    print(
        "Geometry types:",
        dict(
            sorted(
                {
                    geometry_type: sum(
                        feature["geometry"]["type"] == geometry_type
                        for feature in features
                    )
                    for geometry_type in {
                        feature["geometry"]["type"]
                        for feature in features
                    }
                }.items()
            )
        ),
    )
    print(f"Source size: {source_size / 1_000_000:.2f} MB")
    print(f"Output size: {output_size / 1_000_000:.2f} MB")
    print(
        "Size reduction: "
        f"{(1 - output_size / source_size) * 100:.1f}%"
    )
    print()
    print("Validation passed.")


if __name__ == "__main__":
    main()
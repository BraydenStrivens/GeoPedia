"""Process U.S. Virgin Islands Census ZCTAs for GeoPedia.

This processor extracts the six U.S. Virgin Islands ZIP Code Tabulation
Areas (ZCTAs) from the national 2020 Census ZCTA shapefile.

GeoPedia's processed USVI island polygons are used to define a bounding box
and spatially identify the relevant ZCTAs. The original Census ZCTA geometry
is preserved rather than clipped to the island boundaries.

Input:
    data/raw/countries/usa/census/zip-codes/
        tl_2020_us_zcta520/tl_2020_us_zcta520.shp

    public/data/countries/us-virgin-islands/geojson/islands.geojson

Output:
    public/data/countries/us-virgin-islands/geojson/zip-codes.geojson

Runtime properties:
    zip_code

All six mapped ZCTAs share the 008 prefix, so no prefix property is needed
for grouping.

No geometry simplification is performed.
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

ZCTA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "usa"
    / "census"
    / "zip-codes"
    / "tl_2020_us_zcta520"
    / "tl_2020_us_zcta520.shp"
)

ISLANDS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "us-virgin-islands"
    / "geojson"
    / "islands.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "us-virgin-islands"
    / "geojson"
    / "zip-codes.geojson"
)

EXPECTED_ZIP_CODES = {
    "00802",
    "00820",
    "00830",
    "00840",
    "00850",
    "00851",
}


def find_zcta_column(
    columns: list[str],
) -> str:
    """Find the source column containing the five-digit ZCTA code."""
    candidates = [
        "ZCTA5CE20",
        "GEOID20",
        "ZCTA5CE10",
        "GEOID10",
    ]

    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise ValueError(
        "Could not identify the ZCTA code column. "
        f"Available columns: {columns}"
    )


def load_islands() -> gpd.GeoDataFrame:
    """Load GeoPedia's processed USVI island polygons."""
    if not ISLANDS_PATH.exists():
        raise FileNotFoundError(
            "Processed USVI islands file does not exist. "
            "Run process/islands.py first.\n"
            f"Expected: {ISLANDS_PATH}"
        )

    islands = gpd.read_file(
        ISLANDS_PATH
    )

    if islands.empty:
        raise ValueError(
            "Processed USVI island dataset is empty."
        )

    if islands.crs is None:
        raise ValueError(
            "Processed USVI island dataset has no CRS."
        )

    if len(islands) != 3:
        raise ValueError(
            f"Expected 3 USVI islands, found {len(islands)}."
        )

    return islands


def load_candidate_zctas(
    islands: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Read national Census ZCTAs within the USVI bounding box."""
    bounds = islands.total_bounds

    bbox = (
        bounds[0],
        bounds[1],
        bounds[2],
        bounds[3],
    )

    print("Reading Census ZCTAs from:")
    print(ZCTA_PATH)
    print()

    zctas = gpd.read_file(
        ZCTA_PATH,
        bbox=bbox,
    )

    if zctas.empty:
        raise ValueError(
            "No ZCTAs were returned for the USVI bounding box."
        )

    if zctas.crs is None:
        raise ValueError(
            "Census ZCTA source has no CRS."
        )

    print(
        f"Candidate ZCTAs from bounding box: "
        f"{len(zctas)}"
    )
    print(f"Source CRS: {zctas.crs}")
    print()

    return zctas


def filter_usvi_zctas(
    zctas: gpd.GeoDataFrame,
    islands: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Keep Census ZCTAs that spatially intersect the USVI islands."""
    islands = islands.to_crs(
        zctas.crs
    )

    usvi_geometry = (
        islands.geometry.union_all()
    )

    zctas = zctas[
        zctas.geometry.intersects(
            usvi_geometry
        )
    ].copy()

    print(
        "USVI ZCTAs after spatial filtering: "
        f"{len(zctas)}"
    )
    print()

    return zctas


def normalize_zctas(
    zctas: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Normalize ZCTA properties for GeoPedia runtime use."""
    zcta_column = find_zcta_column(
        list(zctas.columns)
    )

    print(
        f"Using Census ZCTA column: "
        f"{zcta_column}"
    )
    print()

    zctas["zip_code"] = (
        zctas[zcta_column]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    zctas = zctas[
        [
            "zip_code",
            "geometry",
        ]
    ].copy()

    zctas = zctas.sort_values(
        "zip_code"
    ).reset_index(
        drop=True
    )

    return zctas


def validate_zctas(
    zctas: gpd.GeoDataFrame,
) -> None:
    """Validate the six expected USVI ZCTAs."""
    if len(zctas) != len(EXPECTED_ZIP_CODES):
        raise ValueError(
            f"Expected {len(EXPECTED_ZIP_CODES)} USVI ZCTAs, "
            f"found {len(zctas)}."
        )

    if not zctas["zip_code"].str.fullmatch(
        r"\d{5}"
    ).all():
        raise ValueError(
            "One or more ZIP codes are not five-digit numeric strings."
        )

    if zctas["zip_code"].duplicated().any():
        raise ValueError(
            "Duplicate ZIP codes found."
        )

    actual_codes = set(
        zctas["zip_code"]
    )

    if actual_codes != EXPECTED_ZIP_CODES:
        raise ValueError(
            "USVI ZIP codes do not match the inspected set.\n"
            f"Expected: {sorted(EXPECTED_ZIP_CODES)}\n"
            f"Found: {sorted(actual_codes)}"
        )

    prefixes = {
        code[:3]
        for code in actual_codes
    }

    if prefixes != {"008"}:
        raise ValueError(
            "Unexpected USVI 3-digit ZIP prefixes. "
            f"Found: {sorted(prefixes)}"
        )

    invalid_geometries = zctas[
        zctas.geometry.isna()
        | zctas.geometry.is_empty
        | ~zctas.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        raise ValueError(
            "Invalid ZCTA geometry found for: "
            f"{invalid_geometries['zip_code'].tolist()}"
        )

    invalid_geometry_types = zctas[
        ~zctas.geometry.geom_type.isin(
            ["Polygon", "MultiPolygon"]
        )
    ]

    if len(invalid_geometry_types) > 0:
        raise ValueError(
            "Unexpected ZCTA geometry types found."
        )

    if zctas.crs is None:
        raise ValueError(
            "Processed ZCTAs have no CRS."
        )


def write_geojson(
    zctas: gpd.GeoDataFrame,
) -> int:
    """Write compact UTF-8 runtime GeoJSON and return its byte size."""
    if str(zctas.crs).upper() != "EPSG:4326":
        zctas = zctas.to_crs(
            "EPSG:4326"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        zctas.to_json(
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

    return len(content.encode("utf-8"))


def main() -> None:
    """Process U.S. Virgin Islands ZIP-code geography."""
    islands = load_islands()

    zctas = load_candidate_zctas(
        islands
    )

    zctas = filter_usvi_zctas(
        zctas,
        islands,
    )

    zctas = normalize_zctas(
        zctas
    )

    validate_zctas(
        zctas
    )

    output_size = write_geojson(
        zctas
    )

    print("U.S. Virgin Islands ZIP codes processed successfully.")
    print(
        f"Features written: {len(zctas)}"
    )
    print()

    for code in zctas["zip_code"]:
        print(f"  {code}")

    print()
    print("3-digit prefix: 008")
    print("Geometry simplification: none")
    print(
        f"Output size: {output_size / 1024:.2f} KB "
        f"({output_size:,} bytes)"
    )
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


if __name__ == "__main__":
    main()
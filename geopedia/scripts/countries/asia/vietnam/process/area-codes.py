"""
Generates Vietnam's telephone area-code geographic datasets.

The script reads GeoPedia's finalized 63-province Vietnam GeoJSON and assigns
each province its Plonk It telephone area code. It writes a full area-code
layer retaining the province boundaries, then dissolves those boundaries by
the first two area-code digits to create the prefix layer.

The leading domestic trunk prefix 0 is presentation-only and is not stored in
the area_code or area_code_prefix properties.

Input:
    public/data/countries/vietnam/geojson/pre-reform-provinces.geojson

Outputs:
    public/data/countries/vietnam/geojson/area-codes.geojson
    public/data/countries/vietnam/geojson/area-code-prefixes-2.geojson

Run from the GeoPedia project root:
    python scripts/countries/asia/vietnam/process/area-codes.py
"""

from pathlib import Path

import geopandas as gpd
from shapely.validation import make_valid


INPUT_PATH = Path(
    "public/data/countries/vietnam/geojson/pre-reform-provinces.geojson"
)

AREA_CODES_OUTPUT_PATH = Path(
    "public/data/countries/vietnam/geojson/area-codes.geojson"
)

PREFIXES_OUTPUT_PATH = Path(
    "public/data/countries/vietnam/geojson/area-code-prefixes-2.geojson"
)

AREA_CODES = {
    "1": "236",
    "2": "251",
    "3": "277",
    "4": "261",
    "5": "262",
    "6": "215",
    "7": "296",
    "8": "254",
    "9": "256",
    "10": "274",
    "11": "271",
    "12": "252",
    "13": "291",
    "14": "204",
    "15": "209",
    "16": "222",
    "17": "275",
    "18": "290",
    "19": "206",
    "20": "292",
    "21": "269",
    "22": "219",
    "23": "24",
    "24": "226",
    "25": "239",
    "26": "28",
    "27": "218",
    "28": "221",
    "29": "220",
    "30": "225",
    "31": "293",
    "32": "258",
    "33": "297",
    "34": "260",
    "35": "214",
    "36": "263",
    "37": "213",
    "38": "205",
    "39": "272",
    "40": "228",
    "41": "238",
    "42": "229",
    "43": "259",
    "44": "210",
    "45": "257",
    "46": "232",
    "47": "235",
    "48": "255",
    "49": "203",
    "50": "233",
    "51": "299",
    "52": "212",
    "53": "276",
    "54": "227",
    "55": "208",
    "56": "234",
    "57": "237",
    "58": "273",
    "59": "294",
    "60": "207",
    "61": "270",
    "62": "211",
    "63": "216",
}

EXPECTED_PREFIXES = {
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
}


def repair_geometry(geometry):
    if geometry is None or geometry.is_empty:
        raise ValueError("Encountered missing or empty geometry.")

    if not geometry.is_valid:
        geometry = make_valid(geometry)

    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(
            f"Expected polygonal geometry, got {geometry.geom_type}."
        )

    return geometry


def main() -> None:
    print("Generating Vietnam telephone area-code data...")

    gdf = gpd.read_file(INPUT_PATH)

    if len(gdf) != 63:
        raise ValueError(
            f"Expected 63 province features, found {len(gdf)}."
        )

    gdf["province_id"] = gdf["province_id"].astype(str)

    if gdf["province_id"].duplicated().any():
        raise ValueError("Duplicate province_id values found.")

    actual_ids = set(gdf["province_id"])
    expected_ids = set(AREA_CODES)

    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids, key=int)
        extra = sorted(actual_ids - expected_ids, key=int)

        raise ValueError(
            "Province ID mismatch.\n"
            f"Missing IDs: {missing}\n"
            f"Unexpected IDs: {extra}"
        )

    gdf["area_code"] = gdf["province_id"].map(AREA_CODES)

    if gdf["area_code"].isna().any():
        raise ValueError("At least one province is missing an area code.")

    if gdf["area_code"].duplicated().any():
        duplicates = sorted(
            gdf.loc[
                gdf["area_code"].duplicated(keep=False),
                "area_code",
            ].unique()
        )

        raise ValueError(
            f"Duplicate full area codes found: {duplicates}"
        )

    gdf["area_code_prefix"] = gdf["area_code"].str[:2]

    actual_prefixes = set(gdf["area_code_prefix"])

    if actual_prefixes != EXPECTED_PREFIXES:
        raise ValueError(
            "Unexpected area-code prefixes.\n"
            f"Expected: {sorted(EXPECTED_PREFIXES)}\n"
            f"Actual:   {sorted(actual_prefixes)}"
        )

    # ------------------------------------------------------------------
    # Full area-code layer
    # ------------------------------------------------------------------

    area_codes_gdf = gdf[
        [
            "province_id",
            "province",
            "area_code",
            "area_code_prefix",
            "geometry",
        ]
    ].copy()

    area_codes_gdf["geometry"] = area_codes_gdf["geometry"].apply(
        repair_geometry
    )

    if len(area_codes_gdf) != 63:
        raise ValueError(
            f"Expected 63 area-code features, found {len(area_codes_gdf)}."
        )

    if area_codes_gdf.geometry.is_empty.any():
        raise ValueError("Empty full area-code geometry found.")

    if not area_codes_gdf.geometry.is_valid.all():
        raise ValueError("Invalid full area-code geometry found.")

    area_codes_gdf = area_codes_gdf.sort_values(
        "province_id",
        key=lambda values: values.astype(int),
    ).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Two-digit prefix layer
    # ------------------------------------------------------------------

    prefixes_gdf = area_codes_gdf[
        ["area_code_prefix", "geometry"]
    ].dissolve(
        by="area_code_prefix",
        as_index=False,
    )

    prefixes_gdf["geometry"] = prefixes_gdf["geometry"].apply(
        repair_geometry
    )

    if len(prefixes_gdf) != 10:
        raise ValueError(
            f"Expected 10 prefix features, found {len(prefixes_gdf)}."
        )

    if prefixes_gdf["area_code_prefix"].duplicated().any():
        raise ValueError("Duplicate area_code_prefix values found.")

    if prefixes_gdf.geometry.is_empty.any():
        raise ValueError("Empty dissolved prefix geometry found.")

    if not prefixes_gdf.geometry.is_valid.all():
        raise ValueError("Invalid dissolved prefix geometry found.")

    prefixes_gdf = prefixes_gdf.sort_values(
        "area_code_prefix"
    ).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------

    AREA_CODES_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    area_codes_gdf.to_file(
        AREA_CODES_OUTPUT_PATH,
        driver="GeoJSON",
    )

    prefixes_gdf.to_file(
        PREFIXES_OUTPUT_PATH,
        driver="GeoJSON",
    )

    print("Vietnam telephone area-code generation complete.")
    print(f"Full area-code regions: {len(area_codes_gdf):,}")
    print(f"Two-digit prefixes:     {len(prefixes_gdf):,}")
    print(
        "Prefixes:              "
        + ", ".join(prefixes_gdf["area_code_prefix"])
    )
    print("Wrote:")
    print(AREA_CODES_OUTPUT_PATH)
    print(PREFIXES_OUTPUT_PATH)


if __name__ == "__main__":
    main()
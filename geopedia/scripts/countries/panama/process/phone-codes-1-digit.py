"""
Generates Panama's 1-digit regional phone-code boundaries for GeoPedia.

Sources:
    public/data/countries/panama/geojson/provinces-comarcas.geojson

    data/manual/countries/panama/phone-codes-1-digit.json

The manual mapping is transcribed from the Plonk It Panama guide:
    https://www.plonkit.net/panama

Plonk It notes that the first digit of a 7-digit Panamanian phone number can
be useful for regionguessing. Numbers beginning with 5, 6, or 8 are not
useful for this clue.

Some geographic regions accept more than one useful first-digit prefix. For
example, a region may have codes ["2", "3"]. Those codes are kept as separate
quiz answers while sharing the same geographic feature.

This processor:

- validates the processed province/comarca source,
- validates the manually researched phone-code mapping,
- removes regions without a useful phone code,
- groups provinces/comarcas by their complete set of valid phone codes,
- dissolves provinces/comarcas that share the same code set,
- validates the resulting phone-code regions,
- writes compact UTF-8 GeoJSON.

Regions whose manual `codes` array is empty intentionally have no output
geometry.
"""

import json
from pathlib import Path

import geopandas as gpd


SOURCE_PATH = Path(
    "public/data/countries/panama/geojson/"
    "provinces-comarcas.geojson"
)

MANUAL_DATA_PATH = Path(
    "data/manual/countries/panama/"
    "phone-codes-1-digit.json"
)

OUTPUT_PATH = Path(
    "public/data/countries/panama/geojson/"
    "phone-codes-1-digit.geojson"
)

EXPECTED_SOURCE_FEATURE_COUNT = 14

EXPECTED_CODES = {
    "2",
    "3",
    "4",
    "7",
    "9",
}

EXPECTED_CODE_SETS = {
    ("2", "3"),
    ("3",),
    ("4",),
    ("7",),
    ("9",),
}


def validate_source(gdf: gpd.GeoDataFrame) -> None:
    """Validate the processed Panama province/comarca input."""

    required_columns = {
        "id",
        "name",
        "type",
        "geometry",
    }

    missing_columns = required_columns - set(gdf.columns)

    if missing_columns:
        raise ValueError(
            "Source is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if len(gdf) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} source features, "
            f"found {len(gdf)}."
        )

    ids = gdf["id"].astype(str).str.strip().str.zfill(2)
    names = gdf["name"].astype(str).str.strip()

    if ids.duplicated().any():
        duplicates = sorted(
            ids[ids.duplicated(keep=False)].unique()
        )

        raise ValueError(
            "Source contains duplicate province/comarca IDs: "
            + ", ".join(duplicates)
        )

    if names.duplicated().any():
        duplicates = sorted(
            names[names.duplicated(keep=False)].unique()
        )

        raise ValueError(
            "Source contains duplicate province/comarca names: "
            + ", ".join(duplicates)
        )

    if gdf.crs is None:
        raise ValueError("Source GeoJSON has no CRS.")

    if gdf.geometry.isna().any():
        raise ValueError("Source contains null geometries.")

    if gdf.geometry.is_empty.any():
        raise ValueError("Source contains empty geometries.")

    if (~gdf.geometry.is_valid).any():
        raise ValueError("Source contains invalid geometries.")

    invalid_geometry_types = set(
        gdf.geometry.geom_type.unique()
    ) - {"Polygon", "MultiPolygon"}

    if invalid_geometry_types:
        raise ValueError(
            "Source contains unsupported geometry types: "
            + ", ".join(sorted(invalid_geometry_types))
        )


def load_manual_data() -> dict:
    """Load the manually researched province-to-phone-code mapping."""

    if not MANUAL_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Manual phone-code data not found: {MANUAL_DATA_PATH}"
        )

    return json.loads(
        MANUAL_DATA_PATH.read_text(encoding="utf-8")
    )


def validate_manual_data(
    data: dict,
    source: gpd.GeoDataFrame,
) -> list[dict]:
    """
    Validate and normalize the manual phone-code mapping.

    Every source province/comarca must have exactly one manual entry.

    `codes` must always be an array:
        ["7"]      -> one useful first-digit code
        ["2", "3"] -> multiple useful first-digit codes
        []         -> no useful code and therefore no quiz geometry
    """

    regions = data.get("regions")

    if not isinstance(regions, list):
        raise ValueError(
            "Manual data must contain a 'regions' array."
        )

    if len(regions) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} manual region entries, "
            f"found {len(regions)}."
        )

    normalized_regions: list[dict] = []
    manual_ids: list[str] = []

    for index, region in enumerate(regions):
        if not isinstance(region, dict):
            raise ValueError(
                f"Manual region entry {index} is not an object."
            )

        required_fields = {
            "provinceId",
            "provinceName",
            "codes",
        }

        missing_fields = required_fields - set(region)

        if missing_fields:
            raise ValueError(
                f"Manual region entry {index} is missing fields: "
                + ", ".join(sorted(missing_fields))
            )

        province_id = str(region["provinceId"]).strip().zfill(2)
        province_name = str(region["provinceName"]).strip()
        codes = region["codes"]

        if not province_id:
            raise ValueError(
                f"Manual region entry {index} has a blank provinceId."
            )

        if not province_name:
            raise ValueError(
                f"Manual region {province_id} has a blank provinceName."
            )

        if not isinstance(codes, list):
            raise ValueError(
                f"Phone codes for {province_id} must be an array."
            )

        normalized_codes: list[str] = []

        for code in codes:
            if not isinstance(code, str):
                raise ValueError(
                    f"Phone codes for {province_id} must contain only strings."
                )

            normalized_code = code.strip()

            if not normalized_code:
                raise ValueError(
                    f"Phone codes for {province_id} cannot contain "
                    "blank values."
                )

            if len(normalized_code) != 1 or not normalized_code.isdigit():
                raise ValueError(
                    f"Invalid 1-digit phone code '{normalized_code}' "
                    f"for {province_id}."
                )

            normalized_codes.append(normalized_code)

        if len(normalized_codes) != len(set(normalized_codes)):
            raise ValueError(
                f"Phone codes for {province_id} contain duplicates: "
                f"{normalized_codes}."
            )

        normalized_codes = sorted(normalized_codes)

        normalized_regions.append(
            {
                "provinceId": province_id,
                "provinceName": province_name,
                "codes": normalized_codes,
            }
        )

        manual_ids.append(province_id)

    duplicate_ids = sorted(
        {
            province_id
            for province_id in manual_ids
            if manual_ids.count(province_id) > 1
        }
    )

    if duplicate_ids:
        raise ValueError(
            "Manual data contains duplicate province IDs: "
            + ", ".join(duplicate_ids)
        )

    source_lookup = {
        str(row.id).strip().zfill(2): str(row.name).strip()
        for row in source.itertuples()
    }

    source_ids = set(source_lookup)
    manual_id_set = set(manual_ids)

    missing_ids = sorted(source_ids - manual_id_set)
    extra_ids = sorted(manual_id_set - source_ids)

    if missing_ids:
        raise ValueError(
            "Manual data is missing source province IDs: "
            + ", ".join(missing_ids)
        )

    if extra_ids:
        raise ValueError(
            "Manual data contains unknown province IDs: "
            + ", ".join(extra_ids)
        )

    for region in normalized_regions:
        province_id = region["provinceId"]
        manual_name = region["provinceName"]
        source_name = source_lookup[province_id]

        if manual_name != source_name:
            raise ValueError(
                f"Province name mismatch for {province_id}: "
                f"manual data has '{manual_name}', "
                f"source has '{source_name}'."
            )

    actual_codes = {
        code
        for region in normalized_regions
        for code in region["codes"]
    }

    if actual_codes != EXPECTED_CODES:
        raise ValueError(
            "Unexpected phone-code set. "
            f"Expected {sorted(EXPECTED_CODES)}, "
            f"found {sorted(actual_codes)}."
        )

    actual_code_sets = {
        tuple(region["codes"])
        for region in normalized_regions
        if region["codes"]
    }

    if actual_code_sets != EXPECTED_CODE_SETS:
        raise ValueError(
            "Unexpected geographic phone-code combinations. "
            f"Expected {sorted(EXPECTED_CODE_SETS)}, "
            f"found {sorted(actual_code_sets)}."
        )

    return normalized_regions


def build_output(
    source: gpd.GeoDataFrame,
    regions: list[dict],
) -> gpd.GeoDataFrame:
    """
    Build and dissolve geographic regions by complete phone-code set.

    Regions with identical `codes` arrays are dissolved together. This keeps
    ["3"] separate from ["2", "3"], even though both accept code 3.
    """

    result = source[
        [
            "id",
            "name",
            "geometry",
        ]
    ].copy()

    result["id"] = (
        result["id"]
        .astype(str)
        .str.strip()
        .str.zfill(2)
    )

    codes_by_id = {
        region["provinceId"]: region["codes"]
        for region in regions
    }

    result["codes"] = result["id"].map(codes_by_id)

    # Empty arrays mean that the source region has no useful first-digit phone
    # clue and should contribute no geometry to the quiz.
    result = result[
        result["codes"].map(bool)
    ].copy()

    # Tuples provide a stable, hashable dissolve key while preserving the full
    # semantic distinction between ["3"] and ["2", "3"].
    result["_code_key"] = result["codes"].map(tuple)

    dissolved = result.dissolve(
        by="_code_key",
        as_index=False,
        sort=True,
    )

    dissolved["codes"] = dissolved["_code_key"].map(list)

    dissolved["id"] = dissolved["codes"].map(
        lambda codes: "-".join(codes)
    )
    
    dissolved["name"] = dissolved["codes"].map(
        lambda codes: " / ".join(codes)
    )

    dissolved = dissolved[
        [
            "id",
            "name",
            "codes",
            "geometry",
        ]
    ]

    dissolved = dissolved.sort_values(
        "id",
        kind="stable",
    ).reset_index(drop=True)

    return gpd.GeoDataFrame(
        dissolved,
        geometry="geometry",
        crs=source.crs,
    )


def validate_output(gdf: gpd.GeoDataFrame) -> None:
    """Validate the generated 1-digit phone-code GeoJSON."""

    expected_feature_count = len(EXPECTED_CODE_SETS)

    if len(gdf) != expected_feature_count:
        raise ValueError(
            f"Expected {expected_feature_count} phone-code regions, "
            f"found {len(gdf)}."
        )

    if gdf["id"].nunique() != expected_feature_count:
        raise ValueError(
            "Generated phone-code feature IDs are not unique."
        )

    actual_code_sets = {
        tuple(codes)
        for codes in gdf["codes"]
    }

    if actual_code_sets != EXPECTED_CODE_SETS:
        raise ValueError(
            "Generated geographic phone-code combinations do not match "
            "the expected set. "
            f"Expected {sorted(EXPECTED_CODE_SETS)}, "
            f"found {sorted(actual_code_sets)}."
        )

    expected_ids = {
        "-".join(code_set)
        for code_set in EXPECTED_CODE_SETS
    }

    actual_ids = set(gdf["id"])

    if actual_ids != expected_ids:
        raise ValueError(
            "Generated phone-code feature IDs do not match the expected set. "
            f"Expected {sorted(expected_ids)}, "
            f"found {sorted(actual_ids)}."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            "Generated phone-code data contains null geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            "Generated phone-code data contains empty geometries."
        )

    if (~gdf.geometry.is_valid).any():
        raise ValueError(
            "Generated phone-code data contains invalid geometries."
        )

    invalid_geometry_types = set(
        gdf.geometry.geom_type.unique()
    ) - {"Polygon", "MultiPolygon"}

    if invalid_geometry_types:
        raise ValueError(
            "Generated phone-code data contains unsupported geometry types: "
            + ", ".join(sorted(invalid_geometry_types))
        )


def write_geojson(gdf: gpd.GeoDataFrame) -> None:
    """Write compact UTF-8 GeoJSON to GeoPedia's public data directory."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = gdf.to_json(
        drop_id=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    OUTPUT_PATH.write_text(
        geojson,
        encoding="utf-8",
    )


def main() -> None:
    """Generate Panama's 1-digit phone-code GeoJSON."""

    print("Panama 1-digit phone-code processor")
    print("=" * 72)
    print(f"Boundary source: {SOURCE_PATH}")
    print(f"Manual data:     {MANUAL_DATA_PATH}")
    print(f"Output:          {OUTPUT_PATH}")
    print()

    print("Reading province/comarca boundaries...")
    source = gpd.read_file(SOURCE_PATH)

    validate_source(source)

    print(f"Source features: {len(source)}")
    print(f"Source CRS: {source.crs}")
    print()

    print("Reading manual phone-code data...")
    manual_data = load_manual_data()

    regions = validate_manual_data(
        manual_data,
        source,
    )

    print(f"Manual entries: {len(regions)}")
    print()

    print("Province/comarca mapping:")

    for region in regions:
        codes = region["codes"]

        display_codes = (
            ", ".join(codes)
            if codes
            else "no useful code"
        )

        print(
            f"  {region['provinceId']}: "
            f"{region['provinceName']} -> {display_codes}"
        )

    print()

    print("Building phone-code regions...")
    output = build_output(
        source,
        regions,
    )

    validate_output(output)

    print(f"Output features: {len(output)}")
    print()
    print("Phone-code geographic regions:")

    for row in output.itertuples():
        print(
            f"  {row.id}: "
            f"{', '.join(row.codes)}"
        )

    print()
    print("Writing GeoJSON...")
    write_geojson(output)

    output_size = OUTPUT_PATH.stat().st_size

    print(
        f"Output size: {output_size / 1024:.1f} KB "
        f"({output_size:,} bytes)"
    )

    print()
    print("Done.")


if __name__ == "__main__":
    main()
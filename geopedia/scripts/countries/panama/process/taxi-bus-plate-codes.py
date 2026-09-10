"""
Build Panama's regional taxi and bus licence-plate code GeoJSON.

The source geometry is the already-processed Panama provinces/comarcas
GeoJSON. Manually researched plate-code assignments are joined to those
features, and regions without a useful taxi/bus plate code are removed.

Every included province has exactly one plate code, so the tracked manual
data uses a `codes` array for consistency with other researched datasets
while the final runtime GeoJSON stores a scalar `code` property.

Inputs:
    public/data/countries/panama/geojson/provinces-comarcas.geojson
    data/manual/countries/panama/taxi-bus-plate-codes.json

Output:
    public/data/countries/panama/geojson/taxi-bus-plate-codes.geojson
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


BOUNDARY_SOURCE = Path(
    "public/data/countries/panama/geojson/provinces-comarcas.geojson"
)

MANUAL_DATA_SOURCE = Path(
    "data/manual/countries/panama/taxi-bus-plate-codes.json"
)

OUTPUT_PATH = Path(
    "public/data/countries/panama/geojson/taxi-bus-plate-codes.geojson"
)

EXPECTED_SOURCE_FEATURE_COUNT = 14
EXPECTED_OUTPUT_FEATURE_COUNT = 10

EXPECTED_CODES = {
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "13",
}

REQUIRED_BOUNDARY_COLUMNS = {
    "id",
    "name",
    "type",
    "geometry",
}

REQUIRED_MANUAL_FIELDS = {
    "provinceId",
    "provinceName",
    "codes",
}


def code_sort_key(code: str) -> int:
    """
    Return the numeric value of a plate code for stable ordering.
    """

    return int(code)


def read_boundaries() -> gpd.GeoDataFrame:
    """
    Read and validate the processed Panama province/comarca boundaries.
    """

    print("Reading province/comarca boundaries...")

    if not BOUNDARY_SOURCE.exists():
        raise FileNotFoundError(
            f"Boundary source does not exist: {BOUNDARY_SOURCE}"
        )

    boundaries = gpd.read_file(BOUNDARY_SOURCE)

    print(f"Source features: {len(boundaries)}")
    print(f"Source CRS: {boundaries.crs}")

    missing_columns = REQUIRED_BOUNDARY_COLUMNS - set(boundaries.columns)

    if missing_columns:
        raise ValueError(
            "Boundary source is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if len(boundaries) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} province/comarca "
            f"features, found {len(boundaries)}."
        )

    if boundaries.crs is None:
        raise ValueError("Boundary source does not have a CRS.")

    if boundaries.crs.to_epsg() != 4326:
        raise ValueError(
            f"Expected EPSG:4326 boundaries, found {boundaries.crs}."
        )

    boundaries = boundaries.copy()

    boundaries["id"] = boundaries["id"].astype(str).str.strip()
    boundaries["name"] = boundaries["name"].astype(str).str.strip()

    if boundaries["id"].duplicated().any():
        duplicate_ids = sorted(
            boundaries.loc[
                boundaries["id"].duplicated(keep=False),
                "id",
            ].unique()
        )

        raise ValueError(
            "Boundary source contains duplicate province/comarca IDs: "
            + ", ".join(duplicate_ids)
        )

    if boundaries["id"].eq("").any():
        raise ValueError(
            "Boundary source contains an empty province/comarca ID."
        )

    if boundaries["name"].eq("").any():
        raise ValueError(
            "Boundary source contains an empty province/comarca name."
        )

    if boundaries.geometry.isna().any():
        raise ValueError(
            "Boundary source contains missing geometry."
        )

    if boundaries.geometry.is_empty.any():
        raise ValueError(
            "Boundary source contains empty geometry."
        )

    if not boundaries.geometry.is_valid.all():
        invalid_count = int((~boundaries.geometry.is_valid).sum())

        raise ValueError(
            f"Boundary source contains {invalid_count} invalid geometries."
        )

    return boundaries


def read_manual_data() -> list[dict[str, object]]:
    """
    Read and validate the manually researched taxi/bus plate-code assignments.
    """

    print()
    print("Reading manual taxi/bus plate-code data...")

    if not MANUAL_DATA_SOURCE.exists():
        raise FileNotFoundError(
            f"Manual data does not exist: {MANUAL_DATA_SOURCE}"
        )

    with MANUAL_DATA_SOURCE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Manual plate-code data must contain a top-level object."
        )

    regions = data.get("regions")

    if not isinstance(regions, list):
        raise ValueError(
            "Manual plate-code data must contain a 'regions' array."
        )

    print(f"Manual entries: {len(regions)}")

    if len(regions) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} manual region "
            f"entries, found {len(regions)}."
        )

    normalized_regions: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for index, entry in enumerate(regions):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Manual region entry {index} must be an object."
            )

        missing_fields = REQUIRED_MANUAL_FIELDS - set(entry)

        if missing_fields:
            raise ValueError(
                f"Manual region entry {index} is missing fields: "
                + ", ".join(sorted(missing_fields))
            )

        province_id = entry["provinceId"]
        province_name = entry["provinceName"]
        codes = entry["codes"]

        if not isinstance(province_id, str):
            raise ValueError(
                f"Manual region entry {index} has a non-string provinceId."
            )

        province_id = province_id.strip()

        if not province_id:
            raise ValueError(
                f"Manual region entry {index} has an empty provinceId."
            )

        if province_id in seen_ids:
            raise ValueError(
                f"Duplicate manual provinceId: {province_id}"
            )

        seen_ids.add(province_id)

        if not isinstance(province_name, str):
            raise ValueError(
                f"Manual region {province_id} has a non-string provinceName."
            )

        province_name = province_name.strip()

        if not province_name:
            raise ValueError(
                f"Manual region {province_id} has an empty provinceName."
            )

        if not isinstance(codes, list):
            raise ValueError(
                f"Manual region {province_id} must use a codes array."
            )

        if len(codes) > 1:
            raise ValueError(
                f"Manual region {province_id} contains more than one "
                "taxi/bus plate code."
            )

        normalized_codes: list[str] = []

        for code in codes:
            if not isinstance(code, str):
                raise ValueError(
                    f"Manual region {province_id} contains a non-string code."
                )

            code = code.strip()

            if not code:
                raise ValueError(
                    f"Manual region {province_id} contains an empty code."
                )

            if not code.isdigit():
                raise ValueError(
                    f"Manual region {province_id} contains a non-numeric "
                    f"plate code: {code!r}"
                )

            normalized_codes.append(code)

        normalized_regions.append(
            {
                "provinceId": province_id,
                "provinceName": province_name,
                "codes": normalized_codes,
            }
        )

    return normalized_regions


def validate_manual_mapping(
    boundaries: gpd.GeoDataFrame,
    regions: list[dict[str, object]],
) -> None:
    """
    Validate manual IDs, exact source names, and expected plate codes.
    """

    boundary_names_by_id = dict(
        zip(
            boundaries["id"],
            boundaries["name"],
        )
    )

    manual_ids = {
        str(region["provinceId"])
        for region in regions
    }

    boundary_ids = set(boundary_names_by_id)

    missing_manual_ids = boundary_ids - manual_ids
    unknown_manual_ids = manual_ids - boundary_ids

    if missing_manual_ids:
        raise ValueError(
            "Manual data is missing province/comarca IDs: "
            + ", ".join(sorted(missing_manual_ids))
        )

    if unknown_manual_ids:
        raise ValueError(
            "Manual data contains unknown province/comarca IDs: "
            + ", ".join(sorted(unknown_manual_ids))
        )

    for region in regions:
        province_id = str(region["provinceId"])
        manual_name = str(region["provinceName"])
        source_name = boundary_names_by_id[province_id]

        if manual_name != source_name:
            raise ValueError(
                f"Province name mismatch for {province_id}: "
                f"manual data has {manual_name!r}, "
                f"source has {source_name!r}."
            )

    observed_codes = {
        code
        for region in regions
        for code in region["codes"]  # type: ignore[union-attr]
    }

    if observed_codes != EXPECTED_CODES:
        missing_codes = EXPECTED_CODES - observed_codes
        unexpected_codes = observed_codes - EXPECTED_CODES

        messages: list[str] = []

        if missing_codes:
            messages.append(
                "missing: "
                + ", ".join(
                    sorted(missing_codes, key=code_sort_key)
                )
            )

        if unexpected_codes:
            messages.append(
                "unexpected: "
                + ", ".join(
                    sorted(unexpected_codes, key=code_sort_key)
                )
            )

        raise ValueError(
            "Manual plate-code set does not match expected codes ("
            + "; ".join(messages)
            + ")."
        )


def print_mapping(
    regions: list[dict[str, object]],
) -> None:
    """
    Print the validated province/comarca-to-plate-code mapping.
    """

    print()
    print("Province/comarca mapping:")

    for region in regions:
        province_id = str(region["provinceId"])
        province_name = str(region["provinceName"])
        codes = region["codes"]

        if codes:
            code_text = codes[0]  # type: ignore[index]
        else:
            code_text = "no useful code"

        print(
            f"  {province_id}: "
            f"{province_name} -> {code_text}"
        )


def build_plate_code_regions(
    boundaries: gpd.GeoDataFrame,
    regions: list[dict[str, object]],
) -> gpd.GeoDataFrame:
    """
    Join manual assignments and remove regions without useful plate codes.
    """

    print()
    print("Building taxi/bus plate-code regions...")

    manual_frame = pd.DataFrame(regions)

    joined = boundaries.merge(
        manual_frame,
        left_on="id",
        right_on="provinceId",
        how="left",
        validate="one_to_one",
    )

    if joined["codes"].isna().any():
        missing_ids = joined.loc[
            joined["codes"].isna(),
            "id",
        ].tolist()

        raise ValueError(
            "No manual plate-code mapping found for source IDs: "
            + ", ".join(missing_ids)
        )

    useful = joined[
        joined["codes"].map(bool)
    ].copy()

    useful["code"] = useful["codes"].map(
        lambda codes: codes[0]
    )

    useful["id"] = useful["code"]
    useful["name"] = useful["code"]

    output = gpd.GeoDataFrame(
        useful[
            [
                "id",
                "name",
                "code",
                "geometry",
            ]
        ].copy(),
        geometry="geometry",
        crs=boundaries.crs,
    )

    return output


def validate_output(
    output: gpd.GeoDataFrame,
) -> None:
    """
    Validate the final taxi/bus plate-code dataset.
    """

    print(f"Output features: {len(output)}")

    if len(output) != EXPECTED_OUTPUT_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_OUTPUT_FEATURE_COUNT} output features, "
            f"found {len(output)}."
        )

    if output["id"].duplicated().any():
        duplicate_ids = sorted(
            output.loc[
                output["id"].duplicated(keep=False),
                "id",
            ].unique(),
            key=code_sort_key,
        )

        raise ValueError(
            "Output contains duplicate IDs: "
            + ", ".join(duplicate_ids)
        )

    observed_codes = set(output["code"])

    if observed_codes != EXPECTED_CODES:
        missing_codes = EXPECTED_CODES - observed_codes
        unexpected_codes = observed_codes - EXPECTED_CODES

        messages: list[str] = []

        if missing_codes:
            messages.append(
                "missing: "
                + ", ".join(
                    sorted(missing_codes, key=code_sort_key)
                )
            )

        if unexpected_codes:
            messages.append(
                "unexpected: "
                + ", ".join(
                    sorted(unexpected_codes, key=code_sort_key)
                )
            )

        raise ValueError(
            "Output plate-code set does not match expected codes ("
            + "; ".join(messages)
            + ")."
        )

    if output.geometry.isna().any():
        raise ValueError(
            "Output contains missing geometry."
        )

    if output.geometry.is_empty.any():
        raise ValueError(
            "Output contains empty geometry."
        )

    if not output.geometry.is_valid.all():
        invalid_count = int((~output.geometry.is_valid).sum())

        raise ValueError(
            f"Output contains {invalid_count} invalid geometries."
        )


def print_output_summary(
    output: gpd.GeoDataFrame,
) -> None:
    """
    Print the final plate-code features in numeric order.
    """

    print()
    print("Taxi/bus plate-code geographic regions:")

    sorted_output = output.assign(
        _sort_key=output["code"].map(code_sort_key)
    ).sort_values("_sort_key")

    for _, row in sorted_output.iterrows():
        print(f"  {row['id']}: {row['code']}")


def write_output(
    output: gpd.GeoDataFrame,
) -> None:
    """
    Write the final GeoJSON as compact UTF-8 JSON.
    """

    print()
    print("Writing GeoJSON...")

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        output.to_json(
            drop_id=True,
        )
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    output_size = OUTPUT_PATH.stat().st_size

    print(
        f"Output size: "
        f"{output_size / 1024:.1f} KB "
        f"({output_size:,} bytes)"
    )


def main() -> None:
    """
    Run the Panama taxi/bus plate-code processing pipeline.
    """

    print("Panama taxi/bus plate-code processor")
    print("=" * 72)
    print(f"Boundary source: {BOUNDARY_SOURCE}")
    print(f"Manual data:     {MANUAL_DATA_SOURCE}")
    print(f"Output:          {OUTPUT_PATH}")
    print()

    boundaries = read_boundaries()
    regions = read_manual_data()

    validate_manual_mapping(
        boundaries,
        regions,
    )

    print_mapping(regions)

    output = build_plate_code_regions(
        boundaries,
        regions,
    )

    validate_output(output)
    print_output_summary(output)
    write_output(output)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
"""Process Puerto Rico barrio boundaries for GeoPedia.

The source is the GeoBoundaries Puerto Rico ADM3 dataset, which contains
901 barrio polygons. Puerto Rico has 902 named barrio subdivisions in the
Census-derived reference data used during source validation, but the
GeoBoundaries dataset does not contain a polygon for Moca barrio-pueblo.
GeoPedia therefore intentionally uses the 901 available GeoBoundaries
polygons rather than fabricating the missing geometry.

GeoBoundaries does not provide each barrio's parent municipality. Parent
municipalities are assigned spatially using GeoPedia's processed Puerto Rico
municipality polygons. Each barrio is assigned to the municipality with which
it has the greatest intersection area.

The municipality and barrio sources come from different datasets and boundary
vintages, so their geometries are not perfectly congruent. The assignment
method intentionally uses only the municipality with the greatest intersection
rather than requiring complete containment.

Output properties:
    barrio_id:
        Stable GeoBoundaries shapeID for the barrio.

    name:
        GeoBoundaries barrio name.

    municipality_id:
        Five-digit Census county-equivalent GEOID of the assigned Puerto Rico
        municipality.

The output geometry is not additionally simplified because the GeoBoundaries
source is already small enough for GeoPedia's runtime use.

Input:
    data/raw/countries/puerto-rico/
        geoBoundaries-PRI-ADM3-all/
            geoBoundaries-PRI-ADM3.geojson

    public/data/countries/puerto-rico/geojson/
        municipalities.geojson

Output:
    public/data/countries/puerto-rico/geojson/
        barrios.geojson
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

BARRIOS_SOURCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "puerto-rico"
    / "geoBoundaries-PRI-ADM3-all"
    / "geoBoundaries-PRI-ADM3.geojson"
)

MUNICIPALITIES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "barrios.geojson"
)

EXPECTED_BARRIO_COUNT = 901
EXPECTED_MUNICIPALITY_COUNT = 78

# WGS 84 / UTM zone 20N. Puerto Rico lies within this zone, making it
# appropriate for the intersection-area comparisons used for assignment.
AREA_CRS = "EPSG:32620"


def validate_source(
    barrios: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> None:
    """Validate the source datasets required by the processor."""
    if len(barrios) != EXPECTED_BARRIO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_BARRIO_COUNT} barrio features, "
            f"found {len(barrios)}."
        )

    if len(municipalities) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(municipalities)}."
        )

    required_barrio_columns = {
        "shapeName",
        "shapeID",
        "geometry",
    }

    missing_barrio_columns = (
        required_barrio_columns - set(barrios.columns)
    )

    if missing_barrio_columns:
        raise ValueError(
            "Barrio source is missing required columns: "
            f"{sorted(missing_barrio_columns)}"
        )

    required_municipality_columns = {
        "municipality_id",
        "name",
        "geometry",
    }

    missing_municipality_columns = (
        required_municipality_columns - set(municipalities.columns)
    )

    if missing_municipality_columns:
        raise ValueError(
            "Municipality source is missing required columns: "
            f"{sorted(missing_municipality_columns)}"
        )

    if barrios.crs is None:
        raise ValueError("Barrio source does not define a CRS.")

    if municipalities.crs is None:
        raise ValueError("Municipality source does not define a CRS.")

    if barrios.geometry.isna().any():
        raise ValueError("Barrio source contains null geometries.")

    if barrios.geometry.is_empty.any():
        raise ValueError("Barrio source contains empty geometries.")

    if not barrios.geometry.is_valid.all():
        raise ValueError("Barrio source contains invalid geometries.")

    if municipalities.geometry.isna().any():
        raise ValueError("Municipality source contains null geometries.")

    if municipalities.geometry.is_empty.any():
        raise ValueError("Municipality source contains empty geometries.")

    if not municipalities.geometry.is_valid.all():
        raise ValueError("Municipality source contains invalid geometries.")

    barrio_ids = barrios["shapeID"].astype(str)

    if barrio_ids.duplicated().any():
        duplicates = sorted(
            barrio_ids[barrio_ids.duplicated(keep=False)].unique()
        )

        raise ValueError(
            f"Duplicate GeoBoundaries barrio shapeIDs: {duplicates}"
        )

    municipality_ids = municipalities["municipality_id"].astype(str)

    if municipality_ids.duplicated().any():
        duplicates = sorted(
            municipality_ids[
                municipality_ids.duplicated(keep=False)
            ].unique()
        )

        raise ValueError(
            f"Duplicate municipality IDs: {duplicates}"
        )

    for municipality_id in municipality_ids:
        if (
            len(municipality_id) != 5
            or not municipality_id.isdigit()
            or not municipality_id.startswith("72")
        ):
            raise ValueError(
                "Invalid Puerto Rico municipality ID: "
                f"{municipality_id}"
            )


def assign_municipalities(
    barrios: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> list[str]:
    """Assign each barrio to its greatest-overlap municipality."""
    barrios_projected = barrios.to_crs(AREA_CRS)
    municipalities_projected = municipalities.to_crs(AREA_CRS)

    municipality_records = [
        (
            str(row.municipality_id),
            row.geometry,
        )
        for row in municipalities_projected.itertuples(index=False)
    ]

    assignments: list[str] = []

    for index, barrio in enumerate(
        barrios_projected.itertuples(index=False),
        start=1,
    ):
        barrio_geometry = barrio.geometry
        best_municipality_id: str | None = None
        best_intersection_area = 0.0

        for municipality_id, municipality_geometry in municipality_records:
            if not barrio_geometry.intersects(municipality_geometry):
                continue

            intersection_area = barrio_geometry.intersection(
                municipality_geometry
            ).area

            if intersection_area > best_intersection_area:
                best_intersection_area = intersection_area
                best_municipality_id = municipality_id

        if best_municipality_id is None:
            raise ValueError(
                "Could not assign municipality to barrio "
                f"{barrio.shapeName} [{barrio.shapeID}]."
            )

        assignments.append(best_municipality_id)

        if index % 100 == 0 or index == len(barrios_projected):
            print(
                f"Assigned municipalities to "
                f"{index}/{len(barrios_projected)} barrios..."
            )

    return assignments


def build_output(
    barrios: gpd.GeoDataFrame,
    municipality_ids: list[str],
) -> gpd.GeoDataFrame:
    """Build the normalized runtime barrio GeoDataFrame."""
    if len(barrios) != len(municipality_ids):
        raise ValueError(
            "Barrio and municipality-assignment counts do not match."
        )

    output = gpd.GeoDataFrame(
        {
            "barrio_id": barrios["shapeID"].astype(str),
            "name": barrios["shapeName"].astype(str).str.strip(),
            "municipality_id": municipality_ids,
        },
        geometry=barrios.geometry.copy(),
        crs=barrios.crs,
    )

    output = output.sort_values(
        by=["municipality_id", "name", "barrio_id"],
        kind="stable",
    ).reset_index(drop=True)

    return output


def validate_output(
    output: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> None:
    """Validate the normalized barrio runtime dataset."""
    if len(output) != EXPECTED_BARRIO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_BARRIO_COUNT} output features, "
            f"found {len(output)}."
        )

    expected_columns = {
        "barrio_id",
        "name",
        "municipality_id",
        "geometry",
    }

    if set(output.columns) != expected_columns:
        raise ValueError(
            "Unexpected output columns. "
            f"Expected {sorted(expected_columns)}, "
            f"found {sorted(output.columns)}."
        )

    if output["barrio_id"].duplicated().any():
        duplicates = sorted(
            output.loc[
                output["barrio_id"].duplicated(keep=False),
                "barrio_id",
            ].unique()
        )

        raise ValueError(
            f"Duplicate output barrio IDs: {duplicates}"
        )

    if output["barrio_id"].isna().any():
        raise ValueError("Output contains null barrio IDs.")

    if output["name"].isna().any():
        raise ValueError("Output contains null barrio names.")

    if output["municipality_id"].isna().any():
        raise ValueError("Output contains null municipality IDs.")

    blank_names = output["name"].str.strip().eq("")

    if blank_names.any():
        raise ValueError("Output contains blank barrio names.")

    valid_municipality_ids = set(
        municipalities["municipality_id"].astype(str)
    )

    output_municipality_ids = set(
        output["municipality_id"].astype(str)
    )

    unknown_municipality_ids = (
        output_municipality_ids - valid_municipality_ids
    )

    if unknown_municipality_ids:
        raise ValueError(
            "Output contains unknown municipality IDs: "
            f"{sorted(unknown_municipality_ids)}"
        )

    if output.geometry.isna().any():
        raise ValueError("Output contains null geometries.")

    if output.geometry.is_empty.any():
        raise ValueError("Output contains empty geometries.")

    if not output.geometry.is_valid.all():
        raise ValueError("Output contains invalid geometries.")


def write_geojson(output: gpd.GeoDataFrame) -> None:
    """Write compact UTF-8 GeoJSON for GeoPedia runtime use."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    geojson = json.loads(output.to_json())

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def print_summary(output: gpd.GeoDataFrame) -> None:
    """Print a concise summary of the generated barrio dataset."""
    municipality_count = output["municipality_id"].nunique()
    unique_name_count = output["name"].nunique()

    duplicate_name_count = (
        output["name"]
        .value_counts()
        .gt(1)
        .sum()
    )

    print()
    print("Puerto Rico barrios processed successfully.")
    print(f"Features written: {len(output)}")
    print(f"Municipalities represented: {municipality_count}")
    print(f"Unique barrio names: {unique_name_count}")
    print(f"Duplicated barrio names: {duplicate_name_count}")
    print("Excluded named subdivision: Moca barrio-pueblo")
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


def main() -> None:
    """Process Puerto Rico barrio boundaries for GeoPedia."""
    print(f"Reading barrios from {BARRIOS_SOURCE_PATH}")
    barrios = gpd.read_file(BARRIOS_SOURCE_PATH)

    print(f"Reading municipalities from {MUNICIPALITIES_PATH}")
    municipalities = gpd.read_file(MUNICIPALITIES_PATH)

    validate_source(
        barrios,
        municipalities,
    )

    print()
    print("Assigning parent municipalities...")

    municipality_ids = assign_municipalities(
        barrios,
        municipalities,
    )

    output = build_output(
        barrios,
        municipality_ids,
    )

    validate_output(
        output,
        municipalities,
    )

    write_geojson(output)
    print_summary(output)


if __name__ == "__main__":
    main()
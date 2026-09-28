"""Inspect GeoBoundaries ADM3 geography for the U.S. Virgin Islands.

This diagnostic script examines the GeoBoundaries ADM3 dataset and compares
its features spatially against GeoPedia's existing three U.S. Virgin Islands
county-equivalent polygons.

It reports:

- GeoBoundaries schema and CRS.
- Feature count and geometry types.
- Names and stable GeoBoundaries IDs.
- Duplicate or blank names.
- Geometry validity.
- Spatial assignment of each ADM3 feature to St. Croix, St. John, or
  St. Thomas using greatest polygon overlap.
- Feature counts by parent island.
- Assignment overlap ratios.

The script does not write runtime data.

Inputs:
    data/raw/countries/us-virgin-islands/
        geoBoundaries-VIR-ADM3-all/
            geoBoundaries-VIR-ADM3.geojson

    public/data/countries/usa/geojson/counties.geojson
"""

from collections import Counter
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

ADM3_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "us-virgin-islands"
    / "geoBoundaries-VIR-ADM3-all"
    / "geoBoundaries-VIR-ADM3.geojson"
)

COUNTIES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "usa"
    / "geojson"
    / "counties.geojson"
)

EXPECTED_ISLAND_COUNT = 3

AREA_CRS = "EPSG:32620"


def load_adm3() -> gpd.GeoDataFrame:
    """Load and validate the GeoBoundaries ADM3 dataset."""
    print("Reading GeoBoundaries ADM3 from:")
    print(ADM3_PATH)
    print()

    adm3 = gpd.read_file(
        ADM3_PATH
    )

    if adm3.empty:
        raise ValueError(
            "GeoBoundaries ADM3 dataset is empty."
        )

    if adm3.crs is None:
        raise ValueError(
            "GeoBoundaries ADM3 dataset has no CRS."
        )

    print("=" * 72)
    print("GEOboundaries ADM3")
    print("=" * 72)
    print(f"Features: {len(adm3)}")
    print(f"CRS: {adm3.crs}")
    print(
        f"Columns: {list(adm3.columns)}"
    )
    print()

    required_columns = {
        "shapeName",
        "shapeID",
        "geometry",
    }

    missing_columns = (
        required_columns - set(adm3.columns)
    )

    if missing_columns:
        raise ValueError(
            "GeoBoundaries ADM3 dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    return adm3


def inspect_names(
    adm3: gpd.GeoDataFrame,
) -> None:
    """Inspect ADM3 names for blanks and duplicates."""
    names = (
        adm3["shapeName"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    blank_count = int(
        (names == "").sum()
    )

    counts = Counter(
        names
    )

    duplicate_names = sorted(
        name
        for name, count in counts.items()
        if name and count > 1
    )

    print("=" * 72)
    print("NAMES")
    print("=" * 72)
    print(
        f"Unique names: {names.nunique()}"
    )
    print(
        f"Blank names: {blank_count}"
    )
    print(
        f"Duplicated names: {len(duplicate_names)}"
    )

    if duplicate_names:
        print()

        for name in duplicate_names:
            print(
                f"  {name}: {counts[name]}"
            )

    print()


def inspect_geometry(
    adm3: gpd.GeoDataFrame,
) -> None:
    """Inspect ADM3 geometry types and validity."""
    geometry_types = Counter(
        adm3.geometry.geom_type
    )

    invalid = adm3[
        adm3.geometry.isna()
        | adm3.geometry.is_empty
        | ~adm3.geometry.is_valid
    ]

    print("=" * 72)
    print("GEOMETRY")
    print("=" * 72)

    for geometry_type, count in sorted(
        geometry_types.items()
    ):
        print(
            f"{geometry_type}: {count}"
        )

    print(
        f"Invalid/empty/null geometries: "
        f"{len(invalid)}"
    )
    print()


def load_islands() -> gpd.GeoDataFrame:
    """Load the three USVI county-equivalent island polygons."""
    counties = gpd.read_file(
        COUNTIES_PATH
    )

    if counties.empty:
        raise ValueError(
            "GeoPedia U.S. counties dataset is empty."
        )

    if counties.crs is None:
        raise ValueError(
            "GeoPedia U.S. counties dataset has no CRS."
        )

    required_columns = {
        "geoid",
        "name",
        "state",
        "geometry",
    }

    missing_columns = (
        required_columns - set(counties.columns)
    )

    if missing_columns:
        raise ValueError(
            "U.S. counties dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    islands = counties[
        counties["state"] == "VI"
    ].copy()

    if len(islands) != EXPECTED_ISLAND_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ISLAND_COUNT} USVI island features, "
            f"found {len(islands)}."
        )

    islands = islands[
        [
            "geoid",
            "name",
            "geometry",
        ]
    ].copy()

    islands = islands.rename(
        columns={
            "geoid": "island_id",
            "name": "island_name",
        }
    )

    return islands


def assign_parent_islands(
    adm3: gpd.GeoDataFrame,
    islands: gpd.GeoDataFrame,
) -> list[dict]:
    """Assign each ADM3 feature to the island with greatest area overlap."""
    adm3_projected = adm3.to_crs(
        AREA_CRS
    )

    islands_projected = islands.to_crs(
        AREA_CRS
    )

    assignments: list[dict] = []

    for index, row in adm3_projected.iterrows():
        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            raise ValueError(
                f"ADM3 feature at index {index} has no usable geometry."
            )

        total_area = geometry.area

        if total_area <= 0:
            raise ValueError(
                f"ADM3 feature at index {index} has zero area."
            )

        overlaps: list[tuple[float, str, str]] = []

        for _, island in islands_projected.iterrows():
            overlap_area = geometry.intersection(
                island.geometry
            ).area

            overlaps.append(
                (
                    overlap_area,
                    island["island_id"],
                    island["island_name"],
                )
            )

        overlaps.sort(
            reverse=True,
            key=lambda item: item[0],
        )

        best_overlap_area, island_id, island_name = overlaps[0]

        overlap_ratio = (
            best_overlap_area / total_area
        )

        original_row = adm3.loc[index]

        assignments.append(
            {
                "shape_id": str(
                    original_row["shapeID"]
                ).strip(),
                "name": str(
                    original_row["shapeName"]
                ).strip(),
                "island_id": str(
                    island_id
                ).strip(),
                "island_name": str(
                    island_name
                ).strip(),
                "overlap_ratio": overlap_ratio,
            }
        )

    return assignments


def print_assignments(
    assignments: list[dict],
) -> None:
    """Print ADM3-to-island spatial assignments."""
    print("=" * 72)
    print("PARENT ISLAND ASSIGNMENTS")
    print("=" * 72)

    for assignment in sorted(
        assignments,
        key=lambda item: (
            item["island_name"],
            item["name"],
            item["shape_id"],
        ),
    ):
        print(
            f"{assignment['name']} | "
            f"{assignment['shape_id']} | "
            f"{assignment['island_name']} "
            f"({assignment['island_id']}) | "
            f"{assignment['overlap_ratio']:.2%}"
        )

    print()


def print_parent_summary(
    assignments: list[dict],
) -> None:
    """Print ADM3 feature counts and overlap quality by parent island."""
    counts = Counter(
        assignment["island_name"]
        for assignment in assignments
    )

    overlap_ratios = [
        assignment["overlap_ratio"]
        for assignment in assignments
    ]

    print("=" * 72)
    print("PARENT SUMMARY")
    print("=" * 72)

    for island_name in sorted(counts):
        print(
            f"{island_name}: {counts[island_name]}"
        )

    print()

    if overlap_ratios:
        print(
            "Lowest assignment overlap: "
            f"{min(overlap_ratios):.2%}"
        )

        print(
            "Average assignment overlap: "
            f"{sum(overlap_ratios) / len(overlap_ratios):.2%}"
        )

    weak_assignments = [
        assignment
        for assignment in assignments
        if assignment["overlap_ratio"] < 0.50
    ]

    print(
        "Assignments below 50% overlap: "
        f"{len(weak_assignments)}"
    )

    if weak_assignments:
        print()

        for assignment in weak_assignments:
            print(
                f"  {assignment['name']} -> "
                f"{assignment['island_name']}: "
                f"{assignment['overlap_ratio']:.2%}"
            )

    print()


def print_source_fields(
    adm3: gpd.GeoDataFrame,
) -> None:
    """Print all source properties for every ADM3 feature."""
    non_geometry_columns = [
        column
        for column in adm3.columns
        if column != "geometry"
    ]

    print("=" * 72)
    print("SOURCE RECORDS")
    print("=" * 72)

    for _, row in adm3.iterrows():
        values = []

        for column in non_geometry_columns:
            values.append(
                f"{column}={row[column]!r}"
            )

        print(
            " | ".join(values)
        )

    print()


def main() -> None:
    """Inspect USVI GeoBoundaries ADM3 geography."""
    adm3 = load_adm3()

    inspect_names(
        adm3
    )

    inspect_geometry(
        adm3
    )

    print_source_fields(
        adm3
    )

    islands = load_islands()

    assignments = assign_parent_islands(
        adm3,
        islands,
    )

    print_assignments(
        assignments
    )

    print_parent_summary(
        assignments
    )

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(
        f"ADM3 features: {len(adm3)}"
    )
    print(
        f"Parent islands represented: "
        f"{len(set(a['island_id'] for a in assignments))}"
    )
    print()

    print("Inspection complete.")


if __name__ == "__main__":
    main()
"""Inspect Costa Rica administrative boundary GeoJSON sources.

This diagnostic script examines the ADM1, ADM2, and ADM3 Costa Rica
administrative-boundary datasets before GeoPedia runtime processing.

For each administrative level it reports:

- Feature count.
- CRS.
- Available source properties.
- Sample source records.
- Blank and duplicate names when a likely name field can be identified.
- Candidate ID, code, and parent fields.
- Geometry types and validity.
- Coordinate counts.
- Approximate compact unsimplified GeoJSON size.
- Geographic bounds.

The script does not write runtime data.

Inputs:
    data/raw/countries/costa-rica/cri_admin_boundaries.geojson/
        cri_admin1.geojson
        cri_admin2.geojson
        cri_admin3.geojson
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "costa-rica"
    / "cri_admin_boundaries.geojson"
)

SOURCE_PATHS = {
    "ADM1": SOURCE_DIR / "cri_admin1.geojson",
    "ADM2": SOURCE_DIR / "cri_admin2.geojson",
    "ADM3": SOURCE_DIR / "cri_admin3.geojson",
}

NAME_CANDIDATES = [
    "name",
    "NAME",
    "Name",
    "nombre",
    "NOMBRE",
    "shapeName",
]

FIELD_KEYWORDS = (
    "id",
    "code",
    "cod",
    "parent",
    "adm",
    "prov",
    "cant",
    "dist",
    "name",
    "nom",
)


def count_coordinates(
    geometry: Any,
) -> int:
    """Count coordinate pairs in a Polygon or MultiPolygon geometry."""
    if geometry is None or geometry.is_empty:
        return 0

    if geometry.geom_type == "Polygon":
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if geometry.geom_type == "MultiPolygon":
        return sum(
            count_coordinates(polygon)
            for polygon in geometry.geoms
        )

    if hasattr(geometry, "geoms"):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    return 0


def format_bytes(
    byte_count: int,
) -> str:
    """Format a byte count using convenient binary units."""
    if byte_count < 1024:
        return f"{byte_count:,} bytes"

    if byte_count < 1024**2:
        return (
            f"{byte_count / 1024:.2f} KB "
            f"({byte_count:,} bytes)"
        )

    return (
        f"{byte_count / 1024**2:.2f} MB "
        f"({byte_count:,} bytes)"
    )


def find_name_column(
    columns: list[str],
) -> str | None:
    """Find a likely administrative-unit name column."""
    for candidate in NAME_CANDIDATES:
        if candidate in columns:
            return candidate

    for column in columns:
        lowered = column.lower()

        if "name" in lowered or "nombre" in lowered:
            return column

    return None


def find_interesting_columns(
    columns: list[str],
) -> list[str]:
    """Find properties likely related to names, IDs, codes, or parents."""
    interesting: list[str] = []

    for column in columns:
        if column == "geometry":
            continue

        lowered = column.lower()

        if any(
            keyword in lowered
            for keyword in FIELD_KEYWORDS
        ):
            interesting.append(column)

    return interesting


def compact_geojson_size(
    frame: gpd.GeoDataFrame,
) -> int:
    """Estimate compact GeoJSON size using geometry only."""
    geometry_only = gpd.GeoDataFrame(
        geometry=frame.geometry,
        crs=frame.crs,
    )

    geojson = json.loads(
        geometry_only.to_json(
            drop_id=True,
        )
    )

    content = json.dumps(
        geojson,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return len(
        content.encode("utf-8")
    )


def inspect_names(
    frame: gpd.GeoDataFrame,
    name_column: str | None,
) -> None:
    """Report name uniqueness and duplicates for an administrative level."""
    print("-" * 72)
    print("NAMES")
    print("-" * 72)

    if name_column is None:
        print(
            "No likely name column was identified."
        )
        print()
        return

    names = (
        frame[name_column]
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

    duplicates = sorted(
        (
            name,
            count,
        )
        for name, count in counts.items()
        if name and count > 1
    )

    print(
        f"Name column: {name_column}"
    )
    print(
        f"Unique names: {names.nunique()}"
    )
    print(
        f"Blank names: {blank_count}"
    )
    print(
        f"Duplicated names: {len(duplicates)}"
    )

    if duplicates:
        print()

        for name, count in duplicates:
            print(
                f"  {name}: {count}"
            )

    print()


def inspect_geometry(
    frame: gpd.GeoDataFrame,
) -> None:
    """Report geometry types, validity, coordinates, bounds, and size."""
    print("-" * 72)
    print("GEOMETRY")
    print("-" * 72)

    geometry_types = Counter(
        frame.geometry.geom_type
    )

    for geometry_type, count in sorted(
        geometry_types.items()
    ):
        print(
            f"{geometry_type}: {count}"
        )

    invalid = frame[
        frame.geometry.isna()
        | frame.geometry.is_empty
        | ~frame.geometry.is_valid
    ]

    coordinate_counts = frame.geometry.apply(
        count_coordinates
    )

    total_coordinates = int(
        coordinate_counts.sum()
    )

    min_x, min_y, max_x, max_y = (
        frame.total_bounds
    )

    print(
        "Invalid/empty/null geometries: "
        f"{len(invalid)}"
    )
    print(
        f"Total coordinates: {total_coordinates:,}"
    )

    if len(frame) > 0:
        print(
            "Average coordinates per feature: "
            f"{total_coordinates / len(frame):,.1f}"
        )
        print(
            "Smallest feature coordinate count: "
            f"{int(coordinate_counts.min()):,}"
        )
        print(
            "Largest feature coordinate count: "
            f"{int(coordinate_counts.max()):,}"
        )

    print(
        "Bounds: "
        f"({min_x:.6f}, {min_y:.6f}) -> "
        f"({max_x:.6f}, {max_y:.6f})"
    )

    estimated_size = compact_geojson_size(
        frame
    )

    print(
        "Approximate compact unsimplified GeoJSON size: "
        f"{format_bytes(estimated_size)}"
    )
    print()


def print_candidate_fields(
    frame: gpd.GeoDataFrame,
) -> None:
    """Print fields that may contain names, codes, IDs, or parents."""
    columns = [
        column
        for column in frame.columns
        if column != "geometry"
    ]

    interesting = find_interesting_columns(
        columns
    )

    print("-" * 72)
    print("CANDIDATE HIERARCHY FIELDS")
    print("-" * 72)

    if not interesting:
        print(
            "No candidate hierarchy fields identified by name."
        )
        print()
        return

    for column in interesting:
        values = (
            frame[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        values = values[
            values != ""
        ]

        unique_values = sorted(
            values.unique()
        )

        print(
            f"{column}: "
            f"{len(unique_values)} unique nonblank value(s)"
        )

        preview = unique_values[:15]

        if preview:
            print(
                "  "
                + ", ".join(
                    repr(value)
                    for value in preview
                )
            )

        if len(unique_values) > len(preview):
            print(
                f"  ... "
                f"{len(unique_values) - len(preview)} more"
            )

    print()


def print_sample_records(
    frame: gpd.GeoDataFrame,
    count: int = 10,
) -> None:
    """Print source properties for a sample of administrative records."""
    property_columns = [
        column
        for column in frame.columns
        if column != "geometry"
    ]

    print("-" * 72)
    print("SAMPLE SOURCE RECORDS")
    print("-" * 72)

    sample = frame.head(
        count
    )

    for _, row in sample.iterrows():
        values = [
            f"{column}={row[column]!r}"
            for column in property_columns
        ]

        print(
            " | ".join(values)
        )

    print()


def inspect_level(
    level: str,
    path: Path,
) -> None:
    """Inspect one Costa Rica administrative-boundary level."""
    print("=" * 72)
    print(level)
    print("=" * 72)
    print("Reading:")
    print(path)
    print()

    if not path.exists():
        raise FileNotFoundError(
            f"{level} source file does not exist: {path}"
        )

    frame = gpd.read_file(
        path
    )

    if frame.empty:
        raise ValueError(
            f"{level} source dataset is empty."
        )

    if frame.crs is None:
        raise ValueError(
            f"{level} source dataset has no CRS."
        )

    print(
        f"Features: {len(frame)}"
    )
    print(
        f"CRS: {frame.crs}"
    )
    print(
        f"Columns: {list(frame.columns)}"
    )
    print()

    name_column = find_name_column(
        list(frame.columns)
    )

    inspect_names(
        frame,
        name_column,
    )

    print_candidate_fields(
        frame
    )

    print_sample_records(
        frame
    )

    inspect_geometry(
        frame
    )


def main() -> None:
    """Inspect Costa Rica ADM1 through ADM3 source datasets."""
    for level, path in SOURCE_PATHS.items():
        inspect_level(
            level,
            path,
        )

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(
        "Costa Rica ADM1-ADM3 inspection complete."
    )


if __name__ == "__main__":
    main()
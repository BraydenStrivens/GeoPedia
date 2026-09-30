"""
Process Malaysia's raw administrative boundaries into GeoPedia's canonical
administrative hierarchy.

geoBoundaries supplies separate ADM1, ADM2, and ADM3 datasets for Malaysia,
but the ADM2 and ADM3 files do not contain parent administrative identifiers.
This script reconstructs those relationships spatially:

    ADM1: State / Federal Territory
    ADM2: District
    ADM3: Sub-District

Each child feature is assigned to the parent geometry with which it has the
largest intersection area. Parent overlap percentages are then reported so
questionable assignments can be reviewed before geometry simplification.

Source names are preserved exactly. This is particularly important at ADM3,
where administrative terms such as MUKIM, PEKAN, BANDAR, LAND DISTRICT, and
TOWN DISTRICT distinguish different kinds of subdivisions and can themselves
be useful geographic clues.

geoBoundaries shapeID values are also preserved as GeoPedia's stable IDs.
ADM1 uses shapeISO instead because geoBoundaries provides ISO 3166-2 codes
for every Malaysian state and federal territory.

This stage intentionally does not simplify geometry. The generated
intermediate files provide the validated hierarchy that later processing can
clean and simplify for public map use.

Inputs
------
data/raw/countries/malaysia/geoBoundaries-MYS-ADM1.geojson
data/raw/countries/malaysia/geoBoundaries-MYS-ADM2.geojson
data/raw/countries/malaysia/geoBoundaries-MYS-ADM3.geojson

Outputs
-------
data/intermediate/countries/malaysia/states.geojson
data/intermediate/countries/malaysia/districts.geojson
data/intermediate/countries/malaysia/sub-districts.geojson

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/process/admin.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry.base import BaseGeometry


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "malaysia"
)

INTERMEDIATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "malaysia"
)

ADM1_PATH = RAW_DIR / "geoBoundaries-MYS-ADM1.geojson"
ADM2_PATH = RAW_DIR / "geoBoundaries-MYS-ADM2.geojson"
ADM3_PATH = RAW_DIR / "geoBoundaries-MYS-ADM3.geojson"

STATES_OUTPUT_PATH = INTERMEDIATE_DIR / "states.geojson"
DISTRICTS_OUTPUT_PATH = INTERMEDIATE_DIR / "districts.geojson"
SUB_DISTRICTS_OUTPUT_PATH = INTERMEDIATE_DIR / "sub-districts.geojson"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPECTED_COUNTS = {
    "ADM1": 16,
    "ADM2": 159,
    "ADM3": 1859,
}

# Intersection areas must be calculated in a projected CRS rather than in
# longitude/latitude degrees. EPSG:6933 is an equal-area global projection
# suitable for comparing the relative areas used during parent assignment.
AREA_CRS = "EPSG:6933"

# Assignments below this percentage are printed individually for review.
REVIEW_OVERLAP_PERCENT = 75.0


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParentAssignment:
    """Records the selected spatial parent for one child feature."""

    child_index: int
    parent_index: int
    overlap_percent: float


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------


def load_admin_file(
    path: Path,
    level: str,
) -> gpd.GeoDataFrame:
    """
    Load and validate one raw geoBoundaries administrative dataset.

    Required source properties are checked before any hierarchy processing
    begins so malformed or unexpected source data fails explicitly.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {level} source file: {path}"
        )

    frame = gpd.read_file(path)

    expected_count = EXPECTED_COUNTS[level]

    if len(frame) != expected_count:
        raise ValueError(
            f"{level} expected {expected_count:,} features but found "
            f"{len(frame):,}."
        )

    required_columns = {
        "shapeName",
        "shapeID",
        "shapeISO",
        "shapeGroup",
        "shapeType",
        "geometry",
    }

    missing_columns = required_columns - set(frame.columns)

    if missing_columns:
        raise ValueError(
            f"{level} is missing required properties: "
            + ", ".join(sorted(missing_columns))
        )

    if frame.geometry.isna().any():
        raise ValueError(
            f"{level} contains features without geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            f"{level} contains empty geometries."
        )

    duplicate_ids = frame["shapeID"].duplicated(
        keep=False
    )

    if duplicate_ids.any():
        values = sorted(
            frame.loc[
                duplicate_ids,
                "shapeID",
            ].astype(str).unique()
        )

        raise ValueError(
            f"{level} contains duplicate shapeID values: "
            + ", ".join(values)
        )

    duplicate_names = frame["shapeName"].duplicated(
        keep=False
    )

    if duplicate_names.any():
        values = sorted(
            frame.loc[
                duplicate_names,
                "shapeName",
            ].astype(str).unique()
        )

        raise ValueError(
            f"{level} contains duplicate shapeName values: "
            + ", ".join(values)
        )

    source_types = set(
        frame["shapeType"].astype(str)
    )

    if source_types != {level}:
        raise ValueError(
            f"{level} contains unexpected shapeType values: "
            f"{sorted(source_types)}"
        )

    return frame


def validate_state_iso_codes(
    states: gpd.GeoDataFrame,
) -> None:
    """
    Validate the ADM1 ISO codes used as GeoPedia's state identifiers.

    ADM1 is the only supplied level with populated shapeISO values, making
    those ISO 3166-2 identifiers preferable to geoBoundaries shapeID values.
    """

    iso_values = states["shapeISO"].astype(str).str.strip()

    if (iso_values == "").any():
        raise ValueError(
            "ADM1 contains an empty shapeISO value."
        )

    if iso_values.duplicated().any():
        duplicates = sorted(
            iso_values[
                iso_values.duplicated(
                    keep=False
                )
            ].unique()
        )

        raise ValueError(
            "ADM1 contains duplicate shapeISO values: "
            + ", ".join(duplicates)
        )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def repair_geometry(
    geometry: BaseGeometry,
) -> BaseGeometry:
    """
    Repair an invalid geometry when necessary.

    GeoPandas/Shapely's make_valid operation is preferred because spatial
    hierarchy assignment requires valid polygon intersections.
    """

    if geometry.is_valid:
        return geometry

    return geometry.make_valid()


def prepare_geometry(
    frame: gpd.GeoDataFrame,
    level: str,
) -> gpd.GeoDataFrame:
    """
    Return a copy with invalid source geometries repaired.

    Repairs are used for spatial calculations and are retained in the
    intermediate outputs when necessary. No simplification is performed.
    """

    prepared = frame.copy()

    invalid_before = int(
        (~prepared.geometry.is_valid).sum()
    )

    if invalid_before:
        prepared["geometry"] = prepared.geometry.map(
            repair_geometry
        )

    invalid_after = int(
        (~prepared.geometry.is_valid).sum()
    )

    print(
        f"{level} invalid geometries: "
        f"{invalid_before:,} -> {invalid_after:,}"
    )

    if invalid_after:
        raise ValueError(
            f"{level} still contains invalid geometries after repair."
        )

    return prepared


# ---------------------------------------------------------------------------
# Spatial hierarchy
# ---------------------------------------------------------------------------


def assign_parents(
    children: gpd.GeoDataFrame,
    parents: gpd.GeoDataFrame,
    child_label: str,
    parent_label: str,
) -> list[ParentAssignment]:
    """
    Assign every child to the parent with the greatest intersection area.

    A spatial index first identifies potentially intersecting parents. Exact
    intersections are then measured in an equal-area projection. The overlap
    percentage represents the fraction of the child's area contained by its
    selected parent.
    """

    print()
    print(
        f"Assigning {child_label} -> {parent_label}..."
    )

    children_area = children.to_crs(
        AREA_CRS
    ).reset_index(drop=True)

    parents_area = parents.to_crs(
        AREA_CRS
    ).reset_index(drop=True)

    parent_spatial_index = parents_area.sindex

    assignments: list[ParentAssignment] = []

    for child_index, child_row in children_area.iterrows():
        child_geometry = child_row.geometry
        child_area = child_geometry.area

        if child_area <= 0:
            raise ValueError(
                f"{child_label} feature {child_index} has zero area."
            )

        candidate_indices = list(
            parent_spatial_index.query(
                child_geometry,
                predicate="intersects",
            )
        )

        if not candidate_indices:
            raise ValueError(
                f"No intersecting {parent_label} found for "
                f"{child_label} feature {child_index}."
            )

        best_parent_index: int | None = None
        best_intersection_area = -1.0

        for parent_index in candidate_indices:
            parent_geometry = parents_area.iloc[
                parent_index
            ].geometry

            intersection_area = child_geometry.intersection(
                parent_geometry
            ).area

            if intersection_area > best_intersection_area:
                best_intersection_area = intersection_area
                best_parent_index = int(parent_index)

        if best_parent_index is None:
            raise ValueError(
                f"Could not determine a {parent_label} for "
                f"{child_label} feature {child_index}."
            )

        overlap_percent = (
            best_intersection_area
            / child_area
            * 100.0
        )

        assignments.append(
            ParentAssignment(
                child_index=int(child_index),
                parent_index=best_parent_index,
                overlap_percent=overlap_percent,
            )
        )

    return assignments


# ---------------------------------------------------------------------------
# Hierarchy reporting
# ---------------------------------------------------------------------------


def print_assignment_report(
    assignments: list[ParentAssignment],
    children: gpd.GeoDataFrame,
    parents: gpd.GeoDataFrame,
    child_name_property: str,
    parent_name_property: str,
    child_label: str,
    parent_label: str,
) -> None:
    """
    Print overlap-quality statistics and all unusually low-overlap assignments.

    Parent selection always uses the parent with the greatest intersection area.
    Assignments below the review threshold are surfaced only as a diagnostic and
    do not change the selected hierarchy.
    """

    overlap_values = [
        assignment.overlap_percent
        for assignment in assignments
    ]

    at_least_99 = sum(
        value >= 99.0
        for value in overlap_values
    )

    between_95_and_99 = sum(
        95.0 <= value < 99.0
        for value in overlap_values
    )

    below_95 = sum(
        value < 95.0
        for value in overlap_values
    )

    print()
    print(
        f"{child_label} -> {parent_label} hierarchy:"
    )
    print(
        f"  Assigned: {len(assignments):,} / {len(children):,}"
    )
    print(
        f"  >= 99% overlap: {at_least_99:,}"
    )
    print(
        f"  95-99% overlap: {between_95_and_99:,}"
    )
    print(
        f"  < 95% overlap: {below_95:,}"
    )
    print(
        f"  Minimum overlap: {min(overlap_values):.2f}%"
    )

    review_assignments = [
        assignment
        for assignment in assignments
        if assignment.overlap_percent < REVIEW_OVERLAP_PERCENT
    ]

    if not review_assignments:
        print(
            f"  Review cases: none"
        )
        return

    print()
    print(
        f"  Review cases (< {REVIEW_OVERLAP_PERCENT:.0f}%):"
    )

    for assignment in sorted(
        review_assignments,
        key=lambda item: item.overlap_percent,
    ):
        child_name = children.iloc[
            assignment.child_index
        ][child_name_property]

        parent_name = parents.iloc[
            assignment.parent_index
        ][parent_name_property]

        print(
            f"    {child_name} -> {parent_name}: "
            f"{assignment.overlap_percent:.2f}%"
        )


# ---------------------------------------------------------------------------
# Canonical GeoPedia frames
# ---------------------------------------------------------------------------


def build_states(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Build GeoPedia's canonical Malaysian ADM1 dataset.

    ISO 3166-2 shapeISO values become state IDs while source names and
    geometries are preserved.
    """

    result = gpd.GeoDataFrame(
        {
            "state_id": source["shapeISO"].astype(str),
            "state": source["shapeName"].astype(str),
        },
        geometry=source.geometry.copy(),
        crs=source.crs,
    )

    return result


def build_districts(
    source: gpd.GeoDataFrame,
    states: gpd.GeoDataFrame,
    assignments: list[ParentAssignment],
) -> gpd.GeoDataFrame:
    """
    Build GeoPedia's canonical Malaysian ADM2 dataset.

    geoBoundaries shapeID values become district IDs and the spatially derived
    ADM1 state relationship is stored directly on every district.
    """

    state_ids: list[str] = []
    state_names: list[str] = []

    for assignment in assignments:
        parent = states.iloc[
            assignment.parent_index
        ]

        state_ids.append(
            str(parent["state_id"])
        )
        state_names.append(
            str(parent["state"])
        )

    return gpd.GeoDataFrame(
        {
            "district_id": source["shapeID"].astype(str),
            "district": source["shapeName"].astype(str),
            "state_id": state_ids,
            "state": state_names,
        },
        geometry=source.geometry.copy(),
        crs=source.crs,
    )


def build_sub_districts(
    source: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
    assignments: list[ParentAssignment],
) -> gpd.GeoDataFrame:
    """
    Build GeoPedia's canonical Malaysian ADM3 dataset.

    geoBoundaries shapeID values become sub-district IDs. District and state
    hierarchy fields are inherited from the selected ADM2 parent.
    """

    district_ids: list[str] = []
    district_names: list[str] = []
    state_ids: list[str] = []
    state_names: list[str] = []

    for assignment in assignments:
        parent = districts.iloc[
            assignment.parent_index
        ]

        district_ids.append(
            str(parent["district_id"])
        )
        district_names.append(
            str(parent["district"])
        )
        state_ids.append(
            str(parent["state_id"])
        )
        state_names.append(
            str(parent["state"])
        )

    return gpd.GeoDataFrame(
        {
            "sub_district_id": source["shapeID"].astype(str),
            "sub_district": source["shapeName"].astype(str),
            "district_id": district_ids,
            "district": district_names,
            "state_id": state_ids,
            "state": state_names,
        },
        geometry=source.geometry.copy(),
        crs=source.crs,
    )


# ---------------------------------------------------------------------------
# Final validation
# ---------------------------------------------------------------------------


def validate_output(
    frame: gpd.GeoDataFrame,
    expected_count: int,
    id_property: str,
    name_property: str,
    label: str,
) -> None:
    """Validate one canonical administrative output before writing it."""

    if len(frame) != expected_count:
        raise ValueError(
            f"{label} output contains {len(frame):,} features; "
            f"expected {expected_count:,}."
        )

    if frame[id_property].isna().any():
        raise ValueError(
            f"{label} contains missing {id_property} values."
        )

    if frame[name_property].isna().any():
        raise ValueError(
            f"{label} contains missing {name_property} values."
        )

    if frame[id_property].duplicated().any():
        raise ValueError(
            f"{label} contains duplicate {id_property} values."
        )

    if frame[name_property].duplicated().any():
        raise ValueError(
            f"{label} contains duplicate {name_property} values."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            f"{label} contains missing geometries."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            f"{label} contains empty geometries."
        )


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def write_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """
    Write a canonical GeoJSON file without GeoPandas' auxiliary index fields.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # GeoDataFrame.to_file can introduce driver-dependent formatting and is
    # unnecessary here. to_json gives us a compact, predictable GeoJSON object.
    geojson: dict[str, Any] = json.loads(
        frame.to_json(
            drop_id=True,
        )
    )

    path.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Process and validate Malaysia's administrative hierarchy."""

    print()
    print("Processing Malaysia administrative boundaries...")
    print()

    # -----------------------------------------------------------------------
    # Load
    # -----------------------------------------------------------------------

    raw_states = load_admin_file(
        ADM1_PATH,
        "ADM1",
    )

    raw_districts = load_admin_file(
        ADM2_PATH,
        "ADM2",
    )

    raw_sub_districts = load_admin_file(
        ADM3_PATH,
        "ADM3",
    )

    validate_state_iso_codes(
        raw_states
    )

    print("Source features:")
    print(
        f"  ADM1: {len(raw_states):,}"
    )
    print(
        f"  ADM2: {len(raw_districts):,}"
    )
    print(
        f"  ADM3: {len(raw_sub_districts):,}"
    )

    # -----------------------------------------------------------------------
    # Geometry preparation
    # -----------------------------------------------------------------------

    print()
    print("Preparing geometry...")

    raw_states = prepare_geometry(
        raw_states,
        "ADM1",
    )

    raw_districts = prepare_geometry(
        raw_districts,
        "ADM2",
    )

    raw_sub_districts = prepare_geometry(
        raw_sub_districts,
        "ADM3",
    )

    # -----------------------------------------------------------------------
    # ADM1
    # -----------------------------------------------------------------------

    states = build_states(
        raw_states
    )

    # -----------------------------------------------------------------------
    # ADM2 -> ADM1
    # -----------------------------------------------------------------------

    district_assignments = assign_parents(
        raw_districts,
        raw_states,
        "ADM2",
        "ADM1",
    )

    print_assignment_report(
        assignments=district_assignments,
        children=raw_districts,
        parents=raw_states,
        child_name_property="shapeName",
        parent_name_property="shapeName",
        child_label="ADM2",
        parent_label="ADM1",
    )

    districts = build_districts(
        raw_districts,
        states,
        district_assignments,
    )

    # -----------------------------------------------------------------------
    # ADM3 -> ADM2
    # -----------------------------------------------------------------------

    sub_district_assignments = assign_parents(
        raw_sub_districts,
        raw_districts,
        "ADM3",
        "ADM2",
    )

    print_assignment_report(
        assignments=sub_district_assignments,
        children=raw_sub_districts,
        parents=raw_districts,
        child_name_property="shapeName",
        parent_name_property="shapeName",
        child_label="ADM3",
        parent_label="ADM2",
    )

    sub_districts = build_sub_districts(
        raw_sub_districts,
        districts,
        sub_district_assignments,
    )

    # -----------------------------------------------------------------------
    # Validate
    # -----------------------------------------------------------------------

    print()
    print("Validating canonical outputs...")

    validate_output(
        states,
        EXPECTED_COUNTS["ADM1"],
        "state_id",
        "state",
        "States",
    )

    validate_output(
        districts,
        EXPECTED_COUNTS["ADM2"],
        "district_id",
        "district",
        "Districts",
    )

    validate_output(
        sub_districts,
        EXPECTED_COUNTS["ADM3"],
        "sub_district_id",
        "sub_district",
        "Sub-Districts",
    )

    print("  States: passed")
    print("  Districts: passed")
    print("  Sub-Districts: passed")

    # -----------------------------------------------------------------------
    # Write
    # -----------------------------------------------------------------------

    print()
    print("Writing intermediate GeoJSON...")

    write_geojson(
        states,
        STATES_OUTPUT_PATH,
    )

    write_geojson(
        districts,
        DISTRICTS_OUTPUT_PATH,
    )

    write_geojson(
        sub_districts,
        SUB_DISTRICTS_OUTPUT_PATH,
    )

    print(
        "  "
        + str(
            STATES_OUTPUT_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print(
        "  "
        + str(
            DISTRICTS_OUTPUT_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print(
        "  "
        + str(
            SUB_DISTRICTS_OUTPUT_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print("Malaysia administrative hierarchy processing complete.")


if __name__ == "__main__":
    main()
"""
Process raw U.S. telephone area-code geography for GeoPedia.

Source:
    data/raw/countries/usa/area-codes.geojson

Output:
    public/data/countries/usa/geojson/area-codes-new.geojson

The raw ArcGIS dataset contains one polygon or multipolygon per telephone area
code. Overlay area codes therefore appear as separate source features whose
geometries may be identical, nested, or partially overlapping.

This processor converts that overlapping source geography into non-overlapping
quiz geography:

1. Validates and repairs the raw ArcGIS geometries.
2. Builds one combined boundary network from all source area-code polygons.
3. Polygonizes that network into atomic, non-overlapping geographic cells.
4. Determines every raw area-code feature covering each atomic cell.
5. Assigns the complete area-code and state set to that cell.
6. Merges cells only when their complete answer and state sets are identical.
7. Validates that all source area codes remain represented and that final
   features do not overlap by positive area.

No geometry simplification is performed here yet. The first goal is to produce
authoritative, topology-correct quiz geography directly from the unsimplified
raw source. Topology-safe simplification can be added after the generated
geography has been visually validated.
"""

from collections import defaultdict
from pathlib import Path

import geopandas as gpd
from shapely import coverage_simplify, get_num_coordinates, make_valid
from shapely.geometry import (
    GeometryCollection,
    MultiLineString,
    MultiPolygon,
    Polygon,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, unary_union


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FILE = Path(
    "data/raw/countries/usa/area-codes.geojson"
)

OUTPUT_FILE = Path(
    "public/data/countries/usa/geojson/area-codes-new.geojson"
)

# Positive-area intersections larger than this are treated as true overlaps
# during final validation. Shared borders and point contacts are allowed.
OVERLAP_AREA_TOLERANCE = 1e-12

# Topology-preserving simplification tolerance in degrees.
#
# Simplification happens only after the raw overlapping source has been
# converted into final non-overlapping semantic regions. coverage_simplify()
# simplifies shared boundaries together so neighboring quiz regions continue
# to use exactly the same border.
SIMPLIFY_TOLERANCE = 0.01


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------


def area_code_sort_key(
    area_code: str,
) -> tuple[int, int | str]:
    """Return a deterministic sort key for telephone area-code strings."""
    try:
        return (0, int(area_code))

    except ValueError:
        return (1, area_code)


def polygonal_only(
    geometry: BaseGeometry,
) -> BaseGeometry:
    """
    Return only polygonal components from a geometry.

    make_valid() can occasionally return GeometryCollections containing lines
    or points in addition to the repaired polygonal components. Those
    lower-dimensional pieces are not relevant to MapLibre fill geography.
    """
    if geometry is None or geometry.is_empty:
        return GeometryCollection()

    if isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        return geometry

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            polygonal = polygonal_only(
                part
            )

            if isinstance(
                polygonal,
                Polygon,
            ):
                polygons.append(
                    polygonal
                )

            elif isinstance(
                polygonal,
                MultiPolygon,
            ):
                polygons.extend(
                    polygonal.geoms
                )

        if not polygons:
            return GeometryCollection()

        return unary_union(
            polygons
        )

    return GeometryCollection()


def get_line_parts(
    geometry: BaseGeometry,
) -> list[BaseGeometry]:
    """Flatten combined boundary linework into parts usable by polygonize()."""
    if geometry.is_empty:
        return []

    if geometry.geom_type == "LineString":
        return [
            geometry
        ]

    if isinstance(
        geometry,
        MultiLineString,
    ):
        return list(
            geometry.geoms
        )

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        parts: list[BaseGeometry] = []

        for part in geometry.geoms:
            parts.extend(
                get_line_parts(part)
            )

        return parts

    raise ValueError(
        "Combined boundary linework produced unsupported geometry type "
        f"{geometry.geom_type}."
    )


def normalize_area_code(
    value: object,
    feature_id: str,
) -> str:
    """Normalize and validate one raw ArcGIS AREA_CODE value."""
    if value is None:
        raise ValueError(
            f"Raw feature {feature_id} has no AREA_CODE."
        )

    area_code = str(
        value
    ).strip()

    if not area_code:
        raise ValueError(
            f"Raw feature {feature_id} has a blank AREA_CODE."
        )

    if not area_code.isdigit():
        raise ValueError(
            f"Raw feature {feature_id} has non-numeric AREA_CODE "
            f"{area_code!r}."
        )

    if len(area_code) != 3:
        raise ValueError(
            f"Raw feature {feature_id} has AREA_CODE {area_code!r}; "
            "expected exactly three digits."
        )

    return area_code


def normalize_state(
    value: object,
    feature_id: str,
) -> str:
    """Normalize and validate one raw ArcGIS STATE abbreviation."""
    if value is None:
        raise ValueError(
            f"Raw feature {feature_id} has no STATE."
        )

    state = str(
        value
    ).strip().upper()

    if not state:
        raise ValueError(
            f"Raw feature {feature_id} has a blank STATE."
        )

    return state

def simplify_output_coverage(
    output: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Simplify final area-code geography while preserving shared topology.

    The output regions already form non-overlapping quiz geography with their
    complete answer sets resolved. Shapely's coverage simplifier processes
    shared edges together, preventing neighboring features from independently
    shifting away from one another and creating gaps, overlaps, or slivers.
    """
    print(
        f"Simplifying final coverage with tolerance "
        f"{SIMPLIFY_TOLERANCE}..."
    )

    coordinates_before = sum(
        get_num_coordinates(geometry)
        for geometry
        in output.geometry
    )

    simplified_geometries = coverage_simplify(
        output.geometry.to_numpy(),
        tolerance=SIMPLIFY_TOLERANCE,
        simplify_boundary=True,
    )

    simplified = output.copy()

    simplified.geometry = gpd.GeoSeries(
        simplified_geometries,
        index=output.index,
        crs=output.crs,
    )

    coordinates_after = sum(
        get_num_coordinates(geometry)
        for geometry
        in simplified.geometry
    )

    reduction = (
        1
        - coordinates_after
        / coordinates_before
    ) * 100

    print(
        f"Coordinates before: "
        f"{coordinates_before:,}"
    )

    print(
        f"Coordinates after:  "
        f"{coordinates_after:,}"
    )

    print(
        f"Coordinate reduction: "
        f"{reduction:.1f}%"
    )

    return simplified


# ---------------------------------------------------------------------------
# Source validation
# ---------------------------------------------------------------------------


def validate_and_normalize_source(
    source: gpd.GeoDataFrame,
) -> None:
    """
    Validate the ArcGIS source and repair invalid polygonal geometries.

    Normalized area-code and state values are written back to the GeoDataFrame
    so all later processing operates on canonical strings.
    """
    required_columns = {
        "OBJECTID",
        "AREA_CODE",
        "STATE",
        "geometry",
    }

    missing_columns = (
        required_columns
        - set(source.columns)
    )

    if missing_columns:
        raise ValueError(
            "Raw area-code source is missing required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    if source.empty:
        raise ValueError(
            "Raw area-code source contains no features."
        )

    if source.crs is None:
        raise ValueError(
            "Raw area-code source has no CRS."
        )

    if source.geometry.isna().any():
        raise ValueError(
            "Raw area-code source contains null geometries."
        )

    if source.geometry.is_empty.any():
        raise ValueError(
            "Raw area-code source contains empty geometries."
        )

    normalized_area_codes: list[str] = []
    normalized_states: list[str] = []

    for row in source.itertuples():
        feature_id = str(
            row.OBJECTID
        ).strip()

        normalized_area_codes.append(
            normalize_area_code(
                row.AREA_CODE,
                feature_id,
            )
        )

        normalized_states.append(
            normalize_state(
                row.STATE,
                feature_id,
            )
        )

    source["AREA_CODE"] = (
        normalized_area_codes
    )

    source["STATE"] = (
        normalized_states
    )

    if source["AREA_CODE"].duplicated().any():
        duplicates = sorted(
            source.loc[
                source["AREA_CODE"].duplicated(
                    keep=False
                ),
                "AREA_CODE",
            ].unique()
        )

        raise ValueError(
            "Raw source contains duplicate AREA_CODE values: "
            + ", ".join(
                duplicates
            )
        )

    invalid_mask = (
        ~source.geometry.is_valid
    )

    invalid_count = int(
        invalid_mask.sum()
    )

    if invalid_count:
        print(
            f"Source contains {invalid_count} invalid geometries. "
            "Repairing them with make_valid()..."
        )

        repaired_geometries: list[
            BaseGeometry
        ] = []

        for row in source.itertuples():
            geometry = row.geometry

            if geometry.is_valid:
                repaired_geometries.append(
                    geometry
                )

                continue

            repaired = make_valid(
                geometry
            )

            repaired = polygonal_only(
                repaired
            )

            if repaired.is_empty:
                raise ValueError(
                    f"AREA_CODE {row.AREA_CODE} became empty "
                    "after make_valid()."
                )

            if not repaired.is_valid:
                raise ValueError(
                    f"AREA_CODE {row.AREA_CODE} is still invalid "
                    "after make_valid()."
                )

            if not isinstance(
                repaired,
                (Polygon, MultiPolygon),
            ):
                raise ValueError(
                    f"AREA_CODE {row.AREA_CODE} became unsupported geometry "
                    f"type {repaired.geom_type} after make_valid()."
                )

            repaired_geometries.append(
                repaired
            )

        source.geometry = (
            repaired_geometries
        )

        print(
            "Invalid source geometries repaired successfully."
        )

    invalid_types = set(
        source.geometry.geom_type.unique()
    ) - {
        "Polygon",
        "MultiPolygon",
    }

    if invalid_types:
        raise ValueError(
            "Raw source contains unsupported geometry types: "
            + ", ".join(
                sorted(
                    invalid_types
                )
            )
        )


def collect_source_area_codes(
    source: gpd.GeoDataFrame,
) -> set[str]:
    """Return every distinct area code represented by the raw source."""
    return set(
        source["AREA_CODE"]
        .astype(str)
        .str.strip()
    )


# ---------------------------------------------------------------------------
# Atomic geography
# ---------------------------------------------------------------------------


def build_atomic_cells(
    source: gpd.GeoDataFrame,
) -> list[Polygon]:
    """
    Cut all raw area-code boundaries into non-overlapping atomic cells.

    Combining all boundaries before polygonization ensures shared and
    intersecting boundaries are noded together consistently.
    """
    print(
        "Building combined raw boundary linework..."
    )

    boundaries = [
        geometry.boundary
        for geometry
        in source.geometry
    ]

    linework = unary_union(
        boundaries
    )

    line_parts = get_line_parts(
        linework
    )

    print(
        f"Boundary line parts: "
        f"{len(line_parts):,}"
    )

    print(
        "Polygonizing raw boundary network..."
    )

    cells = [
        polygon
        for polygon
        in polygonize(
            line_parts
        )
        if not polygon.is_empty
        and polygon.area > 0
    ]

    print(
        f"Polygonized cells: "
        f"{len(cells):,}"
    )

    if not cells:
        raise ValueError(
            "Raw boundary polygonization produced no cells."
        )

    return cells


def classify_atomic_cells(
    source: gpd.GeoDataFrame,
    cells: list[Polygon],
) -> dict[
    tuple[
        tuple[str, ...],
        tuple[str, ...],
    ],
    list[Polygon],
]:
    """
    Determine the complete area-code and state set covering every atomic cell.

    Unlike the repair processor, this function applies no overlap-ratio
    heuristic. These cells come directly from the unsimplified ArcGIS source,
    so every raw feature genuinely covering the cell contributes its area code.
    """
    groups: dict[
        tuple[
            tuple[str, ...],
            tuple[str, ...],
        ],
        list[Polygon],
    ] = defaultdict(
        list
    )

    spatial_index = (
        source.sindex
    )

    skipped_uncovered = 0
    single_answer_cells = 0
    multi_answer_cells = 0

    for index, cell in enumerate(
        cells,
        start=1,
    ):
        # representative_point() is guaranteed to lie inside the cell and
        # avoids ambiguity from choosing a point directly on a boundary.
        point = (
            cell.representative_point()
        )

        candidate_indices = (
            spatial_index.query(
                point,
                predicate="intersects",
            )
        )

        covering_indices: list[int] = []

        for candidate_index in candidate_indices:
            source_index = int(
                candidate_index
            )

            geometry = source.iloc[
                source_index
            ].geometry

            if geometry.covers(
                point
            ):
                covering_indices.append(
                    source_index
                )

        # Polygonization may also produce polygons enclosed by boundary
        # linework but lying inside source holes. Those do not belong to any
        # telephone area-code region and should not enter the output.
        if not covering_indices:
            skipped_uncovered += 1
            continue

        area_codes = {
            str(
                source.iloc[
                    source_index
                ]["AREA_CODE"]
            ).strip()
            for source_index
            in covering_indices
        }

        states = {
            str(
                source.iloc[
                    source_index
                ]["STATE"]
            ).strip()
            for source_index
            in covering_indices
        }

        if not area_codes:
            raise ValueError(
                f"Atomic cell {index} contains no area-code answers."
            )

        answer_key = tuple(
            sorted(
                area_codes,
                key=area_code_sort_key,
            )
        )

        state_key = tuple(
            sorted(
                states
            )
        )

        groups[
            (
                answer_key,
                state_key,
            )
        ].append(
            cell
        )

        if len(
            answer_key
        ) == 1:
            single_answer_cells += 1

        else:
            multi_answer_cells += 1

    covered_cells = (
        single_answer_cells
        + multi_answer_cells
    )

    print(
        f"Covered atomic cells: "
        f"{covered_cells:,}"
    )

    print(
        f"Uncovered/hole cells skipped: "
        f"{skipped_uncovered:,}"
    )

    print(
        f"Single-answer cells: "
        f"{single_answer_cells:,}"
    )

    print(
        f"Multi-answer cells: "
        f"{multi_answer_cells:,}"
    )

    print(
        f"Distinct answer/state sets: "
        f"{len(groups):,}"
    )

    return groups


# ---------------------------------------------------------------------------
# Region construction
# ---------------------------------------------------------------------------


def merge_group(
    geometries: list[Polygon],
    area_codes: tuple[str, ...],
) -> BaseGeometry:
    """Merge atomic cells sharing one complete set of quiz answers."""
    geometry = unary_union(
        geometries
    )

    geometry = polygonal_only(
        geometry
    )

    if geometry.is_empty:
        raise ValueError(
            f"Area-code set {area_codes} produced an empty geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Area-code set {area_codes} produced an invalid geometry."
        )

    if not isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        raise ValueError(
            f"Area-code set {area_codes} produced unsupported geometry "
            f"type {geometry.geom_type}."
        )

    return geometry


def build_output_regions(
    groups: dict[
        tuple[
            tuple[str, ...],
            tuple[str, ...],
        ],
        list[Polygon],
    ],
    crs: object,
) -> gpd.GeoDataFrame:
    """
    Merge atomic cells with identical complete answer and state semantics.

    State membership remains part of the grouping key so GeoPedia's property
    filters can distinguish otherwise-identical answer sets belonging to
    different states or territories.
    """
    rows: list[dict] = []

    sorted_groups = sorted(
        groups.items(),
        key=lambda item: (
            area_code_sort_key(
                item[0][0][0]
            ),
            item[0][0],
            item[0][1],
        ),
    )

    id_counts: dict[
        str,
        int,
    ] = defaultdict(
        int
    )

    for (
        area_codes,
        states,
    ), geometries in sorted_groups:
        geometry = merge_group(
            geometries,
            area_codes,
        )

        base_id = "-".join(
            area_codes
        )

        id_counts[
            base_id
        ] += 1

        if id_counts[
            base_id
        ] == 1:
            region_id = (
                base_id
            )

        else:
            region_id = (
                f"{base_id}-"
                f"{id_counts[base_id]}"
            )

        rows.append(
            {
                "id": region_id,
                "area_codes": list(
                    area_codes
                ),
                "states": list(
                    states
                ),
                "geometry": geometry,
            }
        )

    return gpd.GeoDataFrame(
        rows,
        geometry="geometry",
        crs=crs,
    )


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------


def collect_output_area_codes(
    output: gpd.GeoDataFrame,
) -> set[str]:
    """Return every distinct area code represented by the final output."""
    area_codes: set[str] = set()

    for row in output.itertuples():
        for area_code in row.area_codes:
            area_codes.add(
                str(
                    area_code
                ).strip()
            )

    return area_codes


def validate_no_overlaps(
    output: gpd.GeoDataFrame,
) -> None:
    """
    Confirm that final output features do not overlap by positive area.

    Shared boundaries and point contacts are valid and are ignored.
    """
    print(
        "Checking output for overlapping features..."
    )

    spatial_index = (
        output.sindex
    )

    overlaps: list[
        tuple[
            str,
            str,
            float,
        ]
    ] = []

    for index, row in output.iterrows():
        candidate_indices = (
            spatial_index.query(
                row.geometry,
                predicate="intersects",
            )
        )

        for candidate_index in candidate_indices:
            candidate_index = int(
                candidate_index
            )

            if candidate_index <= index:
                continue

            other = output.iloc[
                candidate_index
            ]

            intersection = (
                row.geometry.intersection(
                    other.geometry
                )
            )

            if intersection.is_empty:
                continue

            overlap_area = (
                intersection.area
            )

            if (
                overlap_area
                > OVERLAP_AREA_TOLERANCE
            ):
                overlaps.append(
                    (
                        str(
                            row["id"]
                        ),
                        str(
                            other["id"]
                        ),
                        overlap_area,
                    )
                )

                if len(
                    overlaps
                ) >= 20:
                    break

        if len(
            overlaps
        ) >= 20:
            break

    if overlaps:
        print()
        print(
            "Detected positive-area overlaps:"
        )

        for (
            first_id,
            second_id,
            overlap_area,
        ) in overlaps:
            print(
                f"  {first_id} / "
                f"{second_id}: "
                f"{overlap_area:.12g}"
            )

        raise ValueError(
            "Processed area-code output still contains overlapping features."
        )

    print(
        "No positive-area overlaps detected."
    )


def validate_output(
    output: gpd.GeoDataFrame,
    source_area_codes: set[str],
) -> None:
    """Validate final topology and preservation of all source answers."""
    if output.empty:
        raise ValueError(
            "Processed area-code output contains no features."
        )

    if output["id"].duplicated().any():
        raise ValueError(
            "Processed output contains duplicate feature IDs."
        )

    if output.geometry.isna().any():
        raise ValueError(
            "Processed output contains null geometries."
        )

    if output.geometry.is_empty.any():
        raise ValueError(
            "Processed output contains empty geometries."
        )

    if (
        ~output.geometry.is_valid
    ).any():
        invalid_count = int(
            (
                ~output.geometry.is_valid
            ).sum()
        )

        raise ValueError(
            f"Processed output contains "
            f"{invalid_count} invalid geometries."
        )

    invalid_types = set(
        output.geometry.geom_type.unique()
    ) - {
        "Polygon",
        "MultiPolygon",
    }

    if invalid_types:
        raise ValueError(
            "Processed output contains unsupported geometry types: "
            + ", ".join(
                sorted(
                    invalid_types
                )
            )
        )

    output_area_codes = (
        collect_output_area_codes(
            output
        )
    )

    missing_area_codes = (
        source_area_codes
        - output_area_codes
    )

    added_area_codes = (
        output_area_codes
        - source_area_codes
    )

    if (
        missing_area_codes
        or added_area_codes
    ):
        raise ValueError(
            "Area-code answer set changed during processing. "
            f"Missing: "
            f"{sorted(missing_area_codes)}; "
            f"added: "
            f"{sorted(added_area_codes)}."
        )

    print(
        f"All {len(source_area_codes):,} source area codes "
        "are represented in the output."
    )

    validate_no_overlaps(
        output
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_multi_answer_regions(
    output: gpd.GeoDataFrame,
) -> None:
    """Print all final regions containing multiple valid area-code answers."""
    rows: list[
        tuple[
            tuple[str, ...],
            tuple[str, ...],
        ]
    ] = []

    for row in output.itertuples():
        area_codes = tuple(
            str(
                area_code
            )
            for area_code
            in row.area_codes
        )

        states = tuple(
            str(
                state
            )
            for state
            in row.states
        )

        if len(
            area_codes
        ) > 1:
            rows.append(
                (
                    area_codes,
                    states,
                )
            )

    rows.sort(
        key=lambda item: (
            area_code_sort_key(
                item[0][0]
            ),
            item[0],
            item[1],
        )
    )

    print(
        f"Multi-answer features: "
        f"{len(rows):,}"
    )

    if not rows:
        return

    print()
    print(
        "Multi-answer regions:"
    )

    for (
        area_codes,
        states,
    ) in rows:
        print(
            "  "
            + " / ".join(
                area_codes
            )
            + " | "
            + ", ".join(
                states
            )
        )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_geojson(
    output: gpd.GeoDataFrame,
) -> None:
    """Write compact UTF-8 GeoJSON without modifying the current runtime file."""
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = output.to_json(
        drop_id=True,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    )

    OUTPUT_FILE.write_text(
        geojson,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Build topology-correct U.S. area-code geography from the raw source."""
    print(
        "U.S. area-code processor"
    )

    print(
        "=" * 72
    )

    print(
        f"Source: {INPUT_FILE}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: "
            f"{INPUT_FILE}"
        )

    print(
        "Reading raw ArcGIS area-code GeoJSON..."
    )

    source = gpd.read_file(
        INPUT_FILE
    )

    validate_and_normalize_source(
        source
    )

    source_area_codes = (
        collect_source_area_codes(
            source
        )
    )

    print(
        f"Source features: "
        f"{len(source):,}"
    )

    print(
        f"Distinct area codes: "
        f"{len(source_area_codes):,}"
    )

    print(
        "Source geometry types:"
    )

    for (
        geometry_type,
        count,
    ) in (
        source.geometry
        .geom_type
        .value_counts()
        .items()
    ):
        print(
            f"  {geometry_type}: "
            f"{count:,}"
        )

    print()

    cells = build_atomic_cells(
        source
    )

    print()

    groups = classify_atomic_cells(
        source,
        cells,
    )

    print()
    print(
        "Merging cells with identical complete answer sets..."
    )

    output = build_output_regions(
        groups,
        source.crs,
    )

    print(
        f"Processed features: "
        f"{len(output):,}"
    )

    print()
    
    output = simplify_output_coverage(
        output
    )

    print()

    validate_output(
        output,
        source_area_codes,
    )

    print()

    print_multi_answer_regions(
        output
    )

    print()
    print(
        "Writing processed GeoJSON..."
    )

    write_geojson(
        output
    )

    output_size = (
        OUTPUT_FILE.stat().st_size
    )

    print()
    print(
        f"Output size: "
        f"{output_size / 1024 / 1024:.2f} MB "
        f"({output_size:,} bytes)"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print()

    print(
        "Done. The existing runtime area-codes.geojson "
        "was not modified."
    )


if __name__ == "__main__":
    main()
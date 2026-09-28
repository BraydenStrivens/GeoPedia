"""Inspect Puerto Rico barrio boundaries and their municipality relationships.

This script compares GeoBoundaries ADM3 barrio polygons against GeoPedia's
processed Puerto Rico municipality polygons and a Census-derived barrio
reference dataset.

For each GeoBoundaries barrio, it measures how much of the barrio's area
overlaps each municipality and assigns the barrio to the municipality with the
largest overlap.

The Census-derived dataset is used only as a reference for validating barrio
names and municipality membership. It is not used as a geometry source.

The script is diagnostic only. It does not write or modify runtime data.

Reports include:
    - Source feature and geometry counts.
    - Municipality feature counts.
    - Barrio-to-municipality assignment quality.
    - Barrio counts per municipality.
    - Duplicate barrio names.
    - Duplicate (municipality, barrio name) pairs.
    - Census-derived barrio record counts.
    - Exact GeoBoundaries/Census municipality-name matches.
    - Census-only barrio records.
    - GeoBoundaries-only barrio records.
    - Duplicate-key differences between the two datasets.

Area calculations use WGS 84 / UTM zone 20N (EPSG:32620), which is suitable
for Puerto Rico and avoids performing area calculations in geographic
latitude/longitude coordinates.
"""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

BARRIOS_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "puerto-rico"
    / "geoBoundaries-PRI-ADM3-all"
    / "geoBoundaries-PRI-ADM3.geojson"
)

CENSUS_BARRIOS_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "puerto-rico"
    / "barrios"
    / "barrios-data.json"
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

EXPECTED_GEBOUNDARIES_BARRIO_COUNT = 901
EXPECTED_MUNICIPALITY_COUNT = 78
EXPECTED_CENSUS_NAMED_BARRIO_COUNT = 902

AREA_CRS = "EPSG:32620"

MATERIAL_OVERLAP_SHARE = 0.001
STRONG_ASSIGNMENT_SHARE = 0.95

CENSUS_UNDEFINED_PREFIX = "Municipio subdivision not defined,"


def format_percent(value: float) -> str:
    """Format a fractional value as a percentage with four decimal places."""
    return f"{value * 100:.4f}%"


def normalize_text(value: str) -> str:
    """Normalize text for case-insensitive cross-dataset comparison."""
    normalized = unicodedata.normalize("NFC", value)
    normalized = re.sub(r"\s+", " ", normalized.strip())
    return normalized.casefold()


def normalize_barrio_name(value: str) -> str:
    """Normalize barrio names while removing Census classification suffixes."""
    name = value.strip()

    lowered = name.casefold()

    if lowered.endswith(" barrio-pueblo"):
        name = name[: -len(" barrio-pueblo")]
    elif lowered.endswith(" barrio"):
        name = name[: -len(" barrio")]

    return normalize_text(name)


def parse_census_barrio_label(label: str) -> tuple[str, str]:
    """Parse a Census-derived barrio label into barrio and municipality names.

    Expected examples:
        "Capáez barrio, Adjuntas Municipio, Puerto Rico"
        "Adjuntas barrio-pueblo, Adjuntas Municipio, Puerto Rico"

    Returns:
        Tuple of:
            barrio name without barrio/barrio-pueblo suffix,
            municipality name without Municipio suffix.
    """
    parts = [part.strip() for part in label.split(",")]

    if len(parts) < 3:
        raise ValueError(f"Unexpected Census barrio label: {label}")

    barrio_part = parts[0]
    municipality_part = parts[1]

    if municipality_part.endswith(" Municipio"):
        municipality_name = municipality_part[: -len(" Municipio")]
    else:
        raise ValueError(
            f"Unexpected Census municipality label: {municipality_part}"
        )

    if barrio_part.casefold().endswith(" barrio-pueblo"):
        barrio_name = barrio_part[: -len(" barrio-pueblo")]
    elif barrio_part.casefold().endswith(" barrio"):
        barrio_name = barrio_part[: -len(" barrio")]
    else:
        barrio_name = barrio_part

    return barrio_name.strip(), municipality_name.strip()


def extract_municipality_id_from_census_geo_id(geo_id: str) -> str:
    """Extract the five-digit Puerto Rico municipality GEOID from Census GEOID.

    Example:
        0600000US7200100401 -> 72001
    """
    match = re.search(r"US(72\d{3})", geo_id)

    if not match:
        raise ValueError(
            f"Could not extract municipality GEOID from Census geo_id: {geo_id}"
        )

    return match.group(1)


def inspect_sources(
    barrios: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> None:
    """Print basic validation and geometry information for both datasets."""
    print("SOURCE SUMMARY")
    print("=" * 80)

    print(f"Barrio source: {BARRIOS_PATH}")
    print(f"Barrio features: {len(barrios)}")
    print(f"Barrio CRS: {barrios.crs}")
    print(
        "Barrio geometry types:",
        dict(Counter(barrios.geometry.geom_type)),
    )
    print(f"Barrio invalid geometries: {(~barrios.geometry.is_valid).sum()}")
    print(f"Barrio empty geometries: {barrios.geometry.is_empty.sum()}")
    print(f"Barrio null geometries: {barrios.geometry.isna().sum()}")

    print()

    print(f"Municipality source: {MUNICIPALITIES_PATH}")
    print(f"Municipality features: {len(municipalities)}")
    print(f"Municipality CRS: {municipalities.crs}")
    print(
        "Municipality geometry types:",
        dict(Counter(municipalities.geometry.geom_type)),
    )
    print(
        "Municipality invalid geometries:",
        (~municipalities.geometry.is_valid).sum(),
    )
    print(
        "Municipality empty geometries:",
        municipalities.geometry.is_empty.sum(),
    )
    print(
        "Municipality null geometries:",
        municipalities.geometry.isna().sum(),
    )

    print()


def validate_sources(
    barrios: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> None:
    """Validate the fields and basic structure required by the inspector."""
    if len(barrios) != EXPECTED_GEBOUNDARIES_BARRIO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_GEBOUNDARIES_BARRIO_COUNT} GeoBoundaries "
            f"barrio features, found {len(barrios)}."
        )

    if len(municipalities) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(municipalities)}."
        )

    required_barrio_columns = {"shapeName", "shapeID", "geometry"}
    missing_barrio_columns = required_barrio_columns - set(barrios.columns)

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

    if barrios["shapeID"].duplicated().any():
        duplicates = sorted(
            barrios.loc[
                barrios["shapeID"].duplicated(keep=False),
                "shapeID",
            ].astype(str)
        )
        raise ValueError(f"Duplicate GeoBoundaries shapeIDs: {duplicates}")

    if municipalities["municipality_id"].duplicated().any():
        duplicates = sorted(
            municipalities.loc[
                municipalities["municipality_id"].duplicated(keep=False),
                "municipality_id",
            ].astype(str)
        )
        raise ValueError(f"Duplicate municipality IDs: {duplicates}")


def load_census_barrio_records() -> list[dict]:
    """Load and normalize Census-derived Puerto Rico barrio reference records."""
    print(f"Reading Census barrio reference from {CENSUS_BARRIOS_PATH}")

    with CENSUS_BARRIOS_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Census barrio reference must be a JSON array.")

    records: list[dict] = []
    skipped_header_rows = 0
    undefined_records = 0

    for row in data:
        if not isinstance(row, dict):
            continue

        geo_id = row.get("geo_id")
        barrio_label = row.get("barrio")

        if geo_id == "Code" and barrio_label == "Barrio":
            skipped_header_rows += 1
            continue

        if not isinstance(geo_id, str) or not isinstance(barrio_label, str):
            continue

        if barrio_label.startswith(CENSUS_UNDEFINED_PREFIX):
            undefined_records += 1
            continue

        barrio_name, municipality_name = parse_census_barrio_label(
            barrio_label
        )

        municipality_id = extract_municipality_id_from_census_geo_id(
            geo_id
        )

        records.append(
            {
                "geo_id": geo_id,
                "raw_label": barrio_label,
                "barrio_name": barrio_name,
                "municipality_name": municipality_name,
                "municipality_id": municipality_id,
                "normalized_barrio_name": normalize_barrio_name(
                    barrio_name
                ),
                "normalized_municipality_name": normalize_text(
                    municipality_name
                ),
                "is_barrio_pueblo": " barrio-pueblo" in barrio_label.casefold(),
            }
        )

    print()
    print("CENSUS BARRIO REFERENCE SUMMARY")
    print("=" * 80)
    print(f"Raw rows: {len(data)}")
    print(f"Header-like rows skipped: {skipped_header_rows}")
    print(f"Undefined subdivision records skipped: {undefined_records}")
    print(f"Named barrio records: {len(records)}")

    if len(records) != EXPECTED_CENSUS_NAMED_BARRIO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CENSUS_NAMED_BARRIO_COUNT} named Census "
            f"barrio records, found {len(records)}."
        )

    return records


def calculate_assignments(
    barrios: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> list[dict]:
    """Calculate municipality overlap shares and assign every barrio."""
    barrios_projected = barrios.to_crs(AREA_CRS).copy()
    municipalities_projected = municipalities.to_crs(AREA_CRS).copy()

    municipality_records = [
        {
            "municipality_id": str(row.municipality_id),
            "municipality_name": str(row.name),
            "geometry": row.geometry,
        }
        for row in municipalities_projected.itertuples(index=False)
    ]

    assignments: list[dict] = []

    for index, barrio in enumerate(
        barrios_projected.itertuples(index=False),
        start=1,
    ):
        barrio_name = str(barrio.shapeName).strip()
        barrio_id = str(barrio.shapeID)
        barrio_geometry = barrio.geometry
        barrio_area = barrio_geometry.area

        if barrio_area <= 0:
            raise ValueError(
                f"Barrio {barrio_id} ({barrio_name}) has zero area."
            )

        overlaps = []

        for municipality in municipality_records:
            municipality_geometry = municipality["geometry"]

            if not barrio_geometry.intersects(municipality_geometry):
                continue

            intersection_area = barrio_geometry.intersection(
                municipality_geometry
            ).area

            if intersection_area <= 0:
                continue

            share = intersection_area / barrio_area

            overlaps.append(
                {
                    "municipality_id": municipality["municipality_id"],
                    "municipality_name": municipality["municipality_name"],
                    "area": intersection_area,
                    "share": share,
                }
            )

        overlaps.sort(
            key=lambda overlap: overlap["area"],
            reverse=True,
        )

        material_overlaps = [
            overlap
            for overlap in overlaps
            if overlap["share"] >= MATERIAL_OVERLAP_SHARE
        ]

        total_covered_share = sum(
            overlap["share"]
            for overlap in overlaps
        )

        if overlaps:
            best = overlaps[0]

            assignment = {
                "barrio_id": barrio_id,
                "barrio_name": barrio_name,
                "normalized_barrio_name": normalize_barrio_name(
                    barrio_name
                ),
                "municipality_id": best["municipality_id"],
                "municipality_name": best["municipality_name"],
                "normalized_municipality_name": normalize_text(
                    best["municipality_name"]
                ),
                "assignment_share": best["share"],
                "total_covered_share": total_covered_share,
                "overlaps": overlaps,
                "material_overlaps": material_overlaps,
            }
        else:
            assignment = {
                "barrio_id": barrio_id,
                "barrio_name": barrio_name,
                "normalized_barrio_name": normalize_barrio_name(
                    barrio_name
                ),
                "municipality_id": None,
                "municipality_name": None,
                "normalized_municipality_name": None,
                "assignment_share": 0.0,
                "total_covered_share": 0.0,
                "overlaps": [],
                "material_overlaps": [],
            }

        assignments.append(assignment)

        if index % 100 == 0 or index == len(barrios_projected):
            print(
                f"Processed {index}/{len(barrios_projected)} barrios..."
            )

    return assignments


def print_assignment_summary(assignments: list[dict]) -> None:
    """Print overall barrio-to-municipality assignment statistics."""
    assigned = [
        assignment
        for assignment in assignments
        if assignment["municipality_id"] is not None
    ]

    unassigned = [
        assignment
        for assignment in assignments
        if assignment["municipality_id"] is None
    ]

    exactly_one_positive_overlap = [
        assignment
        for assignment in assigned
        if len(assignment["overlaps"]) == 1
    ]

    multiple_positive_overlaps = [
        assignment
        for assignment in assigned
        if len(assignment["overlaps"]) > 1
    ]

    exactly_one_material_overlap = [
        assignment
        for assignment in assigned
        if len(assignment["material_overlaps"]) == 1
    ]

    multiple_material_overlaps = [
        assignment
        for assignment in assigned
        if len(assignment["material_overlaps"]) > 1
    ]

    strong_assignments = [
        assignment
        for assignment in assigned
        if assignment["assignment_share"] >= STRONG_ASSIGNMENT_SHARE
    ]

    low_confidence_assignments = [
        assignment
        for assignment in assigned
        if assignment["assignment_share"] < STRONG_ASSIGNMENT_SHARE
    ]

    print()
    print("ASSIGNMENT SUMMARY")
    print("=" * 80)
    print(f"Total barrios: {len(assignments)}")
    print(f"Assigned: {len(assigned)}")
    print(f"Unassigned: {len(unassigned)}")
    print()
    print(
        "Exactly one municipality with any positive overlap: "
        f"{len(exactly_one_positive_overlap)}"
    )
    print(
        "Multiple municipalities with any positive overlap: "
        f"{len(multiple_positive_overlaps)}"
    )
    print()
    print(
        f"Exactly one material overlap "
        f"(>= {format_percent(MATERIAL_OVERLAP_SHARE)}): "
        f"{len(exactly_one_material_overlap)}"
    )
    print(
        f"Multiple material overlaps "
        f"(>= {format_percent(MATERIAL_OVERLAP_SHARE)}): "
        f"{len(multiple_material_overlaps)}"
    )
    print()
    print(
        f"Strong assignments "
        f"(>= {format_percent(STRONG_ASSIGNMENT_SHARE)} in best municipality): "
        f"{len(strong_assignments)}"
    )
    print(
        f"Assignments below "
        f"{format_percent(STRONG_ASSIGNMENT_SHARE)}: "
        f"{len(low_confidence_assignments)}"
    )


def print_unassigned(assignments: list[dict]) -> None:
    """Print barrios that do not overlap any municipality polygon."""
    unassigned = [
        assignment
        for assignment in assignments
        if assignment["municipality_id"] is None
    ]

    print()
    print("UNASSIGNED BARRIOS")
    print("=" * 80)

    if not unassigned:
        print("None.")
        return

    for assignment in sorted(
        unassigned,
        key=lambda item: item["barrio_name"],
    ):
        print(
            f"{assignment['barrio_name']} "
            f"[{assignment['barrio_id']}]"
        )


def print_low_confidence_assignments(assignments: list[dict]) -> None:
    """Print assignments where the best municipality contains under 95%."""
    low_confidence = [
        assignment
        for assignment in assignments
        if assignment["municipality_id"] is not None
        and assignment["assignment_share"] < STRONG_ASSIGNMENT_SHARE
    ]

    print()
    print(
        "LOW-CONFIDENCE ASSIGNMENTS "
        f"(< {format_percent(STRONG_ASSIGNMENT_SHARE)})"
    )
    print("=" * 80)

    if not low_confidence:
        print("None.")
        return

    low_confidence.sort(
        key=lambda assignment: assignment["assignment_share"]
    )

    for assignment in low_confidence:
        print()
        print(
            f"{assignment['barrio_name']} "
            f"[{assignment['barrio_id']}]"
        )
        print(
            f"  Assigned: {assignment['municipality_name']} "
            f"({assignment['municipality_id']})"
        )
        print(
            "  Best overlap: "
            f"{format_percent(assignment['assignment_share'])}"
        )
        print(
            "  Total municipality coverage: "
            f"{format_percent(assignment['total_covered_share'])}"
        )

        print("  Overlaps:")

        for overlap in assignment["overlaps"]:
            print(
                f"    {overlap['municipality_name']} "
                f"({overlap['municipality_id']}): "
                f"{format_percent(overlap['share'])}"
            )


def print_multiple_material_overlaps(assignments: list[dict]) -> None:
    """Print barrios with meaningful overlap across multiple municipalities."""
    ambiguous = [
        assignment
        for assignment in assignments
        if len(assignment["material_overlaps"]) > 1
    ]

    print()
    print(
        "MULTIPLE MATERIAL MUNICIPALITY OVERLAPS "
        f"(>= {format_percent(MATERIAL_OVERLAP_SHARE)} each)"
    )
    print("=" * 80)

    if not ambiguous:
        print("None.")
        return

    ambiguous.sort(
        key=lambda assignment: (
            assignment["municipality_name"] or "",
            assignment["barrio_name"],
        )
    )

    for assignment in ambiguous:
        print()
        print(
            f"{assignment['barrio_name']} "
            f"[{assignment['barrio_id']}]"
        )
        print(
            f"  Assigned: {assignment['municipality_name']} "
            f"({assignment['municipality_id']})"
        )

        for overlap in assignment["material_overlaps"]:
            print(
                f"  {overlap['municipality_name']} "
                f"({overlap['municipality_id']}): "
                f"{format_percent(overlap['share'])}"
            )


def print_counts_by_municipality(
    assignments: list[dict],
    municipalities: gpd.GeoDataFrame,
) -> None:
    """Print the number of assigned barrios for every municipality."""
    counts = Counter(
        assignment["municipality_id"]
        for assignment in assignments
        if assignment["municipality_id"] is not None
    )

    municipality_names = {
        str(row.municipality_id): str(row.name)
        for row in municipalities.itertuples(index=False)
    }

    print()
    print("BARRIO COUNTS BY MUNICIPALITY")
    print("=" * 80)

    for municipality_id, municipality_name in sorted(
        municipality_names.items(),
        key=lambda item: item[1],
    ):
        print(
            f"{counts[municipality_id]:3}  "
            f"{municipality_name:<20}  "
            f"{municipality_id}"
        )

    print()
    print(f"Total assigned: {sum(counts.values())}")


def print_duplicate_names(assignments: list[dict]) -> None:
    """Print barrio names that occur more than once across Puerto Rico."""
    name_counts = Counter(
        assignment["barrio_name"]
        for assignment in assignments
    )

    duplicates = {
        name: count
        for name, count in name_counts.items()
        if count > 1
    }

    print()
    print("DUPLICATE BARRIO NAMES")
    print("=" * 80)
    print(f"Unique barrio names: {len(name_counts)}")
    print(f"Duplicated names: {len(duplicates)}")
    print(
        "Features participating in duplicated names: "
        f"{sum(duplicates.values())}"
    )

    if not duplicates:
        print("None.")
        return

    for name, count in sorted(
        duplicates.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        municipalities = sorted(
            {
                assignment["municipality_name"]
                for assignment in assignments
                if assignment["barrio_name"] == name
                and assignment["municipality_name"] is not None
            }
        )

        municipality_text = ", ".join(municipalities)

        print(
            f"{count:2}  {name:<30}  "
            f"{municipality_text}"
        )


def print_duplicate_municipality_name_pairs(
    assignments: list[dict],
) -> None:
    """Print duplicate barrio names occurring within the same municipality."""
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for assignment in assignments:
        municipality_id = assignment["municipality_id"]

        if municipality_id is None:
            continue

        key = (
            municipality_id,
            assignment["normalized_barrio_name"],
        )

        grouped[key].append(assignment)

    duplicates = {
        key: values
        for key, values in grouped.items()
        if len(values) > 1
    }

    print()
    print("DUPLICATE (MUNICIPALITY, BARRIO NAME) PAIRS")
    print("=" * 80)
    print(f"Duplicate pairs: {len(duplicates)}")

    if not duplicates:
        print("None.")
        return

    for (_, _), values in sorted(
        duplicates.items(),
        key=lambda item: (
            item[1][0]["municipality_name"],
            item[1][0]["barrio_name"],
        ),
    ):
        municipality_name = values[0]["municipality_name"]
        municipality_id = values[0]["municipality_id"]
        barrio_name = values[0]["barrio_name"]

        print()
        print(
            f"{municipality_name} ({municipality_id}) / "
            f"{barrio_name}"
        )

        for assignment in values:
            print(
                f"  {assignment['barrio_id']}  "
                f"{format_percent(assignment['assignment_share'])}"
            )


def compare_with_census(
    assignments: list[dict],
    census_records: list[dict],
) -> None:
    """Compare GeoBoundaries barrio assignments with Census reference records."""
    geoboundaries_by_key: dict[
        tuple[str, str],
        list[dict],
    ] = defaultdict(list)

    census_by_key: dict[
        tuple[str, str],
        list[dict],
    ] = defaultdict(list)

    for assignment in assignments:
        municipality_id = assignment["municipality_id"]

        if municipality_id is None:
            continue

        key = (
            municipality_id,
            assignment["normalized_barrio_name"],
        )

        geoboundaries_by_key[key].append(assignment)

    for record in census_records:
        key = (
            record["municipality_id"],
            record["normalized_barrio_name"],
        )

        census_by_key[key].append(record)

    geoboundaries_keys = set(geoboundaries_by_key)
    census_keys = set(census_by_key)

    shared_keys = geoboundaries_keys & census_keys
    census_only_keys = census_keys - geoboundaries_keys
    geoboundaries_only_keys = geoboundaries_keys - census_keys

    exact_record_matches = 0
    count_mismatch_keys = []

    for key in shared_keys:
        geoboundaries_count = len(geoboundaries_by_key[key])
        census_count = len(census_by_key[key])

        exact_record_matches += min(
            geoboundaries_count,
            census_count,
        )

        if geoboundaries_count != census_count:
            count_mismatch_keys.append(
                (
                    key,
                    geoboundaries_count,
                    census_count,
                )
            )

    print()
    print("GEBOUNDARIES / CENSUS COMPARISON")
    print("=" * 80)
    print(f"GeoBoundaries records: {len(assignments)}")
    print(f"Census named barrio records: {len(census_records)}")
    print(f"Shared municipality/name keys: {len(shared_keys)}")
    print(f"Matched records by key: {exact_record_matches}")
    print(f"Census-only keys: {len(census_only_keys)}")
    print(f"GeoBoundaries-only keys: {len(geoboundaries_only_keys)}")
    print(f"Shared keys with different record counts: {len(count_mismatch_keys)}")

    print()
    print("CENSUS-ONLY BARRIOS")
    print("=" * 80)

    if not census_only_keys:
        print("None.")
    else:
        for key in sorted(
            census_only_keys,
            key=lambda item: (item[0], item[1]),
        ):
            records = census_by_key[key]

            for record in records:
                suffix = " [barrio-pueblo]" if record["is_barrio_pueblo"] else ""

                print(
                    f"{record['municipality_name']} "
                    f"({record['municipality_id']}) / "
                    f"{record['barrio_name']}"
                    f"{suffix}"
                )
                print(f"  {record['geo_id']}")
                print(f"  {record['raw_label']}")

    print()
    print("GEBOUNDARIES-ONLY BARRIOS")
    print("=" * 80)

    if not geoboundaries_only_keys:
        print("None.")
    else:
        for key in sorted(
            geoboundaries_only_keys,
            key=lambda item: (item[0], item[1]),
        ):
            records = geoboundaries_by_key[key]

            for record in records:
                print(
                    f"{record['municipality_name']} "
                    f"({record['municipality_id']}) / "
                    f"{record['barrio_name']}"
                )
                print(
                    f"  {record['barrio_id']}  "
                    f"{format_percent(record['assignment_share'])}"
                )

    print()
    print("SHARED KEYS WITH DIFFERENT RECORD COUNTS")
    print("=" * 80)

    if not count_mismatch_keys:
        print("None.")
    else:
        for key, geoboundaries_count, census_count in sorted(
            count_mismatch_keys,
            key=lambda item: (item[0][0], item[0][1]),
        ):
            geoboundaries_records = geoboundaries_by_key[key]
            census_key_records = census_by_key[key]

            municipality_name = (
                geoboundaries_records[0]["municipality_name"]
                if geoboundaries_records
                else census_key_records[0]["municipality_name"]
            )

            barrio_name = (
                geoboundaries_records[0]["barrio_name"]
                if geoboundaries_records
                else census_key_records[0]["barrio_name"]
            )

            print()
            print(
                f"{municipality_name} ({key[0]}) / {barrio_name}"
            )
            print(
                f"  GeoBoundaries count: {geoboundaries_count}"
            )
            print(
                f"  Census count: {census_count}"
            )

            print("  GeoBoundaries:")

            for record in geoboundaries_records:
                print(
                    f"    {record['barrio_id']}  "
                    f"{format_percent(record['assignment_share'])}"
                )

            print("  Census:")

            for record in census_key_records:
                suffix = (
                    " [barrio-pueblo]"
                    if record["is_barrio_pueblo"]
                    else ""
                )

                print(
                    f"    {record['geo_id']}  "
                    f"{record['barrio_name']}{suffix}"
                )


def main() -> None:
    """Run the Puerto Rico barrio hierarchy and Census comparison inspection."""
    print(f"Reading barrios from {BARRIOS_PATH}")
    barrios = gpd.read_file(BARRIOS_PATH)

    print(f"Reading municipalities from {MUNICIPALITIES_PATH}")
    municipalities = gpd.read_file(MUNICIPALITIES_PATH)

    print()

    inspect_sources(barrios, municipalities)
    validate_sources(barrios, municipalities)

    census_records = load_census_barrio_records()

    print()
    print("Calculating barrio-to-municipality overlaps...")
    assignments = calculate_assignments(
        barrios,
        municipalities,
    )

    print_assignment_summary(assignments)
    print_unassigned(assignments)
    print_low_confidence_assignments(assignments)
    print_multiple_material_overlaps(assignments)
    print_counts_by_municipality(assignments, municipalities)
    print_duplicate_names(assignments)
    print_duplicate_municipality_name_pairs(assignments)
    compare_with_census(assignments, census_records)

    print()
    print("Inspection complete.")


if __name__ == "__main__":
    main()
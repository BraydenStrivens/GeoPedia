"""
Inspect Indonesia postcode administrative IDs against GeoPedia's canonical data.

Purpose
-------
This script determines whether the administrative IDs used by the raw
Indonesia postcode dataset correspond to the stable administrative IDs used
by GeoPedia's canonical Indonesia GeoJSON files.

The postcode dataset contains separate hierarchy files for:

    Admin 1: prov.csv
    Admin 2: kabkota.csv
    Admin 3: kec.csv

These are compared against GeoPedia's canonical:

    Admin 1: provinces.geojson
    Admin 2: regencies.geojson
    Admin 3: sub-districts.geojson

The previous Admin 4 inspection showed that apparently matching village IDs
could refer to completely different villages. For that reason, this script
does not treat an ID match alone as proof that the coding systems correspond.

For every transformed ID match, the administrative names are also compared.
This lets the report distinguish:

    - ID matches with matching names
    - ID matches with different names
    - unmatched CSV records
    - unmatched GeoJSON records

The goal is to determine whether Admin 1, Admin 2, or Admin 3 can safely be
used to transfer postcode-prefix information onto GeoPedia's polygons.

Inputs
------
Raw postcode hierarchy:

    data/raw/countries/indonesia/post-code-data/prov.csv
    data/raw/countries/indonesia/post-code-data/kabkota.csv
    data/raw/countries/indonesia/post-code-data/kec.csv

Canonical administrative GeoJSON:

    data/intermediate/countries/indonesia/provinces.geojson
    data/intermediate/countries/indonesia/regencies.geojson
    data/intermediate/countries/indonesia/sub-districts.geojson

No files are modified by this script.

Requirements
------------
    pip install ijson

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/inspect/post-codes.py
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import ijson


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

POSTCODE_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "indonesia"
    / "post-code-data"
)

INTERMEDIATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "indonesia"
)


# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Dataset:
    """Configuration for one administrative level."""

    label: str

    csv_path: Path
    geojson_path: Path

    geojson_id_property: str
    geojson_name_property: str

    expected_csv_count: int
    expected_geojson_count: int


ADMIN_1 = Dataset(
    label="ADMIN 1 — PROVINCES",
    csv_path=POSTCODE_DATA_DIR / "prov.csv",
    geojson_path=INTERMEDIATE_DIR / "provinces.geojson",
    geojson_id_property="province_id",
    geojson_name_property="province",
    expected_csv_count=34,
    expected_geojson_count=34,
)

ADMIN_2 = Dataset(
    label="ADMIN 2 — REGENCIES / CITIES",
    csv_path=POSTCODE_DATA_DIR / "kabkota.csv",
    geojson_path=INTERMEDIATE_DIR / "regencies.geojson",
    geojson_id_property="regency_id",
    geojson_name_property="regency",
    expected_csv_count=514,
    expected_geojson_count=522,
)

ADMIN_3 = Dataset(
    label="ADMIN 3 — SUB-DISTRICTS",
    csv_path=POSTCODE_DATA_DIR / "kec.csv",
    geojson_path=INTERMEDIATE_DIR / "sub-districts.geojson",
    geojson_id_property="sub_district_id",
    geojson_name_property="sub_district",
    expected_csv_count=7_201,
    expected_geojson_count=7_069,
)

DATASETS = (
    ADMIN_1,
    ADMIN_2,
    ADMIN_3,
)


# ---------------------------------------------------------------------------
# Reporting settings
# ---------------------------------------------------------------------------

SAMPLE_LIMIT = 20


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------

NON_ALPHANUMERIC_PATTERN = re.compile(
    r"[^a-z0-9]+"
)


def normalize_name(
    value: str,
) -> str:
    """
    Normalize an administrative name for conservative comparison.

    This intentionally does not perform fuzzy matching.

    Normalization:
        - Unicode NFKD normalization
        - lowercase
        - remove combining marks
        - normalize punctuation to spaces
        - collapse whitespace
    """

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    value = value.lower()

    value = NON_ALPHANUMERIC_PATTERN.sub(
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_csv_records(
    dataset: Dataset,
) -> dict[str, str]:
    """
    Load raw administrative IDs and names from one postcode hierarchy CSV.
    """

    if not dataset.csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found:\n{dataset.csv_path}"
        )

    records: dict[str, str] = {}

    with dataset.csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        fieldnames = set(
            reader.fieldnames
            or []
        )

        required_columns = {
            "id",
            "nm",
        }

        missing_columns = (
            required_columns
            - fieldnames
        )

        if missing_columns:
            raise ValueError(
                f"{dataset.csv_path.name} is missing required column(s): "
                + ", ".join(
                    sorted(
                        missing_columns
                    )
                )
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            raw_id = (
                row.get(
                    "id",
                    "",
                )
                or ""
            ).strip()

            name = (
                row.get(
                    "nm",
                    "",
                )
                or ""
            ).strip()

            if not raw_id:
                raise ValueError(
                    f"{dataset.csv_path.name} row {row_number:,} "
                    "has a blank ID."
                )

            if not name:
                raise ValueError(
                    f"{dataset.csv_path.name} row {row_number:,} "
                    "has a blank name."
                )

            if raw_id in records:
                raise ValueError(
                    f"{dataset.csv_path.name} contains duplicate ID "
                    f"{raw_id!r}."
                )

            records[
                raw_id
            ] = name

    if len(records) != dataset.expected_csv_count:
        raise ValueError(
            f"{dataset.csv_path.name} record-count mismatch: "
            f"expected {dataset.expected_csv_count:,}, "
            f"got {len(records):,}."
        )

    return records


# ---------------------------------------------------------------------------
# GeoJSON loading
# ---------------------------------------------------------------------------

def load_geojson_records(
    dataset: Dataset,
) -> dict[str, str]:
    """
    Stream administrative IDs and names from one canonical GeoJSON file.

    Geometry is ignored.
    """

    if not dataset.geojson_path.exists():
        raise FileNotFoundError(
            f"GeoJSON not found:\n{dataset.geojson_path}"
        )

    records: dict[str, str] = {}

    feature_count = 0

    with dataset.geojson_path.open(
        "rb"
    ) as file:
        for feature in ijson.items(
            file,
            "features.item",
        ):
            feature_count += 1

            properties = feature.get(
                "properties"
            )

            if not isinstance(
                properties,
                dict,
            ):
                raise ValueError(
                    f"{dataset.geojson_path.name} feature "
                    f"{feature_count:,} has invalid properties."
                )

            feature_id = properties.get(
                dataset.geojson_id_property
            )

            name = properties.get(
                dataset.geojson_name_property
            )

            if not isinstance(
                feature_id,
                str,
            ) or not feature_id.strip():
                raise ValueError(
                    f"{dataset.geojson_path.name} feature "
                    f"{feature_count:,} has an invalid "
                    f"{dataset.geojson_id_property}: {feature_id!r}"
                )

            if not isinstance(
                name,
                str,
            ) or not name.strip():
                raise ValueError(
                    f"{dataset.geojson_path.name} feature "
                    f"{feature_count:,} has an invalid "
                    f"{dataset.geojson_name_property}: {name!r}"
                )

            feature_id = feature_id.strip()
            name = name.strip()

            if feature_id in records:
                raise ValueError(
                    f"{dataset.geojson_path.name} contains duplicate ID "
                    f"{feature_id!r}."
                )

            records[
                feature_id
            ] = name

    if feature_count != dataset.expected_geojson_count:
        raise ValueError(
            f"{dataset.geojson_path.name} feature-count mismatch: "
            f"expected {dataset.expected_geojson_count:,}, "
            f"got {feature_count:,}."
        )

    return records


# ---------------------------------------------------------------------------
# ID transformations
# ---------------------------------------------------------------------------

def compact_csv_id(
    raw_id: str,
) -> str:
    """Remove dots from a postcode hierarchy ID."""

    return raw_id.replace(
        ".",
        "",
    )


def admin_1_candidates(
    raw_id: str,
) -> list[str]:
    """
    Return plausible GeoPedia Admin 1 IDs.

    Example:
        11 -> ID11
    """

    compact = compact_csv_id(
        raw_id
    )

    return [
        f"ID{compact}",
    ]


def admin_2_candidates(
    raw_id: str,
) -> list[str]:
    """
    Return plausible GeoPedia Admin 2 IDs.

    Example:
        11.01 -> ID1101
    """

    compact = compact_csv_id(
        raw_id
    )

    return [
        f"ID{compact}",
    ]


def admin_3_candidates(
    raw_id: str,
) -> list[str]:
    """
    Return plausible GeoPedia Admin 3 IDs.

    The source GeoJSON may encode the third administrative level with a
    trailing zero, so both compact forms are tested.

    Example:
        11.01.01 ->
            ID110101
            ID1101010
    """

    compact = compact_csv_id(
        raw_id
    )

    return [
        f"ID{compact}",
        f"ID{compact}0",
    ]


def get_candidate_ids(
    dataset: Dataset,
    raw_id: str,
) -> list[str]:
    """Return candidate canonical IDs for one CSV administrative ID."""

    if dataset is ADMIN_1:
        return admin_1_candidates(
            raw_id
        )

    if dataset is ADMIN_2:
        return admin_2_candidates(
            raw_id
        )

    if dataset is ADMIN_3:
        return admin_3_candidates(
            raw_id
        )

    raise ValueError(
        f"Unsupported dataset: {dataset.label}"
    )


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IdMatch:
    """One CSV record whose transformed ID exists in the GeoJSON."""

    csv_id: str
    geojson_id: str
    csv_name: str
    geojson_name: str
    names_match: bool


@dataclass(frozen=True)
class ComparisonResult:
    """Results for one administrative level."""

    matches: list[IdMatch]
    unmatched_csv_ids: list[str]
    unmatched_geojson_ids: list[str]


def compare_records(
    dataset: Dataset,
    csv_records: dict[str, str],
    geojson_records: dict[str, str],
) -> ComparisonResult:
    """Compare transformed CSV IDs against canonical GeoJSON IDs."""

    matches: list[IdMatch] = []

    matched_geojson_ids: set[str] = set()

    unmatched_csv_ids: list[str] = []

    for (
        csv_id,
        csv_name,
    ) in csv_records.items():
        candidate_ids = get_candidate_ids(
            dataset,
            csv_id,
        )

        matching_candidates = [
            candidate
            for candidate in candidate_ids
            if candidate in geojson_records
        ]

        if not matching_candidates:
            unmatched_csv_ids.append(
                csv_id
            )
            continue

        if len(matching_candidates) > 1:
            raise ValueError(
                f"{dataset.label}: CSV ID {csv_id!r} matches multiple "
                f"candidate GeoJSON IDs: {matching_candidates}"
            )

        geojson_id = matching_candidates[
            0
        ]

        geojson_name = geojson_records[
            geojson_id
        ]

        matches.append(
            IdMatch(
                csv_id=csv_id,
                geojson_id=geojson_id,
                csv_name=csv_name,
                geojson_name=geojson_name,
                names_match=(
                    normalize_name(
                        csv_name
                    )
                    == normalize_name(
                        geojson_name
                    )
                ),
            )
        )

        matched_geojson_ids.add(
            geojson_id
        )

    unmatched_geojson_ids = sorted(
        set(
            geojson_records
        )
        - matched_geojson_ids
    )

    return ComparisonResult(
        matches=matches,
        unmatched_csv_ids=sorted(
            unmatched_csv_ids
        ),
        unmatched_geojson_ids=unmatched_geojson_ids,
    )


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def percentage(
    numerator: int,
    denominator: int,
) -> float:
    """Return numerator as a percentage of denominator."""

    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100
    )


def print_separator() -> None:
    """Print a standard report separator."""

    print(
        "=" * 78
    )


def print_dataset_report(
    dataset: Dataset,
    csv_records: dict[str, str],
    geojson_records: dict[str, str],
    result: ComparisonResult,
) -> None:
    """Print concise ID-match statistics and representative samples."""

    name_matches = [
        match
        for match in result.matches
        if match.names_match
    ]

    name_mismatches = [
        match
        for match in result.matches
        if not match.names_match
    ]

    print_separator()
    print(
        dataset.label
    )
    print_separator()

    print(
        f"CSV records:                    {len(csv_records):,}"
    )
    print(
        f"GeoJSON records:                {len(geojson_records):,}"
    )
    print(
        f"ID matches:                     {len(result.matches):,}"
    )
    print(
        f"ID + normalized-name matches:   {len(name_matches):,}"
    )
    print(
        f"ID matches with name mismatch:  {len(name_mismatches):,}"
    )
    print(
        f"Unmatched CSV records:          {len(result.unmatched_csv_ids):,}"
    )
    print(
        f"Unmatched GeoJSON records:      {len(result.unmatched_geojson_ids):,}"
    )
    print()

    print(
        f"CSV ID coverage:                "
        f"{percentage(len(result.matches), len(csv_records)):.2f}%"
    )
    print(
        f"GeoJSON ID coverage:            "
        f"{percentage(len(result.matches), len(geojson_records)):.2f}%"
    )
    print(
        f"Confirmed CSV coverage:         "
        f"{percentage(len(name_matches), len(csv_records)):.2f}%"
    )
    print(
        f"Confirmed GeoJSON coverage:     "
        f"{percentage(len(name_matches), len(geojson_records)):.2f}%"
    )

    print()
    print(
        "MATCHED SAMPLES"
    )
    print(
        "-" * 78
    )

    for match in result.matches[
        :SAMPLE_LIMIT
    ]:
        status = (
            "NAME MATCH"
            if match.names_match
            else "NAME MISMATCH"
        )

        print(
            f"{match.csv_id} -> {match.geojson_id} [{status}]"
        )
        print(
            f"  CSV:     {match.csv_name}"
        )
        print(
            f"  GeoJSON: {match.geojson_name}"
        )

    print()
    print(
        "UNMATCHED CSV SAMPLES"
    )
    print(
        "-" * 78
    )

    for csv_id in result.unmatched_csv_ids[
        :SAMPLE_LIMIT
    ]:
        print(
            f"{csv_id}: {csv_records[csv_id]}"
        )

    print()
    print(
        "UNMATCHED GEOJSON SAMPLES"
    )
    print(
        "-" * 78
    )

    for geojson_id in result.unmatched_geojson_ids[
        :SAMPLE_LIMIT
    ]:
        print(
            f"{geojson_id}: {geojson_records[geojson_id]}"
        )

    print()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Compare postcode hierarchy IDs with GeoPedia Admin 1–3 IDs."""

    print(
        "Inspecting Indonesia postcode administrative ID compatibility..."
    )
    print()

    for dataset in DATASETS:
        csv_records = load_csv_records(
            dataset
        )

        geojson_records = load_geojson_records(
            dataset
        )

        result = compare_records(
            dataset,
            csv_records,
            geojson_records,
        )

        print_dataset_report(
            dataset,
            csv_records,
            geojson_records,
            result,
        )

    print_separator()
    print(
        "Inspection complete."
    )
    print_separator()


if __name__ == "__main__":
    main()
"""
Generate reusable Ghana administrative quiz-support data.

Inputs
------
data/intermediate/countries/ghana/admin/regions.geojson
data/intermediate/countries/ghana/admin/districts.geojson

Output
------
src/quiz/quizzes/countries/africa/ghana/data/admin.ts

The generated TypeScript contains administrative names and hierarchy metadata
used by Ghana's feature quizzes. Geometry remains in the runtime GeoJSON and
is not duplicated here.

Run
---
python scripts/countries/ghana/generate/admin-quiz-data.py
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ghana"
    / "admin"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "ghana"
    / "data"
    / "admin.ts"
)

REGIONS_PATH = INPUT_DIR / "regions.geojson"
DISTRICTS_PATH = INPUT_DIR / "districts.geojson"

EXPECTED_REGION_COUNT = 16
EXPECTED_DISTRICT_COUNT = 260


def load_dataset(
    path: Path,
    expected_count: int,
    required_properties: set[str],
) -> gpd.GeoDataFrame:
    """Load and validate one canonical Ghana administrative dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input GeoJSON not found: {path}"
        )

    frame = gpd.read_file(path)

    if len(frame) != expected_count:
        raise ValueError(
            f"Unexpected feature count for {path.name}: "
            f"expected {expected_count}, found {len(frame)}."
        )

    missing = required_properties - set(frame.columns)

    if missing:
        raise ValueError(
            f"{path.name} is missing required properties: "
            f"{sorted(missing)}"
        )

    return frame


def quote(value: str) -> str:
    """Encode a Python string as a TypeScript-compatible JSON string."""
    return json.dumps(
        str(value),
        ensure_ascii=False,
    )


def generate_regions(
    regions: gpd.GeoDataFrame,
) -> str:
    """Generate Ghana's region lookup dictionary."""
    lines = [
        "export const GHANA_REGIONS_BY_ID = {",
    ]

    ordered = regions.sort_values(
        "region"
    )

    for _, row in ordered.iterrows():
        region_id = str(row["region_id"])
        region = str(row["region"])

        lines.append(
            f"  {quote(region_id)}: {{"
        )
        lines.append(
            f"    name: {quote(region)},"
        )
        lines.append(
            "  },"
        )

    lines.append(
        "} as const;"
    )

    return "\n".join(lines)


def generate_districts(
    districts: gpd.GeoDataFrame,
) -> str:
    """Generate Ghana's district lookup dictionary and parent metadata."""
    lines = [
        "export const GHANA_DISTRICTS_BY_ID = {",
    ]

    ordered = districts.sort_values(
        ["region", "district"]
    )

    for _, row in ordered.iterrows():
        district_id = str(
            row["district_id"]
        )
        district = str(
            row["district"]
        )
        region_id = str(
            row["region_id"]
        )
        region = str(
            row["region"]
        )

        lines.append(
            f"  {quote(district_id)}: {{"
        )
        lines.append(
            f"    name: {quote(district)},"
        )
        lines.append(
            f"    regionId: {quote(region_id)},"
        )
        lines.append(
            f"    region: {quote(region)},"
        )
        lines.append(
            "  },"
        )

    lines.append(
        "} as const;"
    )

    return "\n".join(lines)


def validate_data(
    regions: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
) -> None:
    """Validate IDs, names, and Ghana's region-to-district hierarchy."""
    if regions["region_id"].isna().any():
        raise ValueError(
            "Regions contain null IDs."
        )

    if districts["district_id"].isna().any():
        raise ValueError(
            "Districts contain null IDs."
        )

    if regions["region_id"].duplicated().any():
        raise ValueError(
            "Regions contain duplicate IDs."
        )

    if districts["district_id"].duplicated().any():
        raise ValueError(
            "Districts contain duplicate IDs."
        )

    if regions["region"].duplicated().any():
        raise ValueError(
            "Regions contain duplicate names."
        )

    if districts["district"].duplicated().any():
        raise ValueError(
            "Districts contain duplicate names."
        )

    region_names_by_id = dict(
        zip(
            regions["region_id"].astype(str),
            regions["region"].astype(str),
        )
    )

    for _, district in districts.iterrows():
        region_id = str(
            district["region_id"]
        )
        region = str(
            district["region"]
        )

        if region_id not in region_names_by_id:
            raise ValueError(
                f"District references unknown region ID {region_id!r}."
            )

        if region_names_by_id[region_id] != region:
            raise ValueError(
                "District parent-region name does not match "
                f"region ID {region_id!r}."
            )


def main() -> None:
    """Generate Ghana's reusable administrative quiz-support data."""
    print(
        "Generating Ghana administrative quiz data..."
    )

    regions = load_dataset(
        REGIONS_PATH,
        EXPECTED_REGION_COUNT,
        {
            "region_id",
            "region",
        },
    )

    districts = load_dataset(
        DISTRICTS_PATH,
        EXPECTED_DISTRICT_COUNT,
        {
            "district_id",
            "district",
            "region_id",
            "region",
        },
    )

    validate_data(
        regions,
        districts,
    )

    contents = "\n\n".join(
        [
            (
                "/**\n"
                " * Generated Ghana administrative quiz-support data.\n"
                " *\n"
                " * Do not edit this file manually. Regenerate it with:\n"
                " * python scripts/countries/ghana/generate/"
                "admin-quiz-data.py\n"
                " */"
            ),
            generate_regions(regions),
            generate_districts(districts),
        ]
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        contents + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "Ghana administrative quiz data generated."
    )
    print(
        f"  Regions:   {len(regions)}"
    )
    print(
        f"  Districts: {len(districts)}"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
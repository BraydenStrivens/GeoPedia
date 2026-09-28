"""
Create Tunisia's runtime 2-digit postal-prefix GeoJSON.

Input
-----
public/data/countries/tunisia/geojson/governorates.geojson

Output
------
public/data/countries/tunisia/geojson/postal-prefixes.geojson

The already-simplified governorate geometry is reused directly so this derived
dataset does not require another simplification pass.

Each output feature represents one unique set of valid two-digit postal-code
prefixes. Governorates with identical prefix sets are merged into a single
geographic feature. Ben Arous and Manouba both use exactly {11, 20}, so their
polygons are merged.

Other shared prefixes remain separate geographic features when their complete
answer sets differ. GeoPedia's multiple-answer quiz behavior handles those
partial overlaps.

Only properties required by the runtime map and quiz are retained:

    postal_prefix_id
    postal_prefixes
    region_id
    governorate

The `governorate` property provides the map's hover label. Features created
from multiple governorates join their names into a single display label.

The source governorate names are used only while constructing and validating
the derived data and are not retained in the output.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "tunisia"
    / "geojson"
    / "governorates.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "tunisia"
    / "geojson"
    / "postal-prefixes.geojson"
)


EXPECTED_GOVERNORATE_COUNT = 24
EXPECTED_OUTPUT_FEATURE_COUNT = 23

EXPECTED_PREFIXES = {
    "10",
    "11",
    "12",
    "20",
    "21",
    "22",
    "30",
    "31",
    "32",
    "40",
    "41",
    "42",
    "50",
    "51",
    "60",
    "61",
    "70",
    "71",
    "80",
    "81",
    "90",
    "91",
}


# Two-digit postal-code prefixes assigned to each governorate.
#
# These names intentionally match the canonical `governorate` property in
# Tunisia's processed administrative GeoJSON.
POSTAL_PREFIXES_BY_GOVERNORATE = {
    "Ariana": ["20"],
    "Béja": ["90"],
    "Ben Arous": ["11", "20"],
    "Bizerte": ["70"],
    "Gabès": ["60"],
    "Gafsa": ["21"],
    "Jendouba": ["81"],
    "Kairouan": ["31"],
    "Kassérine": ["12"],
    "Kebili": ["42"],
    "Le Kef": ["71"],
    "Mahdia": ["51"],
    "Manubah": ["11", "20"],
    "Médenine": ["41"],
    "Monastir": ["50"],
    "Nabeul": ["80"],
    "Sfax": ["30"],
    "Sidi Bou Zid": ["91"],
    "Siliana": ["61"],
    "Sousse": ["40"],
    "Tataouine": ["32"],
    "Tozeur": ["22"],
    "Tunis": ["10", "20"],
    "Zaghouan": ["11"],
}


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------


def load_governorates() -> gpd.GeoDataFrame:
    """Load and validate Tunisia's simplified governorate runtime geometry."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Governorate GeoJSON not found: {INPUT_PATH}"
        )

    frame = gpd.read_file(
        INPUT_PATH
    )

    if len(frame) != EXPECTED_GOVERNORATE_COUNT:
        raise ValueError(
            "Unexpected governorate count: "
            f"expected {EXPECTED_GOVERNORATE_COUNT}, "
            f"found {len(frame)}."
        )

    required_properties = {
        "governorate_id",
        "governorate",
        "region_id",
    }

    missing_properties = (
        required_properties
        - set(frame.columns)
    )

    if missing_properties:
        raise ValueError(
            "Governorate GeoJSON is missing required properties: "
            f"{sorted(missing_properties)}"
        )

    if frame["governorate_id"].isna().any():
        raise ValueError(
            "Governorate GeoJSON contains a null governorate_id."
        )

    if frame["governorate_id"].duplicated().any():
        raise ValueError(
            "Governorate GeoJSON contains duplicate governorate IDs."
        )

    if frame["governorate"].isna().any():
        raise ValueError(
            "Governorate GeoJSON contains a null governorate name."
        )

    if frame["region_id"].isna().any():
        raise ValueError(
            "Governorate GeoJSON contains a null region_id."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            "Governorate GeoJSON contains null geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            "Governorate GeoJSON contains empty geometry."
        )

    source_names = set(
        frame["governorate"].astype(str)
    )

    mapping_names = set(
        POSTAL_PREFIXES_BY_GOVERNORATE
    )

    missing_mappings = (
        source_names
        - mapping_names
    )

    unknown_mappings = (
        mapping_names
        - source_names
    )

    if missing_mappings:
        raise ValueError(
            "Governorates without postal-prefix mappings: "
            f"{sorted(missing_mappings)}"
        )

    if unknown_mappings:
        raise ValueError(
            "Postal-prefix mappings reference unknown governorates: "
            f"{sorted(unknown_mappings)}"
        )

    return frame


def validate_prefixes() -> None:
    """Validate the configured set of postal-prefix quiz answers."""
    represented_prefixes = {
        prefix
        for prefixes in POSTAL_PREFIXES_BY_GOVERNORATE.values()
        for prefix in prefixes
    }

    if represented_prefixes != EXPECTED_PREFIXES:
        missing = (
            EXPECTED_PREFIXES
            - represented_prefixes
        )

        unexpected = (
            represented_prefixes
            - EXPECTED_PREFIXES
        )

        raise ValueError(
            "Postal-prefix answer set does not match expectations. "
            f"Missing: {sorted(missing)}. "
            f"Unexpected: {sorted(unexpected)}."
        )

    for (
        governorate,
        prefixes,
    ) in POSTAL_PREFIXES_BY_GOVERNORATE.items():
        if not prefixes:
            raise ValueError(
                f"{governorate} has no postal prefixes."
            )

        if len(prefixes) != len(set(prefixes)):
            raise ValueError(
                f"{governorate} contains duplicate postal prefixes."
            )

        for prefix in prefixes:
            if (
                len(prefix) != 2
                or not prefix.isdigit()
            ):
                raise ValueError(
                    f"{governorate} has invalid postal prefix "
                    f"{prefix!r}."
                )


# ---------------------------------------------------------------------------
# Feature construction
# ---------------------------------------------------------------------------


def create_answer_set_id(
    prefixes: tuple[str, ...],
) -> str:
    """
    Create a stable scalar map identity from a complete postal-prefix set.

    Examples:
        ("20",)       -> "20"
        ("11", "20") -> "11-20"
    """
    return "-".join(
        prefixes
    )


def build_postal_prefix_features(
    governorates: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Build one feature for each unique governorate postal-prefix answer set.

    Governorates sharing an identical complete answer set are dissolved into
    one feature. Partial answer overlap does not cause a merge.
    """
    grouped_indexes: dict[
        tuple[str, ...],
        list[Any],
    ] = defaultdict(list)

    for index, row in governorates.iterrows():
        governorate = str(
            row["governorate"]
        )

        prefixes = tuple(
            sorted(
                POSTAL_PREFIXES_BY_GOVERNORATE[
                    governorate
                ],
                key=int,
            )
        )

        grouped_indexes[prefixes].append(
            index
        )

    output_rows = []

    for prefixes in sorted(
        grouped_indexes,
        key=lambda values: tuple(
            int(value)
            for value in values
        ),
    ):
        indexes = grouped_indexes[
            prefixes
        ]

        members = governorates.loc[
            indexes
        ]

        region_ids = {
            str(value)
            for value in members["region_id"]
        }

        if len(region_ids) != 1:
            governorate_names = sorted(
                str(value)
                for value in members[
                    "governorate"
                ]
            )

            raise ValueError(
                "Governorates sharing an identical postal-prefix "
                "answer set cross region boundaries: "
                f"{governorate_names}"
            )

        region_id = next(
            iter(region_ids)
        )

        geometry = members.geometry.union_all()

        if geometry is None or geometry.is_empty:
            raise ValueError(
                "Postal-prefix merge produced empty geometry "
                f"for answer set {prefixes}."
            )
            
        governorate_names = sorted(
            str(value)
            for value in members["governorate"]
        )

        governorate = " / ".join(
            governorate_names
        )

        output_rows.append(
            {
                "postal_prefix_id": create_answer_set_id(
                    prefixes
                ),
                "postal_prefixes": list(
                    prefixes
                ),
                "region_id": region_id,
                "governorate": governorate,
                "geometry": geometry,
            }
        )

    output = gpd.GeoDataFrame(
        output_rows,
        geometry="geometry",
        crs=governorates.crs,
    )

    if len(output) != EXPECTED_OUTPUT_FEATURE_COUNT:
        raise ValueError(
            "Unexpected postal-prefix feature count: "
            f"expected {EXPECTED_OUTPUT_FEATURE_COUNT}, "
            f"found {len(output)}."
        )

    if output["postal_prefix_id"].duplicated().any():
        raise ValueError(
            "Generated postal_prefix_id values are not unique."
        )

    if output.geometry.isna().any():
        raise ValueError(
            "Generated postal-prefix data contains null geometry."
        )

    if output.geometry.is_empty.any():
        raise ValueError(
            "Generated postal-prefix data contains empty geometry."
        )

    return output


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_compact_geojson(
    frame: gpd.GeoDataFrame,
) -> None:
    """Write the runtime postal-prefix dataset as compact UTF-8 GeoJSON."""
    geojson = json.loads(
        frame.to_json(
            ensure_ascii=False,
            drop_id=True,
        )
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
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
    """Create Tunisia's runtime 2-digit postal-prefix GeoJSON."""
    print(
        "Processing Tunisia postal prefixes..."
    )

    validate_prefixes()

    governorates = load_governorates()

    output = build_postal_prefix_features(
        governorates
    )

    write_compact_geojson(
        output
    )

    output_size = (
        OUTPUT_PATH.stat().st_size
        / (1024 * 1024)
    )

    print()
    print(
        "Tunisia postal-prefix processing complete."
    )
    print(
        f"  Source governorates: {len(governorates)}"
    )
    print(
        f"  Runtime features:    {len(output)}"
    )
    print(
        f"  Quiz answers:        {len(EXPECTED_PREFIXES)}"
    )
    print(
        f"  Output size:         {output_size:.2f} MB"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
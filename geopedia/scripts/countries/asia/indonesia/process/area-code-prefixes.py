"""
Build Indonesia's 1-digit and 2-digit landline area-code-prefix GeoJSONs.

This is the final processing step after the raster-based area-code inspection.

The inspector produced a candidate prefix for each of Indonesia's 514 actual
kabupaten/kota. Those candidates were then manually checked against the
reference area-code map. Only confirmed mistakes are overridden here.

Inputs
------
data/intermediate/countries/indonesia/area-codes/candidates.csv
    Candidate regency -> 2-digit area-code-prefix assignments produced by
    scripts/countries/asia/indonesia/inspect/area-code-prefixes.py.

public/data/countries/indonesia/geojson/regencies.geojson
    GeoPedia's already-cleaned and simplified regency/city geometry.

Outputs
-------
public/data/countries/indonesia/geojson/area-code-prefixes-2.geojson
    Dissolved 2-digit area-code-prefix regions. Each feature contains
    prefix_2 and prefix_1.

public/data/countries/indonesia/geojson/area-code-prefixes-1.geojson
    Dissolved 1-digit area-code-prefix regions.

data/intermediate/countries/indonesia/area-codes/verification.png
    Final visual verification map. Assigned administrative features are gray,
    unclassified features are white, thin lines show kabupaten/kota borders,
    and stronger colored lines show the final 2-digit prefix boundaries.

The eight non-administrative features present in GeoPedia's regencies GeoJSON
are excluded from the required 514-unit administrative validation. They are
shown in white on the verification image unless explicitly assigned later.

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/process/area-code-prefixes.py

Dependencies
------------
    pip install geopandas pandas matplotlib shapely
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

AREA_CODES_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "indonesia"
    / "area-codes"
)

CANDIDATES_PATH = (
    AREA_CODES_DIR
    / "candidates.csv"
)

VERIFICATION_PATH = (
    AREA_CODES_DIR
    / "verification.png"
)

REGENCIES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "indonesia"
    / "geojson"
    / "regencies.geojson"
)

OUTPUT_PREFIX_2_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "indonesia"
    / "geojson"
    / "area-code-prefixes-2.geojson"
)

OUTPUT_PREFIX_1_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "indonesia"
    / "geojson"
    / "area-code-prefixes-1.geojson"
)


# ---------------------------------------------------------------------------
# Administrative validation
# ---------------------------------------------------------------------------

EXPECTED_ADMINISTRATIVE_COUNT = 514


# These exist in the source Admin-2 GeoJSON but are not part of Indonesia's
# 514 kabupaten/kota administrative units.
NON_ADMINISTRATIVE_FEATURE_IDS = {
    "ID1288",  # Danau Toba
    "ID1388",  # Danau
    "ID1688",  # Danau
    "ID1888",  # Danau
    "ID3288",  # Waduk Cirata
    "ID3388",  # Wadung Kedungombo
    "ID3399",  # Hutan
    "ID7188",  # Danau
}


# ---------------------------------------------------------------------------
# Manually verified corrections
# ---------------------------------------------------------------------------

# These are the ONLY automatic-classifier assignments that were manually
# determined to be incorrect during visual inspection.
#
# Everything not listed here retains the inspector's candidate assignment.
#
# IDs are used rather than names so this processing step remains deterministic
# even if display names are changed later.

AREA_CODE_PREFIX_OVERRIDES: dict[str, str] = {
    # -----------------------------------------------------------------------
    # Sumatra
    # -----------------------------------------------------------------------

    "ID1172": "65",  # Kota Sabang
    "ID1171": "65",  # Kota Banda Aceh

    "ID1110": "64",  # Bireuen

    "ID1275": "61",  # Kota Medan

    "ID1213": "62",  # Langkat
    "ID1104": "62",  # Aceh Tenggara
    "ID1211": "62",  # Karo
    "ID1210": "62",  # Dairi
    "ID1216": "62",  # Pakpak Bharat
    "ID1276": "62",  # Kota Binjai
    "ID1212": "62",  # Deli Serdang
    "ID1218": "62",  # Serdang Bedagai
    "ID1274": "62",  # Kota Tebing Tinggi

    "ID1217": "63",  # Samosir
    "ID1277": "63",  # Kota Padangsidimpuan

    "ID1811": "72",  # Mesuji

    # -----------------------------------------------------------------------
    # Java
    # -----------------------------------------------------------------------

    "ID3215": "26",  # Karawang
    "ID3213": "26",  # Subang
    "ID3214": "26",  # Purwakarta
    "ID3203": "26",  # Cianjur
    "ID3202": "26",  # Sukabumi
    "ID3272": "26",  # Kota Sukabumi
    "ID3211": "26",  # Sumedang
    "ID3205": "26",  # Garut
    "ID3279": "26",  # Kota Banjar

    "ID3376": "28",  # Kota Tegal
    "ID3375": "28",  # Kota Pekalongan

    "ID3374": "24",  # Kota Semarang

    "ID3322": "29",  # Semarang
    "ID3373": "29",  # Kota Salatiga
    "ID3324": "29",  # Kendal
    "ID3323": "29",  # Temanggung
    "ID3308": "29",  # Magelang
    "ID3371": "29",  # Kota Magelang
    "ID3315": "29",  # Grobogan
    "ID3321": "29",  # Demak

    "ID3524": "32",  # Lamongan
    "ID3517": "32",  # Jombang
    "ID3516": "32",  # Mojokerto
    "ID3576": "32",  # Kota Mojokerto
    "ID3527": "32",  # Sampang
    "ID3528": "32",  # Pamekasan
    "ID3529": "32",  # Sumenep

    "ID3525": "31",  # Gresik
    "ID3578": "31",  # Kota Surabaya
    "ID3526": "31",  # Bangkalan
    "ID3515": "31",  # Sidoarjo

    "ID3574": "33",  # Kota Probolinggo

    # -----------------------------------------------------------------------
    # Nusa Tenggara
    # -----------------------------------------------------------------------

    "ID5108": "36",  # Buleleng

    "ID5308": "38",  # Lembata
    "ID5314": "38",  # Rote Ndao
    "ID5320": "38",  # Sabu Raijua

    # -----------------------------------------------------------------------
    # Sulawesi
    # -----------------------------------------------------------------------

    "ID7108": "43",  # Siau Tagulandang Biaro
    "ID7172": "43",  # Kota Bitung

    "ID7404": "40",  # Kolaka
    "ID7406": "40",  # Bombana
    "ID7415": "40",  # Buton Selatan

    "ID7606": "42",  # Mamuju Tengah
    "ID7604": "42",  # Mamuju
    "ID7603": "42",  # Mamasa
    "ID7318": "42",  # Tana Toraja
    "ID7326": "42",  # Toraja Utara
    "ID7315": "42",  # Pinrang
    "ID7372": "42",  # Kota Parepare

    "ID7313": "48",  # Wajo
    "ID7312": "48",  # Soppeng
    "ID7311": "48",  # Bone
    "ID7307": "48",  # Sinjai

    # -----------------------------------------------------------------------
    # Kalimantan
    # -----------------------------------------------------------------------

    "ID6571": "55",  # Kota Tarakan

    # -----------------------------------------------------------------------
    # Maluku
    # -----------------------------------------------------------------------

    "ID8104": "91",  # Buru
    "ID8109": "91",  # Buru Selatan
    "ID8106": "91",  # Seram Bagian Barat
    "ID8171": "91",  # Kota Ambon
    "ID8103": "91",  # Maluku Tengah
    "ID8107": "91",  # Seram Bagian Timur
    
    # -----------------------------------------------------------------------
    # Previously unclassified
    # -----------------------------------------------------------------------

    "ID3101": "21",  # Kepulauan Seribu
    "ID3575": "34",  # Kota Pasuruan
    "ID6474": "54",  # Kota Bontang
    "ID8172": "91",  # Kota Tual
    
    # -----------------------------------------------------------------------
    # Final verification corrections
    # -----------------------------------------------------------------------

    "ID3217": "22",  # Bandung Barat
    "ID3204": "22",  # Bandung
    "ID3273": "22",  # Kota Bandung
    "ID3277": "22",  # Kota Cimahi

    "ID7414": "40",  # Buton Tengah
}


# ---------------------------------------------------------------------------
# Verification-map settings
# ---------------------------------------------------------------------------

VERIFICATION_FIGURE_WIDTH = 26
VERIFICATION_FIGURE_HEIGHT = 10
VERIFICATION_DPI = 180

ASSIGNED_FILL_COLOR = "#bdbdbd"
UNCLASSIFIED_FILL_COLOR = "#ffffff"

ADMIN_BORDER_COLOR = "#8a8a8a"
ADMIN_BORDER_WIDTH = 0.18

# Matplotlib's default qualitative color cycle is intentionally used for
# prefix borders. The colors themselves carry no semantic meaning.
PREFIX_BORDER_WIDTH = 1.35

LABEL_FONT_SIZE = 7
LABEL_HALO_WIDTH = 2.5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_prefix(value: object) -> str | None:
    """
    Convert a CSV prefix value to a canonical two-character string.

    Examples:
        21
        21.0
        "21"

    all become:
        "21"

    Blank/NaN values become None.
    """

    if value is None:
        return None

    if pd.isna(
        value
    ):
        return None

    text = str(
        value
    ).strip()

    if not text:
        return None

    try:
        numeric = int(
            float(
                text
            )
        )
    except ValueError as error:
        raise ValueError(
            f"Invalid prefix value: {value!r}"
        ) from error

    prefix = str(
        numeric
    )

    if len(
        prefix
    ) != 2:
        raise ValueError(
            "Expected a 2-digit significant prefix, "
            f"got {value!r} -> {prefix!r}"
        )

    return prefix


def ensure_valid_prefix(
    prefix: str,
) -> None:
    """Validate a final significant 2-digit prefix."""

    if (
        len(
            prefix
        )
        != 2
        or not prefix.isdigit()
    ):
        raise ValueError(
            f"Invalid 2-digit prefix: {prefix!r}"
        )

    if prefix.startswith(
        "0"
    ):
        raise ValueError(
            "Prefixes must omit Indonesia's trunk zero. "
            f"Received {prefix!r}."
        )


def display_prefix_2(
    prefix: str,
) -> str:
    """Return the human-readable prefix form, e.g. 21 -> 021-."""

    return f"0{prefix}-"


def display_prefix_1(
    prefix: str,
) -> str:
    """Return the human-readable first-digit form, e.g. 2 -> 02-."""

    return f"0{prefix}-"


def load_candidates(
    path: Path,
) -> pd.DataFrame:
    """Load and validate the inspector candidate table."""

    candidates = pd.read_csv(
        path,
        dtype={
            "regency_id": "string",
            "regency": "string",
        },
    )

    required_columns = {
        "regency_id",
        "regency",
        "prefix_2",
    }

    missing_columns = (
        required_columns
        - set(
            candidates.columns
        )
    )

    if missing_columns:
        raise ValueError(
            "candidates.csv is missing required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    duplicate_ids = candidates[
        candidates[
            "regency_id"
        ].duplicated(
            keep=False
        )
    ]

    if not duplicate_ids.empty:
        raise ValueError(
            "Duplicate regency_id values found in candidates.csv:\n"
            + duplicate_ids[
                [
                    "regency_id",
                    "regency",
                ]
            ].to_string(
                index=False
            )
        )

    return candidates


def load_regencies() -> gpd.GeoDataFrame:
    """Load GeoPedia's canonical public regency geometry."""

    regencies = gpd.read_file(
        REGENCIES_PATH
    )

    required_columns = {
        "regency_id",
        "regency",
        "geometry",
    }

    missing_columns = (
        required_columns
        - set(
            regencies.columns
        )
    )

    if missing_columns:
        raise ValueError(
            "regencies.geojson is missing required properties: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    if regencies[
        "regency_id"
    ].duplicated().any():
        raise ValueError(
            "regencies.geojson contains duplicate regency_id values."
        )

    return regencies


def build_final_assignments(
    candidates: pd.DataFrame,
    regencies: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Join classifier candidates to regency geometry and apply manual overrides.

    Exactly 514 actual administrative units must be present.
    """

    administrative = regencies[
        ~regencies[
            "regency_id"
        ].isin(
            NON_ADMINISTRATIVE_FEATURE_IDS
        )
    ].copy()

    if len(
        administrative
    ) != EXPECTED_ADMINISTRATIVE_COUNT:
        raise ValueError(
            "Unexpected number of administrative regency/city features.\n"
            f"Expected: {EXPECTED_ADMINISTRATIVE_COUNT}\n"
            f"Found:    {len(administrative)}"
        )

    candidate_ids = set(
        candidates[
            "regency_id"
        ].dropna()
    )

    administrative_ids = set(
        administrative[
            "regency_id"
        ]
    )

    missing_candidate_ids = (
        administrative_ids
        - candidate_ids
    )

    extra_candidate_ids = (
        candidate_ids
        - administrative_ids
    )

    if missing_candidate_ids:
        raise ValueError(
            "Administrative features missing from candidates.csv:\n"
            + "\n".join(
                sorted(
                    missing_candidate_ids
                )
            )
        )

    if extra_candidate_ids:
        raise ValueError(
            "candidates.csv contains unexpected administrative IDs:\n"
            + "\n".join(
                sorted(
                    extra_candidate_ids
                )
            )
        )

    override_ids = set(
        AREA_CODE_PREFIX_OVERRIDES
    )

    unknown_override_ids = (
        override_ids
        - administrative_ids
    )

    if unknown_override_ids:
        raise ValueError(
            "Manual overrides contain unknown regency IDs:\n"
            + "\n".join(
                sorted(
                    unknown_override_ids
                )
            )
        )

    candidate_columns = [
        "regency_id",
        "prefix_2",
    ]

    if "status" in candidates.columns:
        candidate_columns.append(
            "status"
        )

    joined = administrative.merge(
        candidates[
            candidate_columns
        ],
        on="regency_id",
        how="left",
        validate="one_to_one",
    )

    joined[
        "candidate_prefix_2"
    ] = joined[
        "prefix_2"
    ].map(
        normalize_prefix
    )

    final_prefixes: list[str | None] = []
    override_applied: list[bool] = []

    for row in joined.itertuples():
        regency_id = row.regency_id

        if regency_id in AREA_CODE_PREFIX_OVERRIDES:
            prefix = AREA_CODE_PREFIX_OVERRIDES[
                regency_id
            ]

            override_applied.append(
                True
            )
        else:
            prefix = normalize_prefix(
                row.candidate_prefix_2
            )

            override_applied.append(
                False
            )

        if prefix is not None:
            ensure_valid_prefix(
                prefix
            )

        final_prefixes.append(
            prefix
        )

    joined[
        "prefix_2"
    ] = final_prefixes

    joined[
        "override_applied"
    ] = override_applied

    joined[
        "prefix_1"
    ] = joined[
        "prefix_2"
    ].map(
        lambda prefix: (
            prefix[0]
            if pd.notna(prefix)
            else None
        )
    )

    return gpd.GeoDataFrame(
        joined,
        geometry="geometry",
        crs=regencies.crs,
    )


def print_override_summary(
    assignments: gpd.GeoDataFrame,
) -> None:
    """Print every manual correction and its original candidate."""

    print()
    print(
        "Manual overrides applied:"
    )
    print()

    overridden = assignments[
        assignments[
            "override_applied"
        ]
    ].copy()

    overridden = overridden.sort_values(
        [
            "region_id",
            "province",
            "regency",
        ]
    )

    for row in overridden.itertuples():
        old = (
            row.candidate_prefix_2
            if pd.notna(row.candidate_prefix_2)
            else "UNCLASSIFIED"
        )

        print(
            f"  {row.regency_id:<8} "
            f"{row.regency:<30} "
            f"{old:>12} -> {row.prefix_2}"
        )

    print()
    print(
        f"Overrides applied: {len(overridden)}"
    )


def validate_final_assignments(
    assignments: gpd.GeoDataFrame,
) -> None:
    """
    Validate the final 514-unit table.

    Unclassified administrative features are reported rather than silently
    discarded. GeoJSON generation is allowed only when all 514 are assigned.
    """

    unclassified = assignments[
        assignments[
            "prefix_2"
        ].isna()
    ]

    print()
    print(
        "Final administrative assignment validation:"
    )
    print()

    print(
        f"  Administrative units: {len(assignments)}"
    )
    print(
        "  Assigned:             "
        f"{assignments['prefix_2'].notna().sum()}"
    )
    print(
        f"  Unclassified:         {len(unclassified)}"
    )

    if not unclassified.empty:
        print()
        print(
            "Remaining unclassified administrative features:"
        )

        for row in unclassified.sort_values(
            [
                "region_id",
                "province",
                "regency",
            ]
        ).itertuples():
            print(
                f"  {row.regency_id:<8} "
                f"{row.regency} "
                f"({row.province})"
            )


def dissolve_prefix_2(
    assignments: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve administrative geometry into 2-digit prefix regions."""

    assigned = assignments[
        assignments[
            "prefix_2"
        ].notna()
    ].copy()

    dissolved = assigned[
        [
            "prefix_2",
            "prefix_1",
            "geometry",
        ]
    ].dissolve(
        by="prefix_2",
        as_index=False,
    )

    dissolved[
        "prefix_1"
    ] = dissolved[
        "prefix_2"
    ].str[
        0
    ]

    dissolved[
        "display"
    ] = dissolved[
        "prefix_2"
    ].map(
        display_prefix_2
    )

    dissolved = dissolved[
        [
            "prefix_2",
            "prefix_1",
            "display",
            "geometry",
        ]
    ].sort_values(
        "prefix_2"
    )

    return dissolved


def dissolve_prefix_1(
    assignments: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve administrative geometry into 1-digit prefix regions."""

    assigned = assignments[
        assignments[
            "prefix_1"
        ].notna()
    ].copy()

    dissolved = assigned[
        [
            "prefix_1",
            "geometry",
        ]
    ].dissolve(
        by="prefix_1",
        as_index=False,
    )

    dissolved[
        "display"
    ] = dissolved[
        "prefix_1"
    ].map(
        display_prefix_1
    )

    dissolved = dissolved[
        [
            "prefix_1",
            "display",
            "geometry",
        ]
    ].sort_values(
        "prefix_1"
    )

    return dissolved


def write_geojson(
    geodataframe: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """Write compact UTF-8 GeoJSON with deterministic feature ordering."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        geodataframe.to_json(
            drop_id=True
        )
    )

    path.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        ),
        encoding="utf-8",
    )


def representative_label_point(
    geometry,
):
    """
    Return a label point that lies inside the geometry.

    For MultiPolygons, label the largest polygon so scattered island groups
    do not place their prefix label in open water.
    """

    if geometry is None or geometry.is_empty:
        return None

    if isinstance(
        geometry,
        MultiPolygon,
    ):
        geometry = max(
            geometry.geoms,
            key=lambda polygon: polygon.area,
        )

    return geometry.representative_point()


def create_verification_png(
    regencies: gpd.GeoDataFrame,
    assignments: gpd.GeoDataFrame,
    prefix_2: gpd.GeoDataFrame,
) -> None:
    """
    Create the final visual verification image.

    Assigned administrative units:
        gray

    Unclassified administrative units:
        white

    Non-administrative source features:
        white

    Internal kabupaten/kota borders:
        thin gray

    Final 2-digit area-code-prefix borders:
        stronger colored outlines

    Labels:
        one 0XX label per dissolved prefix region
    """

    AREA_CODES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    assignment_lookup = assignments[
        [
            "regency_id",
            "prefix_2",
        ]
    ]

    verification = regencies.merge(
        assignment_lookup,
        on="regency_id",
        how="left",
        validate="one_to_one",
    )

    verification = gpd.GeoDataFrame(
        verification,
        geometry="geometry",
        crs=regencies.crs,
    )

    assigned = verification[
        verification[
            "prefix_2"
        ].notna()
    ]

    unassigned = verification[
        verification[
            "prefix_2"
        ].isna()
    ]

    fig, ax = plt.subplots(
        figsize=(
            VERIFICATION_FIGURE_WIDTH,
            VERIFICATION_FIGURE_HEIGHT,
        )
    )

    # White first so holes/unclassified units remain obvious.
    if not unassigned.empty:
        unassigned.plot(
            ax=ax,
            facecolor=UNCLASSIFIED_FILL_COLOR,
            edgecolor=ADMIN_BORDER_COLOR,
            linewidth=ADMIN_BORDER_WIDTH,
            zorder=1,
        )

    if not assigned.empty:
        assigned.plot(
            ax=ax,
            facecolor=ASSIGNED_FILL_COLOR,
            edgecolor=ADMIN_BORDER_COLOR,
            linewidth=ADMIN_BORDER_WIDTH,
            zorder=2,
        )

    # Plot each final prefix separately so adjacent prefix regions receive
    # clearly visible boundaries without relying on the original reference
    # raster's colors.
    color_cycle = plt.rcParams[
        "axes.prop_cycle"
    ].by_key()[
        "color"
    ]

    for index, row in enumerate(
        prefix_2.itertuples()
    ):
        color = color_cycle[
            index
            % len(
                color_cycle
            )
        ]

        single = gpd.GeoSeries(
            [
                row.geometry
            ],
            crs=prefix_2.crs,
        )

        single.boundary.plot(
            ax=ax,
            color=color,
            linewidth=PREFIX_BORDER_WIDTH,
            zorder=4,
        )

    # Prefix labels.
    for row in prefix_2.itertuples():
        point = representative_label_point(
            row.geometry
        )

        if point is None:
            continue

        label = f"0{row.prefix_2}"

        text = ax.text(
            point.x,
            point.y,
            label,
            ha="center",
            va="center",
            fontsize=LABEL_FONT_SIZE,
            color="black",
            zorder=6,
        )

        # White halo keeps labels readable over gray polygons/borders.
        text.set_path_effects(
            [
                __import__(
                    "matplotlib.patheffects",
                    fromlist=[
                        "withStroke"
                    ],
                ).withStroke(
                    linewidth=LABEL_HALO_WIDTH,
                    foreground="white",
                )
            ]
        )

    min_x, min_y, max_x, max_y = regencies.total_bounds

    x_padding = (
        max_x
        - min_x
    ) * 0.015

    y_padding = (
        max_y
        - min_y
    ) * 0.035

    ax.set_xlim(
        min_x - x_padding,
        max_x + x_padding,
    )

    ax.set_ylim(
        min_y - y_padding,
        max_y + y_padding,
    )

    ax.set_aspect(
        "equal",
        adjustable="box",
    )

    ax.axis(
        "off"
    )

    fig.tight_layout(
        pad=0
    )

    fig.savefig(
        VERIFICATION_PATH,
        dpi=VERIFICATION_DPI,
        bbox_inches="tight",
        pad_inches=0.05,
        facecolor="white",
    )

    plt.close(
        fig
    )


def print_prefix_summary(
    prefix_2: gpd.GeoDataFrame,
    prefix_1: gpd.GeoDataFrame,
    assignments: gpd.GeoDataFrame,
) -> None:
    """Print final prefix counts and administrative-unit distribution."""

    print()
    print(
        "Final prefix summary:"
    )
    print()

    print(
        f"  2-digit prefixes: {len(prefix_2)}"
    )

    print(
        "  Values: "
        + ", ".join(
            prefix_2[
                "prefix_2"
            ].tolist()
        )
    )

    print()
    print(
        f"  1-digit prefixes: {len(prefix_1)}"
    )

    print(
        "  Values: "
        + ", ".join(
            prefix_1[
                "prefix_1"
            ].tolist()
        )
    )

    print()
    print(
        "Administrative units per 2-digit prefix:"
    )
    print()

    counts = (
        assignments[
            "prefix_2"
        ]
        .dropna()
        .value_counts()
        .sort_index()
    )

    for prefix, count in counts.items():
        print(
            f"  0{prefix}-  {count:>3}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the final Indonesia area-code-prefix processing pipeline."""

    print(
        "Processing Indonesia area-code prefixes..."
    )
    print()

    print(
        f"Candidates: {CANDIDATES_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        f"Regencies:  {REGENCIES_PATH.relative_to(PROJECT_ROOT)}"
    )

    candidates = load_candidates(
        CANDIDATES_PATH
    )

    regencies = load_regencies()

    print()
    print(
        f"Candidate rows:       {len(candidates)}"
    )
    print(
        f"Regency GeoJSON rows: {len(regencies)}"
    )
    print(
        "Non-admin features:   "
        f"{len(NON_ADMINISTRATIVE_FEATURE_IDS)}"
    )

    assignments = build_final_assignments(
        candidates,
        regencies,
    )

    print_override_summary(
        assignments
    )

    validate_final_assignments(
        assignments
    )

    # Always create the verification image, even if something remains
    # unclassified. White polygons make those gaps easy to spot manually.
    prefix_2_partial = dissolve_prefix_2(
        assignments
    )

    create_verification_png(
        regencies,
        assignments,
        prefix_2_partial,
    )

    print()
    print(
        "Verification PNG:"
    )
    print(
        "  "
        + str(
            VERIFICATION_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    unclassified = assignments[
        assignments[
            "prefix_2"
        ].isna()
    ]

    if not unclassified.empty:
        print()
        print(
            "GeoJSON generation stopped because administrative "
            "features remain unclassified."
        )
        print(
            "Inspect the white features in verification.png, add the "
            "required manual overrides, and run this script again."
        )

        raise SystemExit(
            1
        )

    prefix_2 = prefix_2_partial

    prefix_1 = dissolve_prefix_1(
        assignments
    )

    write_geojson(
        prefix_2,
        OUTPUT_PREFIX_2_PATH,
    )

    write_geojson(
        prefix_1,
        OUTPUT_PREFIX_1_PATH,
    )

    print_prefix_summary(
        prefix_2,
        prefix_1,
        assignments,
    )

    print()
    print(
        "Outputs:"
    )
    print(
        "  "
        + str(
            OUTPUT_PREFIX_2_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )
    print(
        "  "
        + str(
            OUTPUT_PREFIX_1_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )
    print(
        "  "
        + str(
            VERIFICATION_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print(
        "Indonesia area-code-prefix processing complete."
    )


if __name__ == "__main__":
    main()
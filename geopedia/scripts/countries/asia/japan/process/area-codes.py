"""
Process Japan's telephone area-code geography into GeoPedia's canonical
intermediate GeoJSON datasets.

The raw HelloQuiz dataset contains 59 telephone area-code regions. Its
AreaCode values omit Japan's leading domestic trunk prefix "0", so values
such as "11", "96", "3", and "6" represent "011", "096", "03", and "06".

This processor:

1. Reads the raw 59-feature area-code GeoJSON.
2. Validates the source structure and area-code values.
3. Restores the leading "0" to each area code.
4. Adds the broader first-digit prefix used by GeoPedia's prefix quiz.
5. Writes the canonical 59-feature area-code dataset.
6. Dissolves those features by first-digit prefix to create the 9-feature
   prefix dataset.
7. Validates the resulting geometry and expected feature counts.

The generated public files intentionally preserve the source geometry
without simplification because both resulting datasets are already small
enough for direct use by GeoPedia.

Input:
    data/raw/countries/japan/area-codes/
        helloquiz-2-digit-area-codes.geojson

Outputs:
    public/data/countries/japan/geojson/
        area-codes.geojson
        area-code-prefixes.geojson

Run from the GeoPedia project root:

    python scripts/countries/japan/process/area-codes.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_PATH = Path(
    "data/raw/countries/japan/area-codes/"
    "helloquiz-2-digit-area-codes.geojson"
)

OUTPUT_DIR = Path(
    "public/data/countries/japan/geojson"
)

AREA_CODES_OUTPUT_PATH = OUTPUT_DIR / "area-codes.geojson"
PREFIXES_OUTPUT_PATH = OUTPUT_DIR / "area-code-prefixes.geojson"


# ---------------------------------------------------------------------------
# Expected source/output structure
# ---------------------------------------------------------------------------

EXPECTED_AREA_CODE_COUNT = 59
EXPECTED_PREFIX_COUNT = 9

EXPECTED_PREFIX_IDS = {
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
}


# ---------------------------------------------------------------------------
# GeoJSON helpers
# ---------------------------------------------------------------------------


def load_geojson(path: Path) -> dict[str, Any]:
    """Load and validate the basic structure of a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON input does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def write_geojson(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    """Write a canonical GeoJSON FeatureCollection."""
    collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def extract_polygonal_geometry(geometry):
    """
    Return only the polygonal portion of a Shapely geometry.

    Polygon and MultiPolygon geometries are returned directly.
    GeometryCollections are traversed recursively and their polygonal
    components are merged. Lower-dimensional artifacts such as lines and
    points are discarded.
    """
    if geometry is None or geometry.is_empty:
        return None

    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygonal_parts = []

        for child in geometry.geoms:
            polygonal = extract_polygonal_geometry(child)

            if polygonal is None:
                continue

            if isinstance(polygonal, Polygon):
                polygonal_parts.append(polygonal)
            elif isinstance(polygonal, MultiPolygon):
                polygonal_parts.extend(polygonal.geoms)

        if not polygonal_parts:
            return None

        return unary_union(polygonal_parts)

    return None


def validate_polygonal_geometry(
    geometry,
    *,
    label: str,
) -> None:
    """Ensure a geometry is non-empty, valid, and polygonal."""
    if geometry is None:
        raise ValueError(
            f"{label} has no polygonal geometry."
        )

    if geometry.is_empty:
        raise ValueError(
            f"{label} has empty geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{label} has unsupported geometry type "
            f"{geometry.geom_type!r}."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{label} has invalid geometry."
        )


# ---------------------------------------------------------------------------
# Area-code normalization
# ---------------------------------------------------------------------------


def normalize_area_code(raw_code: Any) -> str:
    """
    Restore Japan's leading domestic trunk prefix to a raw area-code value.

    The HelloQuiz source deliberately stores the geographic area-code portion
    without the leading "0":

        "11" -> "011"
        "96" -> "096"
        "3"  -> "03"
        "6"  -> "06"

    The source values are expected to contain one or two digits.
    """
    code = str(raw_code).strip()

    if not code:
        raise ValueError(
            "Encountered an empty AreaCode value."
        )

    if not code.isdigit():
        raise ValueError(
            f"AreaCode must contain only digits: {code!r}"
        )

    if len(code) not in {1, 2}:
        raise ValueError(
            "Expected HelloQuiz AreaCode values to contain "
            f"one or two digits, got {code!r}."
        )

    return f"0{code}"


def get_prefix_id(area_code: str) -> str:
    """
    Return the broad first-digit prefix ID for a normalized area code.

    Examples:
        011 -> 01
        019 -> 01
        03  -> 03
        042 -> 04
        06  -> 06
        099 -> 09
    """
    if (
        len(area_code) < 2
        or not area_code.startswith("0")
        or not area_code.isdigit()
    ):
        raise ValueError(
            f"Invalid normalized area code: {area_code!r}"
        )

    return area_code[:2]


def get_prefix_display(prefix_id: str) -> str:
    """Return the player-facing label for a broad area-code prefix."""
    return f"{prefix_id}-"


# ---------------------------------------------------------------------------
# Area-code processing
# ---------------------------------------------------------------------------


def process_area_codes(
    raw: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Convert the raw HelloQuiz features into GeoPedia's canonical schema.

    Canonical properties:

        area_code_id
        area_code
        prefix_id
        prefix
    """
    raw_features = raw["features"]

    if len(raw_features) != EXPECTED_AREA_CODE_COUNT:
        raise ValueError(
            "Unexpected raw area-code feature count: "
            f"expected {EXPECTED_AREA_CODE_COUNT}, "
            f"got {len(raw_features)}."
        )

    processed = []
    seen_area_codes = set()

    for index, feature in enumerate(raw_features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {index} has no valid properties object."
            )

        if "AreaCode" not in properties:
            raise ValueError(
                f"Feature {index} is missing AreaCode."
            )

        area_code = normalize_area_code(
            properties["AreaCode"]
        )

        if area_code in seen_area_codes:
            raise ValueError(
                f"Duplicate area code: {area_code}"
            )

        seen_area_codes.add(area_code)

        prefix_id = get_prefix_id(area_code)
        prefix = get_prefix_display(prefix_id)

        raw_geometry = feature.get("geometry")

        if raw_geometry is None:
            raise ValueError(
                f"Area code {area_code} has no geometry."
            )

        geometry = shape(raw_geometry)

        validate_polygonal_geometry(
            geometry,
            label=f"Area code {area_code}",
        )

        processed.append(
            {
                "type": "Feature",
                "properties": {
                    "area_code_id": area_code,
                    "area_code": area_code,
                    "prefix_id": prefix_id,
                    "prefix": prefix,
                },
                "geometry": mapping(geometry),
            }
        )

    if len(seen_area_codes) != EXPECTED_AREA_CODE_COUNT:
        raise ValueError(
            "Processed area-code count does not match "
            f"expected count {EXPECTED_AREA_CODE_COUNT}."
        )

    processed.sort(
        key=lambda feature: feature["properties"]["area_code_id"]
    )

    return processed


# ---------------------------------------------------------------------------
# Prefix generation
# ---------------------------------------------------------------------------


def build_prefixes(
    area_code_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Dissolve the 59 area-code regions into the 9 broad prefix regions.

    Every area-code feature contributes its complete geometry to the prefix
    determined by the first digit after the leading domestic trunk "0".
    """
    geometries_by_prefix = defaultdict(list)

    for feature in area_code_features:
        properties = feature["properties"]
        prefix_id = properties["prefix_id"]

        geometries_by_prefix[prefix_id].append(
            shape(feature["geometry"])
        )

    actual_prefix_ids = set(geometries_by_prefix)

    if actual_prefix_ids != EXPECTED_PREFIX_IDS:
        missing = sorted(
            EXPECTED_PREFIX_IDS - actual_prefix_ids
        )
        unexpected = sorted(
            actual_prefix_ids - EXPECTED_PREFIX_IDS
        )

        raise ValueError(
            "Unexpected prefix set. "
            f"Missing: {missing}; "
            f"unexpected: {unexpected}."
        )

    prefixes = []

    for prefix_id in sorted(geometries_by_prefix):
        merged = unary_union(
            geometries_by_prefix[prefix_id]
        )

        merged = extract_polygonal_geometry(merged)

        validate_polygonal_geometry(
            merged,
            label=f"Prefix {prefix_id}",
        )

        prefixes.append(
            {
                "type": "Feature",
                "properties": {
                    "prefix_id": prefix_id,
                    "prefix": get_prefix_display(
                        prefix_id
                    ),
                },
                "geometry": mapping(merged),
            }
        )

    if len(prefixes) != EXPECTED_PREFIX_COUNT:
        raise ValueError(
            "Unexpected prefix feature count: "
            f"expected {EXPECTED_PREFIX_COUNT}, "
            f"got {len(prefixes)}."
        )

    return prefixes


# ---------------------------------------------------------------------------
# Final validation/reporting
# ---------------------------------------------------------------------------


def validate_area_codes(
    features: list[dict[str, Any]],
) -> None:
    """Perform final validation of the canonical area-code dataset."""
    if len(features) != EXPECTED_AREA_CODE_COUNT:
        raise ValueError(
            "Final area-code dataset has "
            f"{len(features)} features; expected "
            f"{EXPECTED_AREA_CODE_COUNT}."
        )

    codes = [
        feature["properties"]["area_code_id"]
        for feature in features
    ]

    if len(codes) != len(set(codes)):
        raise ValueError(
            "Final area-code dataset contains duplicate IDs."
        )

    prefix_counts = Counter(
        feature["properties"]["prefix_id"]
        for feature in features
    )

    if set(prefix_counts) != EXPECTED_PREFIX_IDS:
        raise ValueError(
            "Final area-code dataset contains an "
            "unexpected prefix set."
        )

    for feature in features:
        properties = feature["properties"]
        area_code = properties["area_code_id"]

        if properties["area_code"] != area_code:
            raise ValueError(
                f"Area code {area_code} has inconsistent "
                "area_code properties."
            )

        expected_prefix_id = get_prefix_id(
            area_code
        )

        if properties["prefix_id"] != expected_prefix_id:
            raise ValueError(
                f"Area code {area_code} has incorrect "
                f"prefix_id {properties['prefix_id']!r}."
            )

        if properties["prefix"] != get_prefix_display(
            expected_prefix_id
        ):
            raise ValueError(
                f"Area code {area_code} has incorrect "
                f"prefix display {properties['prefix']!r}."
            )

        validate_polygonal_geometry(
            shape(feature["geometry"]),
            label=f"Area code {area_code}",
        )


def validate_prefixes(
    features: list[dict[str, Any]],
) -> None:
    """Perform final validation of the dissolved prefix dataset."""
    if len(features) != EXPECTED_PREFIX_COUNT:
        raise ValueError(
            "Final prefix dataset has "
            f"{len(features)} features; expected "
            f"{EXPECTED_PREFIX_COUNT}."
        )

    prefix_ids = {
        feature["properties"]["prefix_id"]
        for feature in features
    }

    if prefix_ids != EXPECTED_PREFIX_IDS:
        raise ValueError(
            "Final prefix dataset contains an "
            "unexpected prefix set."
        )

    for feature in features:
        properties = feature["properties"]
        prefix_id = properties["prefix_id"]

        if properties["prefix"] != get_prefix_display(
            prefix_id
        ):
            raise ValueError(
                f"Prefix {prefix_id} has incorrect "
                f"display {properties['prefix']!r}."
            )

        validate_polygonal_geometry(
            shape(feature["geometry"]),
            label=f"Prefix {prefix_id}",
        )


def print_summary(
    area_codes: list[dict[str, Any]],
    prefixes: list[dict[str, Any]],
) -> None:
    """Print a concise processing summary."""
    prefix_counts = Counter(
        feature["properties"]["prefix_id"]
        for feature in area_codes
    )

    print("Japan area-code processing complete.")
    print()
    print(
        f"  Area-code regions: {len(area_codes)}"
    )
    print(
        f"  Prefix regions:    {len(prefixes)}"
    )
    print()
    print("  Area codes by prefix:")

    for prefix_id in sorted(prefix_counts):
        print(
            f"    {get_prefix_display(prefix_id):<4} "
            f"{prefix_counts[prefix_id]}"
        )

    print()
    print(
        f"  Area codes: {AREA_CODES_OUTPUT_PATH}"
    )
    print(
        f"  Prefixes:   {PREFIXES_OUTPUT_PATH}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Process Japan's area-code datasets."""
    print("Processing Japan area-code geography...")
    print()

    raw = load_geojson(RAW_PATH)

    area_codes = process_area_codes(raw)
    prefixes = build_prefixes(area_codes)

    validate_area_codes(area_codes)
    validate_prefixes(prefixes)

    write_geojson(
        AREA_CODES_OUTPUT_PATH,
        area_codes,
    )

    write_geojson(
        PREFIXES_OUTPUT_PATH,
        prefixes,
    )

    print_summary(
        area_codes,
        prefixes,
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ecuador"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "ecuador"
    / "geojson"
)


# ---------------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------------

LEVELS = {
    "provinces": {
        "source": "provinces.geojson",
        "output": "provinces.geojson",
        "target_bytes": 200_000,
        "expected_features": 24,
        "id_property": "province_id",
    },
    "cantons": {
        "source": "cantons.geojson",
        "output": "cantons.geojson",
        "target_bytes": 1_000_000,
        "expected_features": 221,
        "id_property": "canton_id",
    },
    "parishes": {
        "source": "parishes.geojson",
        "output": "parishes.geojson",
        "target_bytes": 3_000_000,
        "expected_features": 1_042,
        "id_property": "parish_id",
    },
}


# Start conservatively and let the search adjust.
#
# These are percentages of retained removable vertices,
# not percentages of file size.
INITIAL_PERCENTAGES = {
    "provinces": 0.30,
    "cantons": 0.45,
    "parishes": 0.60,
}


MIN_PERCENTAGE = 0.01
MAX_PERCENTAGE = 5.0

SEARCH_ITERATIONS = 12

COORDINATE_PRECISION = 0.000001


# ---------------------------------------------------------------------------
# Mapshaper
# ---------------------------------------------------------------------------

def run_mapshaper(
    source_path: Path,
    output_path: Path,
    percentage: float,
) -> None:
    command = [
        "npx",
        "mapshaper",
        str(source_path),
        "-simplify",
        "weighted",
        f"{percentage:.8f}%",
        "keep-shapes",
        "-o",
        f"precision={COORDINATE_PRECISION}",
        "format=geojson",
        "force",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Mapshaper failed.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# GeoJSON normalization
# ---------------------------------------------------------------------------

def load_geojson(
    path: Path,
) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def normalize_runtime_geojson(
    data: dict[str, Any],
    id_property: str,
    expected_features: int,
) -> bytes:
    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Expected a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "GeoJSON features must be a list."
        )

    if len(features) != expected_features:
        raise ValueError(
            f"Expected {expected_features:,} features, "
            f"got {len(features):,}."
        )

    seen_ids: set[str] = set()

    for feature in features:
        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                "Feature is missing properties."
            )

        feature_id = properties.get(
            id_property
        )

        if not isinstance(
            feature_id,
            str,
        ):
            raise ValueError(
                f"Feature is missing "
                f"{id_property!r}."
            )

        if feature_id in seen_ids:
            raise ValueError(
                f"Duplicate feature ID "
                f"{feature_id!r}."
            )

        seen_ids.add(
            feature_id
        )

        # Explicitly restore the GeoJSON top-level ID.
        feature["id"] = feature_id

        geometry = feature.get(
            "geometry"
        )

        if not isinstance(
            geometry,
            dict,
        ):
            raise ValueError(
                f"Feature {feature_id} "
                "has no geometry."
            )

        geometry_type = geometry.get(
            "type"
        )

        if geometry_type not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError(
                f"Feature {feature_id} "
                f"has unexpected geometry "
                f"type {geometry_type!r}."
            )

    normalized = {
        "type": "FeatureCollection",
        "features": features,
    }

    return json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def process_candidate(
    source_path: Path,
    temp_path: Path,
    percentage: float,
    id_property: str,
    expected_features: int,
) -> bytes:
    run_mapshaper(
        source_path,
        temp_path,
        percentage,
    )

    data = load_geojson(
        temp_path
    )

    return normalize_runtime_geojson(
        data,
        id_property,
        expected_features,
    )


# ---------------------------------------------------------------------------
# Percentage search
# ---------------------------------------------------------------------------

def find_best_percentage(
    name: str,
    config: dict[str, Any],
    temp_dir: Path,
) -> tuple[float, bytes]:
    source_path = (
        SOURCE_DIR
        / config["source"]
    )

    temp_path = (
        temp_dir
        / f"{name}.geojson"
    )

    target_bytes = config[
        "target_bytes"
    ]

    id_property = config[
        "id_property"
    ]

    expected_features = config[
        "expected_features"
    ]

    initial_percentage = (
        INITIAL_PERCENTAGES[name]
    )

    print(
        f"Testing initial retention: "
        f"{initial_percentage:.4f}%"
    )

    initial_data = process_candidate(
        source_path,
        temp_path,
        initial_percentage,
        id_property,
        expected_features,
    )

    initial_size = len(
        initial_data
    )

    print(
        f"Initial size: "
        f"{initial_size:,} bytes "
        f"({initial_size / 1_000_000:.3f} MB)"
    )

    # -------------------------------------------------------
    # Establish search bounds.
    # -------------------------------------------------------

    if initial_size <= target_bytes:
        low = initial_percentage
        best_percentage = initial_percentage
        best_data = initial_data

        high = min(
            initial_percentage * 2,
            MAX_PERCENTAGE,
        )

        while high <= MAX_PERCENTAGE:
            candidate = process_candidate(
                source_path,
                temp_path,
                high,
                id_property,
                expected_features,
            )

            size = len(
                candidate
            )

            print(
                f"Testing {high:.6f}% "
                f"→ {size / 1_000_000:.3f} MB"
            )

            if size > target_bytes:
                break

            low = high
            best_percentage = high
            best_data = candidate

            if high == MAX_PERCENTAGE:
                return (
                    best_percentage,
                    best_data,
                )

            high = min(
                high * 2,
                MAX_PERCENTAGE,
            )

    else:
        high = initial_percentage
        low = max(
            initial_percentage / 2,
            MIN_PERCENTAGE,
        )

        best_percentage = -1.0
        best_data = b""

        while low >= MIN_PERCENTAGE:
            candidate = process_candidate(
                source_path,
                temp_path,
                low,
                id_property,
                expected_features,
            )

            size = len(
                candidate
            )

            print(
                f"Testing {low:.6f}% "
                f"→ {size / 1_000_000:.3f} MB"
            )

            if size <= target_bytes:
                best_percentage = low
                best_data = candidate
                break

            high = low

            if low == MIN_PERCENTAGE:
                raise ValueError(
                    f"{name} is still above its "
                    f"size target at "
                    f"{MIN_PERCENTAGE}% retention."
                )

            low = max(
                low / 2,
                MIN_PERCENTAGE,
            )

    # -------------------------------------------------------
    # Binary search for the highest retention percentage
    # that remains under the target.
    # -------------------------------------------------------

    for _ in range(
        SEARCH_ITERATIONS
    ):
        middle = (
            low + high
        ) / 2

        candidate = process_candidate(
            source_path,
            temp_path,
            middle,
            id_property,
            expected_features,
        )

        size = len(
            candidate
        )

        print(
            f"Testing {middle:.6f}% "
            f"→ {size / 1_000_000:.3f} MB"
        )

        if size <= target_bytes:
            low = middle
            best_percentage = middle
            best_data = candidate
        else:
            high = middle

    if best_percentage < 0:
        raise ValueError(
            f"Could not find a valid "
            f"simplification percentage "
            f"for {name}."
        )

    return (
        best_percentage,
        best_data,
    )


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def process_level(
    name: str,
    config: dict[str, Any],
    temp_dir: Path,
) -> None:
    print()
    print(
        f"===== {name.upper()} ====="
    )

    target_bytes = config[
        "target_bytes"
    ]

    percentage, data = (
        find_best_percentage(
            name,
            config,
            temp_dir,
        )
    )

    output_path = (
        OUTPUT_DIR
        / config["output"]
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_bytes(
        data
    )

    final_size = len(
        data
    )

    if final_size > target_bytes:
        raise ValueError(
            f"{name} exceeded target: "
            f"{final_size:,} > "
            f"{target_bytes:,} bytes."
        )

    print()
    print(
        f"Chosen retention: "
        f"{percentage:.6f}%"
    )

    print(
        f"Features:         "
        f"{config['expected_features']:,}"
    )

    print(
        f"Target size:      "
        f"{target_bytes / 1_000_000:.3f} MB"
    )

    print(
        f"Final size:       "
        f"{final_size:,} bytes "
        f"({final_size / 1_000_000:.3f} MB)"
    )

    print(
        f"Output:           "
        f"{output_path}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Generating Ecuador runtime "
        "administrative GeoJSON..."
    )

    with tempfile.TemporaryDirectory() as directory:
        temp_dir = Path(
            directory
        )

        for name, config in LEVELS.items():
            process_level(
                name,
                config,
                temp_dir,
            )

    print()
    print(
        "Finished Ecuador runtime "
        "administrative GeoJSON."
    )


if __name__ == "__main__":
    main()
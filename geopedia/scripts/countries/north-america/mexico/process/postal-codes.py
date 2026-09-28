"""
Process Mexican SEPOMEX postal-code geometry into 2-digit prefix regions.

Source data:
    open-mexico/mexico-geojson
    https://github.com/open-mexico/mexico-geojson

The source repository converts publicly available SEPOMEX / Correos de
México KML postal-code geometry into one GeoJSON file per Mexican state.

Input:
    data/raw/countries/mexico/postal-codes/*.geojson

Output:
    public/data/countries/mexico/geojson/postal-code-prefixes.geojson

Each source feature contains a 5-digit postal code in `d_codigo`.
Features are grouped by the first two digits of that code and dissolved
nationwide into one Polygon or MultiPolygon per 2-digit prefix.

The output also records the first digit and every Mexican state touched
by each prefix so the quiz can later support property-based groups.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely import make_valid, set_precision, union_all
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from shapely.errors import GEOSException


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "mexico"
    / "postal-codes"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "mexico"
    / "geojson"
    / "postal-code-prefixes.geojson"
)

EXPECTED_STATE_IDS = {
    f"{state_id:02d}"
    for state_id in range(1, 33)
}

STATE_FILENAME_PATTERN = re.compile(
    r"^(?P<state_id>\d{2})-.+\.geojson$",
    re.IGNORECASE,
)

POSTAL_CODE_PROPERTY = "d_codigo"

POSTAL_CODE_LENGTH = 5
PREFIX_LENGTH = 2

# EPSG:6372 is a projected CRS suitable for spatial processing in Mexico.
SOURCE_CRS = "EPSG:4326"
PROCESSING_CRS = "EPSG:6372"

# Snap coordinates to a small projected grid before unioning. This helps
# remove tiny inconsistencies along boundaries without visibly changing them.
PRECISION_GRID_METERS = 0.1

# Simplification happens after all postal-code polygons for a prefix have
# been dissolved. Increase only if the resulting runtime file is too large.
SIMPLIFY_TOLERANCE_METERS = 100.0

# Runtime coordinates do not need excessive decimal precision.
COORDINATE_DECIMAL_PLACES = 6


TO_PROCESSING_CRS = Transformer.from_crs(
    SOURCE_CRS,
    PROCESSING_CRS,
    always_xy=True,
)

TO_SOURCE_CRS = Transformer.from_crs(
    PROCESSING_CRS,
    SOURCE_CRS,
    always_xy=True,
)


def load_geojson(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} does not contain a feature list."
        )

    return data


def get_state_files() -> list[tuple[str, Path]]:
    """Return the 32 source state files sorted by INEGI state ID."""

    if not INPUT_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {INPUT_DIRECTORY}"
        )

    state_files: list[tuple[str, Path]] = []
    seen_state_ids: set[str] = set()

    for path in INPUT_DIRECTORY.glob("*.geojson"):
        match = STATE_FILENAME_PATTERN.match(path.name)

        if match is None:
            raise ValueError(
                "Unexpected GeoJSON filename in postal-code source "
                f"directory: {path.name}"
            )

        state_id = match.group("state_id")

        if state_id not in EXPECTED_STATE_IDS:
            raise ValueError(
                f"{path.name} has invalid state ID {state_id}."
            )

        if state_id in seen_state_ids:
            raise ValueError(
                f"Duplicate source file for state {state_id}."
            )

        seen_state_ids.add(state_id)
        state_files.append(
            (
                state_id,
                path,
            )
        )

    missing_state_ids = (
        EXPECTED_STATE_IDS
        - seen_state_ids
    )

    if missing_state_ids:
        raise ValueError(
            "Missing postal-code source files for states: "
            + ", ".join(
                sorted(missing_state_ids)
            )
        )

    if len(state_files) != 32:
        raise ValueError(
            "Expected exactly 32 state GeoJSON files, "
            f"found {len(state_files)}."
        )

    return sorted(
        state_files,
        key=lambda item: item[0],
    )


def normalize_postal_code(
    raw_value: object,
    *,
    filename: str,
    feature_index: int,
) -> str:
    """
    Convert a source `d_codigo` value into a validated 5-digit string.

    JSON numbers are accepted because the source repository commonly stores
    postal codes numerically. Leading zeroes are restored with zero-padding.
    """

    if isinstance(raw_value, bool):
        raise ValueError(
            f"{filename} feature {feature_index} has invalid "
            f"{POSTAL_CODE_PROPERTY}: {raw_value!r}."
        )

    if isinstance(raw_value, int):
        postal_code = str(raw_value)

    elif isinstance(raw_value, float):
        if not raw_value.is_integer():
            raise ValueError(
                f"{filename} feature {feature_index} has non-integer "
                f"{POSTAL_CODE_PROPERTY}: {raw_value!r}."
            )

        postal_code = str(
            int(raw_value)
        )

    elif isinstance(raw_value, str):
        postal_code = raw_value.strip()

    else:
        raise ValueError(
            f"{filename} feature {feature_index} has unsupported "
            f"{POSTAL_CODE_PROPERTY}: {raw_value!r}."
        )

    if not postal_code.isdigit():
        raise ValueError(
            f"{filename} feature {feature_index} has non-numeric "
            f"postal code {postal_code!r}."
        )

    postal_code = postal_code.zfill(
        POSTAL_CODE_LENGTH
    )

    if len(postal_code) != POSTAL_CODE_LENGTH:
        raise ValueError(
            f"{filename} feature {feature_index} has postal code "
            f"{postal_code!r}, expected {POSTAL_CODE_LENGTH} digits."
        )

    return postal_code


def repair_geometry(
    geometry: BaseGeometry,
) -> BaseGeometry:
    """
    Repair geometry while retaining only polygonal components.

    Some SEPOMEX source geometries can become GeometryCollections containing
    a mixture of polygon, line, and point remnants. Those lower-dimensional
    pieces are irrelevant for postal regions and can cause GEOS `make_valid`
    operations to fail, so polygonal components are isolated first.

    If GEOS cannot repair an individual polygon with `make_valid()`, a
    zero-width buffer is used as a fallback for that malformed component.
    """

    if geometry.is_empty:
        raise ValueError(
            "Encountered empty geometry."
        )

    def collect_polygon_parts(
        value: BaseGeometry,
    ) -> list[BaseGeometry]:
        """Recursively collect Polygon components from a geometry."""

        if value.is_empty:
            return []

        if value.geom_type == "Polygon":
            return [value]

        if value.geom_type == "MultiPolygon":
            return list(
                value.geoms
            )

        if value.geom_type == "GeometryCollection":
            parts: list[BaseGeometry] = []

            for part in value.geoms:
                parts.extend(
                    collect_polygon_parts(
                        part
                    )
                )

            return parts

        # Lines, points, and other lower-dimensional remnants do not
        # represent postal-code area and are intentionally discarded.
        return []

    source_parts = collect_polygon_parts(
        geometry
    )

    if not source_parts:
        raise ValueError(
            "Geometry contains no polygonal components."
        )

    repaired_parts: list[BaseGeometry] = []

    for part in source_parts:
        repaired = part

        if not repaired.is_valid:
            try:
                repaired = make_valid(
                    repaired
                )
            except GEOSException:
                # Some malformed source polygons cause GEOS make_valid()
                # itself to fail. buffer(0) is used only as a fallback.
                repaired = repaired.buffer(
                    0
                )

        for repaired_part in collect_polygon_parts(
            repaired
        ):
            if repaired_part.is_empty:
                continue

            if not repaired_part.is_valid:
                try:
                    repaired_part = make_valid(
                        repaired_part
                    )
                except GEOSException:
                    repaired_part = repaired_part.buffer(
                        0
                    )

            repaired_parts.extend(
                collect_polygon_parts(
                    repaired_part
                )
            )

    repaired_parts = [
        part
        for part in repaired_parts
        if not part.is_empty
    ]

    if not repaired_parts:
        raise ValueError(
            "Geometry contains no polygonal area after repair."
        )

    if len(repaired_parts) == 1:
        geometry = repaired_parts[0]

    else:
        try:
            geometry = union_all(
                repaired_parts
            )
        except GEOSException:
            # A final zero-width buffer on individual components can resolve
            # residual topology problems before attempting the union again.
            buffered_parts = [
                part.buffer(0)
                for part in repaired_parts
                if not part.buffer(0).is_empty
            ]

            geometry = union_all(
                buffered_parts
            )

    if geometry.is_empty:
        raise ValueError(
            "Geometry became empty after polygon repair."
        )

    # A union can theoretically produce another collection, so normalize
    # the result one final time.
    if geometry.geom_type == "GeometryCollection":
        final_parts = collect_polygon_parts(
            geometry
        )

        if not final_parts:
            raise ValueError(
                "Repaired GeometryCollection contains no polygons."
            )

        geometry = union_all(
            final_parts
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            "Expected polygonal geometry after repair, "
            f"got {geometry.geom_type}."
        )

    if not geometry.is_valid:
        raise ValueError(
            "Geometry remains invalid after repair."
        )

    return geometry


def prepare_source_geometry(
    geometry_data: dict,
) -> BaseGeometry:
    """
    Convert one source geometry to projected, repaired polygonal geometry.

    Precision snapping occurs in meters after reprojection so tiny coordinate
    discrepancies are less likely to produce slivers during the dissolve.
    """

    geometry = shape(
        geometry_data
    )

    geometry = repair_geometry(
        geometry
    )

    geometry = transform(
        TO_PROCESSING_CRS.transform,
        geometry,
    )

    geometry = repair_geometry(
        geometry
    )

    geometry = set_precision(
        geometry,
        grid_size=PRECISION_GRID_METERS,
        mode="valid_output",
    )

    return repair_geometry(
        geometry
    )


def dissolve_geometries(
    geometries: list[BaseGeometry],
) -> BaseGeometry:
    """Dissolve polygonal geometries into one repaired geometry."""

    if not geometries:
        raise ValueError(
            "Cannot dissolve an empty geometry list."
        )

    dissolved = union_all(
        geometries
    )

    dissolved = repair_geometry(
        dissolved
    )

    if SIMPLIFY_TOLERANCE_METERS > 0:
        dissolved = dissolved.simplify(
            SIMPLIFY_TOLERANCE_METERS,
            preserve_topology=True,
        )

        dissolved = repair_geometry(
            dissolved
        )

    return dissolved


def round_coordinates(
    value: object,
) -> object:
    """
    Recursively round GeoJSON coordinates without altering object structure.

    Geometry operations themselves are performed by Shapely. This step only
    reduces serialized runtime precision after processing is complete.
    """

    if isinstance(value, float):
        return round(
            value,
            COORDINATE_DECIMAL_PLACES,
        )

    if isinstance(value, list):
        return [
            round_coordinates(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: round_coordinates(item)
            for key, item in value.items()
        }

    return value


def create_output_feature(
    prefix: str,
    geometry: BaseGeometry,
    state_ids: set[str],
) -> dict:
    """Create one runtime GeoJSON feature for a 2-digit postal-code prefix."""

    geometry = transform(
        TO_SOURCE_CRS.transform,
        geometry,
    )

    geometry = repair_geometry(
        geometry
    )

    geometry_data = round_coordinates(
        mapping(geometry)
    )

    return {
        "type": "Feature",
        "id": prefix,
        "properties": {
            "postal_code_prefix_id": prefix,
            "postal_code_prefix": prefix,
            "first_digit": prefix[0],
            "state_ids": sorted(
                state_ids
            ),
        },
        "geometry": geometry_data,
    }


def validate_output(
    feature_collection: dict,
) -> None:
    """Validate the generated postal-code-prefix runtime dataset."""

    if feature_collection.get("type") != "FeatureCollection":
        raise ValueError(
            "Output is not a FeatureCollection."
        )

    features = feature_collection.get(
        "features"
    )

    if not isinstance(features, list):
        raise ValueError(
            "Output does not contain a feature list."
        )

    if not features:
        raise ValueError(
            "Output contains no features."
        )

    seen_ids: set[str] = set()

    expected_properties = {
        "postal_code_prefix_id",
        "postal_code_prefix",
        "first_digit",
        "state_ids",
    }

    for feature in features:
        feature_id = feature.get(
            "id"
        )

        if not isinstance(feature_id, str):
            raise ValueError(
                f"Feature has invalid ID {feature_id!r}."
            )

        if len(feature_id) != PREFIX_LENGTH:
            raise ValueError(
                f"Feature ID {feature_id!r} is not "
                f"{PREFIX_LENGTH} digits."
            )

        if not feature_id.isdigit():
            raise ValueError(
                f"Feature ID {feature_id!r} is not numeric."
            )

        if feature_id in seen_ids:
            raise ValueError(
                f"Duplicate prefix feature {feature_id}."
            )

        seen_ids.add(
            feature_id
        )

        properties = feature.get(
            "properties"
        )

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {feature_id} has invalid properties."
            )

        if set(properties) != expected_properties:
            raise ValueError(
                f"Feature {feature_id} has unexpected properties: "
                f"{sorted(properties)}."
            )

        prefix_id = properties.get(
            "postal_code_prefix_id"
        )

        if prefix_id != feature_id:
            raise ValueError(
                f"Feature {feature_id} has mismatched "
                f"postal_code_prefix_id {prefix_id!r}."
            )

        prefix = properties.get(
            "postal_code_prefix"
        )

        if prefix != feature_id:
            raise ValueError(
                f"Feature {feature_id} has mismatched "
                f"postal_code_prefix {prefix!r}."
            )

        first_digit = properties.get(
            "first_digit"
        )

        if first_digit != feature_id[0]:
            raise ValueError(
                f"Feature {feature_id} has invalid first_digit "
                f"{first_digit!r}."
            )

        state_ids = properties.get(
            "state_ids"
        )

        if not isinstance(
            state_ids,
            list,
        ):
            raise ValueError(
                f"Feature {feature_id} has invalid state_ids."
            )

        if not state_ids:
            raise ValueError(
                f"Feature {feature_id} has no state IDs."
            )

        if state_ids != sorted(
            set(state_ids)
        ):
            raise ValueError(
                f"Feature {feature_id} has duplicate or unsorted "
                "state IDs."
            )

        invalid_state_ids = (
            set(state_ids)
            - EXPECTED_STATE_IDS
        )

        if invalid_state_ids:
            raise ValueError(
                f"Feature {feature_id} has invalid state IDs: "
                + ", ".join(
                    sorted(invalid_state_ids)
                )
            )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            geometry_data,
            dict,
        ):
            raise ValueError(
                f"Feature {feature_id} has invalid geometry."
            )

        geometry = shape(
            geometry_data
        )

        geometry = repair_geometry(
            geometry
        )

        if not geometry.is_valid:
            raise ValueError(
                f"Feature {feature_id} has invalid output geometry."
            )


def write_output(
    feature_collection: dict,
) -> None:
    """Write the final compact GeoJSON runtime file."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    """Process all Mexican postal-code source files."""

    state_files = get_state_files()

    prefix_geometries: dict[
        str,
        list[BaseGeometry],
    ] = defaultdict(list)

    prefix_state_ids: dict[
        str,
        set[str],
    ] = defaultdict(set)

    all_postal_codes: set[str] = set()
    
    postal_code_sources: dict[
        str,
        list[str],
    ] = defaultdict(list)

    source_feature_count = 0
    duplicate_postal_code_count = 0
    repaired_geometry_count = 0
    
    skipped_geometry_count = 0
    skipped_geometries: list[str] = []

    print(
        f"Processing {len(state_files)} Mexican state files..."
    )

    for state_id, path in state_files:
        data = load_geojson(
            path
        )

        features = data[
            "features"
        ]

        state_postal_codes: set[str] = set()

        for feature_index, feature in enumerate(
            features
        ):
            if feature.get("type") != "Feature":
                raise ValueError(
                    f"{path.name} feature {feature_index} "
                    "is not a GeoJSON Feature."
                )

            properties = feature.get(
                "properties"
            )

            if not isinstance(
                properties,
                dict,
            ):
                raise ValueError(
                    f"{path.name} feature {feature_index} "
                    "has invalid properties."
                )

            if POSTAL_CODE_PROPERTY not in properties:
                raise ValueError(
                    f"{path.name} feature {feature_index} "
                    f"is missing {POSTAL_CODE_PROPERTY!r}."
                )

            postal_code = normalize_postal_code(
                properties[
                    POSTAL_CODE_PROPERTY
                ],
                filename=path.name,
                feature_index=feature_index,
            )

            prefix = postal_code[
                :PREFIX_LENGTH
            ]

            geometry_data = feature.get(
                "geometry"
            )

            if not isinstance(
                geometry_data,
                dict,
            ):
                raise ValueError(
                    f"{path.name} feature {feature_index} "
                    "has invalid geometry."
                )

            source_geometry = shape(
                geometry_data
            )

            if not source_geometry.is_valid:
                repaired_geometry_count += 1

            try:
                geometry = prepare_source_geometry(
                    geometry_data
                )

            except ValueError as error:
                if str(error) != (
                    "Geometry contains no polygonal area after repair."
                ):
                    raise

                skipped_geometry_count += 1

                skipped_description = (
                    f"{path.name} feature {feature_index}: "
                    f"postal code {postal_code}"
                )

                skipped_geometries.append(
                    skipped_description
                )

                print(
                    f"    WARNING: skipped {skipped_description} "
                    "because its geometry contains no polygonal area "
                    "after repair."
                )

                continue

            prefix_geometries[
                prefix
            ].append(
                geometry
            )

            prefix_state_ids[
                prefix
            ].add(
                state_id
            )

            postal_code_source = (
                f"{path.name} feature {feature_index}"
            )

            if postal_code in all_postal_codes:
                duplicate_postal_code_count += 1

            postal_code_sources[
                postal_code
            ].append(
                postal_code_source
            )

            all_postal_codes.add(
                postal_code
            )

            state_postal_codes.add(
                postal_code
            )

            source_feature_count += 1

        state_prefixes = sorted({
            postal_code[:PREFIX_LENGTH]
            for postal_code in state_postal_codes
        })

        print(
            f"  {state_id} {path.name}: "
            f"{len(features):,} features, "
            f"{len(state_postal_codes):,} postal codes, "
            f"{len(state_prefixes)} prefixes "
            f"({', '.join(state_prefixes)})"
        )

    prefixes = sorted(
        prefix_geometries
    )

    print()
    print(
        f"Found {len(prefixes)} distinct 2-digit prefixes."
    )
    print(
        "Prefixes: "
        + ", ".join(prefixes)
    )

    print()
    print(
        "Dissolving postal-code polygons by prefix..."
    )

    output_features: list[dict] = []

    for prefix in prefixes:
        geometries = prefix_geometries[
            prefix
        ]

        print(
            f"  {prefix}: "
            f"{len(geometries):,} source polygons, "
            f"states {', '.join(sorted(prefix_state_ids[prefix]))}"
        )

        dissolved = dissolve_geometries(
            geometries
        )

        output_features.append(
            create_output_feature(
                prefix,
                dissolved,
                prefix_state_ids[
                    prefix
                ],
            )
        )

    feature_collection = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    validate_output(
        feature_collection
    )

    write_output(
        feature_collection
    )

    multi_state_prefixes = [
        prefix
        for prefix in prefixes
        if len(
            prefix_state_ids[
                prefix
            ]
        ) > 1
    ]

    output_size_mb = (
        OUTPUT_PATH.stat().st_size
        / 1024
        / 1024
    )
    
    duplicate_postal_codes = {
        postal_code: sources
        for postal_code, sources
        in postal_code_sources.items()
        if len(sources) > 1
    }

    print()
    print("Validation passed.")
    print()
    print("Summary:")
    print(
        f"  State files: {len(state_files)}"
    )
    print(
        f"  Source features: {source_feature_count:,}"
    )
    print(
        f"  Unique 5-digit postal codes: "
        f"{len(all_postal_codes):,}"
    )
    print(
        f"  Duplicate postal-code occurrences: "
        f"{duplicate_postal_code_count:,}"
    )
    if duplicate_postal_codes:
        print(
            "  Duplicate postal codes:"
        )

        for postal_code, sources in sorted(
            duplicate_postal_codes.items()
        ):
            print(
                f"    {postal_code}: "
                + ", ".join(
                    sources
                )
            )
    print(
        f"  Invalid source geometries repaired: "
        f"{repaired_geometry_count:,}"
    )
    
    print(
    f"  Source geometries skipped: "
    f"{skipped_geometry_count:,}"
    )

    if skipped_geometries:
        print(
            "  Skipped geometries:"
        )

        for skipped_geometry in skipped_geometries:
            print(
                f"    {skipped_geometry}"
            )
    print(
        f"  2-digit prefixes: {len(prefixes)}"
    )
    print(
        f"  Multi-state prefixes: "
        f"{len(multi_state_prefixes)}"
    )

    if multi_state_prefixes:
        print(
            "  Multi-state prefix IDs: "
            + ", ".join(
                multi_state_prefixes
            )
        )

    print(
        f"  Output size: {output_size_mb:.2f} MB"
    )
    print(
        f"  Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
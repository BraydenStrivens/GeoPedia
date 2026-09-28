from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyproj import CRS, Transformer
from shapely import (
    coverage_simplify,
    make_valid,
    union_all,
)
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import transform as shapely_transform


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "argentina"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "argentina"
    / "geojson"
)

FILES = {
    "full": (
        INPUT_DIR / "phone-codes-full.geojson",
        OUTPUT_DIR / "phone-codes-full.geojson",
    ),
    "3-digit": (
        INPUT_DIR / "phone-codes-3-digit.geojson",
        OUTPUT_DIR / "phone-codes-3-digit.geojson",
    ),
    "2-digit": (
        INPUT_DIR / "phone-codes-2-digit.geojson",
        OUTPUT_DIR / "phone-codes-2-digit.geojson",
    ),
    "1-digit": (
        INPUT_DIR / "phone-codes-1-digit.geojson",
        OUTPUT_DIR / "phone-codes-1-digit.geojson",
    ),
}


# The phone-code regions are already approximate Voronoi regions, so sub-kilometer
# boundary detail is not useful to the quiz. Start conservatively at 500 meters.
#
# Shapely's coverage_simplify() is used instead of simplifying each feature
# independently. That is important here because the phone-code polygons form a
# complete national partition: shared boundaries should remain shared rather
# than becoming independent lines that can create gaps or overlaps.
SIMPLIFY_TOLERANCE_METERS = 500.0

# Runtime coordinates do not need Python's full floating-point precision.
# Five decimal places is roughly meter-level precision in latitude/longitude.
COORDINATE_DECIMAL_PLACES = 5

# The simplified coverage should remain extremely close to the original
# processed coverage. These are failure thresholds, not targets.
MAX_COVERAGE_DIFFERENCE_RATIO = 0.001  # 0.1%
MAX_OVERLAP_RATIO = 0.001  # 0.1%


# A country-centered projected CRS lets the simplification tolerance be
# expressed in meters. LAEA is suitable for a country-scale Argentina dataset.
PROCESSING_CRS = CRS.from_proj4(
    "+proj=laea "
    "+lat_0=-38 "
    "+lon_0=-64 "
    "+datum=WGS84 "
    "+units=m "
    "+no_defs"
)

TO_PROCESSING_CRS = Transformer.from_crs(
    "EPSG:4326",
    PROCESSING_CRS,
    always_xy=True,
)

TO_RUNTIME_CRS = Transformer.from_crs(
    PROCESSING_CRS,
    "EPSG:4326",
    always_xy=True,
)

TO_EQUAL_AREA_CRS = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:6933",
    always_xy=True,
)


def load_geojson(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def write_geojson(
    path: Path,
    feature_collection: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            feature_collection,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def polygonal_only(
    geometry: Any,
) -> Polygon | MultiPolygon:
    if geometry is None or geometry.is_empty:
        return Polygon()

    if isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        return geometry

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        polygon_parts = [
            part
            for part in geometry.geoms
            if isinstance(
                part,
                (Polygon, MultiPolygon),
            )
            and not part.is_empty
        ]

        if not polygon_parts:
            return Polygon()

        return polygonal_only(
            union_all(
                polygon_parts
            )
        )

    return Polygon()


def clean_polygonal(
    geometry: Any,
) -> Polygon | MultiPolygon:
    if geometry is None or geometry.is_empty:
        return Polygon()

    if not geometry.is_valid:
        geometry = make_valid(
            geometry
        )

    geometry = polygonal_only(
        geometry
    )

    if (
        not geometry.is_empty
        and not geometry.is_valid
    ):
        geometry = polygonal_only(
            make_valid(
                geometry
            )
        )

    return geometry


def count_coordinates(
    geometry: Any,
) -> int:
    if geometry is None or geometry.is_empty:
        return 0

    if isinstance(
        geometry,
        Polygon,
    ):
        return (
            len(geometry.exterior.coords)
            + sum(
                len(ring.coords)
                for ring in geometry.interiors
            )
        )

    if isinstance(
        geometry,
        MultiPolygon,
    ):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    return 0


def round_coordinates(
    value: Any,
) -> Any:
    if isinstance(
        value,
        float,
    ):
        return round(
            value,
            COORDINATE_DECIMAL_PLACES,
        )

    if isinstance(
        value,
        list,
    ):
        return [
            round_coordinates(item)
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return [
            round_coordinates(item)
            for item in value
        ]

    return value


def equal_area_geometry(
    geometry: Any,
) -> Any:
    return shapely_transform(
        TO_EQUAL_AREA_CRS.transform,
        geometry,
    )


def area_statistics(
    geometries: list[
        Polygon | MultiPolygon
    ],
) -> tuple[
    float,
    float,
    float,
]:
    union_geometry = clean_polygonal(
        union_all(
            geometries
        )
    )

    union_equal_area = (
        equal_area_geometry(
            union_geometry
        )
    )

    union_area = (
        union_equal_area.area
    )

    individual_area = sum(
        equal_area_geometry(
            geometry
        ).area
        for geometry in geometries
    )

    overlap_area = max(
        0.0,
        individual_area - union_area,
    )

    return (
        union_area,
        individual_area,
        overlap_area,
    )


def simplify_dataset(
    label: str,
    input_path: Path,
    output_path: Path,
) -> None:
    print()
    print(
        "=" * 80
    )
    print(
        f"{label.upper()} PHONE-CODE GEOMETRY"
    )
    print(
        "=" * 80
    )

    data = load_geojson(
        input_path
    )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise RuntimeError(
            f"{input_path} does not contain "
            "a GeoJSON feature list."
        )

    source_geometries: list[
        Polygon | MultiPolygon
    ] = []

    for index, feature in enumerate(
        features
    ):
        geometry_data = feature.get(
            "geometry"
        )

        if geometry_data is None:
            raise RuntimeError(
                f"{label} feature {index} "
                "has no geometry."
            )

        geometry = clean_polygonal(
            shape(
                geometry_data
            )
        )

        if geometry.is_empty:
            raise RuntimeError(
                f"{label} feature {index} "
                "has empty geometry."
            )

        source_geometries.append(
            geometry
        )

    source_union = clean_polygonal(
        union_all(
            source_geometries
        )
    )

    source_coordinate_count = sum(
        count_coordinates(
            geometry
        )
        for geometry
        in source_geometries
    )

    source_size = (
        input_path.stat().st_size
    )

    projected_geometries = [
        clean_polygonal(
            shapely_transform(
                TO_PROCESSING_CRS.transform,
                geometry,
            )
        )
        for geometry
        in source_geometries
    ]

    simplified_projected = list(
        coverage_simplify(
            projected_geometries,
            SIMPLIFY_TOLERANCE_METERS,
            simplify_boundary=True,
        )
    )

    if (
        len(simplified_projected)
        != len(features)
    ):
        raise RuntimeError(
            f"{label} coverage simplification "
            "changed the feature count."
        )

    simplified_geometries: list[
        Polygon | MultiPolygon
    ] = []

    for index, geometry in enumerate(
        simplified_projected
    ):
        geometry = clean_polygonal(
            geometry
        )

        if geometry.is_empty:
            raise RuntimeError(
                f"{label} feature {index} "
                "became empty after simplification."
            )

        runtime_geometry = clean_polygonal(
            shapely_transform(
                TO_RUNTIME_CRS.transform,
                geometry,
            )
        )

        if runtime_geometry.is_empty:
            raise RuntimeError(
                f"{label} feature {index} "
                "became empty after reprojection."
            )

        if not runtime_geometry.is_valid:
            raise RuntimeError(
                f"{label} feature {index} "
                "is invalid after simplification."
            )

        simplified_geometries.append(
            runtime_geometry
        )

    simplified_union = clean_polygonal(
        union_all(
            simplified_geometries
        )
    )

    # Compare simplified coverage with the original coverage while topology
    # operations are still in WGS84. Reproject only the resulting difference
    # when measuring its area.
    coverage_difference = clean_polygonal(
        source_union.symmetric_difference(
            simplified_union
        )
    )

    source_equal_area = (
        equal_area_geometry(
            source_union
        )
    )

    difference_equal_area = (
        equal_area_geometry(
            coverage_difference
        )
    )

    source_area = (
        source_equal_area.area
    )

    coverage_difference_area = (
        difference_equal_area.area
    )

    coverage_difference_ratio = (
        coverage_difference_area
        / max(
            source_area,
            1.0,
        )
    )

    (
        simplified_union_area,
        _,
        simplified_overlap_area,
    ) = area_statistics(
        simplified_geometries
    )

    simplified_overlap_ratio = (
        simplified_overlap_area
        / max(
            source_area,
            1.0,
        )
    )

    if (
        coverage_difference_ratio
        > MAX_COVERAGE_DIFFERENCE_RATIO
    ):
        raise RuntimeError(
            f"{label} simplification changed "
            "coverage too much.\n"
            f"Coverage difference: "
            f"{coverage_difference_ratio:.12%}"
        )

    if (
        simplified_overlap_ratio
        > MAX_OVERLAP_RATIO
    ):
        raise RuntimeError(
            f"{label} simplification created "
            "too much overlap.\n"
            f"Overlap: "
            f"{simplified_overlap_ratio:.12%}"
        )

    output_features: list[
        dict[str, Any]
    ] = []

    for (
        feature,
        geometry,
    ) in zip(
        features,
        simplified_geometries,
        strict=True,
    ):
        geometry_data = mapping(
            geometry
        )

        output_feature = {
            "type": "Feature",
            "id": feature.get("id"),
            "properties": feature.get(
                "properties",
                {},
            ),
            "geometry": {
                "type":
                    geometry_data[
                        "type"
                    ],
                "coordinates":
                    round_coordinates(
                        geometry_data[
                            "coordinates"
                        ]
                    ),
            },
        }

        output_features.append(
            output_feature
        )

    output_collection = {
        "type":
            "FeatureCollection",
        "features":
            output_features,
    }

    write_geojson(
        output_path,
        output_collection,
    )

    output_size = (
        output_path.stat().st_size
    )

    simplified_coordinate_count = sum(
        count_coordinates(
            geometry
        )
        for geometry
        in simplified_geometries
    )

    coordinate_reduction = (
        1.0
        - (
            simplified_coordinate_count
            / max(
                source_coordinate_count,
                1,
            )
        )
    )

    size_reduction = (
        1.0
        - (
            output_size
            / max(
                source_size,
                1,
            )
        )
    )

    print(
        f"Features: "
        f"{len(features):,}"
    )

    print(
        f"Tolerance: "
        f"{SIMPLIFY_TOLERANCE_METERS:,.0f} m"
    )

    print(
        f"Coordinates before: "
        f"{source_coordinate_count:,}"
    )

    print(
        f"Coordinates after:  "
        f"{simplified_coordinate_count:,}"
    )

    print(
        f"Coordinate reduction: "
        f"{coordinate_reduction:.1%}"
    )

    print(
        f"Input size:  "
        f"{source_size / 1_000_000:,.2f} MB"
    )

    print(
        f"Output size: "
        f"{output_size / 1_000_000:,.2f} MB"
    )

    print(
        f"Size reduction: "
        f"{size_reduction:.1%}"
    )

    print(
        f"Coverage difference: "
        f"{coverage_difference_area / 1_000_000:,.6f} km² "
        f"({coverage_difference_ratio:.12%})"
    )

    print(
        f"Simplified union area: "
        f"{simplified_union_area / 1_000_000:,.2f} km²"
    )

    print(
        f"Overlap after simplification: "
        f"{simplified_overlap_area / 1_000_000:,.6f} km² "
        f"({simplified_overlap_ratio:.12%})"
    )

    print(
        f"Wrote: {output_path}"
    )


def main() -> None:
    print(
        "Simplifying Argentina phone-code "
        "GeoJSONs for runtime..."
    )

    for (
        label,
        (
            input_path,
            output_path,
        ),
    ) in FILES.items():
        if not input_path.exists():
            raise FileNotFoundError(
                f"Missing processed input: "
                f"{input_path}"
            )

        simplify_dataset(
            label,
            input_path,
            output_path,
        )

    print()
    print(
        "=" * 80
    )
    print(
        "ARGENTINA PHONE-CODE "
        "SIMPLIFICATION COMPLETE"
    )
    print(
        "=" * 80
    )


if __name__ == "__main__":
    main()
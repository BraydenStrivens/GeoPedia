"""
Process Vietnam's post-reform administrative boundaries.

Sources
-------
Provincial boundaries:
    data/raw/countries/vietnam/post-reform-admin/vnm_admin1.geojson

Commune-level boundaries:
    data/raw/countries/vietnam/post-reform-admin/wards/*.json

The ward source contains one JSON file per province. Each file contains
the province ID/name and its commune-level units. Individual units contain
one or more polygon rings in the custom `polygons` property.

Outputs
-------
data/intermediate/countries/vietnam/post-reform-admin/
    provinces.geojson
    communes.geojson

Expected feature counts
-----------------------
Provinces: 34
Commune-level units: 3,321

Post-reform Vietnam uses a two-tier administrative hierarchy, so the
commune-level output links directly to provinces and intentionally has
no district fields.

This script performs normalization and custom JSON-to-GeoJSON conversion
only. Geometry simplification is handled by a separate script.
"""

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.validation import make_valid


RAW_DIR = Path(
    "data/raw/countries/vietnam/post-reform-admin"
)

PROVINCES_SOURCE = RAW_DIR / "vnm_admin1.geojson"
WARDS_DIR = RAW_DIR / "wards"

OUTPUT_DIR = Path(
    "data/intermediate/countries/vietnam/post-reform-admin"
)

PROVINCES_PATH = OUTPUT_DIR / "provinces.geojson"
COMMUNES_PATH = OUTPUT_DIR / "communes.geojson"

EXPECTED_PROVINCES = 34
EXPECTED_COMMUNES = 3_321


def normalize_province_id(value: object) -> str:
    """
    Normalize province IDs to the bare two-digit codes used by ward files.

    Example:
        VN01 -> 01
    """
    value = str(value).strip()

    if value.upper().startswith("VN"):
        value = value[2:]

    return value


def close_ring(
    coordinates: list[list[float]],
) -> list[list[float]]:
    """Return a polygon ring with matching first and last coordinates."""
    if len(coordinates) < 3:
        raise ValueError(
            f"Polygon ring has fewer than 3 coordinates: {coordinates}"
        )

    ring = [list(point) for point in coordinates]

    if ring[0] != ring[-1]:
        ring.append(ring[0].copy())

    if len(ring) < 4:
        raise ValueError(
            "Closed polygon ring has fewer than 4 coordinate positions."
        )

    return ring


def polygons_to_geometry(
    polygon_parts: list[list[list[float]]],
) -> BaseGeometry:
    """
    Convert the ward source's polygon-part representation to Shapely.

    Each entry in `polygons` is treated as an exterior polygon ring.
    A single part becomes a Polygon; multiple parts become a MultiPolygon.
    """
    if not polygon_parts:
        raise ValueError("Commune-level unit has no polygon parts.")

    polygons: list[Polygon] = []

    for part in polygon_parts:
        ring = close_ring(part)
        polygon = Polygon(ring)

        if polygon.is_empty:
            raise ValueError("Polygon part produced empty geometry.")

        polygons.append(polygon)

    if len(polygons) == 1:
        return polygons[0]

    return MultiPolygon(polygons)


def repair_polygonal_geometry(
    geometry: BaseGeometry,
) -> BaseGeometry:
    """
    Repair invalid geometry and return polygonal geometry only.

    make_valid() can return a GeometryCollection when invalid polygon
    boundaries collapse into lower-dimensional LineString or Point
    components. GeoPedia only needs the polygonal area, so those
    lower-dimensional remnants are discarded.

    Valid Polygon and MultiPolygon geometries are returned unchanged.
    """
    if geometry.is_valid:
        return geometry

    repaired = make_valid(geometry)

    if isinstance(repaired, (Polygon, MultiPolygon)):
        return repaired

    if isinstance(repaired, GeometryCollection):
        polygon_parts: list[Polygon] = []

        for part in repaired.geoms:
            if isinstance(part, Polygon):
                polygon_parts.append(part)

            elif isinstance(part, MultiPolygon):
                polygon_parts.extend(part.geoms)

        if not polygon_parts:
            raise ValueError(
                "Geometry repair produced no polygonal components."
            )

        repaired = unary_union(polygon_parts)

        if isinstance(repaired, (Polygon, MultiPolygon)):
            return repaired

        raise ValueError(
            "Polygonal components did not resolve to "
            f"Polygon/MultiPolygon: {repaired.geom_type}"
        )

    raise ValueError(
        "Geometry repair produced unsupported geometry type: "
        f"{repaired.geom_type}"
    )
    
    
def prepare_provinces() -> gpd.GeoDataFrame:
    """Normalize the official post-reform provincial GeoJSON."""
    source = gpd.read_file(PROVINCES_SOURCE)

    required_columns = {
        "adm1_name1",
        "adm1_pcode",
        "adm1_type_en",
        "adm1_type_vi",
        "geometry",
    }

    missing_columns = required_columns - set(source.columns)

    if missing_columns:
        raise ValueError(
            "Province source is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    provinces = source[
        [
            "adm1_pcode",
            "adm1_name1",
            "adm1_type_en",
            "adm1_type_vi",
            "geometry",
        ]
    ].copy()

    provinces["province_id"] = provinces["adm1_pcode"].map(
        normalize_province_id
    )
    provinces["province"] = provinces["adm1_name1"].astype(str).str.strip()
    provinces["province_type"] = (
        provinces["adm1_type_en"].astype(str).str.strip()
    )
    provinces["province_type_native"] = (
        provinces["adm1_type_vi"].astype(str).str.strip()
    )

    provinces = provinces[
        [
            "province_id",
            "province",
            "province_type",
            "province_type_native",
            "geometry",
        ]
    ]

    if provinces.crs is None:
        raise ValueError("Province source has no CRS.")

    provinces = provinces.to_crs("EPSG:4326")

    # Repair source topology defects while preserving polygonal geometry.
    provinces["geometry"] = provinces.geometry.map(
        repair_polygonal_geometry
    )

    return provinces


def prepare_communes() -> gpd.GeoDataFrame:
    """Combine all 34 province ward files into one commune-level layer."""
    records: list[dict[str, Any]] = []

    ward_files = sorted(
        path
        for path in WARDS_DIR.glob("*.json")
        if path.name.lower() != "index.json"
    )

    if len(ward_files) != EXPECTED_PROVINCES:
        raise ValueError(
            "Unexpected number of province ward files: "
            f"expected {EXPECTED_PROVINCES}, got {len(ward_files)}."
        )

    for path in ward_files:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        province_id = str(data["provinceId"]).strip()
        province_name = str(data["provinceName"]).strip()

        if path.stem != province_id:
            raise ValueError(
                f"{path}: filename ID {path.stem!r} does not match "
                f"provinceId {province_id!r}."
            )

        wards = data.get("wards")

        if not isinstance(wards, list):
            raise ValueError(f"{path}: 'wards' is not a list.")

        for ward in wards:
            commune_id = str(ward["id"]).strip()
            commune_name = str(ward["name"]).strip()
            commune_type = str(ward["type"]).strip()

            geometry = polygons_to_geometry(ward["polygons"])
            geometry = repair_polygonal_geometry(geometry)

            records.append(
                {
                    "province_id": province_id,
                    "province": province_name,
                    "commune_id": commune_id,
                    "commune": commune_name,
                    "commune_type": commune_type,
                    "geometry": geometry,
                }
            )

    return gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs="EPSG:4326",
    )


def validate_layer(
    gdf: gpd.GeoDataFrame,
    *,
    name: str,
    id_column: str,
    expected_count: int,
) -> None:
    """Validate count, IDs, and geometry for a processed layer."""
    if len(gdf) != expected_count:
        raise ValueError(
            f"{name} count mismatch: "
            f"expected {expected_count:,}, got {len(gdf):,}."
        )

    unique_ids = gdf[id_column].nunique()

    if unique_ids != expected_count:
        raise ValueError(
            f"{name} unique ID count mismatch: "
            f"expected {expected_count:,}, got {unique_ids:,}."
        )

    if gdf[id_column].eq("").any():
        raise ValueError(f"{name} contains blank IDs.")

    if gdf.geometry.isna().any():
        raise ValueError(f"{name} contains missing geometry.")

    if gdf.geometry.is_empty.any():
        raise ValueError(f"{name} contains empty geometry.")

    invalid_count = int((~gdf.geometry.is_valid).sum())

    if invalid_count:
        raise ValueError(
            f"{name} contains {invalid_count:,} invalid geometries."
        )


def validate_hierarchy(
    provinces: gpd.GeoDataFrame,
    communes: gpd.GeoDataFrame,
) -> None:
    """Ensure every commune references exactly one known province."""
    province_ids = set(provinces["province_id"])
    commune_parent_ids = set(communes["province_id"])

    missing_parents = sorted(commune_parent_ids - province_ids)
    provinces_without_communes = sorted(province_ids - commune_parent_ids)

    if missing_parents:
        raise ValueError(
            "Commune data references unknown province IDs: "
            + ", ".join(missing_parents)
        )

    if provinces_without_communes:
        raise ValueError(
            "Provinces contain no commune-level units: "
            + ", ".join(provinces_without_communes)
        )

    province_names = dict(
        zip(
            provinces["province_id"],
            provinces["province"],
        )
    )

    mismatches: list[str] = []

    for province_id, group in communes.groupby("province_id"):
        ward_names = set(group["province"])

        if len(ward_names) != 1:
            mismatches.append(
                f"{province_id}: multiple ward-source province names"
            )
            continue

        ward_name = next(iter(ward_names))
        province_name = province_names[province_id]

        if ward_name != province_name:
            mismatches.append(
                f"{province_id}: {ward_name!r} != {province_name!r}"
            )

    if mismatches:
        raise ValueError(
            "Province-name hierarchy mismatches:\n"
            + "\n".join(mismatches)
        )


def main() -> None:
    print("Processing Vietnam post-reform administrative data...")

    provinces = prepare_provinces()
    communes = prepare_communes()

    validate_layer(
        provinces,
        name="Provinces",
        id_column="province_id",
        expected_count=EXPECTED_PROVINCES,
    )

    validate_layer(
        communes,
        name="Commune-level units",
        id_column="commune_id",
        expected_count=EXPECTED_COMMUNES,
    )

    validate_hierarchy(provinces, communes)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    provinces.to_file(PROVINCES_PATH, driver="GeoJSON")
    communes.to_file(COMMUNES_PATH, driver="GeoJSON")

    print()
    print("Vietnam post-reform administrative processing complete.")
    print(f"Provinces:           {len(provinces):,}")
    print(f"Commune-level units: {len(communes):,}")
    print()
    print(f"Wrote: {PROVINCES_PATH}")
    print(f"Wrote: {COMMUNES_PATH}")


if __name__ == "__main__":
    main()
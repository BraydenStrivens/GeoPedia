"""
Builds Colombia's 4-digit postal-code regions for GeoPedia.

Source:
    public/data/countries/colombia/geojson/municipalities.geojson

Output:
    public/data/countries/colombia/geojson/postal-codes-4-digit.geojson

Each municipality contains one or more logical 4-digit postal-code answers.

Municipalities are grouped only when their complete answer sets are identical.
For example:

    A -> ["0510"]
    B -> ["0510"]
    C -> ["0510", "0520"]

A and B may be merged because their complete answer sets match exactly.
C must remain separate because it has a different answer set, even though it
shares "0510" with A and B.

This prevents overlapping runtime polygons while still allowing neighboring
features with identical answer semantics to be dissolved together.

Bogotá is represented by the synthetic answer:

    bogota-1101-1120

which corresponds to the 1101 through 1120 postal-prefix range.
"""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


SOURCE_PATH = Path(
    "public/data/countries/colombia/geojson/municipalities.geojson"
)

OUTPUT_PATH = Path(
    "public/data/countries/colombia/geojson/postal-codes-4-digit.geojson"
)

EXPECTED_MUNICIPALITY_COUNT = 1122

BOGOTA_POSTAL_ANSWER = "bogota-1101-1120"

EXPECTED_LOGICAL_ANSWER_COUNT = 305


def polygonal_only(
    geometry: BaseGeometry,
) -> BaseGeometry:
    """
    Return only the polygonal portion of a geometry.

    Geometry repair can occasionally produce GeometryCollections containing
    lower-dimensional artifacts. GeoPedia only needs polygonal components.
    """
    if geometry is None or geometry.is_empty:
        return geometry

    if isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        return geometry

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            if isinstance(part, Polygon):
                polygons.append(part)

            elif isinstance(part, MultiPolygon):
                polygons.extend(part.geoms)

            elif isinstance(
                part,
                GeometryCollection,
            ):
                nested = polygonal_only(part)

                if isinstance(
                    nested,
                    Polygon,
                ):
                    polygons.append(nested)

                elif isinstance(
                    nested,
                    MultiPolygon,
                ):
                    polygons.extend(
                        nested.geoms
                    )

        if not polygons:
            return GeometryCollection()

        return unary_union(polygons)

    return GeometryCollection()


def validate_source(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Validate the processed municipality dataset."""
    required_columns = {
        "id",
        "department_id",
        "name",
        "postal_code_4_digit",
        "geometry",
    }

    missing_columns = (
        required_columns - set(gdf.columns)
    )

    if missing_columns:
        raise ValueError(
            "Municipality source is missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    if len(gdf) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(gdf)}."
        )

    if gdf.crs is None:
        raise ValueError(
            "Municipality GeoJSON has no CRS."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            "Municipality GeoJSON contains null geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            "Municipality GeoJSON contains empty geometries."
        )

    if (~gdf.geometry.is_valid).any():
        raise ValueError(
            "Municipality GeoJSON contains invalid geometries."
        )

    municipality_ids = (
        gdf["id"]
        .astype(str)
        .str.strip()
    )

    if municipality_ids.duplicated().any():
        raise ValueError(
            "Municipality GeoJSON contains duplicate IDs."
        )


def get_postal_answers(
    value: object,
    municipality_id: str,
) -> tuple[str, ...]:
    """
    Normalize one municipality's postal answers into a canonical tuple.

    GeoPandas may deserialize GeoJSON array properties as NumPy arrays rather
    than ordinary Python lists. Array-like values are converted before
    validation.

    The returned tuple is sorted so answer-set equality is independent of
    source ordering.
    """
    if isinstance(value, str):
        answers = [value]

    elif hasattr(value, "tolist"):
        converted = value.tolist()

        if isinstance(converted, str):
            answers = [converted]

        elif isinstance(converted, list):
            answers = converted

        else:
            raise ValueError(
                f"Municipality {municipality_id} has unsupported "
                "postal_code_4_digit data after array conversion."
            )

    elif isinstance(value, (list, tuple)):
        answers = list(value)

    else:
        raise ValueError(
            f"Municipality {municipality_id} has an unsupported "
            f"postal_code_4_digit value: {value!r} "
            f"({type(value).__name__})."
        )

    normalized_answers: list[str] = []

    for answer in answers:
        if not isinstance(answer, str):
            raise ValueError(
                f"Municipality {municipality_id} contains a non-string "
                f"postal answer: {answer!r}"
            )

        normalized = answer.strip()

        if not normalized:
            raise ValueError(
                f"Municipality {municipality_id} contains a blank "
                "postal answer."
            )

        validate_postal_answer(
            normalized
        )

        normalized_answers.append(
            normalized
        )

    if not normalized_answers:
        raise ValueError(
            f"Municipality {municipality_id} has no postal answers."
        )

    if len(normalized_answers) != len(
        set(normalized_answers)
    ):
        raise ValueError(
            f"Municipality {municipality_id} contains duplicate "
            "postal answers."
        )

    return tuple(
        sorted(normalized_answers)
    )


def validate_postal_answer(
    answer: str,
) -> None:
    """Validate one logical 4-digit postal answer."""
    if answer == BOGOTA_POSTAL_ANSWER:
        return

    if len(answer) != 4 or not answer.isdigit():
        raise ValueError(
            f"Invalid 4-digit postal answer: {answer}"
        )


def merge_geometries(
    geometries: list[BaseGeometry],
    answer_key: tuple[str, ...],
) -> BaseGeometry:
    """
    Merge polygons belonging to one identical complete answer set.

    Because every source polygon in the group has identical quiz semantics,
    dissolving them cannot create ambiguous overlapping answer regions.
    """
    geometry = unary_union(
        geometries
    )

    if not geometry.is_valid:
        geometry = geometry.make_valid()

    geometry = polygonal_only(
        geometry
    )

    if geometry is None or geometry.is_empty:
        raise ValueError(
            f"Postal answer set {answer_key} produced an empty geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Postal answer set {answer_key} produced an invalid geometry."
        )

    if not isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        raise ValueError(
            f"Postal answer set {answer_key} produced unsupported "
            f"geometry type {geometry.geom_type}."
        )

    return geometry


def build_postal_regions(
    municipalities: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Build non-overlapping postal regions grouped by complete answer set.

    Features are merged only when every answer attached to the source polygons
    is identical. Partial answer overlap does not cause a merge.
    """
    geometries_by_answers: dict[
        tuple[str, ...],
        list[BaseGeometry],
    ] = {}

    municipality_ids_by_answers: dict[
        tuple[str, ...],
        list[str],
    ] = {}

    department_ids_by_answers: dict[
        tuple[str, ...],
        set[str],
    ] = {}

    municipality_names_by_answers: dict[
        tuple[str, ...],
        list[str],
    ] = {}

    for row in municipalities.itertuples():
        municipality_id = str(
            row.id
        ).strip()

        department_id = str(
            row.department_id
        ).strip()

        municipality_name = str(
            row.name
        ).strip()

        answers = get_postal_answers(
            row.postal_code_4_digit,
            municipality_id,
        )

        geometries_by_answers.setdefault(
            answers,
            [],
        ).append(
            row.geometry
        )

        municipality_ids_by_answers.setdefault(
            answers,
            [],
        ).append(
            municipality_id
        )

        department_ids_by_answers.setdefault(
            answers,
            set(),
        ).add(
            department_id
        )

        municipality_names_by_answers.setdefault(
            answers,
            [],
        ).append(
            municipality_name
        )

    rows: list[dict] = []

    sorted_answer_sets = sorted(
        geometries_by_answers,
        key=lambda answers: (
            BOGOTA_POSTAL_ANSWER in answers,
            answers,
        ),
    )

    for answers in sorted_answer_sets:
        geometry = merge_geometries(
            geometries_by_answers[answers],
            answers,
        )

        municipality_ids = sorted(
            municipality_ids_by_answers[answers]
        )

        municipality_names = sorted(
            municipality_names_by_answers[answers]
        )

        department_ids = sorted(
            department_ids_by_answers[answers]
        )

        if len(department_ids) == 1:
            department_property: str | list[str] = (
                department_ids[0]
            )
        else:
            department_property = department_ids

        feature_id = "-".join(
            answers
        )

        rows.append(
            {
                "id": feature_id,
                "postal_code_4_digit": list(
                    answers
                ),
                "department_id": department_property,
                "municipality_ids": municipality_ids,
                "municipality_names": municipality_names,
                "geometry": geometry,
            }
        )

    return gpd.GeoDataFrame(
        rows,
        geometry="geometry",
        crs=municipalities.crs,
    )


def collect_logical_answers(
    gdf: gpd.GeoDataFrame,
) -> set[str]:
    """Collect every distinct logical postal answer represented by the map."""
    answers: set[str] = set()

    for value in gdf[
        "postal_code_4_digit"
    ]:
        if hasattr(value, "tolist"):
            value = value.tolist()

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "Output postal_code_4_digit must always be an array."
            )

        for answer in value:
            if not isinstance(answer, str):
                raise ValueError(
                    "Output contains a non-string postal answer."
                )

            answers.add(answer)

    return answers


def validate_output(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Validate the completed non-overlapping postal-code geography."""
    if gdf.empty:
        raise ValueError(
            "Postal output contains no features."
        )

    if gdf["id"].duplicated().any():
        raise ValueError(
            "Postal output contains duplicate feature IDs."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            "Postal output contains null geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            "Postal output contains empty geometries."
        )

    if (~gdf.geometry.is_valid).any():
        raise ValueError(
            "Postal output contains invalid geometries."
        )

    invalid_types = set(
        gdf.geometry.geom_type.unique()
    ) - {
        "Polygon",
        "MultiPolygon",
    }

    if invalid_types:
        raise ValueError(
            "Postal output contains unsupported geometry types: "
            + ", ".join(
                sorted(invalid_types)
            )
        )

    logical_answers = collect_logical_answers(
        gdf
    )

    if len(logical_answers) != EXPECTED_LOGICAL_ANSWER_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_LOGICAL_ANSWER_COUNT} logical postal "
            f"answers, found {len(logical_answers)}."
        )

    if BOGOTA_POSTAL_ANSWER not in logical_answers:
        raise ValueError(
            "Postal output is missing Bogotá's synthetic answer."
        )

    answer_sets = []

    for value in gdf[
        "postal_code_4_digit"
    ]:
        if hasattr(value, "tolist"):
            value = value.tolist()

        answer_sets.append(
            tuple(
                sorted(value)
            )
        )

    if len(answer_sets) != len(
        set(answer_sets)
    ):
        raise ValueError(
            "Postal output contains duplicate answer sets that should "
            "have been merged."
        )


def write_geojson(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Write compact UTF-8 GeoJSON to GeoPedia's runtime data directory."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = gdf.to_json(
        drop_id=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    OUTPUT_PATH.write_text(
        geojson,
        encoding="utf-8",
    )


def print_summary(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Print information about the generated answer-set regions."""
    logical_answers = collect_logical_answers(
        gdf
    )

    single_answer_regions = 0
    multi_answer_regions = 0

    for value in gdf[
        "postal_code_4_digit"
    ]:
        if hasattr(value, "tolist"):
            value = value.tolist()

        if len(value) == 1:
            single_answer_regions += 1
        else:
            multi_answer_regions += 1

    print(
        f"Runtime features: {len(gdf)}"
    )
    print(
        f"Logical postal answers: {len(logical_answers)}"
    )
    print(
        f"Single-answer features: {single_answer_regions}"
    )
    print(
        f"Multi-answer features: {multi_answer_regions}"
    )

    if multi_answer_regions:
        print()
        print("Multi-answer regions:")

        multi = gdf[
            gdf["postal_code_4_digit"].map(
                lambda value: (
                    len(
                        value.tolist()
                        if hasattr(value, "tolist")
                        else value
                    )
                    > 1
                )
            )
        ]

        for row in multi.itertuples():
            answers = (
                row.postal_code_4_digit.tolist()
                if hasattr(
                    row.postal_code_4_digit,
                    "tolist",
                )
                else row.postal_code_4_digit
            )

            print(
                "  "
                + ", ".join(answers)
                + ": "
                + ", ".join(
                    row.municipality_names
                )
            )


def main() -> None:
    """Generate Colombia's non-overlapping 4-digit postal-code geography."""
    print("Colombia 4-digit postal-code processor")
    print("=" * 72)
    print(f"Source: {SOURCE_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    print("Reading municipalities...")

    municipalities = gpd.read_file(
        SOURCE_PATH
    )

    validate_source(
        municipalities
    )

    print(
        f"Municipalities: {len(municipalities)}"
    )
    print()

    print(
        "Grouping municipalities by complete postal answer set..."
    )

    output = build_postal_regions(
        municipalities
    )

    validate_output(
        output
    )

    print_summary(
        output
    )

    print()
    print("Writing GeoJSON...")

    write_geojson(
        output
    )

    output_size = OUTPUT_PATH.stat().st_size

    print()
    print(
        f"Output size: {output_size / 1024:.1f} KB "
        f"({output_size:,} bytes)"
    )
    print()
    print("Done.")


if __name__ == "__main__":
    main()
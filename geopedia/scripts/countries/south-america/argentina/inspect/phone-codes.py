from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "countries" / "argentina"

AREA_CODE_1_PATH = RAW_DIR / "areaCodeData1.csv"
AREA_CODE_2_PATH = RAW_DIR / "areaCodeData2.js"
LOCALITIES_PATH = (
    RAW_DIR / "c1fc1f5b-dfe3-5231-9f3b-f7c703b906c7.json"
)


def normalize_text(value: str) -> str:
    value = value.strip().upper()

    value = unicodedata.normalize("NFD", value)
    value = "".join(
        char
        for char in value
        if unicodedata.category(char) != "Mn"
    )

    value = value.replace("’", "'")
    value = value.replace("`", "'")

    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_province(value: str) -> str:
    value = normalize_text(value)

    aliases = {
        "CAPITAL FEDERAL": "CIUDAD DE BUENOS AIRES",
        "CABA": "CIUDAD DE BUENOS AIRES",
        "CIUDAD AUTONOMA DE BUENOS AIRES": "CIUDAD DE BUENOS AIRES",
        "TIERRA DEL FUEGO ANTARTIDA E ISLAS DEL ATLANTICO SUR":
            "TIERRA DEL FUEGO",
        "TIERRA DEL FUEGO ANTARTIDA E ISLAS DEL ATLANTICO SUR A I A S":
            "TIERRA DEL FUEGO",
    }

    return aliases.get(value, value)


def read_area_code_csv() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    with AREA_CODE_1_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)

        header = next(reader, None)

        if header is None:
            return rows

        for row in reader:
            if len(row) < 3:
                continue

            code = row[0].strip()
            locality = row[1].strip()
            province = row[2].strip()

            if not code or not locality or not province:
                continue

            rows.append(
                {
                    "code": code,
                    "locality": locality,
                    "province": province,
                }
            )

    return rows


def decode_js_string(value: str) -> str:
    return bytes(value, "utf-8").decode(
        "unicode_escape"
    )


def read_area_code_js() -> list[dict[str, str]]:
    text = AREA_CODE_2_PATH.read_text(
        encoding="utf-8",
    )

    object_pattern = re.compile(
        r"\{(.*?)\}",
        re.DOTALL,
    )

    field_pattern = {
        "province": re.compile(
            r'provincia\s*:\s*"((?:\\.|[^"\\])*)"',
            re.DOTALL,
        ),
        "locality": re.compile(
            r'localidad\s*:\s*"((?:\\.|[^"\\])*)"',
            re.DOTALL,
        ),
        "code": re.compile(
            r'codigo\s*:\s*"((?:\\.|[^"\\])*)"',
            re.DOTALL,
        ),
    }

    rows: list[dict[str, str]] = []

    for match in object_pattern.finditer(text):
        body = match.group(1)

        values: dict[str, str] = {}

        for key, pattern in field_pattern.items():
            field_match = pattern.search(body)

            if field_match is None:
                break

            values[key] = decode_js_string(
                field_match.group(1)
            ).strip()

        if len(values) != 3:
            continue

        rows.append(values)

    return rows


def read_localities() -> list[dict[str, object]]:
    data = json.loads(
        LOCALITIES_PATH.read_text(
            encoding="utf-8",
        )
    )

    fields = [
        field["id"]
        for field in data["fields"]
    ]

    rows: list[dict[str, object]] = []

    for record in data["records"]:
        row = dict(zip(fields, record))

        geometry_text = row.get("geojson")

        geometry = None

        if geometry_text:
            geometry = json.loads(
                str(geometry_text)
            )

        rows.append(
            {
                "id": row.get("_id"),
                "province": str(
                    row.get("nom_prov") or ""
                ).strip(),
                "department": str(
                    row.get("nom_depto") or ""
                ).strip(),
                "locality": str(
                    row.get("nombre") or ""
                ).strip(),
                "type": str(
                    row.get("tipo") or ""
                ).strip(),
                "source": str(
                    row.get("fuente") or ""
                ).strip(),
                "geometry": geometry,
            }
        )

    return rows


def print_area_code_stats(
    label: str,
    rows: list[dict[str, str]],
) -> None:
    print()
    print("=" * 72)
    print(label)
    print("=" * 72)

    print(f"Rows: {len(rows):,}")

    unique_codes = {
        row["code"]
        for row in rows
    }

    unique_localities = {
        (
            normalize_province(row["province"]),
            normalize_text(row["locality"]),
        )
        for row in rows
    }

    provinces = Counter(
        normalize_province(row["province"])
        for row in rows
    )

    code_lengths = Counter(
        len(row["code"])
        for row in rows
    )

    duplicate_pairs = Counter(
        (
            normalize_province(row["province"]),
            normalize_text(row["locality"]),
        )
        for row in rows
    )

    duplicate_count = sum(
        count > 1
        for count in duplicate_pairs.values()
    )

    locality_multiple_codes: dict[
        tuple[str, str],
        set[str],
    ] = defaultdict(set)

    for row in rows:
        key = (
            normalize_province(row["province"]),
            normalize_text(row["locality"]),
        )

        locality_multiple_codes[key].add(
            row["code"]
        )

    conflicting_localities = {
        key: codes
        for key, codes
        in locality_multiple_codes.items()
        if len(codes) > 1
    }

    print(f"Unique codes: {len(unique_codes):,}")
    print(
        "Unique province/locality pairs: "
        f"{len(unique_localities):,}"
    )
    print(
        "Province/locality pairs appearing more than once: "
        f"{duplicate_count:,}"
    )
    print(
        "Province/locality pairs with multiple codes: "
        f"{len(conflicting_localities):,}"
    )

    print()
    print("Code lengths:")

    for length in sorted(code_lengths):
        print(
            f"  {length} digits: "
            f"{code_lengths[length]:,}"
        )

    print()
    print("Provinces:")

    for province, count in sorted(
        provinces.items()
    ):
        print(
            f"  {province}: {count:,}"
        )

    if conflicting_localities:
        print()
        print(
            "Sample localities mapped to multiple codes:"
        )

        for (
            (province, locality),
            codes,
        ) in list(
            sorted(
                conflicting_localities.items()
            )
        )[:20]:
            print(
                f"  {province} / {locality}: "
                f"{sorted(codes)}"
            )


def print_locality_stats(
    rows: list[dict[str, object]],
) -> None:
    print()
    print("=" * 72)
    print("OFFICIAL LOCALITY GEOMETRY")
    print("=" * 72)

    print(f"Rows: {len(rows):,}")

    provinces = Counter(
        normalize_province(
            str(row["province"])
        )
        for row in rows
    )

    types = Counter(
        str(row["type"])
        for row in rows
    )

    sources = Counter(
        str(row["source"])
        for row in rows
    )

    geometry_types = Counter()

    missing_geometry = 0

    for row in rows:
        geometry = row["geometry"]

        if not geometry:
            missing_geometry += 1
            continue

        geometry_types[
            str(geometry.get("type"))
        ] += 1

    duplicate_names = Counter(
        (
            normalize_province(
                str(row["province"])
            ),
            normalize_text(
                str(row["locality"])
            ),
        )
        for row in rows
    )

    duplicate_count = sum(
        count > 1
        for count in duplicate_names.values()
    )

    print(
        f"Missing geometry: "
        f"{missing_geometry:,}"
    )

    print(
        "Duplicate normalized province/locality pairs: "
        f"{duplicate_count:,}"
    )

    print()
    print("Geometry types:")

    for geometry_type, count in sorted(
        geometry_types.items()
    ):
        print(
            f"  {geometry_type}: {count:,}"
        )

    print()
    print("Settlement types:")

    for locality_type, count in types.most_common():
        print(
            f"  {locality_type}: {count:,}"
        )

    print()
    print("Sources:")

    for source, count in sources.most_common():
        print(
            f"  {source}: {count:,}"
        )

    print()
    print("Provinces:")

    for province, count in sorted(
        provinces.items()
    ):
        print(
            f"  {province}: {count:,}"
        )


def compare_to_geometry(
    label: str,
    area_rows: list[dict[str, str]],
    locality_rows: list[dict[str, object]],
) -> None:
    print()
    print("=" * 72)
    print(f"{label} -> OFFICIAL GEOMETRY MATCHING")
    print("=" * 72)

    geometry_index: dict[
        tuple[str, str],
        list[dict[str, object]],
    ] = defaultdict(list)

    for row in locality_rows:
        key = (
            normalize_province(
                str(row["province"])
            ),
            normalize_text(
                str(row["locality"])
            ),
        )

        geometry_index[key].append(row)

    matched = []
    unmatched = []

    for row in area_rows:
        key = (
            normalize_province(row["province"]),
            normalize_text(row["locality"]),
        )

        matches = geometry_index.get(
            key,
            [],
        )

        if matches:
            matched.append(
                (row, matches)
            )
        else:
            unmatched.append(row)

    total = len(area_rows)

    match_percent = (
        len(matched) / total * 100
        if total
        else 0
    )

    print(f"Rows: {total:,}")
    print(f"Matched: {len(matched):,}")
    print(f"Unmatched: {len(unmatched):,}")
    print(
        f"Exact normalized match rate: "
        f"{match_percent:.2f}%"
    )

    ambiguous = [
        (row, matches)
        for row, matches in matched
        if len(matches) > 1
    ]

    print(
        "Matches with multiple geometry candidates: "
        f"{len(ambiguous):,}"
    )

    if unmatched:
        print()
        print("First 50 unmatched rows:")

        for row in unmatched[:50]:
            print(
                f"  {row['code']:>4} | "
                f"{row['province']} | "
                f"{row['locality']}"
            )

    if ambiguous:
        print()
        print(
            "First 20 ambiguous geometry matches:"
        )

        for row, matches in ambiguous[:20]:
            print(
                f"  {row['code']:>4} | "
                f"{row['province']} | "
                f"{row['locality']} "
                f"-> {len(matches)} candidates"
            )

            for match in matches[:5]:
                print(
                    "       "
                    f"{match['department']} | "
                    f"{match['type']} | "
                    f"{match['source']}"
                )


def compare_area_code_sources(
    rows_1: list[dict[str, str]],
    rows_2: list[dict[str, str]],
) -> None:
    print()
    print("=" * 72)
    print("AREA-CODE SOURCE COMPARISON")
    print("=" * 72)

    source_1: dict[
        tuple[str, str],
        set[str],
    ] = defaultdict(set)

    source_2: dict[
        tuple[str, str],
        set[str],
    ] = defaultdict(set)

    for row in rows_1:
        key = (
            normalize_province(row["province"]),
            normalize_text(row["locality"]),
        )

        source_1[key].add(
            row["code"]
        )

    for row in rows_2:
        key = (
            normalize_province(row["province"]),
            normalize_text(row["locality"]),
        )

        source_2[key].add(
            row["code"]
        )

    common = set(source_1) & set(source_2)

    same_codes = 0
    conflicting_codes = []

    for key in common:
        if source_1[key] == source_2[key]:
            same_codes += 1
        else:
            conflicting_codes.append(
                (
                    key,
                    source_1[key],
                    source_2[key],
                )
            )

    print(
        f"Source 1 unique locality pairs: "
        f"{len(source_1):,}"
    )
    print(
        f"Source 2 unique locality pairs: "
        f"{len(source_2):,}"
    )
    print(
        f"Pairs present in both: "
        f"{len(common):,}"
    )
    print(
        f"Same code assignment: "
        f"{same_codes:,}"
    )
    print(
        f"Different code assignment: "
        f"{len(conflicting_codes):,}"
    )

    print(
        f"Only in source 1: "
        f"{len(set(source_1) - set(source_2)):,}"
    )
    print(
        f"Only in source 2: "
        f"{len(set(source_2) - set(source_1)):,}"
    )

    if conflicting_codes:
        print()
        print(
            "First 30 conflicting assignments:"
        )

        for (
            (province, locality),
            codes_1,
            codes_2,
        ) in sorted(
            conflicting_codes
        )[:30]:
            print(
                f"  {province} / {locality}"
            )
            print(
                f"    source 1: "
                f"{sorted(codes_1)}"
            )
            print(
                f"    source 2: "
                f"{sorted(codes_2)}"
            )


def main() -> None:
    print("Loading Argentina phone-code sources...")

    area_rows_1 = read_area_code_csv()
    area_rows_2 = read_area_code_js()
    locality_rows = read_localities()

    print_area_code_stats(
        "AREA CODE DATA 1 (CSV)",
        area_rows_1,
    )

    print_area_code_stats(
        "AREA CODE DATA 2 (JS)",
        area_rows_2,
    )

    print_locality_stats(
        locality_rows,
    )

    compare_area_code_sources(
        area_rows_1,
        area_rows_2,
    )

    compare_to_geometry(
        "AREA CODE DATA 1",
        area_rows_1,
        locality_rows,
    )

    compare_to_geometry(
        "AREA CODE DATA 2",
        area_rows_2,
        locality_rows,
    )


if __name__ == "__main__":
    main()
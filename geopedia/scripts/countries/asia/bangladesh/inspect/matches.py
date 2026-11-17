
"""
Compare Bangladesh ADM1–ADM3 boundaries with Bengali-name references.

Sources:
  - geoBoundaries ADM1–ADM3
  - bgd_admin_boundaries.geojson ADM1–ADM3
  - ifahimreza_bangladesh_geojson JSONs and enriched ADM3 GeoJSON

Matching:
  1. Exact or normalized English names
  2. Verified parent relationships
  3. Explicit spelling aliases
  4. Polygon overlap for unresolved ADM3 features

Only unique, sufficiently strong matches are accepted.
Ambiguous and unresolved records are reported for review.

Run:
  python scripts/countries/asia/bangladesh/inspect/matches.py

Dependencies:
  pip install ijson shapely
"""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import ijson
from shapely.geometry import shape
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / "data/raw/countries/bangladesh"

GEOBOUNDARIES = RAW
HDX = RAW / "bgd_admin_boundaries.geojson"
REFERENCE = RAW / "ifahimreza_bangladesh_geojson"

MAX_EXAMPLES = 50

# Minimum intersection-over-union for a spatial match.
MIN_IOU = 0.90

# Minimum separation from the second-best spatial candidate.
MIN_IOU_MARGIN = 0.10


# Explicit English-name equivalences.
# Add entries only after confirming they refer to the same place.
ALIASES = {
    "barisal": "barishal",
    "chittagong": "chattogram",
    "bogra": "bogura",
    "jessore": "jashore",
    "comilla": "cumilla",
    "rajshani": "rajshahi",
    "brahamanbaria": "brahmanbaria",
    "netrakona": "netrokona",
    "chapainababganj": "chapainawabganj",
    "moulvibazar": "maulvibazar",
    "khagrachhari": "khagrachari",
    "sirajganj": "sirajgonj",
}


def normalize(value):
    if value is None:
        return ""

    value = unicodedata.normalize("NFKC", str(value))
    value = value.casefold().strip()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "", value)

    return value


NORMALIZED_ALIASES = {
    normalize(key): normalize(value)
    for key, value in ALIASES.items()
}


def canonical(value):
    value = normalize(value)
    return NORMALIZED_ALIASES.get(value, value)


def same_name(a, b):
    return bool(canonical(a)) and canonical(a) == canonical(b)


def load_json_records(path, key):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    return data[key]


def load_features(path, level, source, geometries=False):
    records = []

    with path.open("rb") as file:
        for index, feature in enumerate(
            ijson.items(file, "features.item", use_float=True)
        ):
            props = feature.get("properties") or {}

            if source == "geoBoundaries":
                name = props.get("shapeName", "")
                division = ""
                district = ""
                code = props.get("shapeID", "")

            elif source == "HDX":
                name = props.get(f"adm{level}_name", "")
                division = props.get("adm1_name", "")
                district = props.get("adm2_name", "")
                code = props.get(f"adm{level}_pcode", "")

            else:
                name = props.get("name", "")
                division = props.get("division_name", "")
                district = props.get("district_name", "")
                code = props.get("upazila_id", "")

            record = {
                "index": index,
                "name": name,
                "division": division,
                "district": district,
                "code": code,
                "native": props.get("bn_name", ""),
                "division_native": props.get(
                    "division_bn_name", ""
                ),
                "district_native": props.get(
                    "district_bn_name", ""
                ),
                "source_name": props.get("source_name", ""),
                "district_id": props.get("district_id", ""),
                "division_id": props.get("division_id", ""),
            }

            if geometries:
                geometry = feature.get("geometry")
                record["geometry"] = (
                    shape(geometry) if geometry else None
                )

            records.append(record)

    return records


def build_references():
    divisions = load_json_records(
        REFERENCE / "bd-divisions.json", "divisions"
    )
    districts = load_json_records(
        REFERENCE / "bd-districts.json", "districts"
    )
    upazilas = load_json_records(
        REFERENCE / "bd-upazilas.json", "upazilas"
    )

    division_by_id = {
        str(row["id"]): row for row in divisions
    }
    district_by_id = {
        str(row["id"]): row for row in districts
    }

    references = {1: [], 2: [], 3: []}

    for row in divisions:
        references[1].append({
            "id": str(row["id"]),
            "name": row["name"],
            "native": row.get("bn_name", ""),
            "division": row["name"],
            "district": "",
        })

    for row in districts:
        division = division_by_id.get(
            str(row["division_id"])
        )

        references[2].append({
            "id": str(row["id"]),
            "name": row["name"],
            "native": row.get("bn_name", ""),
            "division": division["name"] if division else "",
            "district": row["name"],
        })

    for row in upazilas:
        district = district_by_id.get(
            str(row["district_id"])
        )

        division = (
            division_by_id.get(str(district["division_id"]))
            if district else None
        )

        references[3].append({
            "id": str(row["id"]),
            "name": row["name"],
            "native": row.get("bn_name", ""),
            "division": division["name"] if division else "",
            "district": district["name"] if district else "",
        })

    return references


def parent_compatible(source, reference, level):
    if level >= 2:
        a = source.get("division", "")
        b = reference.get("division", "")

        if a and b and not same_name(a, b):
            return False

    if level >= 3:
        a = source.get("district", "")
        b = reference.get("district", "")

        if a and b and not same_name(a, b):
            return False

    return True


def name_candidates(source, references, level):
    candidates = [
        row for row in references
        if same_name(source["name"], row["name"])
    ]

    compatible = [
        row for row in candidates
        if parent_compatible(source, row, level)
    ]

    return compatible


def spatial_candidates(source, references, tree, geom_lookup):
    geometry = source.get("geometry")

    if geometry is None or geometry.is_empty:
        return []

    candidates = []

    for index in tree.query(geometry):
        reference = references[int(index)]
        other = reference.get("geometry")

        if other is None or other.is_empty:
            continue

        intersection = geometry.intersection(other).area
        union = geometry.area + other.area - intersection

        if union <= 0:
            continue

        iou = intersection / union

        candidates.append((iou, reference))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def match_records(
    sources,
    references,
    level,
    use_spatial=False,
):
    results = []

    tree = None

    if use_spatial:
        geometries = [
            row["geometry"] for row in references
        ]
        tree = STRtree(geometries)

    for source in sources:
        candidates = name_candidates(
            source, references, level
        )

        matched = None
        method = None

        if len(candidates) == 1:
            matched = candidates[0]
            method = "name"

        elif use_spatial and tree is not None:
            spatial = spatial_candidates(
                source, references, tree, None
            )

            if spatial:
                best_iou, best = spatial[0]
                second_iou = (
                    spatial[1][0] if len(spatial) > 1 else 0
                )

                if (
                    best_iou >= MIN_IOU
                    and best_iou - second_iou >= MIN_IOU_MARGIN
                ):
                    matched = best
                    method = "spatial"

        if matched is None:
            method = (
                "ambiguous" if len(candidates) > 1
                else "unmatched"
            )

        results.append({
            "source": source,
            "match": matched,
            "method": method,
        })

    return results


def combine_reference_matches(source_rows, json_refs, enriched):
    """
    Map enriched ADM3 features to JSON references using their
    administrative IDs first, then verified names and parents.

    A missing Bengali label may be filled from the JSON reference.
    Existing nonempty labels are retained.
    """
    json_by_id = {
        str(row["id"]): row for row in json_refs
    }

    combined = []

    for row in enriched:
        record = dict(row)
        candidate = None

        if row["code"]:
            candidate = json_by_id.get(str(row["code"]))

            if candidate and not parent_compatible(
                row, candidate, 3
            ):
                candidate = None

            if candidate and not same_name(
                row["name"], candidate["name"]
            ):
                candidate = None

        if candidate is None:
            matches = name_candidates(
                row, json_refs, 3
            )

            if len(matches) == 1:
                candidate = matches[0]

        if candidate and not record["native"]:
            record["native"] = candidate["native"]

        combined.append(record)

    return combined


def print_report(label, results):
    counts = Counter(row["method"] for row in results)

    native = sum(
        bool(row["match"] and row["match"].get("native"))
        for row in results
    )

    parent_verified = sum(
        bool(
            row["match"]
            and row["source"].get("division")
            and (
                row["source"].get("district")
                or not row["match"].get("district")
            )
        )
        for row in results
    )

    print(f"\n{label}")
    print(f"  Features: {len(results)}")
    print(f"  Name matches: {counts['name']}")
    print(f"  Spatial matches: {counts['spatial']}")
    print(f"  Native labels: {native}")
    print(f"  Parent fields present: {parent_verified}")
    print(f"  Unmatched: {counts['unmatched']}")
    print(f"  Ambiguous: {counts['ambiguous']}")

    for status in ("unmatched", "ambiguous"):
        rows = [
            row["source"]["name"]
            for row in results
            if row["method"] == status
        ]

        if rows:
            print(f"  {status.title()} examples:")
            for name in rows[:MAX_EXAMPLES]:
                print(f"    - {name}")


def main():
    references = build_references()

    enriched_path = REFERENCE / "bangladesh.geojson"

    enriched = load_features(
        enriched_path,
        3,
        "enriched",
        geometries=True,
    )

    combined = combine_reference_matches(
        enriched,
        references[3],
        enriched,
    )

    original_native = sum(
        bool(row["native"]) for row in enriched
    )
    combined_native = sum(
        bool(row["native"]) for row in combined
    )

    print("Bangladesh administrative dataset comparison")
    print("=" * 65)

    print("\nADM3 Bengali-name reference coverage")
    print(f"  Enriched GeoJSON: {original_native}/544")
    print(f"  Combined references: {combined_native}/544")

    for level in (1, 2, 3):
        print(f"\n{'=' * 65}")
        print(f"ADM{level}")
        print("=" * 65)

        geoboundaries = load_features(
            GEOBOUNDARIES /
            f"geoBoundaries-BGD-ADM{level}.geojson",
            level,
            "geoBoundaries",
            geometries=(level == 3),
        )

        hdx = load_features(
            HDX / f"bgd_admin{level}.geojson",
            level,
            "HDX",
            geometries=(level == 3),
        )

        if level < 3:
            reference = references[level]
        else:
            reference = combined

        geo_results = match_records(
            geoboundaries,
            reference,
            level,
            use_spatial=(level == 3),
        )

        hdx_results = match_records(
            hdx,
            reference,
            level,
            use_spatial=(level == 3),
        )

        print_report("geoBoundaries", geo_results)
        print_report("HDX", hdx_results)

    print("\nComparison complete.")


if __name__ == "__main__":
    main()

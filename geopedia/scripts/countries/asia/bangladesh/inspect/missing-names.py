
"""
Inspect missing Bengali names in Bangladesh's enriched ADM3 GeoJSON.

Compares the 544 GeoJSON features with the 494 upazila JSON records.

Matching:
  1. ID + verified English name and parent district
  2. Normalized English name + verified parent district
  3. Unique normalized English name when parent is unavailable
  4. Fuzzy suggestions for unresolved records (never auto-accepted)

Reports missing names, possible matches, ID conflicts, and coverage.

Run:
  python scripts/countries/asia/bangladesh/inspect/missing_names.py

Dependencies:
  Python standard library only
"""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]

SOURCE = (
    ROOT
    / "data/raw/countries/bangladesh/ifahimreza_bangladesh_geojson"
)

OUTPUT = (
    ROOT
    / "data/raw/countries/bangladesh/adm3_missing_names_report.json"
)

MAX_SUGGESTIONS = 5
MIN_SUGGESTION_SCORE = 0.55


ALIASES = {
    "barisal": "barishal",
    "chittagong": "chattogram",
    "bogra": "bogura",
    "jessore": "jashore",
    "comilla": "cumilla",
    "rajshani": "rajshahi",
    "brahamanbaria": "brahmanbaria",
    "netrakona": "netrokona",
    "khagrachhari": "khagrachari",
    "sirajganj": "sirajgonj",
}


def normalize(value):
    if not value:
        return ""

    value = unicodedata.normalize("NFKC", str(value))
    value = value.casefold().strip()
    value = value.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", value)


ALIASES = {
    normalize(key): normalize(value)
    for key, value in ALIASES.items()
}


def canonical(value):
    value = normalize(value)
    return ALIASES.get(value, value)


def same_name(a, b):
    return bool(canonical(a)) and canonical(a) == canonical(b)


def load_records(filename, key):
    with (SOURCE / filename).open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, list) else data[key]


def build_reference():
    divisions = load_records("bd-divisions.json", "divisions")
    districts = load_records("bd-districts.json", "districts")
    upazilas = load_records("bd-upazilas.json", "upazilas")

    division_by_id = {
        str(row["id"]): row for row in divisions
    }

    district_by_id = {
        str(row["id"]): row for row in districts
    }

    records = []

    for row in upazilas:
        district = district_by_id.get(str(row["district_id"]))

        division = (
            division_by_id.get(str(district["division_id"]))
            if district else None
        )

        records.append({
            "id": str(row["id"]),
            "name": row["name"],
            "native": row.get("bn_name", ""),
            "district_id": str(row["district_id"]),
            "district": district["name"] if district else "",
            "division": division["name"] if division else "",
        })

    return records


def load_geojson():
    with (SOURCE / "bangladesh.geojson").open(
        "r", encoding="utf-8"
    ) as file:
        data = json.load(file)

    return [
        {
            "index": index,
            **feature["properties"],
        }
        for index, feature in enumerate(data["features"])
    ]


def parent_status(feature, reference):
    feature_district_id = str(
        feature.get("district_id") or ""
    )

    feature_district = feature.get("district_name") or ""

    if feature_district_id:
        if feature_district_id != reference["district_id"]:
            return "conflict"

        return "verified"

    if feature_district:
        if not same_name(feature_district, reference["district"]):
            return "conflict"

        return "verified"

    return "unknown"


def get_suggestions(feature, references):
    name = canonical(feature.get("name", ""))

    suggestions = []

    for reference in references:
        score = SequenceMatcher(
            None, name, canonical(reference["name"])
        ).ratio()

        parent = parent_status(feature, reference)

        if parent == "conflict":
            continue

        if score < MIN_SUGGESTION_SCORE:
            continue

        suggestions.append({
            "id": reference["id"],
            "name": reference["name"],
            "native": reference["native"],
            "district": reference["district"],
            "division": reference["division"],
            "similarity": round(score, 3),
            "parent_status": parent,
        })

    suggestions.sort(
        key=lambda row: (
            row["parent_status"] == "verified",
            row["similarity"],
        ),
        reverse=True,
    )

    return suggestions[:MAX_SUGGESTIONS]


def match_feature(feature, references, by_id):
    name = feature.get("name", "")
    feature_id = str(feature.get("upazila_id") or "")

    conflicts = []

    if feature_id and feature_id in by_id:
        candidate = by_id[feature_id]

        name_matches = same_name(name, candidate["name"])
        parent = parent_status(feature, candidate)

        if name_matches and parent != "conflict":
            return candidate, "id_and_name", conflicts

        conflicts.append({
            "type": "id_mismatch",
            "candidate": candidate["name"],
            "candidate_district": candidate["district"],
            "name_matches": name_matches,
            "parent_status": parent,
        })

    candidates = [
        row for row in references
        if same_name(name, row["name"])
        and parent_status(feature, row) != "conflict"
    ]

    verified = [
        row for row in candidates
        if parent_status(feature, row) == "verified"
    ]

    if len(verified) == 1:
        return verified[0], "name_and_parent", conflicts

    if len(verified) > 1:
        return None, "ambiguous", conflicts

    if len(candidates) == 1:
        return candidates[0], "unique_name", conflicts

    if len(candidates) > 1:
        return None, "ambiguous", conflicts

    return None, "unmatched", conflicts


def main():
    references = build_reference()
    features = load_geojson()

    by_id = {row["id"]: row for row in references}

    counts = Counter()
    missing = []
    conflicts = []
    recovered = []

    for feature in features:
        existing_native = feature.get("bn_name") or ""

        match, method, feature_conflicts = match_feature(
            feature, references, by_id
        )

        counts[method] += 1

        if feature_conflicts:
            conflicts.append({
                "feature": feature["name"],
                "index": feature["index"],
                "conflicts": feature_conflicts,
            })

        if existing_native:
            continue

        if match and match["native"]:
            recovered.append({
                "index": feature["index"],
                "name": feature["name"],
                "native": match["native"],
                "district": match["district"],
                "method": method,
            })
            continue

        missing.append({
            "index": feature["index"],
            "name": feature.get("name", ""),
            "source_name": feature.get("source_name", ""),
            "upazila_id": feature.get("upazila_id", ""),
            "district_id": feature.get("district_id", ""),
            "district": feature.get("district_name", ""),
            "division": feature.get("division_name", ""),
            "status": method,
            "suggestions": get_suggestions(
                feature, references
            ),
        })

    original_native = sum(
        bool(row.get("bn_name")) for row in features
    )

    print("Bangladesh ADM3 Bengali-name inspection")
    print("=" * 65)

    print(f"\nTotal features: {len(features)}")
    print(f"Original Bengali names: {original_native}")
    print(f"Additional names recovered: {len(recovered)}")
    print(
        f"Total coverage: "
        f"{original_native + len(recovered)}/{len(features)}"
    )
    print(f"Still missing: {len(missing)}")

    print("\nMatching methods (all features):")
    for method, count in counts.most_common():
        print(f"  {method}: {count}")

    print(f"\nID conflicts: {len(conflicts)}")

    by_district = defaultdict(list)

    for row in missing:
        district = row["district"] or "(Unknown district)"
        by_district[district].append(row)

    print("\nUnresolved features by district:")
    for district in sorted(by_district):
        rows = by_district[district]

        print(f"\n  {district} ({len(rows)})")

        for row in rows:
            print(f"    - {row['name']}")

            for suggestion in row["suggestions"][:3]:
                print(
                    f"        ? {suggestion['name']} "
                    f"[{suggestion['district']}] "
                    f"({suggestion['similarity']:.3f}, "
                    f"{suggestion['parent_status']})"
                )

    report = {
        "summary": {
            "total_features": len(features),
            "original_native": original_native,
            "recovered": len(recovered),
            "remaining": len(missing),
            "matching_methods": dict(counts),
        },
        "recovered": recovered,
        "missing": missing,
        "id_conflicts": conflicts,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(f"\nDetailed report saved to:\n  {OUTPUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Load Person A's data/receptors/*.json evidence files into Person B's
discordance SQLite store, converting between the two schemas.

Person A's schema (data/schema.md) and Person B's EvidenceRecord
(discordance/models.py) diverged since they were built in parallel -- this is
the adapter that reconciles them so Person A's pipeline output is directly
usable by the Builder/Query MCP tools without either side changing their
native format.

Usage: python3 scripts/load_into_discordance.py [data/receptors/or51e2.json ...]
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from discordance import init_db, insert_record, EvidenceRecord  # noqa: E402

# Person A source_type -> Person B SourceType
SOURCE_TYPE_MAP = {
    "literature": "primary_study",
    "patent": "patent",
    "tcga": "database_derived",
    "pdb": "database_derived",
    "chembl": "database_derived",
    # Unpublished, unreplicated wet-lab data doesn't fit neatly into Person B's
    # enum -- "preliminary" is the closest existing category (single-source,
    # not yet peer-reviewed) and keeps it out of "primary_study" so it isn't
    # weighted as published literature consensus.
    "unpublished_primary": "preliminary",
}

# Person A direction -> Person B Direction (Person B has no "unclear"; those
# records are structural/TCGA cross-checks with no tumor-direction claim of
# their own, so they map to "neutral" and rely on cancer_type/mechanism text
# to carry the actual finding).
DIRECTION_MAP = {
    "tumor-suppressive": "tumor_suppressive",
    "tumor-promoting": "tumor_promoting",
    "neutral": "neutral",
    "unclear": "neutral",
}

CANCER_TYPE_MAP = {
    "prostate": "prostate_cancer",
    "melanoma": "melanoma",
    "pan-cancer": "pan_cancer",
    "kidney chromophobe (KICH)": "kidney_chromophobe",
    None: "unknown",
}


def convert(record: dict) -> EvidenceRecord:
    direction_context = "activation_effect"
    if record["source_type"] in ("tcga", "pdb", "chembl"):
        direction_context = (
            "genetic_alteration" if record["source_type"] == "tcga" else "expression_pattern"
        )

    confidence_note = record["verification_notes"]
    if not record["verified_by_person_a"]:
        confidence_note = "UNVERIFIED. " + confidence_note

    return EvidenceRecord(
        source=record["citation"],
        source_type=SOURCE_TYPE_MAP[record["source_type"]],
        claim=record["claim"],
        gene=record["receptor"],
        direction=DIRECTION_MAP[record["direction"]],
        direction_context=direction_context,
        cancer_type=CANCER_TYPE_MAP.get(record["cancer_type"], record["cancer_type"]),
        model_system=record["model_system"] or "not specified",
        mechanism=record["mechanism"] or "not specified",
        sample_size=record["sample_size"],
        independent_replications=record["replication_count"],
        confidence_note=confidence_note,
    )


def main():
    paths = [Path(p) for p in sys.argv[1:]] or list((REPO_ROOT / "data" / "receptors").glob("*.json"))
    if not paths:
        print("No evidence files found under data/receptors/.")
        return

    init_db()
    total_inserted = 0
    total_skipped = 0
    for path in paths:
        records = json.loads(path.read_text())
        print(f"{path}: {len(records)} records")
        for raw in records:
            ev = convert(raw)
            row_id = insert_record(ev)
            if row_id is not None:
                print(f"  Inserted: [{row_id}] {ev.source[:60]}")
                total_inserted += 1
            else:
                print(f"  Skipped (duplicate): {ev.source[:60]}")
                total_skipped += 1

    print(f"\nDone. {total_inserted} inserted, {total_skipped} skipped as duplicates.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Load all evidence sources into Person B's discordance SQLite store.

Sources handled:
  - data/receptors/*.json          (Person A verified records)
  - data/receptors/*_fulltext_candidates.json  (PMC figure-level extractions)
  - data/expansion_results.json    (PubMed expansion pipeline)

Usage:
  python3 scripts/load_into_discordance.py                  # JSON records only
  python3 scripts/load_into_discordance.py --all            # everything
  python3 scripts/load_into_discordance.py --candidates     # include fulltext candidates
  python3 scripts/load_into_discordance.py --expansion      # include PubMed expansion
  python3 scripts/load_into_discordance.py data/receptors/or51e2.json  # specific file
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from discordance import init_db, insert_record, EvidenceRecord  # noqa: E402

# ── Schema adapters ───────────────────────────────────────────────────────────

SOURCE_TYPE_MAP = {
    "literature":        "primary_study",
    "patent":            "patent",
    "tcga":              "database_derived",
    "pdb":               "database_derived",
    "chembl":            "database_derived",
    "unpublished_primary": "preliminary",
}

DIRECTION_MAP = {
    "tumor-suppressive": "tumor_suppressive",
    "tumor-promoting":   "tumor_promoting",
    "neutral":           "neutral",
    "unclear":           "neutral",
}

# Full cancer type normalisation: Person A labels + TCGA project codes + multi-cancer slugs
CANCER_TYPE_MAP = {
    # Person A labels
    "prostate":                      "prostate_cancer",
    "prostate_cancer":               "prostate_cancer",
    "melanoma":                      "melanoma",
    "pan-cancer":                    "pan_cancer",
    "pan_cancer":                    "pan_cancer",
    "colorectal":                    "colorectal_cancer",
    "colon":                         "colorectal_cancer",
    "colorectal_cancer":             "colorectal_cancer",
    "kidney chromophobe (KICH)":     "kidney_chromophobe",
    "kidney_chromophobe":            "kidney_chromophobe",
    "lung":                          "lung_cancer",
    "lung_cancer":                   "lung_cancer",
    "ovarian":                       "ovarian_cancer",
    "ovarian_cancer":                "ovarian_cancer",
    "cholangiocarcinoma":            "cholangiocarcinoma",
    "breast":                        "breast_cancer",
    "bladder":                       "bladder_cancer",
    "liver":                         "liver_cancer",
    "pancreatic":                    "pancreatic_cancer",
    "gastric":                       "gastric_cancer",
    "glioma":                        "glioma",
    "glioblastoma":                  "glioblastoma",
    "leukemia":                      "leukemia",
    "lymphoma":                      "lymphoma",
    "neuroblastoma":                 "neuroblastoma",
    # TCGA project codes (from tcga_pull.py cohort-level records)
    "PRAD":   "prostate_cancer",
    "KICH":   "kidney_chromophobe",
    "OV":     "ovarian_cancer",
    "LUAD":   "lung_cancer",
    "LUSC":   "lung_cancer",
    "CHOL":   "cholangiocarcinoma",
    "COAD":   "colorectal_cancer",
    "READ":   "colorectal_cancer",
    "BRCA":   "breast_cancer",
    "BLCA":   "bladder_cancer",
    "LIHC":   "liver_cancer",
    "PAAD":   "pancreatic_cancer",
    "STAD":   "gastric_cancer",
    "GBM":    "glioblastoma",
    "LGG":    "glioma",
    "LAML":   "leukemia",
    "DLBC":   "lymphoma",
    "SKCM":   "melanoma",
    "UCEC":   "uterine_cancer",
    "HNSC":   "head_neck_cancer",
    "KIRC":   "kidney_clear_cell",
    "KIRP":   "kidney_papillary",
    "THCA":   "thyroid_cancer",
    "CESC":   "cervical_cancer",
    "ESCA":   "esophageal_cancer",
    "SARC":   "sarcoma",
    "UCS":    "uterine_carcinosarcoma",
    "MESO":   "mesothelioma",
    "UVM":    "uveal_melanoma",
    "TGCT":   "testicular_cancer",
    "THYM":   "thymoma",
    "PCPG":   "pheochromocytoma",
    "ACC":    "adrenocortical_carcinoma",
    "DLBC":   "lymphoma",
    # Free-text cancer types
    "solid tumors (unspecified)": "solid_tumors",
    None: "unknown",
}

# Multi-cancer strings that should expand to multiple records
_MULTI_CANCER_MAP = {
    "lung, ovarian, cholangiocarcinoma (epithelial tumors)": [
        "lung_cancer", "ovarian_cancer", "cholangiocarcinoma"
    ],
    "lung, ovarian, cholangiocarcinoma": [
        "lung_cancer", "ovarian_cancer", "cholangiocarcinoma"
    ],
}

# Endpoint hints derived from known paper citations
_CITATION_ENDPOINT_HINTS = (
    ("neuhaus", "proliferation"),
    ("sanz", "2014", "invasiveness"),
    ("sanz", "2016", "tumor_growth"),
    ("rodriguez", "tumor_growth"),
    ("pronin", "proliferation"),
    ("gelis", "proliferation"),
    ("jovancevic", "proliferation"),
    ("weber", "proliferation"),
    ("martin", "car_t_cytotoxicity"),
    ("thomsen", "proliferation"),
    ("xie", "proliferation"),
    ("marelli", "immune_evasion"),
)


def _infer_endpoint(record: dict) -> str:
    explicit = record.get("endpoint")
    if explicit and explicit not in ("", "not specified", None):
        return explicit
    cite = (record.get("citation") or "").lower()
    for hint in _CITATION_ENDPOINT_HINTS:
        if len(hint) == 3:
            needle, year, endpoint = hint
            if needle in cite and year in cite:
                return endpoint
        else:
            needle, endpoint = hint
            if needle in cite:
                return endpoint
    claim = (record.get("claim") or "").lower()
    for word in ("invasiveness", "invasion", "proliferation", "apoptosis", "migration", "growth"):
        if word in claim:
            return "invasiveness" if word.startswith("invas") else (
                "tumor_growth" if word == "growth" else word
            )
    return "not specified"


def _resolve_cancer_type(raw) -> str:
    """Resolve a cancer_type value to a normalised slug."""
    if not raw:
        return "unknown"
    if isinstance(raw, str) and raw in CANCER_TYPE_MAP:
        return CANCER_TYPE_MAP[raw]
    if isinstance(raw, str):
        # Try lowercase match
        lower = raw.lower().strip()
        for k, v in CANCER_TYPE_MAP.items():
            if isinstance(k, str) and k.lower() == lower:
                return v
        # Last resort: slug it
        return onto_slug_cancer(raw)
    return "unknown"


def _is_chembl_activity(record: dict) -> bool:
    """True for per-compound ChEMBL activity records (not the summary record)."""
    citation = record.get("citation") or ""
    return record.get("source_type") == "chembl" and "activity" in citation.lower()


def onto_slug_cancer(raw: str) -> str:
    return raw.lower().replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")[:64]


def _is_verified(record: dict) -> bool:
    if "verified_by_person_a" in record:
        return bool(record["verified_by_person_a"])
    notes = (record.get("verification_notes") or "").upper()
    if any(tag in notes for tag in (
        "AUTO-EXTRACTED", "NOT YET", "NOT INDEPENDENTLY", "CANDIDATE", "K PRO'S BASELINE",
    )):
        return False
    return True


def _infer_direction_context(record: dict, source_type_raw: str) -> str:
    explicit = record.get("direction_context")
    if explicit:
        return explicit

    if source_type_raw == "tcga":
        return "genetic_alteration"
    if source_type_raw == "pdb":
        return "expression_pattern"
    if source_type_raw == "chembl" and not _is_chembl_activity(record):
        return "expression_pattern"

    claim = (record.get("claim") or "").lower()
    mech = (record.get("mechanism") or "").lower()
    text = f"{claim} {mech}"

    if re.search(r"crispr[- ]?cas9|crispr knockout|crispr[- ]?ko|gene knockout", text):
        return "genetic_alteration"
    if "knockout" in text and "or51e2" in text:
        return "genetic_alteration"
    if re.search(r"\bshrna\b|sirna knockdown|knockdown of (psgr|or51e2)", text):
        return "genetic_alteration"
    if "inducible" in text and ("overexpress" in text or "expression" in text):
        return "expression_pattern"
    if "overexpression drives" in text or "psgr overexpression" in text:
        return "expression_pattern"
    if "transgenic" in text and "overexpress" in text:
        return "expression_pattern"

    return "activation_effect"


def convert(record: dict) -> list[EvidenceRecord]:
    """
    Convert one Person A JSON record to one or more EvidenceRecord objects.

    Returns a list because multi-cancer records (e.g. OR2H1's
    'lung, ovarian, cholangiocarcinoma') expand to one record per cancer type
    rather than a single record with an unusable compound cancer slug.
    """
    source_type_raw = record["source_type"]
    source_type = SOURCE_TYPE_MAP.get(source_type_raw, "preliminary")
    if not _is_verified(record):
        source_type = "preliminary"

    direction_context = _infer_direction_context(record, source_type_raw)

    direction_raw = record.get("direction", "unclear")
    direction = DIRECTION_MAP.get(direction_raw, "neutral")

    confidence_note = record.get("verification_notes") or ""
    if not _is_verified(record):
        confidence_note = "UNVERIFIED. " + confidence_note

    cancer_raw = record.get("cancer_type")
    endpoint = _infer_endpoint(record)

    # Expand multi-cancer records into one record per cancer type
    multi = _MULTI_CANCER_MAP.get(cancer_raw) if isinstance(cancer_raw, str) else None
    if multi:
        cancer_types = multi
    else:
        cancer_types = [_resolve_cancer_type(cancer_raw)]

    records = []
    for cancer_type in cancer_types:
        records.append(EvidenceRecord(
            source=record["citation"],
            source_type=source_type,
            claim=record["claim"],
            gene=record["receptor"],
            direction=direction,
            direction_context=direction_context,
            endpoint=endpoint,
            cancer_type=cancer_type,
            model_system=(record.get("model_system") or "not specified"),
            mechanism=(record.get("mechanism") or "not specified"),
            sample_size=record.get("sample_size"),
            independent_replications=record.get("replication_count"),
            confidence_note=confidence_note,
        ))
    return records


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_json_file(path: Path, label: str = "") -> tuple[int, int]:
    """Load one receptors/*.json file. Returns (inserted, skipped)."""
    records = json.loads(path.read_text())
    inserted = skipped = 0
    tag = label or path.name
    print(f"{tag}: {len(records)} records")
    for raw in records:
        for ev in convert(raw):
            row_id = insert_record(ev)
            if row_id is not None:
                print(f"  Inserted: [{row_id}] {ev.source[:60]}")
                inserted += 1
            else:
                print(f"  Skipped (dup): {ev.source[:55]}")
                skipped += 1
    return inserted, skipped


def load_fulltext_candidates(repo_root: Path) -> tuple[int, int]:
    """
    Load PMC figure-level extraction candidates as preliminary records.

    These are deliberately kept separate from verified records — they carry
    UNVERIFIED prefix and use source_type='preliminary' (weight 0.4 vs 1.0).
    Including them makes replication counts from figure methods sections visible
    in the graph, improving evidence scoring for the papers they cover.
    """
    candidate_files = list((repo_root / "data" / "receptors").glob("*_fulltext_candidates.json"))
    if not candidate_files:
        print("  No _fulltext_candidates.json files found.")
        return 0, 0

    total_inserted = total_skipped = 0
    for path in candidate_files:
        records = json.loads(path.read_text())
        print(f"{path.name}: {len(records)} candidate records")
        for raw in records:
            # Force to preliminary so weight is 0.4 not 1.0, and direction_context
            # is preserved from the candidate (usually activation_effect or neutral)
            raw_copy = dict(raw)
            raw_copy["source_type"] = "literature"  # convert() will map to primary_study...
            # ...but we override after
            ev_list = convert(raw_copy)
            for ev in ev_list:
                # Downgrade to preliminary — these are machine-extracted, not Person A verified
                ev.source_type = "preliminary"
                row_id = insert_record(ev)
                if row_id is not None:
                    print(f"  Inserted candidate: [{row_id}] {ev.source[:55]}")
                    total_inserted += 1
                else:
                    print(f"  Skipped candidate (dup): {ev.source[:50]}")
                    total_skipped += 1
    return total_inserted, total_skipped


def load_expansion_results(repo_root: Path) -> tuple[int, int]:
    """
    Load PubMed expansion pipeline results (data/expansion_results.json).

    These are auto-extracted from PubMed abstracts — direction/endpoint may be
    None when extraction was ambiguous. All loaded as preliminary/neutral.
    """
    exp_path = repo_root / "data" / "expansion_results.json"
    if not exp_path.exists():
        print("  data/expansion_results.json not found.")
        return 0, 0

    expansion = json.loads(exp_path.read_text())
    total_inserted = total_skipped = 0

    for receptor_run in expansion:
        receptor = receptor_run.get("receptor", "UNKNOWN")
        results = receptor_run.get("results", [])
        if not results:
            continue
        print(f"Expansion results for {receptor}: {len(results)} records")
        for raw in results:
            direction_raw = raw.get("direction") or "unclear"
            direction = DIRECTION_MAP.get(direction_raw, "neutral")
            cancer_raw = raw.get("cancer_type")
            cancer_type = _resolve_cancer_type(cancer_raw) if cancer_raw else "unknown"
            ev = EvidenceRecord(
                source=raw.get("citation") or f"PubMed PMID {raw.get('pmid', 'unknown')}",
                source_type="preliminary",
                claim=raw.get("abstract") or raw.get("claim") or raw.get("title") or "No claim extracted",
                gene=receptor,
                direction=direction,
                direction_context="activation_effect",
                endpoint=raw.get("endpoint") or "not specified",
                cancer_type=cancer_type,
                model_system=raw.get("model_system") or "not specified",
                mechanism=raw.get("mechanism") or "not specified",
                sample_size=None,
                independent_replications=None,
                confidence_note=(
                    "AUTO-EXTRACTED from PubMed abstract. Not verified against full text. "
                    "Direction and endpoint extracted by keyword rules — treat as hypothesis only."
                ),
            )
            row_id = insert_record(ev)
            if row_id is not None:
                print(f"  Inserted expansion: [{row_id}] {ev.source[:55]}")
                total_inserted += 1
            else:
                print(f"  Skipped expansion (dup): {ev.source[:50]}")
                total_skipped += 1

    return total_inserted, total_skipped


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Load all evidence sources into discordance DB")
    parser.add_argument(
        "files", nargs="*", type=Path,
        help="Specific receptor JSON files to load (default: all data/receptors/*.json)"
    )
    parser.add_argument(
        "--candidates", action="store_true",
        help="Also load PMC fulltext candidate records (preliminary weight)"
    )
    parser.add_argument(
        "--expansion", action="store_true",
        help="Also load PubMed expansion pipeline results"
    )
    parser.add_argument(
        "--all", action="store_true", dest="load_all",
        help="Load everything: verified records + candidates + expansion results"
    )
    args = parser.parse_args()

    if args.load_all:
        args.candidates = True
        args.expansion = True

    if args.files:
        paths = [Path(p) for p in args.files if p and not str(p).startswith("#")]
    else:
        paths = [
            p for p in (REPO_ROOT / "data" / "receptors").glob("*.json")
            if not p.name.endswith("_fulltext_candidates.json")
        ]
    if not paths:
        print("No evidence files found under data/receptors/.")
        return

    init_db()
    total_inserted = total_skipped = 0

    for path in sorted(paths):
        if not path.exists():
            print(f"Skipping missing path: {path}")
            continue
        ins, sk = load_json_file(path)
        total_inserted += ins
        total_skipped += sk

    if args.candidates:
        print("\n--- Fulltext candidates ---")
        ins, sk = load_fulltext_candidates(REPO_ROOT)
        total_inserted += ins
        total_skipped += sk

    if args.expansion:
        print("\n--- PubMed expansion results ---")
        ins, sk = load_expansion_results(REPO_ROOT)
        total_inserted += ins
        total_skipped += sk

    print(f"\nDone. {total_inserted} inserted, {total_skipped} skipped as duplicates.")


if __name__ == "__main__":
    main()

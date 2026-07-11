#!/usr/bin/env python3
"""
PubMed expansion pipeline: search for papers about an olfactory receptor,
extract structured evidence fields via code-based extraction, and insert
preliminary records into the Discordance graph.

For receptors without verified ground truth (OR2H1, OR51B4, OR2C3), this
is an initial extraction run. Records are marked verified_by_person_a=False
and source_type="preliminary" — they queue for human review, not demo use.

Usage:
    python3 scripts/pubmed_expand.py --receptor OR2H1
    python3 scripts/pubmed_expand.py --receptor OR51E2 --max-results 20
    python3 scripts/pubmed_expand.py --all-receptors
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib import request, parse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from discordance import init_db, insert_record, get_records, EvidenceRecord

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DB_PATH = REPO_ROOT / "evidence.db"

# Search terms per receptor — include aliases and gene synonyms
RECEPTOR_SEARCH = {
    "OR51E2": '"OR51E2" OR "PSGR" OR "prostate specific G protein coupled receptor"',
    "OR2H1":  '"OR2H1"',
    "OR51B4": '"OR51B4"',
    "OR2C3":  '"OR2C3"',
}

# Cancer type keywords for normalisation
CANCER_TYPE_MAP = {
    "prostate": "prostate_cancer",
    "lung": "lung_cancer",
    "ovarian": "ovarian_cancer",
    "cholangiocarcinoma": "cholangiocarcinoma",
    "colorectal": "colorectal_cancer",
    "colon": "colorectal_cancer",
    "melanoma": "melanoma",
    "kidney": "kidney_cancer",
    "breast": "breast_cancer",
    "bladder": "bladder_cancer",
    "liver": "liver_cancer",
    "pancreatic": "pancreatic_cancer",
    "gastric": "gastric_cancer",
    "stomach": "gastric_cancer",
    "leukemia": "leukemia",
    "lymphoma": "lymphoma",
    "glioma": "glioma",
    "glioblastoma": "glioblastoma",
}

# ── PubMed fetch helpers ───────────────────────────────────────────────────────

def search_pubmed(query: str, max_results: int = 30) -> list[str]:
    """Return list of PMIDs matching query."""
    params = {
        "db": "pubmed",
        "term": f"({query}) AND (cancer[tiab] OR tumor[tiab] OR tumour[tiab] OR carcinoma[tiab] OR neoplasm[tiab] OR olfactory[tiab])",
        "retmode": "json",
        "retmax": str(max_results),
        "sort": "relevance",
    }
    url = f"{EUTILS}/esearch.fcgi?{parse.urlencode(params)}"
    try:
        with request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"  Search failed: {e}", file=sys.stderr)
        return []


def fetch_medline(pmid: str) -> Optional[dict]:
    """Fetch and parse a MEDLINE record for a PMID. Returns dict of fields."""
    params = {"db": "pubmed", "id": pmid, "rettype": "medline", "retmode": "text"}
    url = f"{EUTILS}/efetch.fcgi?{parse.urlencode(params)}"
    try:
        with request.urlopen(url, timeout=10) as r:
            text = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Fetch failed for PMID {pmid}: {e}", file=sys.stderr)
        return None

    record: dict[str, list[str]] = {}
    current_tag = None
    for line in text.splitlines():
        if len(line) > 6 and line[4] == "-" and line[0] != " ":
            current_tag = line[:4].strip()
            record.setdefault(current_tag, []).append(line[6:].strip())
        elif current_tag and line.startswith("      "):
            record[current_tag][-1] += " " + line.strip()

    def get(tag: str) -> str:
        return " ".join(record.get(tag, [])).strip()

    doi_raw = get("LID")
    doi = re.search(r"10\.\S+\s*\[doi\]", doi_raw)
    doi_str = doi.group(0).replace(" [doi]", "") if doi else ""

    return {
        "pmid": pmid,
        "title": get("TI"),
        "abstract": get("AB"),
        "authors": get("AU"),
        "journal": get("JT") or get("TA"),
        "year": get("DP")[:4] if get("DP") else "????",
        "doi": doi_str,
        "citation": _build_citation(get("AU"), get("DP")[:4], get("TI"), get("JT") or get("TA"), doi_str),
    }


def _build_citation(authors: str, year: str, title: str, journal: str, doi: str) -> str:
    first_author = authors.split("\n")[0].strip() if authors else "Unknown"
    title_clean = title.rstrip(".")
    doi_part = f" doi:{doi}" if doi else ""
    return f"{first_author} ({year}). \"{title_clean}.\" {journal}.{doi_part}"


# ── Code-based extraction ─────────────────────────────────────────────────────

_SUPPRESS_VERBS = [
    "inhibit", "suppress", "reduc", "decreas", "attenu", "abrogate",
    "anti-tumor", "anti-proliferative", "anti-cancer", "block", "impair",
]
_PROMOTE_VERBS = [
    "promot", "enhanc", "increas", "stimulat", "facilitat", "accelerat",
    "pro-tumor", "pro-tumorigenic", "induc", "trigger", "activ",
]
_CANCER_OUTCOMES = [
    "proliferat", "tumor", "cancer", "growth", "invasiv", "invasion",
    "metastas", "carcinogenesis", "tumorigenesis", "neoplasia", "stemness",
    "aggressiv",
]
_EXPLICIT_SUPPRESS = ["tumor suppressive", "tumor-suppressive", "tumor suppressor"]
_EXPLICIT_PROMOTE  = ["tumor promoting", "tumor-promoting", "pro-tumorigenic", "oncogenic"]

_ENDPOINT_RULES: list[tuple[list[str], str]] = [
    (["proliferat", "cell growth", "cell cycle", "viabilit", "BrdU", "MTT", "Ki-67"], "proliferation"),
    (["invasiv", "invasion", "collagen gel", "transwell", "matrigel invasion"], "invasiveness"),
    (["migrat", "scratch assay", "wound healing", "motility"], "migration"),
    (["apoptos", "cell death", "caspase", "TUNEL", "annexin V", "sub-G1"], "apoptosis"),
    (["tumor growth", "xenograft", "tumor volume", "tumor weight", "PIN", "intraepithelial neoplasia"], "tumor growth (in vivo)"),
    (["express", "mRNA", "protein level", "immunohistochem", "IHC", "western blot"], "expression"),
]

_MECHANISM_RULES: list[tuple[list[str], str]] = [
    (["mapk", "p44/42", "erk1/2", "erk 1/2"], "MAPK/ERK"),
    (["ca2+", "calcium", "intracellular ca"], "Ca2+ signaling"),
    (["nf-kb", "nf-κb", "nfkb", "rela"], "NF-κB"),
    (["pi3k", "pi3kgamma", "pi3k-gamma", "pi3 kinase"], "PI3K"),
    (["gbeta", "gβγ", "g-protein", "gpcr signaling"], "G-protein"),
    (["camp", "adenylyl cyclase", "cyclic amp"], "cAMP"),
    (["akt", "protein kinase b", "pkb"], "AKT"),
    (["plc", "phospholipase c"], "PLC"),
    (["p38", "sapk", "jnk", "stress kinase"], "p38/JNK"),
    (["wnt", "beta-catenin"], "Wnt/β-catenin"),
    (["egfr", "her2", "receptor tyrosine kinase"], "RTK"),
    (["car-t", "car t", "chimeric antigen"], "CAR-T immunotherapy"),
]

_MODEL_SYSTEM_RULES: list[tuple[list[str], str]] = [
    (["lncap", "ln cap"], "LNCaP"),
    (["xenograft", "subcutaneous tumor", "flank tumor"], "xenograft"),
    (["transgenic mouse", "transgenic mice", "knock-in", "probasin"], "transgenic mouse"),
    (["du145", "du-145"], "DU145"),
    (["pc-3", "pc3 "], "PC-3"),
    (["22rv1", "22 rv1"], "22Rv1"),
    (["a549", "h1299", "h460"], "lung cancer cell line"),
    (["ovcar", "skov3", "hey"], "ovarian cancer cell line"),
    (["hek293", "hek 293"], "HEK293"),
    (["tcga", "gdc api", "cohort"], "TCGA cohort"),
    (["rpe", "retinal pigment"], "RPE cells"),
    (["melanoma cell", "mel-2", "sk-mel", "a375"], "melanoma cell line"),
    (["organoid", "3d culture", "spheroid"], "3D organoid"),
    (["primary cell", "primary culture", "patient-derived"], "primary patient cells"),
]


def _first_rule_match(text: str, rules: list[tuple[list[str], str]], default: str = "not specified") -> str:
    lower = text.lower()
    for keywords, label in rules:
        if any(kw in lower for kw in keywords):
            return label
    return default


def _direction_vote(text: str) -> str:
    """
    Vote-based direction detection — counts independent verb + outcome signals
    rather than requiring adjacent phrases, so 'suppresses prostate cancer
    proliferation' matches even with words in between.
    """
    lower = text.lower()
    # Check for explicit labels first
    if any(p in lower for p in _EXPLICIT_SUPPRESS):
        return "tumor_suppressive"
    if any(p in lower for p in _EXPLICIT_PROMOTE):
        return "tumor_promoting"

    has_cancer_outcome = any(kw in lower for kw in _CANCER_OUTCOMES)
    sup_verb = sum(1 for kw in _SUPPRESS_VERBS if kw in lower)
    pro_verb = sum(1 for kw in _PROMOTE_VERBS if kw in lower)

    if not has_cancer_outcome:
        return "neutral"
    if sup_verb > pro_verb:
        return "tumor_suppressive"
    if pro_verb > sup_verb:
        return "tumor_promoting"
    return "neutral"


def _detect_cancer_type(text: str) -> str:
    lower = text.lower()
    for keyword, mapped in CANCER_TYPE_MAP.items():
        if keyword in lower:
            return mapped
    return "unknown"


def code_extract(medline: dict, receptor: str) -> dict:
    """Code-based field extraction from a MEDLINE record."""
    full_text = f"{medline['title']} {medline['abstract']}"
    return {
        "receptor": receptor,
        "direction": _direction_vote(full_text),
        "endpoint": _first_rule_match(full_text, _ENDPOINT_RULES),
        "mechanism": _first_rule_match(full_text, _MECHANISM_RULES),
        "model_system": _first_rule_match(full_text, _MODEL_SYSTEM_RULES),
        "cancer_type": _detect_cancer_type(full_text),
        "claim": medline["title"],  # title as the claim summary
    }


# ── Graph insertion ───────────────────────────────────────────────────────────

def build_evidence_record(medline: dict, extracted: dict) -> EvidenceRecord:
    direction = extracted["direction"]
    # Map cancer context to direction_context
    direction_context = "activation_effect"
    endpoint = extracted["endpoint"]
    if endpoint == "expression":
        direction_context = "expression_pattern"

    cancer = extracted["cancer_type"]
    if cancer == "unknown":
        cancer = "pan_cancer"

    return EvidenceRecord(
        source=medline["citation"],
        source_type="preliminary",
        claim=medline["title"],
        gene=extracted["receptor"],
        direction=direction if direction in ("tumor_suppressive", "tumor_promoting") else "neutral",
        direction_context=direction_context,
        endpoint=endpoint,
        cancer_type=cancer,
        model_system=extracted["model_system"],
        mechanism=extracted["mechanism"],
        sample_size=None,
        independent_replications=None,
        confidence_note=(
            f"AUTO-EXTRACTED from abstract. Not verified against full text. "
            f"PMID: {medline['pmid']}. Queued for Person A review."
        ),
    )


# ── Benchmark / report ────────────────────────────────────────────────────────

def load_ground_truth(receptor: str) -> list[dict]:
    path = REPO_ROOT / "data" / "receptors" / f"{receptor.lower()}.json"
    if not path.exists():
        return []
    records = json.loads(path.read_text())
    return [r for r in records if r.get("verified_by_person_a") and r.get("source_type") == "literature"]


def score_against_gt(extracted: dict, gt: dict) -> dict:
    """Quick field-match score against a ground truth record."""
    gt_dir = gt.get("direction", "").replace("-", "_")
    ex_dir = extracted["direction"]
    dir_match = int(gt_dir == ex_dir)

    gt_ep = gt.get("endpoint", "not specified").lower()
    ex_ep = extracted["endpoint"].lower()
    ep_terms = set(re.split(r"[\s,/()+]+", gt_ep)) - {"and", "or", "in", "vivo", "not", "specified"}
    ep_match = round(len({t for t in ep_terms if t in ex_ep}) / max(len(ep_terms), 1), 2)

    return {"direction": dir_match, "endpoint": ep_match}


# ── Main ──────────────────────────────────────────────────────────────────────

def run_receptor(receptor: str, max_results: int, dry_run: bool) -> dict:
    query = RECEPTOR_SEARCH.get(receptor, f'"{receptor}"')
    print(f"\n{'='*64}")
    print(f"Receptor: {receptor}")
    print(f"Query:    {query}")

    print("  Searching PubMed...")
    pmids = search_pubmed(query, max_results)
    print(f"  Found {len(pmids)} papers: {pmids}")

    ground_truth = load_ground_truth(receptor)
    gt_pmids = set()
    for gt in ground_truth:
        doi_match = re.search(r"10\.\S+", gt.get("raw_excerpt_or_link", ""))
        if doi_match:
            gt_pmids.add(doi_match.group(0).rstrip(".,;"))

    results = []
    inserted = 0
    skipped_existing = 0
    new_papers: list[dict] = []

    for pmid in pmids:
        time.sleep(0.4)  # NCBI rate limit
        medline = fetch_medline(pmid)
        if not medline or not medline["abstract"]:
            continue

        extracted = code_extract(medline, receptor)

        # Score against ground truth if we have a matching GT record
        gt_match = None
        for gt in ground_truth:
            first_author = medline["authors"].split("\n")[0].split()[0].lower() if medline["authors"] else ""
            gt_author = gt["citation"].split()[0].lower()
            gt_year = re.search(r"(19|20)\d{2}", gt["citation"])
            if first_author == gt_author and gt_year and gt_year.group(0) == medline["year"]:
                gt_match = gt
                break

        score = score_against_gt(extracted, gt_match) if gt_match else None

        result = {
            "pmid": pmid,
            "citation": medline["citation"][:80],
            "year": medline["year"],
            "extracted": extracted,
            "gt_score": score,
            "gt_matched": gt_match is not None,
        }
        results.append(result)
        new_papers.append((medline, extracted))

        print(f"\n  [{pmid}] {medline['title'][:65]}...")
        print(f"    dir={extracted['direction']:20} ep={extracted['endpoint']:20} cancer={extracted['cancer_type']}")
        print(f"    model={extracted['model_system']:25} mech={extracted['mechanism']}")
        if score:
            print(f"    GT match: dir={score['direction']} ep={score['endpoint']:.2f}")

        if not dry_run:
            ev = build_evidence_record(medline, extracted)
            row_id = insert_record(ev)
            if row_id:
                inserted += 1
            else:
                skipped_existing += 1

    # Summary
    print(f"\n  Summary: {len(results)} papers processed, {inserted} new inserted, {skipped_existing} already in DB")

    gt_scored = [r for r in results if r["gt_matched"]]
    if gt_scored:
        dir_acc = sum(r["gt_score"]["direction"] for r in gt_scored) / len(gt_scored)
        ep_acc = sum(r["gt_score"]["endpoint"] for r in gt_scored) / len(gt_scored)
        print(f"  Benchmark vs ground truth ({len(gt_scored)} papers): direction={dir_acc:.2f} endpoint={ep_acc:.2f}")

    return {
        "receptor": receptor,
        "papers_found": len(pmids),
        "papers_processed": len(results),
        "inserted": inserted,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receptor", help="Single receptor to expand (e.g. OR2H1)")
    parser.add_argument("--all-receptors", action="store_true", help="Run all 4 receptors")
    parser.add_argument("--max-results", type=int, default=20, help="Max PubMed results per receptor")
    parser.add_argument("--dry-run", action="store_true", help="Extract but don't insert into DB")
    args = parser.parse_args()

    init_db(DB_PATH)

    receptors = list(RECEPTOR_SEARCH.keys()) if args.all_receptors else [args.receptor or "OR51E2"]

    all_results = []
    for receptor in receptors:
        result = run_receptor(receptor, args.max_results, args.dry_run)
        all_results.append(result)
        time.sleep(1)  # be polite between receptors

    # Save full results
    out_path = REPO_ROOT / "data" / "expansion_results.json"
    out_path.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\nFull results saved to {out_path}")

    # Print cross-receptor summary
    print(f"\n{'='*64}")
    print("CROSS-RECEPTOR SUMMARY")
    print(f"{'Receptor':<12}  {'Found':>6}  {'Inserted':>8}  {'GT papers':>10}")
    for r in all_results:
        gt_n = sum(1 for p in r["results"] if p["gt_matched"])
        print(f"  {r['receptor']:<10}  {r['papers_found']:>6}  {r['inserted']:>8}  {gt_n:>10}")


if __name__ == "__main__":
    main()

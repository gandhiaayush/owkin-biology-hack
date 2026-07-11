#!/usr/bin/env python3
"""
Extraction benchmark: compare LLM-based vs code-based evidence extraction
against Person A's manually verified ground-truth records.

Tests whether an automated pipeline would produce the same fields that a
human researcher verified against full text — specifically whether it catches
the Sanz vs Neuhaus endpoint distinction (the hardest case).

Usage:
    python3 scripts/benchmark_extraction.py [--model claude-sonnet-5]

Output: per-field accuracy table + a report saved to data/benchmark_results.json
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

try:
    import anthropic
except ImportError:
    print("anthropic SDK not installed. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# ── PubMed fetch ──────────────────────────────────────────────────────────────

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def doi_to_pmid(doi: str) -> Optional[str]:
    """Resolve a DOI to a PubMed ID via E-utilities esearch."""
    params = {"db": "pubmed", "term": f"{doi}[doi]", "retmode": "json", "retmax": "1"}
    url = f"{EUTILS_BASE}/esearch.fcgi?{parse.urlencode(params)}"
    try:
        with request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        ids = data.get("esearchresult", {}).get("idlist", [])
        return ids[0] if ids else None
    except Exception as e:
        print(f"  WARNING: DOI→PMID lookup failed for {doi}: {e}", file=sys.stderr)
        return None


def fetch_abstract_by_pmid(pmid: str) -> Optional[str]:
    """Fetch abstract text from PubMed E-utilities by PMID (MEDLINE format)."""
    params = {"db": "pubmed", "id": pmid, "rettype": "medline", "retmode": "text"}
    url = f"{EUTILS_BASE}/efetch.fcgi?{parse.urlencode(params)}"
    try:
        with request.urlopen(url, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        # Parse "AB  -" continuation lines from MEDLINE format
        abstract_lines = []
        in_abstract = False
        for line in text.splitlines():
            if line.startswith("AB  -"):
                in_abstract = True
                abstract_lines.append(line[6:].strip())
            elif in_abstract:
                if line.startswith("      "):
                    abstract_lines.append(line.strip())
                else:
                    break
        return " ".join(abstract_lines) if abstract_lines else None
    except Exception as e:
        print(f"  WARNING: could not fetch PMID {pmid}: {e}", file=sys.stderr)
        return None


def fetch_abstract(doi: str) -> Optional[str]:
    """Resolve DOI → PMID → abstract. Returns None if either step fails."""
    pmid = doi_to_pmid(doi)
    if not pmid:
        return None
    time.sleep(0.35)  # NCBI rate limit: max 3 req/s without API key
    return fetch_abstract_by_pmid(pmid)


# ── Ground truth loading ──────────────────────────────────────────────────────

def load_ground_truth() -> list[dict]:
    path = REPO_ROOT / "data" / "receptors" / "or51e2.json"
    records = json.loads(path.read_text())
    return [r for r in records if r["source_type"] == "literature" and r["verified_by_person_a"]]


def citation_key(citation: str) -> str:
    """Extract 'FirstAuthor YYYY' key from a full citation string."""
    year_m = re.search(r"(19|20)\d{2}", citation)
    author_m = re.match(r"\s*([A-Za-z][A-Za-z\-]+)", citation)
    year = year_m.group(0) if year_m else "????"
    author = author_m.group(1) if author_m else "Unknown"
    return f"{author} et al. {year}"


# ── LLM extraction ────────────────────────────────────────────────────────────

EXTRACTION_SCHEMA = {
    "name": "extract_evidence",
    "description": (
        "Extract structured evidence from a biomedical abstract about an olfactory receptor in cancer. "
        "Be precise: base every field strictly on what the abstract states, not background knowledge."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["tumor-suppressive", "tumor-promoting", "neutral", "unclear"],
                "description": (
                    "The net effect of activating this receptor on tumor biology as stated in the abstract. "
                    "'unclear' if the abstract does not make a directional claim."
                ),
            },
            "endpoint": {
                "type": "string",
                "description": (
                    "The specific biological outcome measured in the study "
                    "(e.g. 'proliferation', 'invasiveness', 'apoptosis', 'migration', "
                    "'tumor growth'). Not what the receptor does in general — what the assay measured."
                ),
            },
            "mechanism": {
                "type": "string",
                "description": "The molecular pathway or mechanism named in the abstract (e.g. 'MAPK activation', 'NF-kB pathway', 'PI3K-gamma / Gbeta-gamma'). 'not specified' if absent.",
            },
            "model_system": {
                "type": "string",
                "description": "The experimental model used (e.g. 'LNCaP cells', 'xenograft', 'melanoma tissue', 'RPE cells').",
            },
            "cancer_type": {
                "type": "string",
                "description": "The cancer type studied, or null if the model system is non-cancerous.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "How clearly the abstract supports the fields you extracted.",
            },
            "extraction_notes": {
                "type": "string",
                "description": "Any caveats, ambiguities, or things the abstract left unclear.",
            },
        },
        "required": ["direction", "endpoint", "mechanism", "model_system", "cancer_type", "confidence", "extraction_notes"],
    },
}


def llm_extract(abstract: str, citation: str, model: str) -> Optional[dict]:
    """Call Claude to extract structured fields from an abstract."""
    client = anthropic.Anthropic()
    prompt = (
        f"Extract structured evidence from this biomedical abstract.\n\n"
        f"Citation: {citation}\n\n"
        f"Abstract:\n{abstract}\n\n"
        "Focus on what the abstract explicitly states. "
        "For 'endpoint': identify the specific biological outcome measured by the assay "
        "(proliferation? invasiveness? apoptosis? tumor growth in vivo?), not the general conclusion."
    )
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=[EXTRACTION_SCHEMA],
            tool_choice={"type": "tool", "name": "extract_evidence"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "extract_evidence":
                return block.input
    except Exception as e:
        print(f"  LLM error: {e}", file=sys.stderr)
    return None


# ── Code-based (baseline) extraction ─────────────────────────────────────────

_DIRECTION_KEYWORDS = {
    "tumor-suppressive": [
        "inhibit", "suppress", "reduce", "decrease", "anti-tumor", "anti-proliferative",
        "apoptosis", "cell death", "growth arrest",
    ],
    "tumor-promoting": [
        "promot", "enhanc", "increas", "stimulat", "pro-tumor", "invasiv", "metastas",
        "xenograft growth", "tumor growth",
    ],
}

_ENDPOINT_KEYWORDS = {
    "proliferation": ["proliferat", "cell growth", "cell cycle", "BrdU", "MTT", "viabilit"],
    "invasiveness": ["invasiv", "invasion", "collagen", "matrigel", "transwell", "metastas"],
    "apoptosis": ["apoptos", "cell death", "caspase", "TUNEL", "annexin"],
    "migration": ["migrat", "wound healing", "scratch assay"],
    "tumor growth": ["xenograft", "tumor volume", "tumor weight", "PIN", "intraepithelial"],
}

_MODEL_SYSTEM_KEYWORDS = {
    "LNCaP": ["lncap"],
    "xenograft": ["xenograft", "transgenic mouse", "in vivo"],
    "melanoma cells": ["melanoma", "sk-mel", "a375"],
    "RPE cells": ["rpe", "retinal pigment"],
    "HEK293": ["hek293", "hek 293"],
}

_MECHANISM_KEYWORDS = {
    "MAPK / Ca2+": ["mapk", "p44", "p42", "erk", "calcium", "ca2+"],
    "NF-kB": ["nf-kb", "nf-κb", "rela"],
    "PI3K-gamma / Gbeta-gamma": ["pi3k", "pi3kgamma", "gbeta", "gβγ", "gallein"],
    "cAMP / ERK / AKT": ["camp", "adenylyl cyclase", "erk1/2", "akt"],
}


def _first_match(text: str, keyword_map: dict[str, list[str]]) -> str:
    lower = text.lower()
    for label, keywords in keyword_map.items():
        if any(kw in lower for kw in keywords):
            return label
    return "not specified"


def code_extract(abstract: str) -> dict:
    """Rule-based extraction using keyword matching."""
    direction = "unclear"
    sup_hits = sum(1 for kw in _DIRECTION_KEYWORDS["tumor-suppressive"] if kw in abstract.lower())
    pro_hits = sum(1 for kw in _DIRECTION_KEYWORDS["tumor-promoting"] if kw in abstract.lower())
    if sup_hits > pro_hits:
        direction = "tumor-suppressive"
    elif pro_hits > sup_hits:
        direction = "tumor-promoting"

    return {
        "direction": direction,
        "endpoint": _first_match(abstract, _ENDPOINT_KEYWORDS),
        "mechanism": _first_match(abstract, _MECHANISM_KEYWORDS),
        "model_system": _first_match(abstract, _MODEL_SYSTEM_KEYWORDS),
        "cancer_type": "prostate" if "prostat" in abstract.lower() else (
            "melanoma" if "melanoma" in abstract.lower() else None
        ),
    }


# ── Scoring ───────────────────────────────────────────────────────────────────

def normalise_direction(d: str) -> str:
    return d.replace("-", "_").lower().strip()


def endpoint_match(extracted: str, ground_truth: str) -> float:
    """Partial credit: check if extracted endpoint contains key terms from ground truth."""
    if not extracted or not ground_truth:
        return 0.0
    e = extracted.lower()
    g = ground_truth.lower()
    if e == g:
        return 1.0
    # Check for key term overlap
    gt_terms = set(re.split(r"[\s,/()]+", g)) - {"and", "or", "in", "vivo"}
    ex_terms = set(re.split(r"[\s,/()]+", e)) - {"and", "or", "in", "vivo"}
    overlap = gt_terms & ex_terms
    if overlap:
        return round(len(overlap) / len(gt_terms), 2)
    return 0.0


_MECHANISM_ALIASES = {
    "mapk": ["mapk", "p44", "p42", "erk", "mek"],
    "ca2+": ["ca2+", "calcium", "intracellular ca"],
    "nf-kb": ["nf-kb", "nf-κb", "nfkb", "rela", "nf kb"],
    "pi3k": ["pi3k", "pi3kgamma", "pi3k-gamma"],
    "gbeta": ["gbeta", "gβγ", "gbeta-gamma"],
    "camp": ["camp", "adenylyl cyclase", "adenylate cyclase"],
    "akt": ["akt", "protein kinase b"],
}


def mechanism_match(extracted: str, ground_truth: str) -> float:
    """
    Pathway keyword overlap — checks canonical pathway names against aliases,
    so 'MAPK activation' matches 'p44/42 activation and Ca2+ increase'.
    """
    if not extracted or extracted == "not specified":
        return 0.0
    e = extracted.lower()
    g = ground_truth.lower()

    # Find which canonical pathways appear in each
    def pathway_hits(text: str) -> set:
        hits = set()
        for canonical, aliases in _MECHANISM_ALIASES.items():
            if any(alias in text for alias in aliases):
                hits.add(canonical)
        return hits

    gt_pathways = pathway_hits(g)
    ex_pathways = pathway_hits(e)
    if not gt_pathways:
        # Fall back to token overlap if no canonical pathway found in GT
        gt_tokens = set(re.findall(r"[a-z0-9]{3,}", g)) - {"and", "or", "the", "via", "not"}
        ex_tokens = set(re.findall(r"[a-z0-9]{3,}", e)) - {"and", "or", "the", "via", "not"}
        overlap = gt_tokens & ex_tokens
        return round(len(overlap) / max(len(gt_tokens), 1), 2)

    overlap = gt_pathways & ex_pathways
    return round(len(overlap) / len(gt_pathways), 2)


def score_extraction(extracted: dict, ground_truth: dict) -> dict[str, float | str]:
    gt_dir = normalise_direction(ground_truth.get("direction", ""))
    ex_dir = normalise_direction(extracted.get("direction", ""))
    direction_correct = int(gt_dir == ex_dir)

    ep_score = endpoint_match(
        extracted.get("endpoint", ""),
        ground_truth.get("endpoint", "not specified"),
    )

    mech_score = mechanism_match(
        extracted.get("mechanism", ""),
        ground_truth.get("mechanism", ""),
    )

    gt_model = ground_truth.get("model_system", "").lower()
    ex_model = extracted.get("model_system", "").lower()
    model_correct = int(
        any(term in ex_model for term in gt_model.split()[:2]) or
        any(term in gt_model for term in ex_model.split()[:2])
    )

    gt_cancer = (ground_truth.get("cancer_type") or "").lower()
    ex_cancer = (extracted.get("cancer_type") or "").lower()
    cancer_correct = int(gt_cancer in ex_cancer or ex_cancer in gt_cancer)

    return {
        "direction": direction_correct,
        "endpoint": ep_score,
        "mechanism": mech_score,
        "model_system": model_correct,
        "cancer_type": cancer_correct,
        "overall": round((direction_correct + ep_score + mech_score + model_correct + cancer_correct) / 5, 2),
    }


# ── Report ────────────────────────────────────────────────────────────────────

def print_result_row(label: str, scores: dict, extracted: dict, ground_truth: dict):
    print(f"\n  {'─'*60}")
    print(f"  {label}")
    print(f"  Direction  GT={ground_truth.get('direction'):20}  EX={extracted.get('direction'):20}  ✓={scores['direction']}")
    print(f"  Endpoint   GT={str(ground_truth.get('endpoint','?'))[:20]:20}  EX={str(extracted.get('endpoint','?'))[:20]:20}  score={scores['endpoint']}")
    print(f"  Mechanism  score={scores['mechanism']:.2f}")
    print(f"             GT: {str(ground_truth.get('mechanism',''))[:80]}")
    print(f"             EX: {str(extracted.get('mechanism',''))[:80]}")
    print(f"  Model sys  GT={str(ground_truth.get('model_system',''))[:20]:20}  EX={str(extracted.get('model_system',''))[:20]:20}  ✓={scores['model_system']}")
    print(f"  Cancer     GT={str(ground_truth.get('cancer_type',''))[:20]:20}  EX={str(extracted.get('cancer_type',''))[:20]:20}  ✓={scores['cancer_type']}")
    print(f"  OVERALL: {scores['overall']:.2f}/1.00")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-sonnet-5", help="Claude model ID")
    parser.add_argument("--no-llm", action="store_true", help="Only run code-based extraction")
    args = parser.parse_args()

    ground_truth_records = load_ground_truth()
    print(f"Ground truth: {len(ground_truth_records)} verified literature records\n")

    results = []
    llm_totals = {k: [] for k in ["direction", "endpoint", "mechanism", "model_system", "cancer_type", "overall"]}
    code_totals = {k: [] for k in ["direction", "endpoint", "mechanism", "model_system", "cancer_type", "overall"]}

    for gt in ground_truth_records:
        ckey = citation_key(gt["citation"])
        doi = None
        # Extract DOI from raw_excerpt_or_link field (format: "doi:10.xxx/yyy")
        link = gt.get("raw_excerpt_or_link", "")
        doi_match = re.search(r"doi[:\s]+(\S+)", link, re.IGNORECASE)
        if doi_match:
            doi = doi_match.group(1).rstrip(".,; \t")

        print(f"\n{'='*64}")
        print(f"Paper: {ckey}")
        print(f"DOI:   {doi or 'NOT FOUND'}")

        abstract = None
        if doi:
            print("  Resolving DOI → PMID → abstract...")
            abstract = fetch_abstract(doi)
            time.sleep(0.35)

        if not abstract:
            print("  SKIP — no abstract available")
            continue

        print(f"  Abstract ({len(abstract)} chars): {abstract[:120]}...")

        # Code-based extraction
        code_result = code_extract(abstract)
        code_scores = score_extraction(code_result, gt)
        print_result_row("CODE-BASED extraction", code_scores, code_result, gt)
        for k in code_totals:
            code_totals[k].append(code_scores[k])

        # LLM extraction
        llm_result = None
        llm_scores = None
        if not args.no_llm:
            print(f"\n  Calling Claude ({args.model})...")
            llm_result = llm_extract(abstract, gt["citation"], model=args.model)
            if llm_result:
                llm_scores = score_extraction(llm_result, gt)
                print_result_row("LLM extraction", llm_scores, llm_result, gt)
                for k in llm_totals:
                    llm_totals[k].append(llm_scores[k])
                if llm_result.get("extraction_notes"):
                    print(f"\n  LLM notes: {llm_result['extraction_notes'][:200]}")

        results.append({
            "citation_key": ckey,
            "doi": doi,
            "ground_truth": gt,
            "abstract_length": len(abstract),
            "code_extraction": code_result,
            "code_scores": code_scores,
            "llm_extraction": llm_result,
            "llm_scores": llm_scores,
        })

    # ── Summary ────────────────────────────────────────────────────────────────
    n = len(results)
    if n == 0:
        print("\nNo results — check PubMed connectivity.")
        return

    print(f"\n\n{'='*64}")
    print(f"BENCHMARK SUMMARY ({n} papers)")
    print(f"{'='*64}")
    print(f"{'Field':<16}  {'Code':>8}  {'LLM':>8}  {'Delta':>8}")
    print(f"{'─'*44}")
    for field in ["direction", "endpoint", "mechanism", "model_system", "cancer_type", "overall"]:
        code_avg = sum(code_totals[field]) / len(code_totals[field]) if code_totals[field] else 0
        if llm_totals[field] and not args.no_llm:
            llm_avg = sum(llm_totals[field]) / len(llm_totals[field])
            delta = f"{llm_avg - code_avg:+.2f}"
            llm_str = f"{llm_avg:.2f}"
        else:
            llm_str = "N/A"
            delta = "N/A"
        print(f"  {field:<14}  {code_avg:>8.2f}  {llm_str:>8}  {delta:>8}")

    print(f"\nKey test case: Sanz 2014 endpoint (should be 'invasiveness', not 'proliferation')")
    sanz_result = next((r for r in results if "Sanz" in r["citation_key"]), None)
    if sanz_result:
        code_ep = sanz_result["code_extraction"].get("endpoint", "?")
        llm_ep = sanz_result["llm_extraction"].get("endpoint", "?") if sanz_result.get("llm_extraction") else "N/A"
        print(f"  Code extracted endpoint: {code_ep!r}")
        print(f"  LLM  extracted endpoint: {llm_ep!r}")
        print(f"  Ground truth:            'invasiveness'")

    # Save results
    out_path = REPO_ROOT / "data" / "benchmark_results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()

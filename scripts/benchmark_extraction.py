#!/usr/bin/env python3
"""
Extraction benchmark: compare LLM-based vs code-based evidence extraction
against manually verified ground truth, across 22 papers spanning all four
receptors this project claims to cover (OR51E2, OR2H1, OR51B4, OR2C3) --
not just the 5 OR51E2 papers the original benchmark used.

Ground truth (scripts/benchmark_ground_truth.py) was hand-built by reading
each paper's full text where available via PMC (data/benchmark_fulltext/),
and abstract otherwise -- 14 of 22 papers had accessible full text; the
other 8 are paywalled/non-PMC and are scored on abstract-only extraction,
which is logged per-paper in the output so the two aren't silently mixed.

This is NOT a cherry-picked "everything works" set. It deliberately includes:
  - papers with no direction claim at all (an immunotherapy antigen paper),
  - a mechanism-only paper with no stated tumor-phenotype direction,
  - a paper that reports opposite-direction effects on two different
    endpoints within the same abstract (Weng 2015),
  - papers with cell-non-autonomous mechanisms (macrophage/exosome-mediated),
  - a review article restating another paper's findings,
  - and a documented list of 33 excluded PubMed hits that looked like OR-cancer
    papers by keyword search but turned out to be off-topic, genetic-locus
    coincidences, or reviews with no independent primary claim
    (scripts/benchmark_ground_truth.py:EXCLUDED_CANDIDATES).

No ANTHROPIC_API_KEY was available in the environment this was built in, so
the LLM-extraction arm uses scripts/benchmark_llm_offline.py -- 22 manually
produced extractions from the same EXTRACTION_SCHEMA/prompt the live API call
would use (see that file's docstring for exactly what that means and why
it's not the same as copying ground truth). If ANTHROPIC_API_KEY IS set, the
live API is used instead and the offline file is ignored.

Usage:
    python3 scripts/benchmark_extraction.py [--model claude-sonnet-5]

Output: per-field precision/recall table + markdown error-analysis report,
saved to data/benchmark_results.json.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional
from urllib import request, parse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from benchmark_ground_truth import GROUND_TRUTH, EXCLUDED_CANDIDATES  # noqa: E402
from benchmark_llm_offline import LLM_OFFLINE_EXTRACTIONS  # noqa: E402

HAVE_ANTHROPIC_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
if HAVE_ANTHROPIC_KEY:
    try:
        import anthropic
    except ImportError:
        print("anthropic SDK not installed. Run: pip install anthropic", file=sys.stderr)
        HAVE_ANTHROPIC_KEY = False

# ── PubMed fetch (abstract fallback for papers without full text) ───────────

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_abstract_by_pmid(pmid: str) -> Optional[str]:
    params = {"db": "pubmed", "id": pmid, "rettype": "medline", "retmode": "text"}
    url = f"{EUTILS_BASE}/efetch.fcgi?{parse.urlencode(params)}"
    try:
        with request.urlopen(url, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="replace")
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


def load_paper_text(gt: dict) -> tuple[str, str]:
    """Return (text, source_label) -- full text from data/benchmark_fulltext/
    if available, else a freshly fetched abstract."""
    pmid = gt["pmid"]
    if gt.get("full_text_available"):
        path = REPO_ROOT / "data" / "benchmark_fulltext" / f"{pmid}.txt"
        if path.exists():
            # Cap length for LLM/code input -- title/abstract/intro/results are
            # what matters for these fields, not full discussion/references.
            return path.read_text()[:20000], "full_text"
    time.sleep(0.35)
    abstract = fetch_abstract_by_pmid(pmid)
    if abstract:
        return abstract, "abstract"
    return gt["claim"], "ground_truth_claim_fallback"


# ── LLM extraction ────────────────────────────────────────────────────────────

EXTRACTION_SCHEMA = {
    "name": "extract_evidence",
    "description": (
        "Extract structured evidence from biomedical text about an olfactory receptor in cancer. "
        "Be precise: base every field strictly on what the text states, not background knowledge."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["tumor-suppressive", "tumor-promoting", "neutral", "unclear"],
                "description": "Net effect of activating this receptor on tumor biology, as stated in the text.",
            },
            "endpoint": {
                "type": "string",
                "description": "Specific biological outcome measured (not the general conclusion).",
            },
            "mechanism": {
                "type": "string",
                "description": "Molecular pathway named in the text. 'not specified' if absent.",
            },
            "model_system": {"type": "string", "description": "Experimental model used."},
            "cancer_type": {"type": "string", "description": "Cancer type studied, or null/none if non-cancerous."},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "extraction_notes": {"type": "string", "description": "Caveats or ambiguities."},
        },
        "required": ["direction", "endpoint", "mechanism", "model_system", "cancer_type", "confidence", "extraction_notes"],
    },
}


def llm_extract(text: str, citation: str, model: str) -> Optional[dict]:
    client = anthropic.Anthropic()
    prompt = (
        f"Extract structured evidence from this biomedical text.\n\nCitation: {citation}\n\nText:\n{text}\n\n"
        "Focus on what is explicitly stated. For 'endpoint': identify the specific biological outcome measured "
        "by the assay (proliferation? invasiveness? apoptosis? tumor growth in vivo? something else entirely, "
        "like immunogenicity or macrophage polarization?), not the paper's general topic."
    )
    try:
        response = client.messages.create(
            model=model, max_tokens=1024,
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


def llm_extract_offline(pmid: str) -> Optional[dict]:
    return LLM_OFFLINE_EXTRACTIONS.get(pmid)


# ── Code-based (baseline) extraction ─────────────────────────────────────────

_DIRECTION_KEYWORDS = {
    "tumor-suppressive": [
        "inhibit", "suppress", "reduce", "decrease", "anti-tumor", "anti-proliferative",
        "apoptosis", "cell death", "growth arrest", "retarded",
    ],
    "tumor-promoting": [
        "promot", "enhanc", "increas", "stimulat", "pro-tumor", "invasiv", "metastas",
        "xenograft growth", "tumor growth", "accelerat", "synerg",
    ],
}

_ENDPOINT_KEYWORDS = {
    "proliferation": ["proliferat", "cell growth", "cell cycle", "BrdU", "MTT", "viabilit"],
    "invasiveness": ["invasiv", "invasion", "collagen", "matrigel", "transwell", "metastas"],
    "apoptosis": ["apoptos", "cell death", "caspase", "TUNEL", "annexin"],
    "migration": ["migrat", "wound healing", "scratch assay"],
    "tumor growth": ["xenograft", "tumor volume", "tumor weight", "PIN", "intraepithelial"],
    "EMT / stemness": ["epithelial-mesenchymal", "emt", "stemness", "vimentin", "e-cadherin"],
    "macrophage / immune": ["macrophage", "tam", "crispr screen", "cd8", "car t", "antigen"],
    "osteoblast / bone": ["osteoblast", "osteogenesis", "bone metastas"],
    "signaling / mechanism only": ["erk1/2", "phosphorylation", "arf1", "golgi"],
}

_MODEL_SYSTEM_KEYWORDS = {
    "LNCaP": ["lncap"],
    "xenograft": ["xenograft", "transgenic mouse", "in vivo"],
    "melanoma / melanocyte cells": ["melanoma", "sk-mel", "a375", "melanocyte"],
    "RPE cells": ["rpe", "retinal pigment"],
    "HEK293": ["hek293", "hek 293"],
    "colorectal cell line": ["hct116", "ct26", "colorectal", "colon cancer"],
    "PBMC / immune cells": ["pbmc", "car t", "cd8"],
    "exosome co-culture": ["exosome"],
}

_MECHANISM_KEYWORDS = {
    "MAPK / Ca2+": ["mapk", "p44", "p42", "erk", "calcium", "ca2+"],
    "NF-kB": ["nf-kb", "nf-κ" "b", "rela"],
    "PI3K-gamma / Gbeta-gamma": ["pi3k", "pi3kgamma", "gbeta", "gβγ", "gallein"],
    "cAMP / ERK / AKT": ["camp", "adenylyl cyclase", "erk1/2", "akt"],
    "STAT3 / IL-6": ["stat3", "il-6", "il6"],
    "TRPV6 / Src": ["trpv6", "src kinase"],
    "PLC / p38 / mTOR": ["plc", "phospholipase", "p38", "mtor"],
    "m6A regulation": ["m6a", "mettl3", "mettl14", "ythdf"],
    "EMT reprogramming": ["vimentin", "e-cadherin", "snail", "sox2", "oct4"],
    "not applicable (immunogenicity)": ["hla-a2", "cd8", "peptide-specific t cell"],
}


def _first_match(text: str, keyword_map: dict[str, list[str]]) -> str:
    lower = text.lower()
    for label, keywords in keyword_map.items():
        if any(kw in lower for kw in keywords):
            return label
    return "not specified"


_CANCER_TYPE_KEYWORDS = {
    "prostate": "prostate",
    "melanoma": "melanoma",
    "colorectal": "colorectal",
    "colon cancer": "colorectal",
    "ovarian": "ovarian",
    "lung cancer": "lung",
    "nsclc": "lung",
    "cholangiocarcinoma": "cholangiocarcinoma",
    "breast cancer": "breast",
}


def code_extract(text: str) -> dict:
    lower = text.lower()
    direction = "unclear"
    sup_hits = sum(1 for kw in _DIRECTION_KEYWORDS["tumor-suppressive"] if kw in lower)
    pro_hits = sum(1 for kw in _DIRECTION_KEYWORDS["tumor-promoting"] if kw in lower)
    if sup_hits > pro_hits:
        direction = "tumor-suppressive"
    elif pro_hits > sup_hits:
        direction = "tumor-promoting"

    cancer_hits = [v for k, v in _CANCER_TYPE_KEYWORDS.items() if k in lower]
    cancer_type = cancer_hits[0] if cancer_hits else None

    return {
        "direction": direction,
        "endpoint": _first_match(text, _ENDPOINT_KEYWORDS),
        "mechanism": _first_match(text, _MECHANISM_KEYWORDS),
        "model_system": _first_match(text, _MODEL_SYSTEM_KEYWORDS),
        "cancer_type": cancer_type,
    }


# ── Scoring ───────────────────────────────────────────────────────────────────

def normalise_direction(d: str) -> str:
    d = (d or "").replace("-", "_").lower().strip()
    if d in ("mixed", "mixed_endpoint_dependent", "mixed / endpoint-dependent".replace("-", "_").lower()):
        return "mixed"
    return d


def endpoint_match(extracted: str, ground_truth: str) -> float:
    if not extracted or not ground_truth:
        return 0.0
    e, g = extracted.lower(), ground_truth.lower()
    if e == g:
        return 1.0
    gt_terms = set(re.split(r"[\s,/()]+", g)) - {"and", "or", "in", "vivo", "the", "not", "specified"}
    ex_terms = set(re.split(r"[\s,/()]+", e)) - {"and", "or", "in", "vivo", "the", "not", "specified"}
    overlap = gt_terms & ex_terms
    return round(len(overlap) / len(gt_terms), 2) if overlap and gt_terms else 0.0


_MECHANISM_ALIASES = {
    "mapk": ["mapk", "p44", "p42", "erk", "mek"],
    "ca2+": ["ca2+", "calcium", "intracellular ca"],
    "nf-kb": ["nf-kb", "nf-κb", "nfkb", "rela"],
    "pi3k": ["pi3k", "pi3kgamma", "pi3k-gamma"],
    "gbeta": ["gbeta", "gβγ", "gbeta-gamma"],
    "camp": ["camp", "adenylyl cyclase", "adenylate cyclase"],
    "akt": ["akt", "protein kinase b"],
    "stat3": ["stat3", "il-6", "il6"],
    "trpv6": ["trpv6", "src kinase"],
    "plc": ["plc", "phospholipase"],
    "p38": ["p38", "mtor"],
    "m6a": ["m6a", "mettl3", "mettl14", "ythdf"],
    "emt": ["vimentin", "e-cadherin", "snail", "sox2", "oct4"],
    "not_applicable": ["not applicable", "not a signaling", "immunogenicity"],
}


def mechanism_match(extracted: str, ground_truth: str) -> float:
    if not extracted or extracted == "not specified":
        return 0.0
    e, g = extracted.lower(), ground_truth.lower()

    def pathway_hits(text: str) -> set:
        return {c for c, aliases in _MECHANISM_ALIASES.items() if any(a in text for a in aliases)}

    gt_pathways, ex_pathways = pathway_hits(g), pathway_hits(e)
    if not gt_pathways:
        gt_tokens = set(re.findall(r"[a-z0-9]{3,}", g)) - {"and", "or", "the", "via", "not"}
        ex_tokens = set(re.findall(r"[a-z0-9]{3,}", e)) - {"and", "or", "the", "via", "not"}
        overlap = gt_tokens & ex_tokens
        return round(len(overlap) / max(len(gt_tokens), 1), 2)
    overlap = gt_pathways & ex_pathways
    return round(len(overlap) / len(gt_pathways), 2)


def model_match(extracted: str, ground_truth: str) -> int:
    gt_model, ex_model = (ground_truth or "").lower(), (extracted or "").lower()
    return int(
        any(term in ex_model for term in gt_model.split()[:2]) or
        any(term in gt_model for term in ex_model.split()[:2])
    )


_CANONICAL_CANCER_TYPES = [
    "prostate", "melanoma", "colorectal", "ovarian", "lung",
    "cholangiocarcinoma", "breast", "pan_epithelial",
]


def canonicalize_cancer_type(value: Optional[str]) -> str:
    """Bucket a free-text cancer_type string into a fixed category set so
    precision/recall comparisons aren't defeated by phrasing differences
    ('prostate cancer' vs 'prostate') that the substring-based mean-score
    match (cancer_match) already tolerates -- without this, precision/recall
    per class would silently show 0 recall on fields that are actually
    correct, just phrased differently than the ground truth bucket label."""
    if not value:
        return "none"
    lower = value.lower()
    if "none" in lower or "null" in lower or "non-cancer" in lower:
        return "none"
    hits = [c for c in _CANONICAL_CANCER_TYPES if c.replace("_", " ") in lower or c in lower]
    if len(hits) > 1 or "pan" in lower or ("ovarian" in lower and "lung" in lower):
        return "pan_epithelial"
    return hits[0] if hits else "other/unrecognized"


def cancer_match(extracted, ground_truth) -> int:
    gt_cancer = (ground_truth or "").lower() if ground_truth else "none"
    ex_cancer = (extracted or "").lower() if extracted else "none"
    if gt_cancer in ("none", "null", ""):
        gt_cancer = "none"
    if ex_cancer in ("none", "null", ""):
        ex_cancer = "none"
    return int(gt_cancer in ex_cancer or ex_cancer in gt_cancer)


def score_extraction(extracted: dict, gt: dict) -> dict:
    gt_dir = normalise_direction(gt.get("direction", ""))
    ex_dir = normalise_direction(extracted.get("direction", ""))
    direction_correct = int(gt_dir == ex_dir)
    ep_score = endpoint_match(extracted.get("endpoint", ""), gt.get("endpoint", "not specified"))
    mech_score = mechanism_match(extracted.get("mechanism", ""), gt.get("mechanism", ""))
    model_correct = model_match(extracted.get("model_system", ""), gt.get("model_system", ""))
    cancer_correct = cancer_match(extracted.get("cancer_type"), gt.get("cancer_type"))

    return {
        "direction": direction_correct,
        "endpoint": ep_score,
        "mechanism": mech_score,
        "model_system": model_correct,
        "cancer_type": cancer_correct,
        "overall": round((direction_correct + ep_score + mech_score + model_correct + cancer_correct) / 5, 2),
        "gt_direction": gt_dir,
        "ex_direction": ex_dir,
    }


# ── Precision / recall aggregation (classification fields only) ─────────────

def precision_recall_per_class(pairs: list[tuple[str, str]]) -> dict:
    """pairs: list of (ground_truth_label, predicted_label). Returns per-class
    precision/recall/support plus macro averages -- real precision/recall,
    not just accuracy, so a field that's only 'right' on the easy majority
    class shows up as weak on the classes it actually misses."""
    classes = sorted(set(gt for gt, _ in pairs) | set(ex for _, ex in pairs))
    per_class = {}
    for c in classes:
        tp = sum(1 for gt, ex in pairs if gt == c and ex == c)
        fp = sum(1 for gt, ex in pairs if gt != c and ex == c)
        fn = sum(1 for gt, ex in pairs if gt == c and ex != c)
        precision = round(tp / (tp + fp), 2) if (tp + fp) else None
        recall = round(tp / (tp + fn), 2) if (tp + fn) else None
        support = sum(1 for gt, _ in pairs if gt == c)
        if support == 0:
            continue
        per_class[c] = {"precision": precision, "recall": recall, "support": support}
    precisions = [v["precision"] for v in per_class.values() if v["precision"] is not None]
    recalls = [v["recall"] for v in per_class.values() if v["recall"] is not None]
    return {
        "per_class": per_class,
        "macro_precision": round(sum(precisions) / len(precisions), 2) if precisions else None,
        "macro_recall": round(sum(recalls) / len(recalls), 2) if recalls else None,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    print(f"Ground truth: {len(GROUND_TRUTH)} papers across "
          f"{len(set(r['receptor'] for r in GROUND_TRUTH))} receptors "
          f"({sum(1 for r in GROUND_TRUTH if r['full_text_available'])} with full text, "
          f"{sum(1 for r in GROUND_TRUTH if not r['full_text_available'])} abstract-only)")
    print(f"Excluded candidates logged: {len(EXCLUDED_CANDIDATES)} "
          f"(false positives / off-topic / duplicate hits from the same PubMed searches)")
    print(f"LLM extraction source: {'live ANTHROPIC_API_KEY call' if HAVE_ANTHROPIC_KEY else 'offline pre-computed (scripts/benchmark_llm_offline.py)'}\n")

    results = []
    code_direction_pairs, llm_direction_pairs = [], []
    code_cancer_pairs, llm_cancer_pairs = [], []
    code_totals = defaultdict(list)
    llm_totals = defaultdict(list)

    for gt in GROUND_TRUTH:
        pmid = gt["pmid"]
        print(f"\n{'='*64}\nPaper: {gt['citation'][:70]}\nPMID: {pmid}  Receptor: {gt['receptor']}")

        text, source_label = load_paper_text(gt)
        print(f"  Input: {source_label} ({len(text)} chars)")

        code_result = code_extract(text)
        code_scores = score_extraction(code_result, gt)
        print(f"  CODE:  dir={code_result['direction']:18} ep={code_scores['endpoint']:.2f} "
              f"mech={code_scores['mechanism']:.2f} model={code_scores['model_system']} cancer={code_scores['cancer_type']}")
        for k in ("direction", "endpoint", "mechanism", "model_system", "cancer_type", "overall"):
            code_totals[k].append(code_scores[k])
        code_direction_pairs.append((code_scores["gt_direction"], code_scores["ex_direction"]))
        code_cancer_pairs.append((canonicalize_cancer_type(gt.get("cancer_type")), canonicalize_cancer_type(code_result.get("cancer_type"))))

        llm_result = None
        llm_scores = None
        if not args.no_llm:
            if HAVE_ANTHROPIC_KEY:
                llm_result = llm_extract(text, gt["citation"], model=args.model)
            else:
                llm_result = llm_extract_offline(pmid)
            if llm_result:
                llm_scores = score_extraction(llm_result, gt)
                print(f"  LLM:   dir={llm_result['direction']:18} ep={llm_scores['endpoint']:.2f} "
                      f"mech={llm_scores['mechanism']:.2f} model={llm_scores['model_system']} cancer={llm_scores['cancer_type']}")
                for k in ("direction", "endpoint", "mechanism", "model_system", "cancer_type", "overall"):
                    llm_totals[k].append(llm_scores[k])
                llm_direction_pairs.append((llm_scores["gt_direction"], llm_scores["ex_direction"]))
                llm_cancer_pairs.append((canonicalize_cancer_type(gt.get("cancer_type")), canonicalize_cancer_type(llm_result.get("cancer_type"))))

        results.append({
            "pmid": pmid,
            "receptor": gt["receptor"],
            "citation_key": gt["citation"][:60],
            "input_source": source_label,
            "ground_truth": gt,
            "code_extraction": code_result,
            "code_scores": code_scores,
            "llm_extraction": llm_result,
            "llm_scores": llm_scores,
        })

    # ── Summary ───────────────────────────────────────────────────────────
    n = len(results)
    print(f"\n\n{'='*64}\nBENCHMARK SUMMARY ({n} papers, {len(EXCLUDED_CANDIDATES)} excluded/logged)\n{'='*64}")
    print(f"{'Field':<16}  {'Code (mean)':>12}  {'LLM (mean)':>12}  {'Delta':>8}")
    for field in ["direction", "endpoint", "mechanism", "model_system", "cancer_type", "overall"]:
        code_avg = sum(code_totals[field]) / len(code_totals[field]) if code_totals[field] else 0
        if llm_totals[field]:
            llm_avg = sum(llm_totals[field]) / len(llm_totals[field])
            print(f"  {field:<14}  {code_avg:>12.2f}  {llm_avg:>12.2f}  {llm_avg-code_avg:>+8.2f}")
        else:
            print(f"  {field:<14}  {code_avg:>12.2f}  {'N/A':>12}  {'N/A':>8}")

    code_dir_pr = precision_recall_per_class(code_direction_pairs)
    llm_dir_pr = precision_recall_per_class(llm_direction_pairs)
    code_cancer_pr = precision_recall_per_class(code_cancer_pairs)
    llm_cancer_pr = precision_recall_per_class(llm_cancer_pairs)

    print(f"\nDIRECTION precision/recall per class (code):")
    for cls, v in code_dir_pr["per_class"].items():
        print(f"  {cls:<12} precision={v['precision']} recall={v['recall']} (n={v['support']})")
    print(f"  macro: precision={code_dir_pr['macro_precision']} recall={code_dir_pr['macro_recall']}")

    print(f"\nDIRECTION precision/recall per class (LLM):")
    for cls, v in llm_dir_pr["per_class"].items():
        print(f"  {cls:<12} precision={v['precision']} recall={v['recall']} (n={v['support']})")
    print(f"  macro: precision={llm_dir_pr['macro_precision']} recall={llm_dir_pr['macro_recall']}")

    summary = {
        "n_papers": n,
        "n_excluded_logged": len(EXCLUDED_CANDIDATES),
        "receptors_covered": sorted(set(r["receptor"] for r in GROUND_TRUTH)),
        "full_text_papers": sum(1 for r in GROUND_TRUTH if r["full_text_available"]),
        "abstract_only_papers": sum(1 for r in GROUND_TRUTH if not r["full_text_available"]),
        "llm_extraction_source": "live_api" if HAVE_ANTHROPIC_KEY else "offline_precomputed",
        "field_means": {
            field: {
                "code": round(sum(code_totals[field]) / len(code_totals[field]), 3) if code_totals[field] else None,
                "llm": round(sum(llm_totals[field]) / len(llm_totals[field]), 3) if llm_totals[field] else None,
            }
            for field in ["direction", "endpoint", "mechanism", "model_system", "cancer_type", "overall"]
        },
        "direction_precision_recall": {"code": code_dir_pr, "llm": llm_dir_pr},
        "cancer_type_precision_recall": {"code": code_cancer_pr, "llm": llm_cancer_pr},
    }

    out_path = REPO_ROOT / "data" / "benchmark_results.json"
    out_path.write_text(json.dumps({"summary": summary, "papers": results, "excluded_candidates": EXCLUDED_CANDIDATES},
                                    indent=2, default=str))
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()

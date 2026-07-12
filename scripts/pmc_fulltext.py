#!/usr/bin/env python3
"""Fetch PMC full-text XML for a paper and extract figure-level, methods-grounded
evidence candidates -- the fix for the abstract-only extraction gap (Person A's
existing pipeline only ever saw title+abstract via MEDLINE, so sample_size and
replication_count were always null and multi-figure papers collapsed to one
evidence record).

This is a CANDIDATE generator, not an auto-committer: it writes proposed
figure-level records to a review file (data/receptors/<receptor>_fulltext_candidates.json)
rather than merging into the verified data/receptors/<receptor>.json directly.
Person A reviews and hand-merges the ones that check out -- full-text figure
captions still need a human to confirm the caption's claim matches what the
receptor's role actually is (see e.g. the OR51E1-vs-OR51E2 check this pipeline
doesn't do automatically).

IMPORTANT LIMITATION (found while building this): not every paper claimed to be
"in PMC" actually has machine-readable full text via this API -- some PMC
records are metadata-only (front matter) with the body/back withheld from the
OA subset, even for older, seemingly-open papers. This script detects that case
explicitly and reports it rather than silently returning nothing.

Usage:
    python3 scripts/pmc_fulltext.py --pmcid PMC3885679 --receptor OR51E2 --citation-hint "Sanz et al. 2014"
    python3 scripts/pmc_fulltext.py --doi 10.1371/journal.pone.0085110 --receptor OR51E2
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional
from urllib import request, parse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Reuse the keyword rule tables from the existing abstract-only pipeline rather
# than duplicating them -- same classification logic, just fed richer text.
from pubmed_expand import (  # noqa: E402
    _direction_vote, _first_rule_match, _detect_cancer_type,
    _ENDPOINT_RULES, _MECHANISM_RULES, _MODEL_SYSTEM_RULES,
)

import xml.etree.ElementTree as ET

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
IDCONV = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"

_NEGATIVE_RESULT_PHRASES = [
    "not significantly different", "no significant effect", "did not induce",
    "no significant difference", "had no effect", "did not observe an increased",
    "could not replicate", "no significant change", "not statistically significant",
]

_N_PATTERNS = [
    re.compile(r"\bn\s*=\s*(\d+)\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\s+(?:mice|animals|rats)\s+per\s+group", re.IGNORECASE),
    re.compile(r"\bperformed\s+(\d+)\s+times\b", re.IGNORECASE),
    re.compile(r"\bperformed\s+(\d+)\s*(?:to|-)\s*\d+\s+times\b", re.IGNORECASE),
]


def doi_to_pmcid(doi: str) -> Optional[str]:
    url = f"{IDCONV}?{parse.urlencode({'ids': doi, 'format': 'json'})}"
    with request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    records = data.get("records", [])
    if not records or "pmcid" not in records[0]:
        return None
    return records[0]["pmcid"]


def fetch_pmc_xml(pmcid: str) -> ET.Element:
    pmcid_num = pmcid.replace("PMC", "")
    params = {"db": "pmc", "id": pmcid_num, "rettype": "xml", "retmode": "xml"}
    url = f"{EUTILS}/efetch.fcgi?{parse.urlencode(params)}"
    with request.urlopen(url, timeout=20) as resp:
        xml_bytes = resp.read()
    return ET.fromstring(xml_bytes)


def has_full_text(root: ET.Element) -> bool:
    """Some PMC records return only <front> (metadata) with no <body> --
    that means the paper is indexed but not in the machine-readable OA subset."""
    return root.find(".//body") is not None


def extract_n_values(text: str) -> list[int]:
    values = []
    for pattern in _N_PATTERNS:
        for m in pattern.finditer(text):
            values.append(int(m.group(1)))
    return values


def is_negative_result(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in _NEGATIVE_RESULT_PHRASES)


def extract_figures(root: ET.Element) -> list[dict]:
    figs = []
    for fig in root.findall(".//fig"):
        label_el = fig.find("label")
        cap_el = fig.find("caption")
        label = label_el.text if label_el is not None else "Figure ?"
        caption = "".join(cap_el.itertext()) if cap_el is not None else ""
        if not caption:
            continue
        figs.append({"label": label, "caption": caption})
    return figs


def extract_results_paragraphs(root: ET.Element) -> list[str]:
    paragraphs = []
    body = root.find(".//body")
    if body is None:
        return paragraphs
    for sec in body.findall(".//sec"):
        title_el = sec.find("title")
        title = (title_el.text or "") if title_el is not None else ""
        if "result" in title.lower() or "discussion" in title.lower():
            for p in sec.findall("./p"):
                text = "".join(p.itertext())
                if text.strip():
                    paragraphs.append(text)
    return paragraphs


def build_candidate_record(receptor: str, citation: str, fig: dict, matched_paragraph: str) -> dict:
    combined_text = f"{fig['caption']} {matched_paragraph}"
    n_values = extract_n_values(combined_text)
    negative = is_negative_result(matched_paragraph) or is_negative_result(fig["caption"])

    direction = _direction_vote(combined_text)
    endpoint = _first_rule_match(combined_text, _ENDPOINT_RULES)
    mechanism = _first_rule_match(combined_text, _MECHANISM_RULES)
    model_system = _first_rule_match(combined_text, _MODEL_SYSTEM_RULES)
    cancer_type = _detect_cancer_type(combined_text)

    return {
        "receptor": receptor,
        "source_type": "literature",
        "citation": f"{citation}, {fig['label']} (figure-level, full-text extraction)",
        "claim": fig["caption"][:400],
        "mechanism": mechanism if mechanism != "not specified" else None,
        "direction": ("neutral" if negative else direction.replace("_", "-")),
        "endpoint": endpoint if endpoint != "not specified" else None,
        "model_system": model_system if model_system != "not specified" else None,
        "sample_size": None,
        "replication_count": max(n_values) if n_values else None,
        "cancer_type": cancer_type if cancer_type not in ("unknown",) else None,
        "verified_by_person_a": False,
        "verification_notes": (
            "CANDIDATE, NOT YET MERGED. Auto-extracted from PMC full-text XML figure caption "
            + (f"+ matched Results/Discussion paragraph. " if matched_paragraph else ". ")
            + ("Negative-result phrase detected in surrounding text -- flagged direction=neutral "
               "rather than trusting the keyword vote. " if negative else "")
            + f"N/replication values found in text: {n_values or 'none'}. "
            "Person A must confirm this figure's receptor identity, endpoint, and quantitative "
            "claim against the source before merging into the verified evidence file -- keyword "
            "extraction on figure captions can misattribute claims (e.g. a caption mentioning two "
            "receptors where only one was actually tested in that panel)."
        ),
        "raw_excerpt_or_link": fig["caption"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pmcid", help="PMC ID, e.g. PMC3885679")
    parser.add_argument("--doi", help="DOI to resolve to a PMCID first")
    parser.add_argument("--receptor", required=True)
    parser.add_argument("--citation-hint", default=None, help="Short citation label for output records")
    args = parser.parse_args()

    pmcid = args.pmcid
    if not pmcid and args.doi:
        print(f"Resolving DOI {args.doi} to PMCID...")
        pmcid = doi_to_pmcid(args.doi)
        if not pmcid:
            print(f"  No PMCID found for DOI {args.doi} -- not in PMC at all.")
            sys.exit(1)
        print(f"  -> {pmcid}")

    if not pmcid:
        print("Must supply --pmcid or --doi")
        sys.exit(1)

    print(f"Fetching PMC full text for {pmcid}...")
    root = fetch_pmc_xml(pmcid)

    if not has_full_text(root):
        print(f"  NO FULL TEXT AVAILABLE for {pmcid} -- this record is metadata-only in PMC "
              "(not in the machine-readable Open Access subset), despite being indexed. "
              "This paper needs a different path (Unpaywall PDF / manual fetch).")
        sys.exit(2)

    title_el = root.find(".//article-title")
    title = "".join(title_el.itertext()) if title_el is not None else "(untitled)"
    print(f"  Title: {title}")

    figures = extract_figures(root)
    paragraphs = extract_results_paragraphs(root)
    print(f"  {len(figures)} figures, {len(paragraphs)} results/discussion paragraphs")

    citation = args.citation_hint or f"{pmcid} full text"
    candidates = []
    for fig in figures:
        # naive match: find the results paragraph most likely describing this figure
        matched = ""
        for p in paragraphs:
            if fig["label"] and fig["label"] in p:
                matched = p
                break
        candidates.append(build_candidate_record(args.receptor, citation, fig, matched))

    out_file = REPO_ROOT / "data" / "receptors" / f"{args.receptor.lower()}_fulltext_candidates.json"
    existing = json.loads(out_file.read_text()) if out_file.exists() else []
    existing = [r for r in existing if not r["citation"].startswith(citation)]
    existing.extend(candidates)
    out_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")

    for c in candidates:
        label = c["citation"].split(",")[1].strip() if "," in c["citation"] else "?"
        print(f"  [{label:12}] direction={c['direction']:16} "
              f"endpoint={c['endpoint'] or 'n/a':16} "
              f"reps={c['replication_count']}")

    print(f"\nWrote {len(candidates)} candidate records to {out_file}")
    print("These are NOT in the verified evidence file -- review and hand-merge into "
          f"data/receptors/{args.receptor.lower()}.json.")


if __name__ == "__main__":
    main()

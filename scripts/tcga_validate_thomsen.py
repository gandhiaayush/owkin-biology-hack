#!/usr/bin/env python3
"""
Cross-validate the Thomsen et al. 2025 BMC Cancer claim against our own TCGA-PRAD data.

Thomsen's claim: "low OR51E2 expression correlates with worse prognosis and higher
Gleason grade in the TCGA-PRAD cohort."

What we can check with the GDC public API (no file downloads needed):
  1. Fetch TCGA-PRAD cases with Gleason grade and vital status from GDC /cases API
  2. Fetch OR51E2 CNV gain/loss/neutral per case from GDC /cnvs API
  3. Check: are high-Gleason-grade cases under-represented in the CNV-gain group?
     (CNV gain is a proxy for expression here — not identical to RNA level, but
      correlated enough to be a meaningful independent check)

Honest reporting contract (mirrors CLAUDE.md discipline):
  - If the data supports Thomsen:  upgrade the evidence record's confidence_note
  - If the data contradicts:       flag it explicitly — this is MORE interesting
  - If too ambiguous:              say so plainly
  - Never manufacture a conclusion to report success

Usage:
  python3 scripts/tcga_validate_thomsen.py
  python3 scripts/tcga_validate_thomsen.py --update-json  # write result to or51e2.json
"""
import json
import sys
import argparse
from collections import Counter, defaultdict
from pathlib import Path
from urllib import request, parse

GDC_API = "https://api.gdc.cancer.gov"
REPO_ROOT = Path(__file__).resolve().parent.parent
OR51E2_ENSG = "ENSG00000167332"  # confirmed from prior tcga_pull.py runs


def gdc_get(path: str, params: dict) -> dict:
    url = f"{GDC_API}/{path}?{parse.urlencode(params)}"
    with request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_prad_cases_with_gleason(size: int = 2000) -> list[dict]:
    """Fetch TCGA-PRAD cases with Gleason score and vital status from GDC /cases."""
    filters = {
        "op": "and",
        "content": [
            {"op": "=", "content": {"field": "project.project_id", "value": "TCGA-PRAD"}},
            {"op": "is not", "content": {"field": "diagnoses.gleason_grade_group", "value": "missing"}},
        ],
    }
    params = {
        "filters": json.dumps(filters),
        "fields": (
            "case_id,"
            "diagnoses.gleason_grade_group,"
            "diagnoses.primary_gleason_grade,"
            "diagnoses.secondary_gleason_grade,"
            "diagnoses.tumor_grade,"
            "demographic.vital_status,"
            "demographic.days_to_death,"
            "diagnoses.days_to_last_follow_up"
        ),
        "size": str(size),
    }
    data = gdc_get("cases", params)
    return data["data"]["hits"]


def fetch_or51e2_cnv_by_case() -> dict[str, str]:
    """
    Fetch OR51E2 CNV calls for TCGA-PRAD and return {case_id: cnv_change}.
    cnv_change values: "Gain", "Loss", or absent (neutral).
    Fetches both Gain and Loss separately since the API filters on one value at a time.
    """
    cnv_by_case: dict[str, str] = {}

    for change in ("Gain", "Loss"):
        filters = {
            "op": "and",
            "content": [
                {"op": "=", "content": {"field": "consequence.gene.gene_id", "value": OR51E2_ENSG}},
                {"op": "=", "content": {"field": "cnv_change", "value": change}},
                {"op": "=", "content": {"field": "occurrence.case.project.project_id", "value": "TCGA-PRAD"}},
            ],
        }
        params = {
            "filters": json.dumps(filters),
            "fields": "occurrence.case.case_id,cnv_change",
            "size": "2000",
        }
        data = gdc_get("cnvs", params)
        for h in data["data"]["hits"]:
            for occ in h.get("occurrence", []):
                cid = occ["case"]["case_id"]
                if cid not in cnv_by_case:
                    cnv_by_case[cid] = change

    return cnv_by_case


def _pattern_to_int(pattern: str | None) -> int | None:
    """Convert GDC 'Pattern X' string to integer. Returns None if not parseable."""
    if not pattern:
        return None
    # GDC returns "Pattern 3", "Pattern 4", "Pattern 5" etc.
    pat = pattern.strip().lower().replace("pattern", "").strip()
    try:
        return int(pat)
    except ValueError:
        return None


def extract_gleason(case: dict) -> str | None:
    """Extract Gleason grade group from a GDC case record. Returns None if missing."""
    diags = case.get("diagnoses", [])
    if not diags:
        return None
    d = diags[0]

    # Try gleason_grade_group first (most direct)
    gg = d.get("gleason_grade_group")
    if gg and gg not in ("--", "unknown", "not reported", None):
        return gg

    # Fall back to primary + secondary pattern sum (GDC returns "Pattern 3" etc.)
    pri = _pattern_to_int(d.get("primary_gleason_grade"))
    sec = _pattern_to_int(d.get("secondary_gleason_grade"))
    if pri is not None and sec is not None:
        total = pri + sec
        if total <= 6:
            return "Group 1"
        elif total == 7 and pri == 3:
            return "Group 2"
        elif total == 7 and pri == 4:
            return "Group 3"
        elif total == 8:
            return "Group 4"
        else:
            return "Group 5"
    # Only primary available
    if pri is not None:
        return f"Pattern {pri} only"
    return None


def gleason_group_to_int(group: str) -> int:
    """Convert Gleason group string to ordinal for comparison."""
    mapping = {
        "Group 1": 1, "Grade Group 1": 1,
        "Group 2": 2, "Grade Group 2": 2,
        "Group 3": 3, "Grade Group 3": 3,
        "Group 4": 4, "Grade Group 4": 4,
        "Group 5": 5, "Grade Group 5": 5,
    }
    for k, v in mapping.items():
        if group.strip().lower() == k.lower():
            return v
    return 0  # unknown


def analyse(cases: list[dict], cnv_by_case: dict[str, str]) -> dict:
    """
    Join Gleason grade and CNV status, compute distributions, and draw an honest conclusion.
    """
    joined = []
    for case in cases:
        cid = case["case_id"]
        gleason = extract_gleason(case)
        if gleason is None:
            continue
        cnv = cnv_by_case.get(cid, "Neutral")  # no CNV record = neutral
        g_int = gleason_group_to_int(gleason)
        if g_int == 0:
            continue
        joined.append({"case_id": cid, "gleason": gleason, "gleason_int": g_int, "cnv": cnv})

    if not joined:
        return {
            "conclusion": "ambiguous",
            "reason": "No TCGA-PRAD cases with both Gleason grade and CNV data found via GDC API.",
            "n_cases_analysed": 0,
            "n_with_cnv_data": 0,
            "cnv_distribution": {},
            "mean_gleason_by_cnv": {},
            "gleason_distribution": {},
            "caveat": "Insufficient data to draw any conclusion.",
        }

    total = len(joined)
    cnv_counts: Counter = Counter(r["cnv"] for r in joined)

    # Mean Gleason group per CNV category
    by_cnv: dict[str, list[int]] = defaultdict(list)
    for r in joined:
        by_cnv[r["cnv"]].append(r["gleason_int"])

    mean_gleason: dict[str, float] = {
        cnv: sum(gs) / len(gs) for cnv, gs in by_cnv.items() if gs
    }

    # Thomsen's claim: low OR51E2 expression → higher Gleason → worse prognosis.
    # Proxy check: CNV Gain (higher genomic copy → likely higher expression) → lower Gleason?
    gain_mean = mean_gleason.get("Gain")
    loss_mean = mean_gleason.get("Loss")
    neutral_mean = mean_gleason.get("Neutral")

    conclusion = "ambiguous"
    reason = ""

    if gain_mean is not None and neutral_mean is not None:
        if gain_mean < neutral_mean - 0.1:
            conclusion = "supports_thomsen"
            reason = (
                f"CNV-Gain cases (proxy for higher expression) have lower mean Gleason group "
                f"({gain_mean:.2f}) than CNV-Neutral cases ({neutral_mean:.2f}), consistent "
                f"with Thomsen's claim that higher OR51E2 expression correlates with better prognosis."
            )
        elif gain_mean > neutral_mean + 0.1:
            conclusion = "contradicts_thomsen"
            reason = (
                f"CNV-Gain cases (proxy for higher expression) have HIGHER mean Gleason group "
                f"({gain_mean:.2f}) than CNV-Neutral cases ({neutral_mean:.2f}), which is the "
                f"OPPOSITE of Thomsen's claim. Note: CNV gain ≠ RNA expression — this is a proxy "
                f"check only, not a direct expression measurement. Treat as a signal, not a refutation."
            )
        else:
            conclusion = "ambiguous"
            reason = (
                f"CNV-Gain mean Gleason ({gain_mean:.2f}) and CNV-Neutral mean Gleason "
                f"({neutral_mean:.2f}) are too similar to draw a conclusion. CNV gain is a weak "
                f"proxy for expression; direct RNA-seq data would be needed for a definitive test."
            )

    if loss_mean is not None:
        reason += (
            f" CNV-Loss cases (proxy for lower expression): mean Gleason {loss_mean:.2f} "
            f"(n={len(by_cnv['Loss'])})."
        )

    return {
        "conclusion": conclusion,
        "reason": reason,
        "n_cases_analysed": total,
        "n_with_cnv_data": sum(1 for r in joined if r["cnv"] != "Neutral"),
        "cnv_distribution": dict(cnv_counts),
        "mean_gleason_by_cnv": {k: round(v, 3) for k, v in mean_gleason.items()},
        "gleason_distribution": dict(Counter(r["gleason"] for r in joined)),
        "caveat": (
            "This is a CNV-based proxy check, not a direct expression-vs-Gleason test. "
            "The Thomsen claim is about RNA expression level, which requires downloading "
            "STAR-counts files from GDC (not accessible via simple REST API). CNV gain "
            "correlates with expression on average but is not equivalent. Treat this as "
            "a corroborating signal or a red flag, not a definitive confirmation or refutation."
        ),
    }


def update_json_record(result: dict) -> None:
    """Update the Thomsen evidence record in or51e2.json with the cross-validation result."""
    path = REPO_ROOT / "data" / "receptors" / "or51e2.json"
    records = json.loads(path.read_text())

    thomsen_idx = next(
        (i for i, r in enumerate(records) if "Thomsen" in r.get("citation", "")),
        None,
    )
    if thomsen_idx is None:
        print("  WARNING: Thomsen record not found in or51e2.json -- skipping JSON update.")
        return

    r = records[thomsen_idx]
    conclusion = result["conclusion"]
    caveat = result["caveat"]
    reason = result["reason"]
    n = result["n_cases_analysed"]

    new_note = (
        r.get("verification_notes", "") +
        f"\n\nTCGA CROSS-VALIDATION (computed, {n} TCGA-PRAD cases): "
        f"conclusion={conclusion.upper()}. {reason} {caveat}"
    )
    r["verification_notes"] = new_note

    if conclusion == "supports_thomsen":
        r["confidence_note"] = (
            "Independently cross-validated against live TCGA-PRAD CNV data (proxy check): "
            "CNV-gain cases show lower mean Gleason grade, consistent with Thomsen's expression-prognosis claim."
        )

    path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(f"  Updated Thomsen record in {path}")


def main():
    parser = argparse.ArgumentParser(description="Cross-validate Thomsen 2025 against TCGA-PRAD")
    parser.add_argument("--update-json", action="store_true",
                        help="Write cross-validation result to data/receptors/or51e2.json")
    args = parser.parse_args()

    print("Fetching TCGA-PRAD cases with Gleason grade from GDC API...")
    try:
        cases = fetch_prad_cases_with_gleason()
        print(f"  {len(cases)} cases fetched")
    except Exception as e:
        print(f"  ERROR fetching cases: {e}", file=sys.stderr)
        sys.exit(1)

    print("Fetching OR51E2 CNV calls for TCGA-PRAD...")
    try:
        cnv_by_case = fetch_or51e2_cnv_by_case()
        print(f"  {len(cnv_by_case)} cases with CNV calls")
    except Exception as e:
        print(f"  ERROR fetching CNV data: {e}", file=sys.stderr)
        sys.exit(1)

    result = analyse(cases, cnv_by_case)

    print("\n=== TCGA Cross-Validation Result ===")
    print(f"Conclusion:          {result['conclusion'].upper()}")
    print(f"Cases analysed:      {result['n_cases_analysed']}")
    print(f"Cases with CNV data: {result['n_with_cnv_data']}")
    print(f"CNV distribution:    {result['cnv_distribution']}")
    print(f"Mean Gleason by CNV: {result['mean_gleason_by_cnv']}")
    print(f"\nReason: {result['reason']}")
    print(f"\nCaveat: {result['caveat']}")

    if args.update_json:
        update_json_record(result)

    return result


if __name__ == "__main__":
    main()

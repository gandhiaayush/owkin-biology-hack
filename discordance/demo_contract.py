"""
Adapts Discordance's internal query result into the frozen demo contract shape
that Person C's frontend (demos/or51e2-tension-map.html, demos/baseline-vs-augmented.html,
demos/mocks/or51e2-query.embed.js) was built and validated against.

WHY THIS EXISTS: Person C designed and tested their rendering code against
demos/mocks/or51e2-query.json before the real graph pipeline existed. That mock has
top-level keys like `consensus`, `tumor_suppressive`, `adjudication.needs_judgment`,
`baseline_contrast` -- server.py's real `query_graph` tool returns a differently-shaped
dict (`consensus_status`, `contradictions`, `subgraph`, ...) with almost no overlapping
keys, and is registered under the name `query_graph` rather than `query_or_graph` (the
name used in demos/KPRO_MCP_HOOKUP.md and the mock's own "tool" field). Swapping the
static mock for a live call without this adapter would silently break both demo pages
and mismatch the tool name the hookup doc tells organizers/Person C to call.

This module is the fix: `to_demo_contract()` produces the exact contract shape from
real EvidenceRecord data, and server.py exposes it under the `query_or_graph` tool name
to match what's already documented and demoed against.
"""
from __future__ import annotations

import re
from typing import Optional

from .models import EvidenceRecord
from .scoring import compute_direction_scores, score_record, score_record_with_reason
from .contradiction import detect_contradictions
from .rules import generate_rules
from .graph import build_graph
from .scoring import ELICITATION_THRESHOLD

# Known receptor aliases / structural cross-refs, for the `receptor` block.
# Extend this as receptor #2/#3 get added -- falls back to a reasonable default
# (no alias, no PDB) for anything not listed rather than raising.
_RECEPTOR_INFO = {
    "OR51E2": {"aliases": ["PSGR", "OR51E2"], "pdb": "8F76"},
}

_YEAR_RE = re.compile(r"(19|20)\d{2}")
_LIGAND_RE = re.compile(
    r"(β-ionone|beta-ionone|α-ionone|alpha-ionone|androstenone|propionate|acetate)",
    re.IGNORECASE,
)


def _source_block(r: EvidenceRecord) -> dict:
    year_match = _YEAR_RE.search(r.source)
    return {
        "type": r.source_type,
        "label": r.source[:90],
        "year": int(year_match.group(0)) if year_match else None,
    }


def _ligand(r: EvidenceRecord) -> Optional[str]:
    m = _LIGAND_RE.search(f"{r.claim} {r.mechanism}")
    return m.group(0) if m else None


def _evidence_id(r: EvidenceRecord, idx: int) -> str:
    return f"e{r.id if r.id is not None else idx}"


def _evidence_entry(r: EvidenceRecord, idx: int, status: Optional[str]) -> dict:
    weight, weight_reason = score_record_with_reason(r)
    entry = {
        "id": _evidence_id(r, idx),
        "claim": r.claim,
        "direction": "exploratory" if status == "exploratory" else r.direction,
        "weight": round(weight, 3),
        "weight_reason": weight_reason,
        "source": _source_block(r),
        "model": r.model_system,
        "endpoint": r.endpoint if getattr(r, "endpoint", "not specified") != "not specified" else "not specified",
    }
    lig = _ligand(r)
    if lig:
        entry["ligand"] = lig
    if status == "exploratory":
        entry["confidence"] = "low"
    return entry


def to_demo_contract(
    records: list[EvidenceRecord],
    gene: str,
    cancer_type: str,
    query_text: str = "",
) -> dict:
    """Build the exact demos/mocks/or51e2-query.json contract shape from live records."""
    if not records:
        alias_info = _RECEPTOR_INFO.get(gene.upper(), {"aliases": [gene], "pdb": None})
        return {
            "tool": "query_or_graph",
            "version": "0.1.0",
            "contract_for": "Person B Query MCP -> Person C demo surface",
            "query": {"text": query_text, "entities": [gene], "cancer": cancer_type},
            "receptor": {"id": gene, **alias_info},
            "consensus": [], "tumor_suppressive": [], "tumor_promoting": [], "exploratory": [],
            "tensions": [], "rules": [],
            "scores": {
                "tumor_suppressive_mass": 0.0, "tumor_promoting_mass": 0.0,
                "balance_abs_delta": 0.0, "balance_threshold": 0.0,
            },
            "adjudication": {
                "status": "no_data", "needs_judgment": False,
                "reason": "No evidence in graph for this gene/cancer context.",
                "elicitation": None,
                "fallback_without_elicitation": {
                    "return_to_client": True,
                    "instruction": "No data to adjudicate -- ingest evidence first.",
                },
            },
            "baseline_contrast": {
                "plain_k_pro_expected": "No comparison available -- no evidence loaded yet.",
                "augmented_expected": "No comparison available -- no evidence loaded yet.",
            },
        }

    scores = compute_direction_scores(records)
    contradictions = detect_contradictions(records)
    rules = generate_rules(records)
    graph = build_graph(records, contradictions)

    status_by_id = {
        n.meta.get("record_id"): n.meta.get("status")
        for n in graph.nodes.values()
        if n.type == "Claim"
    }

    consensus, suppressive, promoting, exploratory = [], [], [], []
    for idx, r in enumerate(records):
        status = status_by_id.get(r.id)
        entry = _evidence_entry(r, idx, status)
        if status == "exploratory":
            exploratory.append(entry)
        elif r.direction == "tumor_suppressive":
            suppressive.append(entry)
        elif r.direction == "tumor_promoting":
            promoting.append(entry)
        else:
            consensus.append(entry)

    tensions = []
    for i, c in enumerate(contradictions):
        tensions.append({
            "id": f"t{i}",
            "title": f"{gene} activation outcome in {cancer_type.replace('_', ' ')} is contested",
            "summary": c.divergence_hypothesis,
            "left": {
                "label": "Tumor-suppressive",
                "evidence_ids": [_evidence_id(r, j) for j, r in enumerate(c.suppressive_records)],
            },
            "right": {
                "label": "Tumor-promoting",
                "evidence_ids": [_evidence_id(r, j) for j, r in enumerate(c.promoting_records)],
            },
            "hypotheses": [c.divergence_hypothesis],
            "same_model_system": c.same_model_system,
            "same_endpoint": c.same_endpoint,
            "deadlock": c.deadlock,
        })

    rules_out = [
        {
            "id": f"r{i}",
            "text": r.claim,
            "confidence": r.confidence_label,
            "n_independent_sources": len(r.sources),
            "qualification": "Contested -- do not treat as settled" if r.contested else "",
        }
        for i, r in enumerate(rules)
    ]

    delta = abs(scores.suppressive.score - scores.promoting.score)
    total_mass = scores.suppressive.score + scores.promoting.score
    # ELICITATION_THRESHOLD is a ratio range (e.g. 0.4-0.6 of total mass); convert to
    # an equivalent absolute-delta threshold in the same units as balance_abs_delta,
    # since that's what this contract shape reports. Width of the ratio window is
    # (upper - lower); delta <= threshold <=> ratio within [lower, upper].
    ratio_window_half_width = (ELICITATION_THRESHOLD[1] - ELICITATION_THRESHOLD[0]) / 2
    balance_threshold = round(ratio_window_half_width * 2 * total_mass, 3) if total_mass > 0 else 0.0
    needs_judgment = bool(scores.elicitation_needed and contradictions)

    def _short(source: str) -> str:
        return source.split(",")[0].split("(")[0].strip()

    sup_sources = ", ".join(sorted({_short(r.source) for r in contradictions[0].suppressive_records})) if contradictions else ""
    pro_sources = ", ".join(sorted({_short(r.source) for r in contradictions[0].promoting_records})) if contradictions else ""

    adjudication = {
        "status": "deadlock" if needs_judgment else scores.consensus_status,
        "needs_judgment": needs_judgment,
        "reason": (
            "Support and oppose masses are within balance threshold on the same "
            "receptor/cell-line family."
            if needs_judgment else
            "Evidence is not currently balanced enough to require adjudication."
        ),
        "elicitation": {
            "message": (
                f"{gene} activation evidence is balanced between tumor-suppressive and "
                "tumor-promoting claims. How should we proceed?"
            ),
            "options": [
                {"id": "suppressive", "label": "Weight tumor-suppressive evidence more heavily"},
                {"id": "promoting", "label": "Weight tumor-promoting evidence more heavily"},
                {"id": "keep_contested", "label": "Keep as contested -- do not merge into one rule"},
            ],
        } if needs_judgment else None,
        "fallback_without_elicitation": {
            "return_to_client": True,
            "instruction": (
                "If MCP elicitation is unavailable, return this object and wait for the "
                "researcher's next message selecting an option id."
            ),
        },
    }

    baseline_contrast = {
        "plain_k_pro_expected": (
            "A smoothed or hedged single narrative that the receptor may have "
            "context-dependent effects, without explicitly staging the primary-literature "
            "split as a first-class tension."
        ),
        "augmented_expected": (
            f"Explicit contested cluster ({sup_sources or 'suppressive sources'} vs. "
            f"{pro_sources or 'promoting sources'}) with sources, weights, endpoint labels, "
            "confidence-qualified rules, and needs_judgment elicitation."
            if contradictions else
            "Sourced, confidence-weighted claims with no unresolved contradiction currently detected."
        ),
    }

    alias_info = _RECEPTOR_INFO.get(gene.upper(), {"aliases": [gene], "pdb": None})

    return {
        "tool": "query_or_graph",
        "version": "0.1.0",
        "contract_for": "Person B Query MCP -> Person C demo surface",
        "query": {
            "text": query_text or (
                f"Does activating {gene} suppress or promote "
                f"{cancer_type.replace('_', ' ')} phenotypes?"
            ),
            "entities": sorted(set([gene] + alias_info.get("aliases", []))),
            "cancer": cancer_type,
        },
        "receptor": {"id": gene, **alias_info},
        "consensus": consensus,
        "tumor_suppressive": suppressive,
        "tumor_promoting": promoting,
        "exploratory": exploratory,
        "tensions": tensions,
        "scores": {
            "tumor_suppressive_mass": round(scores.suppressive.score, 3),
            "tumor_promoting_mass": round(scores.promoting.score, 3),
            "balance_abs_delta": round(delta, 3),
            "balance_threshold": balance_threshold,
            "weight_breakdown": {
                "tumor_suppressive": [
                    {"source": r.source[:60], "weight": round(score_record(r), 3),
                     "reason": score_record_with_reason(r)[1]}
                    for r in scores.suppressive.records
                ],
                "tumor_promoting": [
                    {"source": r.source[:60], "weight": round(score_record(r), 3),
                     "reason": score_record_with_reason(r)[1]}
                    for r in scores.promoting.records
                ],
                "note": (
                    "Individual weights sum to the mass totals above. "
                    "Patents are tracked separately (commercial_interest only) and excluded from mass."
                ),
            },
        },
        "rules": rules_out,
        "adjudication": adjudication,
        "baseline_contrast": baseline_contrast,
    }

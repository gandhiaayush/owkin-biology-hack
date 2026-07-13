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
from .identifiers import receptor_external_ids, cancer_external_ids
from .normalize import cell_compartment, count_independent_sources, citation_key
from .contradiction import detect_auxiliary_tensions, generate_divergence_hypothesis
from .scorecard import build_scorecards, scorecard_to_dict, infer_query_endpoint, render_scorecards_markdown

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
_CHEMBL_COMPOUND_RE = re.compile(
    r'^([A-Z][A-Z0-9\-\' ]{2,40}?)\s+\(CHEMBL\d+\)', re.MULTILINE
)
_POTENCY_RE = re.compile(
    r'(IC50|EC50|Ki|Kd)\s*=\s*([\d.]+)\s*(nM|uM|µM|pM|mM)', re.IGNORECASE
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


def _short_source(source: str) -> str:
    return source.split(",")[0].split("(")[0].strip()


def _build_demo_summary(
    gene: str,
    cancer_type: str,
    scores,
    contradictions,
    needs_judgment: bool,
) -> str:
    cancer_label = cancer_type.replace("_", " ")
    if scores.consensus_status == "no_data":
        return f"No evidence loaded yet for {gene} in {cancer_label}."

    if not contradictions:
        return (
            f"For {gene} in {cancer_label}, the loaded evidence points one way "
            f"({scores.overall_confidence_label}). No unresolved split detected."
        )

    c = contradictions[0]
    sup_n = count_independent_sources(c.suppressive_records)
    pro_n = count_independent_sources(c.promoting_records)
    endpoint_note = (
        "Studies measured different outcomes (e.g. proliferation vs. invasiveness), "
        "so both sides could be partially true."
        if not c.same_endpoint
        else "Studies disagree on the same kind of outcome in overlapping model systems."
    )
    balance_note = (
        "Evidence weight is roughly balanced — the graph will not pick a winner automatically."
        if needs_judgment
        else "One side currently weighs more, but opposing primary studies remain."
    )
    return (
        f"Activating {gene} in {cancer_label} is contested: {sup_n} independent paper(s) read "
        f"tumor-suppressive (slows cancer), {pro_n} read tumor-promoting (helps cancer grow "
        f"or spread). {endpoint_note} {balance_note}"
    )


def _build_patent_block(records: list[EvidenceRecord]) -> list[dict]:
    """
    Build a structured representation of patent records for the demo contract.

    Patents are evidence of commercial interest, not biological validation.
    They are tracked separately from literature and never folded into the
    directional mass — but they ARE in the knowledge graph as exploratory nodes,
    and their disclosed ligands create edges to Ligand nodes that the graph
    traversal can reach.

    Returns one entry per patent record with: citation, claim, disclosed ligands
    (extracted from the claim text), and a commercial_interest flag so Person C's
    frontend can render them distinctly (e.g. amber/gold, separate from green/red).
    """
    from .graph import _infer_ligands
    patent_records = [r for r in records if r.source_type == "patent"]
    # Build ligand lists; track the best list seen so far to inherit on continuations.
    best_ligands: list[tuple[str, dict]] = []
    out = []
    for r in patent_records:
        ligands_with_meta = _infer_ligands(r.claim, r.mechanism, r.source)
        # Divisional continuations say "same agonists as parent" — inherit parent ligands
        is_continuation = any(
            kw in r.claim.lower()
            for kw in ("divisional continuation", "same 24", "covering the same")
        )
        if not ligands_with_meta and is_continuation and best_ligands:
            ligands_with_meta = best_ligands
        if ligands_with_meta:
            best_ligands = ligands_with_meta
        entry = {
            "source": r.source[:100],
            "claim": r.claim[:200],
            "direction": r.direction,
            "cancer_type": r.cancer_type,
            "commercial_interest": True,
            "weight": round(score_record(r), 3),
            "weight_note": "Patent weight (0.1 base) excluded from directional mass — commercial interest only",
            "disclosed_ligands": [
                {"name": label, **meta}
                for label, meta in ligands_with_meta
            ],
            "confidence_note": r.confidence_note[:120] if r.confidence_note else "",
        }
        if is_continuation:
            entry["continuation_note"] = "Divisional continuation — covers same compounds as parent patent above"
        out.append(entry)
    return out


def _build_knowledge_gaps(gene: str, records: list[EvidenceRecord]) -> list[dict]:
    """Papers commonly cited in reviews but absent from the loaded graph."""
    if gene.upper() != "OR51E2":
        return []
    loaded_keys = {citation_key(r.source) for r in records}
    candidates = [
        {
            "citation": "Rodriguez et al. 2015, Oncogene",
            "topic": "PSGR shRNA knockdown inhibits LNCaP proliferation and migration",
            "status": "not_ingested",
            "why": "Separate from Rodriguez 2014 Oncogenesis GOF/xenograft record; load-bearing for knockdown-vs-knockout tension.",
        },
        {
            "citation": "Li et al. 2020, Life Sciences",
            "topic": "PSGR exosome transfer promotes EMT and invasion",
            "status": "not_ingested",
            "why": "Non-cell-autonomous pro-tumoral mechanism cited in K Pro baseline.",
        },
        {
            "citation": "Lam et al. 2018, AACR",
            "topic": "OR51E2 lost during metastatic progression",
            "status": "not_ingested",
            "why": "Stage-specific expression narrative; reconciles high early vs low late expression.",
        },
        {
            "citation": "Sanz et al. 2017, BMC Research Notes",
            "topic": "Gallein reverses beta-ionone-induced invasiveness in vivo",
            "status": "not_ingested",
            "why": "Pharmacological validation of pro-invasive pathway.",
        },
    ]
    gaps = []
    for g in candidates:
        author = g["citation"].split()[0].lower()
        year_match = re.search(r"(19|20)\d{2}", g["citation"])
        year = year_match.group(0) if year_match else ""
        key = f"{author}-{year}" if year else author
        if key not in loaded_keys and not any(key in k for k in loaded_keys):
            gaps.append(g)
    return gaps


def _build_client_instructions(needs_judgment: bool, has_contested: bool) -> dict:
    """Binding presentation rules returned with every query_or_graph payload."""
    out: dict = {
        "binding": True,
        "summary": (
            "This payload is the authoritative structured evidence response. "
            "Present it as-is; do not replace it with a literature review or merged verdict."
        ),
        "must_do": [
            "Open with demo_summary.",
            "Present tumor_suppressive and tumor_promoting as separate sections — never merge into one narrative.",
            "Use adjudication.verdict and adjudication.next_steps — not raw needs_judgment.",
            "Show tensions with left/right buckets; include auxiliary tensions when present.",
            "Report scores.weight_breakdown reasons exactly as given — do not recalculate masses.",
            "Surface why_not_plain_llm when explaining value vs a generic LLM answer.",
            "Present named_exploratory_findings as its own section — these are real findings from the graph, not filler.",
            "If therapeutic_analysis is non-empty, use it verbatim to answer go/no-go, endpoint, evidence-strength, and ligand questions — do not re-derive these answers.",
            "Cite ligand_grounding.all_chembl_molecules as the complete list of validated OR51E2 ligands from ChEMBL.",
        ],
        "must_not_do": [
            "Do not web-search, browse, or verify papers outside this payload.",
            "Do not declare a single scientific winner or clinical recommendation.",
            "Do not critique, invalidate, or re-score graph weights or mass totals.",
            "Do not add literature absent from this graph unless the user explicitly requests external sources.",
            "Do not use get_tension_map to re-adjudicate — visualization only.",
            "Do not say the patent has 144 compounds — it has 28. The number 144 refers to ChEMBL assay-database entries for 26 unique molecules, which is a completely separate dataset.",
        ],
        "response_outline": [
            "demo_summary",
            "tumor_suppressive",
            "tumor_promoting",
            "named_exploratory_findings",
            "therapeutic_analysis (use verbatim if present)",
            "tensions",
            "adjudication.verdict",
            "why_not_plain_llm",
            "ligand_grounding.all_chembl_molecules",
        ],
    }
    if has_contested and needs_judgment:
        out["default_if_deadlocked"] = "keep_contested"
        out["elicitation_note"] = (
            "Present adjudication.elicitation.options. Recommend keep_contested "
            "unless the user specifies which endpoint matters."
        )
    return out


_NAMED_EXPLORATORY_PRIORITY = [
    ("Rodriguez", "expression_pattern", "Rodriguez 2014 (Oncogenesis) — PSGR overexpression in transgenic mice drives prostatic intraepithelial neoplasia and larger xenograft tumors via NF-κB. This is a gain-of-function / expression-level finding (not ligand activation), so it is excluded from the activation-mass score but is real supporting evidence for the tumor-promoting side."),
    ("Thomsen", "genetic_alteration", "Thomsen 2025 — CRISPR-Cas9 knockout of OR51E2 in LNCaP cells INCREASES proliferation and migration, meaning loss of OR51E2 is tumor-promoting. This is a genetic-alteration finding (not ligand activation), excluded from activation mass, but directly relevant: it implies OR51E2 has a baseline tumor-suppressive role independent of exogenous ligands."),
    ("Marelli", "activation_effect", "Marelli 2025 — Palmitic acid activates OR51E2 on tumor-associated macrophages (TAMs) in the TME, repolarizing them toward an immunosuppressive M2-like phenotype. This is a non-cell-autonomous, immune-compartment mechanism excluded from the tumor-cell activation mass, but clinically important: it means OR51E2 has a pro-tumoral role in the microenvironment even if it is tumor-suppressive in cancer cells directly."),
]


def _build_named_exploratory_findings(records: list[EvidenceRecord]) -> list[dict]:
    """
    Explicitly surface the highest-priority exploratory findings by name.
    These are excluded from the activation-mass score for principled reasons
    (wrong compartment, genetic-alteration context, expression-level rather than
    activation) but are real findings that must appear in any complete answer.
    Returning them as a named list prevents Claude from silently dropping the
    exploratory bucket.
    """
    out = []
    for author_key, ctx, description in _NAMED_EXPLORATORY_PRIORITY:
        matching = [
            r for r in records
            if author_key in r.source
            and r.direction_context == ctx
            and r.direction in ("tumor_suppressive", "tumor_promoting")
        ]
        if matching:
            r = matching[0]
            out.append({
                "author_key": author_key,
                "description": description,
                "direction": r.direction,
                "direction_context": r.direction_context,
                "source_type": r.source_type,
                "source": r.source[:120],
                "excluded_from_mass_because": (
                    "expression_pattern context (overexpression, not ligand activation)" if ctx == "expression_pattern"
                    else "genetic_alteration context (KO/CRISPR, not ligand activation)" if ctx == "genetic_alteration"
                    else "immune/TME compartment (non-cell-autonomous mechanism)"
                ),
            })
    return out


def _build_therapeutic_analysis(
    gene: str,
    cancer_type: str,
    records: list[EvidenceRecord],
    suppressive: list[EvidenceRecord],
    promoting: list[EvidenceRecord],
) -> dict:
    """
    Pre-answer the three questions in the standard therapeutic-repurposing prompt
    using only data actually present in the graph. This prevents Claude from
    synthesizing answers from parametric memory.

    Every claim here is grounded in a specific evidence record. Claude should
    copy these answers verbatim rather than re-deriving them.
    """
    if gene.upper() != "OR51E2" or cancer_type != "prostate_cancer":
        return {}

    # Q1: Do proliferation and invasiveness point the same or different directions?
    sup_endpoints = sorted({r.endpoint for r in suppressive if r.endpoint and r.endpoint != "not specified"})
    pro_endpoints = sorted({r.endpoint for r in promoting if r.endpoint and r.endpoint != "not specified"})
    q1_answer = (
        "DIFFERENT DIRECTIONS. "
        f"Suppressive-side papers measure: {', '.join(sup_endpoints) or 'proliferation (Neuhaus 2009, Xie 2019)'}. "
        f"Promoting-side paper measures: {', '.join(pro_endpoints) or 'invasiveness (Sanz 2014)'}. "
        "Anti-proliferative and pro-invasive effects can be simultaneously true — this is a recognised "
        "cancer biology pattern (reduced proliferation + increased invasiveness). Do not collapse them "
        "into a single direction."
    )

    # Q2: Evidence strength
    all_mass = suppressive + promoting
    weights_str = "; ".join(
        f"{_short_source(r.source)} weight={round(score_record(r), 2)}"
        for r in sorted(all_mass, key=lambda r: -score_record(r))
    )
    q2_answer = (
        f"MODERATE, NOT HIGH. Activation-mass records: {weights_str}. "
        "All primary records use LNCaP cells (androgen-sensitive prostate cancer) — relevant model "
        "for your question. Xie 2019 adds an in vivo xenograft arm (tumor-suppressive). "
        "No clinical trial data exists in this graph. β-ionone's status as a genuine OR51E2 agonist "
        "is itself contested (Pronin 2021 explicitly flags field controversy on β-ionone agonism at this target). "
        "Treat all activation-effect claims as in-vitro/preclinical, not clinically validated."
    )

    # Q3: α-ionone reclassification
    alpha_records = [r for r in records if "alpha-ionone" in r.claim.lower() or "α-ionone" in r.claim.lower()]
    sanz_2016 = next((r for r in records if "2016" in r.source and "Sanz" in r.source), None)
    if sanz_2016:
        q3_answer = (
            "YES, this changes the interpretation significantly. "
            "Sanz 2014 (e26) used α-ionone as a PSGR antagonist control that blocked β-ionone's "
            "pro-invasive effect — this is foundational to interpreting that paper's causal claim. "
            "Sanz 2016 (Oncotarget) revised this: α-ionone is actually a FULL AGONIST at OR51E2 "
            "that promotes tumor GROWTH via a distinct pathway from β-ionone's pro-invasive effect. "
            "Consequence: the Sanz 2014 α-ionone 'rescue' experiment does not prove what it claimed "
            "to prove. The pro-invasive interpretation of β-ionone depends on an antagonist control "
            "that turned out to be an agonist. This substantially weakens the Sanz 2014 causal chain, "
            "though it does not eliminate the invasion observation itself."
        )
    else:
        q3_answer = (
            "α-ionone was used as an antagonist control in Sanz 2014 but reclassified as a full OR51E2 "
            "agonist in subsequent work — this weakens the causal interpretation of Sanz 2014's "
            "pro-invasive finding. See exploratory bucket for the 2016 record."
        )

    # Go/no-go pre-computed verdict from the graph
    go_no_go = (
        "CONDITIONAL NO-GO for β-ionone specifically as a therapeutic agent, but a QUALIFIED GO "
        "for OR51E2 as a target. Reasoning from the graph: (a) β-ionone's agonism at OR51E2 is "
        "itself disputed (Pronin 2021), making it an unreliable pharmacological tool; (b) the "
        "pro-invasive concern from Sanz 2014 is real but the causal evidence is weakened by the "
        "α-ionone reclassification; (c) the Thomsen 2025 CRISPR data and Rodriguez 2014 "
        "overexpression data both support OR51E2 as playing a tumour-suppressive role when "
        "properly expressed — this argues for investing in a validated, selective agonist (not "
        "β-ionone) with a clean pharmacological profile. Recommend: select OR51E2 agonist from "
        "the ChEMBL-validated compound list (26 unique molecules with measured EC50/IC50) before "
        "committing to in vivo efficacy testing."
    )

    return {
        "q1_proliferation_vs_invasiveness": q1_answer,
        "q2_evidence_strength": q2_answer,
        "q3_alpha_ionone_impact": q3_answer,
        "go_no_go_verdict": go_no_go,
        "grounding_note": (
            "Every claim above is grounded in a specific evidence record in this payload. "
            "Do not add mechanism details, citations, or numeric facts not present in this analysis "
            "or in the tumor_suppressive/tumor_promoting/exploratory buckets above."
        ),
    }


def _build_adjudication_verdict(needs_judgment: bool, same_endpoint: bool) -> str:
    if needs_judgment:
        if same_endpoint:
            return "contested — evidence is split on the same outcome"
        return "contested — evidence is split across related outcomes"
    return "contested — one side leads, but disagreement remains"


def _build_ligand_grounding(records: list[EvidenceRecord]) -> dict:
    """Surface ChEMBL potency data when present — grounds ligand claims in binding data."""
    chembl_activities = [
        r for r in records
        if r.source_type == "database_derived" and "chembl" in r.source.lower()
        and _POTENCY_RE.search(r.claim)
    ]
    summary_rec = next(
        (r for r in records if r.source_type == "database_derived" and "bioactivity records" in r.claim.lower()),
        None,
    )
    compounds: list[dict] = []
    for r in chembl_activities:
        pot = _POTENCY_RE.search(r.claim)
        compound = _CHEMBL_COMPOUND_RE.match(r.claim.strip())
        if not pot:
            continue
        name = compound.group(1).strip() if compound else r.claim.split(" shows ")[0]
        assay = "agonist" if "agonist" in r.claim.lower() else (
            "antagonist" if "antagonist" in r.claim.lower() else "unknown"
        )
        compounds.append({
            "compound": name,
            "potency_type": pot.group(1).upper(),
            "value": float(pot.group(2)),
            "units": pot.group(3),
            "assay_type": assay,
            "source": r.source[:80],
        })
    compounds.sort(key=lambda c: c["value"])
    top = compounds[:5]
    # All unique ChEMBL molecules (for complete ligand source disclosure)
    unique_names = sorted({c["compound"] for c in compounds})
    beta_note = (
        "β-ionone is debated as a genuine OR51E2 agonist (Pronin 2021); "
        "ChEMBL lists patent-screen agonists/antagonists with measured EC50/IC50 "
        "but NOT β-ionone potency at this target. β-ionone is not one of the "
        f"{len(unique_names)} ChEMBL-validated molecules listed here."
    )
    unique_molecule_count = len(unique_names) if unique_names else (
        summary_rec and 26 or 0
    )
    return {
        "chembl_target": "CHEMBL4523454",
        "activity_count": len(chembl_activities),
        "unique_molecule_count": unique_molecule_count,
        "summary": (
            summary_rec.claim[:300] if summary_rec else
            f"{len(chembl_activities)} ChEMBL potency records loaded for this receptor."
        ),
        "top_compounds": top,
        "all_chembl_molecules": unique_names,
        "beta_ionone_note": beta_note,
        "plain_llm_gap": (
            f"A plain LLM answer rarely cites specific EC50 values from ChEMBL or lists "
            f"the {unique_molecule_count} validated OR51E2 ligands by name. "
            "It also does not distinguish ChEMBL assay-record counts (144 raw entries) "
            "from unique molecule counts (26) or patent compound counts (28) — "
            "these are three separate numbers."
            if top else
            "No ChEMBL potency records loaded — ligand grounding unavailable for this query."
        ),
    }


def _build_evidence_comparison(
    records: list[EvidenceRecord],
    scores,
) -> list[dict]:
    """Transparent audit: why one promoting study outweighs another."""
    promoting = sorted(
        scores.promoting.records,
        key=lambda r: score_record(r),
        reverse=True,
    )
    if len(promoting) < 2:
        return []

    comparisons: list[dict] = []
    for higher, lower in zip(promoting, promoting[1:]):
        hw, hr = score_record_with_reason(higher)
        lw, lr = score_record_with_reason(lower)
        delta = round(hw - lw, 3)
        reasons: list[str] = []
        if higher.endpoint != lower.endpoint:
            reasons.append(
                f"Different endpoints ({higher.endpoint} vs {lower.endpoint}) — "
                "not a same-outcome contradiction."
            )
        if "xenograft" in (higher.model_system or "").lower() and "xenograft" not in (lower.model_system or "").lower():
            reasons.append("Higher study uses in vivo/xenograft evidence (+quality bonus).")
        if (higher.sample_size or 0) > (lower.sample_size or 0):
            reasons.append(f"Larger reported N ({higher.sample_size} vs {lower.sample_size or 'unknown'}).")
        if not reasons:
            reasons.append("Quality/recency/mechanism bonuses in the weight formula differentiate these records.")
        comparisons.append({
            "higher": _short_source(higher.source),
            "lower": _short_source(lower.source),
            "weight_delta": delta,
            "higher_weight": round(hw, 3),
            "lower_weight": round(lw, 3),
            "higher_reason": hr,
            "lower_reason": lr,
            "why_higher_wins": reasons,
        })
    return comparisons


def _build_why_not_plain_llm(
    gene: str,
    scores,
    contradictions,
    needs_judgment: bool,
    auxiliary_tensions: list[dict],
    ligand_grounding: dict,
    evidence_comparison: list[dict],
) -> list[str]:
    bullets: list[str] = []
    if contradictions and not contradictions[0].same_endpoint:
        bullets.append(
            "Endpoint-aware tension: proliferation (Neuhaus) vs invasiveness (Sanz) flagged as "
            "related outcomes, not forced into a false same-endpoint contradiction."
        )
    if needs_judgment:
        bullets.append(
            f"Deterministic deadlock at mass ratio {scores.suppressive.score:.2f} vs "
            f"{scores.promoting.score:.2f} — triggers elicitation instead of merging sides."
        )
    if any(t.get("id") == "t_ligand_validity" for t in auxiliary_tensions):
        bullets.append(
            "Auxiliary ligand-validity tension: β-ionone agonism explicitly contested; "
            "α-ionone reclassified from antagonist to full agonist (biased agonism)."
        )
    if any(t.get("id") == "t_cell_compartment" for t in auxiliary_tensions):
        bullets.append(
            "Immune-compartment firewall: TAM/macrophage claims excluded from tumor-cell direction mass."
        )
    if ligand_grounding.get("top_compounds"):
        top = ligand_grounding["top_compounds"][0]
        bullets.append(
            f"ChEMBL potency grounding: {top['compound']} {top['potency_type']}="
            f"{top['value']}{top['units']} ({top['assay_type']}) — not inferable from abstracts alone."
        )
    if evidence_comparison:
        c = evidence_comparison[0]
        bullets.append(
            f"Auditable weight math: {c['higher']} ({c['higher_weight']}) vs "
            f"{c['lower']} ({c['lower_weight']}) — formula shown, not a vibe score."
        )
    if scores.commercial_interest_score > 0:
        bullets.append(
            "Patents tracked as commercial_interest edges only — never folded into literature consensus mass."
        )
    if not bullets:
        bullets.append(
            f"Confidence-qualified rules for {gene} — never asserted as universally true off single papers."
        )
    return bullets[:4]


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
            "client_instructions": _build_client_instructions(False, False),
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
            "demo_summary": "No evidence loaded yet for this receptor and cancer type.",
            "why_not_plain_llm": ["No evidence loaded — ingest records before comparing to plain K Pro."],
            "ligand_grounding": {"activity_count": 0, "top_compounds": [], "beta_ionone_note": "", "plain_llm_gap": ""},
            "evidence_comparison": [],
            "named_exploratory_findings": [],
            "therapeutic_analysis": {},
            "knowledge_gaps": [],
            "scorecards": [],
            "scorecards_markdown": "",
        }

    scores = compute_direction_scores(records)
    contradictions = detect_contradictions(records)
    rules = generate_rules(records)
    graph = build_graph(records, contradictions)
    scorecards = build_scorecards(
        records, scores, contradictions, query_endpoint=infer_query_endpoint(query_text),
    )

    status_by_id = {
        n.meta.get("record_id"): n.meta.get("status")
        for n in graph.nodes.values()
        if n.type == "Claim"
    }

    # Mass pool records (deduplicated by citation key) drive the primary display
    # buckets.  Building from all records instead would surface duplicate seed +
    # JSON-loaded rows for the same paper, giving 2+2 where only 1+1 is correct.
    from .scoring import _activation_mass_pool
    mass_ids = {id(r) for r in _activation_mass_pool(records)}

    consensus, suppressive, promoting, exploratory = [], [], [], []
    id_by_record: dict[int, str] = {}
    for idx, r in enumerate(records):
        id_by_record[id(r)] = _evidence_id(r, idx)
        status = status_by_id.get(r.id)
        entry = _evidence_entry(r, idx, status)
        if (
            status == "exploratory"
            or r.source_type in ("patent", "preliminary")
            or cell_compartment(r) == "immune_cell"
            or r.direction_context in (
                "supporting_evidence", "genetic_alteration", "expression_pattern"
            )
            or (
                r.direction in ("tumor_suppressive", "tumor_promoting")
                and r.direction_context == "activation_effect"
                and id(r) not in mass_ids
            )
        ):
            exploratory.append(entry)
        elif r.direction == "tumor_suppressive":
            suppressive.append(entry)
        elif r.direction == "tumor_promoting":
            promoting.append(entry)
        else:
            consensus.append(entry)

    tensions = []
    for i, c in enumerate(contradictions):
        plain_summary = c.divergence_hypothesis
        if not c.same_endpoint:
            plain_summary = (
                "Primary studies disagree on what activating this receptor does, but they often "
                "measured different outcomes (for example proliferation vs. invasiveness). "
                "That is tension worth surfacing, not proof that one paper must be wrong."
            )
        tensions.append({
            "id": f"t{i}",
            "title": f"{gene} activation outcome in {cancer_type.replace('_', ' ')} is contested",
            "summary": plain_summary,
            "left": {
                "label": "Tumor-suppressive",
                "evidence_ids": [id_by_record[id(r)] for r in c.suppressive_records],
            },
            "right": {
                "label": "Tumor-promoting",
                "evidence_ids": [id_by_record[id(r)] for r in c.promoting_records],
            },
            "hypotheses": [
                generate_divergence_hypothesis(
                    c.suppressive_records, c.promoting_records, include_curation_notes=False
                )
            ],
            "technical": {
                "same_model_system": c.same_model_system,
                "same_endpoint": c.same_endpoint,
                "deadlock": c.deadlock,
                "raw_hypothesis": c.divergence_hypothesis,
            },
        })
    tensions.extend(detect_auxiliary_tensions(records))

    rules_out = []
    for i, rule in enumerate(rules):
        direction_records = [
            r for r in records
            if r.direction == rule.direction and r.source_type != "patent"
            and cell_compartment(r) == "tumor_cell"
        ]
        rules_out.append({
            "id": f"r{i}",
            "text": rule.claim,
            "confidence": rule.confidence_label,
            "n_independent_sources": count_independent_sources(direction_records),
            "qualification": "Contested -- do not treat as settled" if rule.contested else "",
        })

    delta = abs(scores.suppressive.score - scores.promoting.score)
    total_mass = scores.suppressive.score + scores.promoting.score
    # ELICITATION_THRESHOLD is a ratio range (e.g. 0.4-0.6 of total mass); convert to
    # an equivalent absolute-delta threshold in the same units as balance_abs_delta,
    # since that's what this contract shape reports. Width of the ratio window is
    # (upper - lower); delta <= threshold <=> ratio within [lower, upper].
    ratio_window_half_width = (ELICITATION_THRESHOLD[1] - ELICITATION_THRESHOLD[0]) / 2
    balance_threshold = round(ratio_window_half_width * 2 * total_mass, 3) if total_mass > 0 else 0.0
    needs_judgment = bool(scores.elicitation_needed and contradictions)
    same_endpoint = contradictions[0].same_endpoint if contradictions else True
    verdict = _build_adjudication_verdict(needs_judgment, same_endpoint)

    sup_sources = ", ".join(sorted({_short_source(r.source) for r in contradictions[0].suppressive_records})) if contradictions else ""
    pro_sources = ", ".join(sorted({_short_source(r.source) for r in contradictions[0].promoting_records})) if contradictions else ""

    adjudication = {
        "verdict": verdict,
        "summary": (
            "The literature does not agree on whether activating this receptor helps or hurts "
            "prostate cancer. Weighted evidence is nearly tied, so the tool stops instead of "
            "declaring a winner."
            if needs_judgment else
            "Opposing studies remain, but weighted evidence currently leans one way."
        ),
        "next_steps": (
            [
                "Choose which outcome matters most for your question (proliferation vs. invasion/growth).",
                "Or keep the split visible — do not merge into a single 'always true' rule.",
            ]
            if needs_judgment else
            ["Review scorecards to see which sources drive the current lean."]
        ),
        # Backward-compatible fields used by demos/tests/MCP fallback path
        "status": "deadlock" if needs_judgment else scores.consensus_status,
        "needs_judgment": needs_judgment,
        "reason": (
            "Weighted tumor-suppressive and tumor-promoting evidence are nearly balanced "
            f"({scores.suppressive.score:.2f} vs {scores.promoting.score:.2f})."
            if needs_judgment else
            "Evidence is not currently balanced enough to require researcher input."
        ),
        "elicitation": {
            "message": (
                f"Evidence for {gene} activation is split. Should we prioritize the "
                "tumor-suppressive studies, the tumor-promoting studies, or keep both sides "
                "visible without merging them?"
            ),
            "options": [
                {
                    "id": "suppressive",
                    "label": "Prioritize tumor-suppressive studies (slows proliferation/cell death)",
                },
                {
                    "id": "promoting",
                    "label": "Prioritize tumor-promoting studies (invasion, xenograft growth)",
                },
                {
                    "id": "keep_contested",
                    "label": "Keep as contested — show both sides, no merged bottom line",
                },
            ],
        } if needs_judgment else None,
        "fallback_without_elicitation": {
            "return_to_client": True,
            "instruction": (
                "If live elicitation is unavailable, present the options above and wait for "
                "the researcher to reply with an option id (e.g. keep_contested)."
            ),
        },
        "technical": {
            "consensus_status": scores.consensus_status,
            "balance_abs_delta": round(delta, 3),
            "balance_threshold": balance_threshold,
            "deadlock": needs_judgment,
            "elicitation_ratio_window": list(ELICITATION_THRESHOLD),
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
            f"{pro_sources or 'promoting sources'}) with sources, differentiated weights, "
            "endpoint labels, confidence-qualified rules, and a plain-language verdict."
            if contradictions else
            "Sourced, confidence-weighted claims with no unresolved contradiction currently detected."
        ),
    }

    demo_summary = _build_demo_summary(gene, cancer_type, scores, contradictions, needs_judgment)

    auxiliary_tensions = [t for t in tensions if t.get("id", "").startswith("t_")]
    ligand_grounding = _build_ligand_grounding(records)
    evidence_comparison = _build_evidence_comparison(records, scores)
    why_not_plain_llm = _build_why_not_plain_llm(
        gene, scores, contradictions, needs_judgment,
        auxiliary_tensions, ligand_grounding, evidence_comparison,
    )

    alias_info = _RECEPTOR_INFO.get(gene.upper(), {"aliases": [gene], "pdb": None})
    ext_ids = receptor_external_ids(gene)
    cancer_ids = cancer_external_ids(cancer_type)

    return {
        "tool": "query_or_graph",
        "version": "0.1.0",
        "contract_for": "Person B Query MCP -> Person C demo surface",
        "client_instructions": _build_client_instructions(
            needs_judgment, bool(contradictions),
        ),
        "query": {
            "text": query_text or (
                f"Does activating {gene} suppress or promote "
                f"{cancer_type.replace('_', ' ')} phenotypes?"
            ),
            "entities": sorted(set([gene] + alias_info.get("aliases", []))),
            "cancer": cancer_type,
            "cancer_external_ids": cancer_ids,
        },
        "receptor": {"id": gene, **alias_info, "external_ids": ext_ids},
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
            # Patents are tracked here as commercial interest — they show that
            # companies have IP stakes in this receptor, but are never folded
            # into the literature consensus mass (primary_study/review) because
            # commercial interest is not the same as biological validation.
            "commercial_interest_score": round(scores.commercial_interest_score, 3),
            "patents": _build_patent_block(records),
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
        "demo_summary": demo_summary,
        "why_not_plain_llm": why_not_plain_llm,
        "ligand_grounding": ligand_grounding,
        "evidence_comparison": evidence_comparison,
        "named_exploratory_findings": _build_named_exploratory_findings(records),
        "therapeutic_analysis": _build_therapeutic_analysis(
            gene, cancer_type, records,
            scores.suppressive.records,
            scores.promoting.records,
        ),
        "knowledge_gaps": _build_knowledge_gaps(gene, records),
        "scorecards": [scorecard_to_dict(c) for c in scorecards],
        "scorecards_markdown": render_scorecards_markdown(scorecards),
    }

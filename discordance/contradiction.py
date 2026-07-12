from __future__ import annotations
import re
from .models import EvidenceRecord, ContradictionPair
from .scoring import _activation_mass_pool
from .normalize import (
    endpoints_confirmed_different,
    endpoints_overlap,
    model_overlap_kind,
    models_overlap,
    cell_compartment,
)

_DIVERGENCE_PATTERNS = {
    ("same_model", "different_direction"): (
        "Same model family with opposing directional claims on overlapping endpoints. "
        "Review ligand identity/purity, assay protocol, and whether gain-of-function vs "
        "loss-of-function designs are being compared."
    ),
    ("different_model", "different_direction"): (
        "Different model systems with opposing directional claims: may reflect tumor microenvironment "
        "differences absent in cell culture, or distinct tumor stage contexts (e.g. early PIN vs. invasive disease). "
        "In vivo and in vitro results can both be valid in their respective contexts."
    ),
    ("mixed_model", "different_direction"): (
        "Mixed model systems (cell line and xenograft both present) with opposing directions: "
        "consider whether in vivo and in vitro conditions drive different signaling states. "
        "Also verify ligand specificity — some agonists (α-ionone vs. β-ionone) may activate different pathways."
    ),
}


def _endpoint_key(suppressive: list[EvidenceRecord], promoting: list[EvidenceRecord]) -> bool:
    """
    True when endpoints overlap (same outcome family) OR cannot be confirmed different.
    False only when both sides have known tokens and zero overlap.
    """
    if endpoints_confirmed_different(suppressive, promoting):
        return False
    if endpoints_overlap(suppressive, promoting):
        return True
    # Unknown endpoints — conservative default (do not falsely soften)
    return True


def _model_system_key(suppressive: list[EvidenceRecord], promoting: list[EvidenceRecord]) -> str:
    return model_overlap_kind(suppressive, promoting)


def generate_divergence_hypothesis(
    suppressive: list[EvidenceRecord],
    promoting: list[EvidenceRecord],
    *,
    include_curation_notes: bool = True,
) -> str:
    model_key = _model_system_key(suppressive, promoting)
    same_endpoint = _endpoint_key(suppressive, promoting)

    if not same_endpoint:
        s_endpoints = sorted({r.endpoint for r in suppressive if r.endpoint != "not specified"})
        p_endpoints = sorted({r.endpoint for r in promoting if r.endpoint != "not specified"})
        base = (
            f"CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures "
            f"{', '.join(s_endpoints) or 'an unspecified endpoint'}; promoting evidence measures "
            f"{', '.join(p_endpoints) or 'an unspecified endpoint'}. This is contested on overall "
            "clinical/therapeutic implication, but not a strict same-endpoint contradiction — both "
            "effects could be simultaneously true (e.g. reduced proliferation alongside increased "
            "invasiveness is a recognized cancer biology pattern). Do not present as a flat two-sided "
            "contradiction; present as divergent evidence on distinct outcomes."
        )
    else:
        base = _DIVERGENCE_PATTERNS.get(
            (model_key, "different_direction"),
            "Opposing directional claims detected. Review model systems, endpoints, and ligand specificity.",
        )

    if not include_curation_notes:
        return base

    notes = []
    for r in suppressive + promoting:
        if r.confidence_note and (
            "controversy" in r.confidence_note.lower() or "ligand" in r.confidence_note.lower()
        ):
            notes.append(f"Note from {r.source.split(',')[0]}: {r.confidence_note[:120]}")
    if notes:
        base += " Additionally: " + " | ".join(notes)
    return base


def detect_contradictions(
    records: list[EvidenceRecord],
    direction_context_filter: str = "activation_effect",
) -> list[ContradictionPair]:
    """
    Return ContradictionPair objects for opposing directions under the same direction_context.
    Uses tumor-intrinsic activation records only for the primary direction split.
    """
    if direction_context_filter == "activation_effect":
        tumor_intrinsic = _activation_mass_pool(records)
    else:
        filtered = [r for r in records if r.direction_context == direction_context_filter]
        tumor_intrinsic = [
            r for r in filtered
            if cell_compartment(r) == "tumor_cell" and r.source_type not in ("patent", "preliminary")
        ]

    suppressive = [r for r in tumor_intrinsic if r.direction == "tumor_suppressive"]
    promoting = [r for r in tumor_intrinsic if r.direction == "tumor_promoting"]

    if not suppressive or not promoting:
        return []

    hypothesis = generate_divergence_hypothesis(suppressive, promoting, include_curation_notes=True)

    total = len(suppressive) + len(promoting)
    ratio = len(suppressive) / total
    deadlock = 0.4 <= ratio <= 0.6

    return [
        ContradictionPair(
            suppressive_records=suppressive,
            promoting_records=promoting,
            same_model_system=_model_system_key(suppressive, promoting) == "same_model",
            same_endpoint=_endpoint_key(suppressive, promoting),
            divergence_hypothesis=hypothesis,
            deadlock=deadlock,
        )
    ]


def detect_auxiliary_tensions(records: list[EvidenceRecord]) -> list[dict]:
    """
    Secondary tension axes beyond the primary direction split.
    These do not replace the main contradiction — they explain *why* a flat merge fails.
    """
    tensions: list[dict] = []
    activation = [r for r in records if r.direction_context == "activation_effect"]

    # 1. Ligand validity / biased agonism
    ligand_records = [
        r for r in activation
        if re.search(r"beta-ionone|alpha-ionone|β-ionone|α-ionone", f"{r.claim} {r.mechanism}", re.I)
    ]
    controversy = [r for r in ligand_records if "controversy" in (r.confidence_note or "").lower()]
    alpha_full_agonist = [
        r for r in ligand_records
        if re.search(r"alpha-ionone|α-ionone", r.claim, re.I)
        and re.search(r"full.{0,20}agonist", r.claim, re.I)
    ]
    beta_driven = [r for r in ligand_records if re.search(r"beta-ionone|β-ionone", r.claim, re.I)]
    if controversy or (alpha_full_agonist and beta_driven):
        tensions.append({
            "id": "t_ligand_validity",
            "title": "Ligand validity / biased agonism",
            "summary": (
                "Beta-ionone agonism at OR51E2 is explicitly contested; alpha-ionone was later "
                "reclassified from antagonist control to full agonist (Sanz 2014 vs Sanz 2016). "
                "Promoting claims that depend on beta-ionone pharmacology are load-bearing and disputed."
            ),
            "evidence_ids": [f"e{r.id}" for r in ligand_records if r.id is not None],
        })

    # 2. Cell compartment (tumor intrinsic vs TAM / immune)
    immune = [r for r in activation if cell_compartment(r) == "immune_cell"]
    tumor_directional = [
        r for r in activation
        if cell_compartment(r) == "tumor_cell"
        and r.direction in ("tumor_suppressive", "tumor_promoting")
        and r.source_type != "patent"
    ]
    if immune and tumor_directional:
        tensions.append({
            "id": "t_cell_compartment",
            "title": "Cell compartment split (tumor cell vs TAM)",
            "summary": (
                "Some OR51E2 claims are tumor-cell intrinsic; others are macrophage/TAM non-cell-autonomous. "
                "These are not opposing claims about the same compartment — do not bucket immune claims "
                "into tumor-cell direction mass."
            ),
            "immune_evidence_ids": [f"e{r.id}" for r in immune if r.id is not None],
            "tumor_intrinsic_evidence_ids": [f"e{r.id}" for r in tumor_directional if r.id is not None],
        })

    # 3. Gain-of-function vs loss-of-function (expression vs genetic manipulation)
    ko_records = [
        r for r in records
        if r.direction_context == "genetic_alteration"
        and r.direction in ("tumor_suppressive", "tumor_promoting")
        and re.search(r"knockout|knock-out|knockdown|crispr|shrna|sirna", r.claim, re.I)
    ]
    oe_records = [
        r for r in records
        if r.direction_context == "expression_pattern"
        and r.direction in ("tumor_suppressive", "tumor_promoting")
        and re.search(r"overexpression|transgenic", r.claim, re.I)
    ]
    if ko_records and oe_records:
        tensions.append({
            "id": "t_gain_loss",
            "title": "Gain-of-function vs loss-of-function",
            "summary": (
                "CRISPR knockout and transgenic overexpression studies point in opposite directions "
                "on shared endpoints (e.g. tumor growth). Classic expression-level / dosage confound — "
                "treat as its own hypothesis axis, not a flat literature disagreement."
            ),
            "loss_of_function_ids": [f"e{r.id}" for r in ko_records if r.id is not None],
            "gain_of_function_ids": [f"e{r.id}" for r in oe_records if r.id is not None],
        })

    return tensions

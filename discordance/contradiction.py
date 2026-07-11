from __future__ import annotations
from .models import EvidenceRecord, ContradictionPair

_DIVERGENCE_PATTERNS = {
    ("same_model", "different_direction"): (
        "Same model system with opposing directional claims: likely differences in endpoint measured "
        "(e.g. proliferation vs. invasiveness), ligand concentration or purity, or assay protocol. "
        "Check whether both papers measure the same biological outcome before treating as a true contradiction."
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
    True when we cannot confirm endpoints differ (treat as same-endpoint contradiction).
    False when known endpoints on both sides differ — soften framing.
    """
    all_records = suppressive + promoting
    known_endpoints = {r.endpoint for r in all_records if r.endpoint != "not specified"}
    if len(known_endpoints) >= 2:
        return False
    return True


def _model_system_key(suppressive: list[EvidenceRecord], promoting: list[EvidenceRecord]) -> str:
    s_models = {r.model_system for r in suppressive}
    p_models = {r.model_system for r in promoting}
    overlap = s_models & p_models
    if overlap:
        return "same_model"
    all_models = s_models | p_models
    if len(all_models) > 2:
        return "mixed_model"
    return "different_model"


def generate_divergence_hypothesis(
    suppressive: list[EvidenceRecord],
    promoting: list[EvidenceRecord],
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
    Given evidence for one gene (+ optional cancer filter upstream), return
    ContradictionPair objects for opposing directions under the same direction_context.
    """
    filtered = [r for r in records if r.direction_context == direction_context_filter]

    suppressive = [r for r in filtered if r.direction == "tumor_suppressive"]
    promoting = [r for r in filtered if r.direction == "tumor_promoting"]

    if not suppressive or not promoting:
        return []

    hypothesis = generate_divergence_hypothesis(suppressive, promoting)

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

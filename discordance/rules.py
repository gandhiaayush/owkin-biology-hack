from __future__ import annotations
from .models import EvidenceRecord, Rule
from .contradiction import detect_contradictions
from .scoring import compute_direction_scores


def generate_rules(
    records: list[EvidenceRecord],
    direction_context_filter: str = "activation_effect",
) -> list[Rule]:
    """
    Given a list of evidence records for one (gene, cancer_type) context,
    return confidence-qualified Rules.

    When evidence is contested, both directions are returned as separate rules
    with their individual confidence labels — never merged into a single winner.
    Never assert universally true from a single source.
    """
    scores = compute_direction_scores(records, direction_context_filter)
    contradictions = detect_contradictions(records, direction_context_filter)
    is_contested = bool(contradictions)

    rules: list[Rule] = []

    if scores.suppressive.records:
        sources = [r.source for r in scores.suppressive.records]
        mechanisms = list({r.mechanism for r in scores.suppressive.records if r.mechanism != "not specified"})
        mechanism_text = "; ".join(mechanisms) if mechanisms else "mechanism not specified"
        rules.append(Rule(
            direction="tumor_suppressive",
            claim=_synthesize_claim("tumor_suppressive", scores.suppressive.records),
            confidence_label=scores.suppressive.confidence_label,
            sources=sources,
            mechanism=mechanism_text,
            contested=is_contested,
        ))

    if scores.promoting.records:
        sources = [r.source for r in scores.promoting.records]
        mechanisms = list({r.mechanism for r in scores.promoting.records if r.mechanism != "not specified"})
        mechanism_text = "; ".join(mechanisms) if mechanisms else "mechanism not specified"
        rules.append(Rule(
            direction="tumor_promoting",
            claim=_synthesize_claim("tumor_promoting", scores.promoting.records),
            confidence_label=scores.promoting.confidence_label,
            sources=sources,
            mechanism=mechanism_text,
            contested=is_contested,
        ))

    return rules


def _synthesize_claim(direction: str, records: list[EvidenceRecord]) -> str:
    """Build a short natural-language claim from the record set. Never says 'always true'."""
    gene = records[0].gene if records else "this receptor"
    n = len(records)
    qualifier = "may" if n == 1 else "appears to"
    verb = "suppress tumor growth" if direction == "tumor_suppressive" else "promote tumor growth or invasiveness"
    caveat = " (single source — treat as hypothesis)" if n == 1 else f" (supported by {n} independent sources)"
    return f"{gene} activation {qualifier} {verb}{caveat}"

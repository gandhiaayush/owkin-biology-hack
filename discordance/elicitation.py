from __future__ import annotations
from .models import ContradictionPair, DirectionScores


def should_trigger_elicitation(scores: DirectionScores) -> bool:
    return scores.elicitation_needed


def build_elicitation_question(
    gene: str,
    cancer_type: str,
    contradiction: ContradictionPair,
    scores: DirectionScores,
) -> str:
    s = scores.suppressive
    p = scores.promoting

    sup_sources = "\n".join(
        f"    - {r.source}: {r.claim}" for r in s.records
    )
    pro_sources = "\n".join(
        f"    - {r.source}: {r.claim}" for r in p.records
    )

    return f"""DEADLOCK DETECTED: Balanced evidence for {gene} role in {cancer_type.replace('_', ' ')}.

Tumor-suppressive evidence (score: {s.score:.2f}):
{sup_sources}

Tumor-promoting evidence (score: {p.score:.2f}):
{pro_sources}

Divergence hypothesis: {contradiction.divergence_hypothesis[:300]}

To generate a confidence-qualified rule, please indicate your interpretation:
A) Weight tumor-suppressive data more heavily → report as suppressive (lower confidence)
B) Weight tumor-promoting data more heavily → report as promoting (lower confidence)
C) Treat as genuinely distinct endpoints — report both without adjudication (recommended)
D) Request additional MOSAIC context before deciding
"""

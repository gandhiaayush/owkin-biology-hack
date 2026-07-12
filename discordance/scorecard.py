"""
Source scorecards: the end-of-query output layer.

After the graph has been queried and traversed (contradictions detected,
directions scored, rules generated), a researcher still has to look at a pile
of evidence records and figure out, for each one: is this any good, what is it
actually useful for here, and why did the system bother showing it to me at
all? That reasoning already exists implicitly in scoring.py/contradiction.py
-- this module makes it explicit and per-source, rather than leaving the
researcher to reverse-engineer a weight number.

build_scorecards() is pure: given the same records/contradictions/scores the
rest of the pipeline already computed, it produces one SourceScorecard per
evidence record actually relevant to the query, ranked so the most load-
bearing sources come first.
"""
from __future__ import annotations

from .models import ContradictionPair, DirectionScores, EvidenceRecord, SourceScorecard
from .scoring import score_record_with_reason

_MIN_STRONG_REPLICATIONS = 3
_MIN_REASONABLE_SAMPLE = 50

_SPECIFICITY_CONTROL_TERMS = (
    "sirna", "knockdown", "knockout", "crispr", "-/-", "negative control",
    "does not express", "do not express", "specificity",
)
_IN_VIVO_TERMS = ("xenograft", "in vivo", "mouse", "mice", "nsg", "transgenic")
_NEGATIVE_RESULT_TERMS = (
    "not significantly different", "no significant effect", "did not induce",
    "not statistically significant", "no effect",
)


def _strengths(r: EvidenceRecord) -> list[str]:
    out: list[str] = []
    text = f"{r.claim} {r.mechanism} {r.model_system}".lower()

    if r.source_type == "primary_study":
        out.append("Peer-reviewed primary data, not a review or preliminary extraction.")
    if r.independent_replications is not None and r.independent_replications >= _MIN_STRONG_REPLICATIONS:
        out.append(f"Independently replicated ({r.independent_replications}x) -- not a one-off result.")
    if r.sample_size is not None and r.sample_size >= _MIN_REASONABLE_SAMPLE:
        out.append(f"Reasonably powered (N={r.sample_size}).")
    if any(term in text for term in _IN_VIVO_TERMS):
        out.append("In vivo evidence, not just a cell-culture proxy.")
    if any(term in text for term in _SPECIFICITY_CONTROL_TERMS):
        out.append("Includes a receptor-specificity control (knockdown/knockout/negative-control cell line).")
    if r.endpoint and r.endpoint != "not specified":
        out.append(f"Endpoint explicitly identified ({r.endpoint}), not left ambiguous.")
    if not out:
        out.append("No standout strength beyond baseline source-type credibility.")
    return out


def _limitations(r: EvidenceRecord) -> list[str]:
    out: list[str] = []
    text = f"{r.claim} {r.mechanism}".lower()
    note = (r.confidence_note or "").lower()

    if r.source_type == "preliminary":
        out.append("Auto-extracted (e.g. from an abstract or figure caption), not yet manually verified.")
    if r.source_type == "patent":
        out.append("Evidence of commercial interest, not independent biological validation -- weight accordingly.")
    if r.independent_replications in (None, 0):
        out.append("Unreplicated (N=1 or unknown) -- treat as a hypothesis, not an established finding.")
    if r.sample_size is None:
        out.append("Sample size not reported.")
    if "unverified" in note:
        out.append("Explicitly flagged unverified in its own confidence note.")
    if any(term in text for term in _NEGATIVE_RESULT_TERMS):
        out.append("Contains a negative/null result for at least part of its claim -- don't overstate the positive framing.")
    if not out:
        out.append("No major limitation flagged.")
    return out


def _best_for(r: EvidenceRecord, query_endpoint: str | None) -> str:
    if r.source_type == "database_derived":
        return "Corroborating expression/CNV/structural signal only -- not a direction or mechanism claim on its own."
    if r.source_type == "patent":
        return "Signals commercial/therapeutic interest in this target -- not evidence the biology is settled."
    if r.source_type == "preliminary":
        return "A lead worth chasing down and manually verifying, not something to cite as-is."
    if query_endpoint and r.endpoint and r.endpoint != "not specified":
        if r.endpoint == query_endpoint:
            return f"Directly answers the '{query_endpoint}' question this query is asking about."
        return f"Answers a related but distinct question (measures '{r.endpoint}', not '{query_endpoint}') -- useful context, not a direct answer."
    return f"Supports the {r.direction.replace('_', '-')} case for {r.gene} in {r.cancer_type.replace('_', ' ')}."


def _selection_reason(
    r: EvidenceRecord,
    scores: DirectionScores,
    contradictions: list[ContradictionPair],
    rank_in_direction: int,
) -> str:
    in_contradiction = any(
        r in c.suppressive_records or r in c.promoting_records for c in contradictions
    )
    if in_contradiction:
        other = "tumor-promoting" if r.direction == "tumor_suppressive" else "tumor-suppressive"
        return (
            f"Selected because it's part of the contested cluster -- one side of a "
            f"{r.direction.replace('_', '-')} vs. {other} split that the graph could not "
            "resolve on its own."
        )
    if rank_in_direction == 0:
        return f"Highest-weighted {r.direction.replace('_', '-')} source for this gene/cancer context."
    return f"Contributes supporting weight to the {r.direction.replace('_', '-')} case (rank {rank_in_direction + 1} by weight)."


def build_scorecards(
    records: list[EvidenceRecord],
    scores: DirectionScores,
    contradictions: list[ContradictionPair],
    query_endpoint: str | None = None,
) -> list[SourceScorecard]:
    """
    Build one scorecard per activation-effect record actually contributing to
    the direction scores (i.e. the same records compute_direction_scores/
    detect_contradictions already considered) -- database_derived/patent
    records are included too since they're still relevant context for a
    researcher, just scored/labeled differently.

    Ranked so the most load-bearing sources (highest weight, or part of an
    unresolved contradiction) come first -- this is the order a researcher
    should actually read them in, not insertion order.
    """
    by_direction: dict[str, list[EvidenceRecord]] = {"tumor_suppressive": [], "tumor_promoting": []}
    for r in scores.suppressive.records:
        by_direction["tumor_suppressive"].append(r)
    for r in scores.promoting.records:
        by_direction["tumor_promoting"].append(r)

    rank_of: dict[int, int] = {}
    for direction_records in by_direction.values():
        ranked = sorted(
            enumerate(direction_records),
            key=lambda pair: score_record_with_reason(pair[1])[0],
            reverse=True,
        )
        for rank, (_, r) in enumerate(ranked):
            rank_of[id(r)] = rank

    considered = by_direction["tumor_suppressive"] + by_direction["tumor_promoting"]
    # Include neutral/context records (patents, database_derived, expression-pattern
    # evidence) that were part of the original record set but excluded from the
    # direction scoring -- they're still worth a scorecard, just ranked last.
    considered_ids = {id(r) for r in considered}
    context_only = [r for r in records if id(r) not in considered_ids]

    cards: list[SourceScorecard] = []
    for r in considered:
        weight, weight_reason = score_record_with_reason(r)
        in_contradiction = any(
            r in c.suppressive_records or r in c.promoting_records for c in contradictions
        )
        cards.append(SourceScorecard(
            source=r.source,
            source_type=r.source_type,
            direction=r.direction,
            weight=round(weight, 3),
            weight_reason=weight_reason,
            strengths=_strengths(r),
            limitations=_limitations(r),
            best_for=_best_for(r, query_endpoint),
            selection_reason=_selection_reason(r, scores, contradictions, rank_of.get(id(r), 0)),
            contested=in_contradiction,
            endpoint=r.endpoint,
        ))

    for r in context_only:
        weight, weight_reason = score_record_with_reason(r)
        cards.append(SourceScorecard(
            source=r.source,
            source_type=r.source_type,
            direction=r.direction,
            weight=round(weight, 3),
            weight_reason=weight_reason,
            strengths=_strengths(r),
            limitations=_limitations(r),
            best_for=_best_for(r, query_endpoint),
            selection_reason=(
                "Selected as background context (expression/structural/commercial data) "
                "rather than a direct direction claim."
            ),
            contested=False,
            endpoint=r.endpoint,
        ))

    cards.sort(key=lambda c: (not c.contested, -c.weight))
    return cards


_QUERY_ENDPOINT_TERMS = ("proliferation", "invasiveness", "invasion", "migration", "apoptosis", "expression")


def infer_query_endpoint(query_text: str) -> str | None:
    """Best-effort guess at which endpoint a free-text query is asking about, so
    scorecards can flag which sources directly answer it vs. adjacent context."""
    lower = (query_text or "").lower()
    for candidate in _QUERY_ENDPOINT_TERMS:
        if candidate in lower:
            return "invasiveness" if candidate == "invasion" else candidate
    return None


def scorecard_to_dict(c: SourceScorecard) -> dict:
    return {
        "source": c.source,
        "source_type": c.source_type,
        "direction": c.direction,
        "weight": c.weight,
        "weight_reason": c.weight_reason,
        "strengths": c.strengths,
        "limitations": c.limitations,
        "best_for": c.best_for,
        "selection_reason": c.selection_reason,
        "contested": c.contested,
        "endpoint": c.endpoint,
    }

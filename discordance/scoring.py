from __future__ import annotations
from .models import EvidenceRecord, ScoredDirection, DirectionScores, ConsensusStatus
from .normalize import is_tumor_intrinsic_activation, cell_compartment

SOURCE_WEIGHTS: dict[str, float] = {
    "primary_study": 1.0,
    "review": 0.7,
    "preliminary": 0.4,
    "database_derived": 0.6,
    "patent": 0.1,
}

ELICITATION_THRESHOLD = (0.4, 0.6)  # fire when suppressive_ratio is in this range


def score_record(r: EvidenceRecord) -> float:
    """Compute a numeric weight for one evidence record."""
    base = SOURCE_WEIGHTS.get(r.source_type, 0.5)
    # independent_replications=None means "unknown" — give a small penalty vs. confirmed 0
    reps = r.independent_replications if r.independent_replications is not None else -1
    replication_bonus = 0.2 * min(max(reps, 0), 5)
    sample_bonus = 0.1 * min(r.sample_size or 0, 1000) / 1000
    return base * (1 + replication_bonus + sample_bonus)


def score_record_with_reason(r: EvidenceRecord) -> tuple[float, str]:
    """Compute weight and return a human-readable explanation of how it was derived.

    The reason string mirrors the actual score_record() formula exactly — any
    change to score_record() must be reflected here to keep the display honest.
    """
    base = SOURCE_WEIGHTS.get(r.source_type, 0.5)
    reps = r.independent_replications if r.independent_replications is not None else -1
    replication_bonus = 0.2 * min(max(reps, 0), 5)
    sample_bonus = 0.1 * min(r.sample_size or 0, 1000) / 1000
    score = base * (1 + replication_bonus + sample_bonus)

    rep_str = (
        f"{r.independent_replications} independent replications → +{replication_bonus:.2f}"
        if r.independent_replications is not None and r.independent_replications > 0
        else ("replications unknown → +0.00" if r.independent_replications is None
              else "0 replications → +0.00")
    )
    samp_str = (
        f"N={r.sample_size} → +{sample_bonus:.3f}" if r.sample_size else "N=unknown → +0.000"
    )
    reason = (
        f"{r.source_type} (base={base:.1f}) × (1 + {rep_str}, {samp_str}) = {score:.3f}"
    )
    return score, reason


def get_confidence_label(records: list[EvidenceRecord]) -> str:
    if not records:
        return "no evidence"
    n = len(records)
    max_reps = max(
        (r.independent_replications for r in records if r.independent_replications is not None),
        default=None,
    )
    if n == 1:
        if max_reps is None:
            return "unreplicated (N=1, replication unknown) — treat as hypothesis"
        if max_reps == 0:
            return "unreplicated (N=1) — treat as hypothesis"
        return f"replicated (N=1 primary, {max_reps} independent) — moderate confidence"
    return f"converging evidence (N={n} sources)"


def compute_direction_scores(
    records: list[EvidenceRecord],
    direction_context_filter: str = "activation_effect",
) -> DirectionScores:
    filtered = [r for r in records if r.direction_context == direction_context_filter]
    # Tumor-intrinsic activation claims only — exclude TAM/immune (Marelli) and patents from mass
    directional_pool = [
        r for r in filtered
        if (direction_context_filter != "activation_effect" or is_tumor_intrinsic_activation(r))
        and r.source_type != "patent"
    ]

    suppressive_recs = [r for r in directional_pool if r.direction == "tumor_suppressive"]
    promoting_recs = [r for r in directional_pool if r.direction == "tumor_promoting"]
    patent_recs = [r for r in filtered if r.source_type == "patent"]
    immune_recs = [
        r for r in filtered
        if direction_context_filter == "activation_effect"
        and cell_compartment(r) == "immune_cell"
    ]

    s_score = sum(score_record(r) for r in suppressive_recs)
    p_score = sum(score_record(r) for r in promoting_recs)
    commercial_score = sum(score_record(r) for r in patent_recs) + sum(
        score_record(r) for r in immune_recs
    )  # immune/TAM claims tracked separately, not in direction mass

    total = s_score + p_score

    # Determine consensus status
    if total == 0:
        status: ConsensusStatus = "no_data"
        elicitation_needed = False
        overall_label = "no evidence available"
    elif not suppressive_recs and not promoting_recs:
        status = "no_data"
        elicitation_needed = False
        overall_label = "no directional evidence"
    elif suppressive_recs and not promoting_recs:
        status = "consensus_suppressive" if len(suppressive_recs) > 1 else "single_source"
        elicitation_needed = False
        overall_label = f"tumor-suppressive ({get_confidence_label(suppressive_recs)})"
    elif promoting_recs and not suppressive_recs:
        status = "consensus_promoting" if len(promoting_recs) > 1 else "single_source"
        elicitation_needed = False
        overall_label = f"tumor-promoting ({get_confidence_label(promoting_recs)})"
    else:
        # Both directions have evidence
        ratio = s_score / total
        elicitation_needed = ELICITATION_THRESHOLD[0] <= ratio <= ELICITATION_THRESHOLD[1]
        status = "contested"
        overall_label = (
            f"CONTESTED — suppressive score {s_score:.2f} vs. promoting score {p_score:.2f}; "
            "see contradiction report"
        )

    return DirectionScores(
        suppressive=ScoredDirection(
            direction="tumor_suppressive",
            score=s_score,
            records=suppressive_recs,
            confidence_label=get_confidence_label(suppressive_recs),
        ),
        promoting=ScoredDirection(
            direction="tumor_promoting",
            score=p_score,
            records=promoting_recs,
            confidence_label=get_confidence_label(promoting_recs),
        ),
        commercial_interest_score=commercial_score,
        consensus_status=status,
        overall_confidence_label=overall_label,
        elicitation_needed=elicitation_needed,
    )

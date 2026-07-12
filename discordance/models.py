from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional


SourceType = Literal["primary_study", "review", "preliminary", "patent", "database_derived"]
Direction = Literal["tumor_suppressive", "tumor_promoting", "neutral"]
DirectionContext = Literal["activation_effect", "expression_pattern", "genetic_alteration"]
ConsensusStatus = Literal[
    "contested", "consensus_suppressive", "consensus_promoting", "single_source", "no_data"
]


@dataclass
class EvidenceRecord:
    source: str
    source_type: SourceType
    claim: str
    gene: str
    direction: Direction
    cancer_type: str
    model_system: str
    mechanism: str = "not specified"
    direction_context: DirectionContext = "activation_effect"
    # What biological outcome was actually measured (e.g. "proliferation",
    # "invasiveness", "apoptosis", "migration"). Distinct from direction_context,
    # which separates activation-effect claims from expression/genetic-alteration
    # claims -- endpoint distinguishes *within* activation_effect records whether
    # two studies measured the same thing. Two records can share direction_context
    # (both are functional activation-effect claims) and still not be a true
    # same-endpoint contradiction if one measures proliferation and the other
    # measures invasiveness -- see the Neuhaus/Sanz OR51E2 case, which is exactly
    # this pattern (confirmed by Person A's full-text verification).
    endpoint: str = "not specified"
    sample_size: Optional[int] = None
    independent_replications: Optional[int] = None
    confidence_note: str = ""
    id: Optional[int] = None


@dataclass
class ContradictionPair:
    suppressive_records: list[EvidenceRecord]
    promoting_records: list[EvidenceRecord]
    same_model_system: bool
    same_endpoint: bool  # False when endpoint is known and differs -- softens "contradiction" framing
    divergence_hypothesis: str
    deadlock: bool  # True when scores are balanced (0.4–0.6 ratio)


@dataclass
class ScoredDirection:
    direction: Direction
    score: float
    records: list[EvidenceRecord]
    confidence_label: str


@dataclass
class DirectionScores:
    suppressive: ScoredDirection
    promoting: ScoredDirection
    commercial_interest_score: float  # patents only, not folded into above
    consensus_status: ConsensusStatus
    overall_confidence_label: str
    elicitation_needed: bool


@dataclass
class Rule:
    direction: Direction
    claim: str
    confidence_label: str
    sources: list[str]
    mechanism: str
    contested: bool


@dataclass
class SourceScorecard:
    """
    Per-source summary for the end-of-query output: not just "here is the
    evidence" but why this particular source is trustworthy (or isn't), what
    it's actually useful for given the researcher's query, and why it was
    surfaced at all. This is the thing a researcher reads instead of having to
    reverse-engineer the weighting logic themselves.
    """
    source: str
    source_type: SourceType
    direction: Direction
    weight: float
    weight_reason: str
    strengths: list[str]
    limitations: list[str]
    best_for: str
    selection_reason: str
    contested: bool
    endpoint: str = "not specified"
    unique_insight: str | None = None


@dataclass
class QueryResponse:
    gene: str
    cancer_type: str
    query: str
    consensus_status: ConsensusStatus
    overall_confidence_label: str
    rules: list[Rule]
    contradictions: list[ContradictionPair]
    elicitation_triggered: bool
    elicitation_response: Optional[str]
    tension_map_data: dict

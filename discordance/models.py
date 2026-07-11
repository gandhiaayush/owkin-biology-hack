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
    sample_size: Optional[int] = None
    independent_replications: Optional[int] = None
    confidence_note: str = ""
    id: Optional[int] = None


@dataclass
class ContradictionPair:
    suppressive_records: list[EvidenceRecord]
    promoting_records: list[EvidenceRecord]
    same_model_system: bool
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

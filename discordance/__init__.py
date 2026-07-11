from .models import EvidenceRecord, ContradictionPair, Rule, DirectionScores, QueryResponse
from .db import init_db, insert_record, get_records, get_all_records
from .contradiction import detect_contradictions
from .scoring import compute_direction_scores, score_record, get_confidence_label
from .rules import generate_rules

__all__ = [
    "EvidenceRecord",
    "ContradictionPair",
    "Rule",
    "DirectionScores",
    "QueryResponse",
    "init_db",
    "insert_record",
    "get_records",
    "get_all_records",
    "detect_contradictions",
    "compute_direction_scores",
    "score_record",
    "get_confidence_label",
    "generate_rules",
]

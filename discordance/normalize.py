"""Normalization helpers for endpoints, model systems, and cell compartments."""
from __future__ import annotations

import re

from .models import EvidenceRecord

# Canonical endpoint tokens for overlap detection (not full ontology IDs yet)
_ENDPOINT_ALIASES: dict[str, str] = {
    "proliferation": "proliferation",
    "cell growth": "proliferation",
    "tumor growth": "tumor_growth",
    "growth": "tumor_growth",
    "invasiveness": "invasiveness",
    "invasion": "invasiveness",
    "migration": "migration",
    "apoptosis": "apoptosis",
    "cell death": "apoptosis",
    "prognosis": "prognosis",
    "gleason": "prognosis",
    "immune evasion": "immune_evasion",
    "tam polarization": "immune_evasion",
}


def endpoint_tokens(endpoint: str) -> set[str]:
    """Tokenize a possibly compound endpoint string into canonical tokens."""
    if not endpoint or endpoint == "not specified":
        return set()
    text = endpoint.lower()
    found: set[str] = set()
    for needle, canonical in _ENDPOINT_ALIASES.items():
        if needle in text:
            found.add(canonical)
    if not found:
        for part in re.split(r"[,;/]|\band\b", text):
            part = part.strip()
            if part:
                found.add(part.replace(" ", "_"))
    return found


def endpoints_overlap(records_a: list[EvidenceRecord], records_b: list[EvidenceRecord]) -> bool:
    """True if any canonical endpoint token appears on both sides."""
    a = set()
    b = set()
    for r in records_a:
        a |= endpoint_tokens(r.endpoint)
    for r in records_b:
        b |= endpoint_tokens(r.endpoint)
    if not a or not b:
        return False
    return bool(a & b)


def endpoints_confirmed_different(
    records_a: list[EvidenceRecord], records_b: list[EvidenceRecord]
) -> bool:
    """True only when both sides have known tokens and there is zero overlap."""
    a = set()
    b = set()
    for r in records_a:
        a |= endpoint_tokens(r.endpoint)
    for r in records_b:
        b |= endpoint_tokens(r.endpoint)
    if not a or not b:
        return False
    return len(a & b) == 0


def model_families(model_system: str) -> set[str]:
    """Map free-text model labels to coarse families for overlap checks."""
    m = model_system.lower()
    families: set[str] = set()
    if "lncap" in m:
        families.add("lncap")
    if "xenograft" in m:
        families.add("xenograft")
    if "transgenic" in m or "psgr-transgenic" in m.replace(" ", ""):
        families.add("transgenic_mouse")
    if "hek293" in m:
        families.add("hek293")
    if "tcga" in m:
        families.add("tcga_cohort")
    if "tam" in m or "macrophage" in m:
        families.add("tam_model")
    if not families:
        families.add(model_system.lower().strip())
    return families


def models_overlap(records_a: list[EvidenceRecord], records_b: list[EvidenceRecord]) -> bool:
    """True if any model-system family overlaps between record sets."""
    a: set[str] = set()
    b: set[str] = set()
    for r in records_a:
        a |= model_families(r.model_system)
    for r in records_b:
        b |= model_families(r.model_system)
    return bool(a & b)


def model_overlap_kind(
    suppressive: list[EvidenceRecord], promoting: list[EvidenceRecord]
) -> str:
    if models_overlap(suppressive, promoting):
        return "same_model"
    all_families = set()
    for r in suppressive + promoting:
        all_families |= model_families(r.model_system)
    if len(all_families) > 2:
        return "mixed_model"
    return "different_model"


def cell_compartment(record: EvidenceRecord) -> str:
    """tumor_cell | immune_cell | mixed — inferred from claim/mechanism/model text."""
    text = f"{record.claim} {record.mechanism} {record.model_system}".lower()
    # Word-boundary checks — avoid false positives like "immune" inside "invasion"
    # or "tme" inside "co-treatment".
    immune_patterns = (
        r"\bmacrophage", r"\btam\b", r"tumor-associated macrophage",
        r"\bimmune\b", r"non-cell-autonomous", r"\bcd8\b", r"\btme\b", r"immunosupp",
    )
    if any(re.search(p, text) for p in immune_patterns):
        return "immune_cell"
    return "tumor_cell"


def is_tumor_intrinsic_activation(record: EvidenceRecord) -> bool:
    """Records that should vote in tumor-cell activation deadlock math."""
    if record.direction_context != "activation_effect":
        return False
    if record.source_type == "patent":
        return False
    return cell_compartment(record) == "tumor_cell"


def count_independent_sources(records: list[EvidenceRecord]) -> int:
    """Count non-patent primary/review sources, collapsing obvious patent families."""
    seen: set[str] = set()
    n = 0
    for r in records:
        if r.source_type == "patent":
            continue
        key = r.source.split("(")[0].strip().lower()[:60]
        if key in seen:
            continue
        seen.add(key)
        n += 1
    return n

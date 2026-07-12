"""Controlled vocabulary for the Discordance evidence graph.

This is the runtime ontology: shared names for node/edge kinds and allowed
direction/source values. Protégé can mirror these classes; the live system
uses this module so missing assertions stay open-world (absence ≠ false).

OR-specific subclasses (ClassA_OR, OdorantLigand, BiasedAgonism, …) refine
the generic graph schema for olfactory-receptor-in-cancer evidence without
requiring a separate graph database.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import EvidenceRecord

# Node classes (Protégé-style)
NODE_TYPES = (
    "Receptor",
    "CancerType",
    "ModelSystem",
    "Endpoint",
    "Paper",
    "Claim",
    "Direction",
    "Ligand",
    "Mechanism",
)

# OR-in-cancer subclasses — refine NODE_TYPES for our domain
OR_SUBCLASSES: dict[str, tuple[str, ...]] = {
    "Receptor": ("ClassA_OR", "EctopicallyExpressedOR"),
    "Ligand": ("OdorantLigand", "MetaboliteLigand", "BiasedAgonist"),
    "ModelSystem": (
        "EndogenousReceptorModel",
        "HeterologousExpressionModel",
        "XenograftModel",
        "CohortStudy",
    ),
    "Endpoint": (
        "ProliferationEndpoint",
        "InvasivenessEndpoint",
        "ApoptosisEndpoint",
        "ExpressionEndpoint",
        "PrognosisEndpoint",
    ),
    "Claim": (
        "ActivationEffectClaim",
        "ExpressionPatternClaim",
        "GeneticAlterationClaim",
        "CommercialInterestClaim",
    ),
    "Paper": (
        "PrimaryStudyPaper",
        "ReviewPaper",
        "PatentDocument",
        "DatabaseDerivedRecord",
        "PreliminaryStudyPaper",
    ),
}

# Edge / object-property kinds
EDGE_TYPES = (
    "about_receptor",      # Claim → Receptor
    "in_cancer",           # Claim → CancerType
    "in_model",            # Claim → ModelSystem
    "measures_endpoint",   # Claim → Endpoint
    "asserts_direction",   # Claim → Direction
    "from_paper",          # Claim → Paper
    "via_mechanism",       # Claim → Mechanism
    "uses_ligand",         # Claim → Ligand (optional)
    "tension_with",        # Claim → Claim (opposing direction, same context)
)

# Domain/range hints for OWL export and documentation
OR_EDGE_SEMANTICS: dict[str, tuple[str, tuple[str, ...]]] = {
    "about_receptor": ("Claim", ("Receptor", "ClassA_OR")),
    "in_cancer": ("Claim", ("CancerType",)),
    "in_model": ("Claim", ("ModelSystem",)),
    "measures_endpoint": ("Claim", ("Endpoint",)),
    "asserts_direction": ("Claim", ("Direction",)),
    "from_paper": ("Claim", ("Paper",)),
    "via_mechanism": ("Claim", ("Mechanism",)),
    "uses_ligand": ("Claim", ("Ligand", "OdorantLigand", "BiasedAgonist")),
    "tension_with": ("Claim", ("Claim",)),
}

DATA_PROPERTIES: dict[str, str] = {
    "hasDirection": "tumor_suppressive | tumor_promoting | neutral",
    "hasWeight": "evidence weight score",
    "hasDirectionContext": "activation_effect | expression_pattern | genetic_alteration",
    "hasSourceType": "primary_study | review | patent | …",
}

DIRECTIONS = ("tumor_suppressive", "tumor_promoting", "neutral")
DIRECTION_CONTEXTS = ("activation_effect", "expression_pattern", "genetic_alteration")
SOURCE_TYPES = ("primary_study", "review", "preliminary", "patent", "database_derived")

_LIGAND_PATTERNS = (
    (re.compile(r"β-ionone|beta-ionone", re.I), "β-ionone", "BiasedAgonist"),
    (re.compile(r"α-ionone|alpha-ionone", re.I), "α-ionone", "BiasedAgonist"),
    (re.compile(r"androstenone", re.I), "androstenone", "OdorantLigand"),
    (re.compile(r"propionate|acetate", re.I), "short-chain fatty acid", "MetaboliteLigand"),
    (re.compile(r"palmitic", re.I), "palmitic acid", "MetaboliteLigand"),
)

# Consensus / tension display hints for Person C tension maps
STATUS_COLORS = {
    "consensus": "green",
    "contested": "red",
    "exploratory": "amber",
    "structural": "blue",
    "neutral": "gray",
}


def classify_claim_subtype(record: "EvidenceRecord") -> str:
    if record.source_type == "patent":
        return "CommercialInterestClaim"
    return {
        "activation_effect": "ActivationEffectClaim",
        "expression_pattern": "ExpressionPatternClaim",
        "genetic_alteration": "GeneticAlterationClaim",
    }.get(record.direction_context, "ActivationEffectClaim")


def classify_paper_subtype(source_type: str) -> str:
    return {
        "primary_study": "PrimaryStudyPaper",
        "review": "ReviewPaper",
        "patent": "PatentDocument",
        "database_derived": "DatabaseDerivedRecord",
        "preliminary": "PreliminaryStudyPaper",
    }.get(source_type, "PrimaryStudyPaper")


def classify_model_subtype(model_system: str) -> str:
    m = model_system.lower()
    if "tcga" in m or "cohort" in m:
        return "CohortStudy"
    if "xenograft" in m or "in vivo" in m or "mouse" in m:
        return "XenograftModel"
    if "hek293" in m or "transient" in m or "heterologous" in m:
        return "HeterologousExpressionModel"
    if "lncap" in m or "endogenous" in m:
        return "EndogenousReceptorModel"
    return "EndogenousReceptorModel"


def classify_endpoint_subtype(endpoint: str) -> str:
    e = endpoint.lower()
    if "prolif" in e:
        return "ProliferationEndpoint"
    if "invas" in e or "migrat" in e:
        return "InvasivenessEndpoint"
    if "apopt" in e or "death" in e:
        return "ApoptosisEndpoint"
    if "prognos" in e or "gleason" in e:
        return "PrognosisEndpoint"
    if "express" in e:
        return "ExpressionEndpoint"
    return "ProliferationEndpoint"


def infer_ligand_subtype(claim: str, mechanism: str = "") -> str | None:
    text = f"{claim} {mechanism}"
    for pattern, label, _subtype in _LIGAND_PATTERNS:
        if pattern.search(text):
            return label
    return None


def infer_ligand_class(claim: str, mechanism: str = "") -> str | None:
    text = f"{claim} {mechanism}"
    for pattern, _label, subtype in _LIGAND_PATTERNS:
        if pattern.search(text):
            return subtype
    return None


def receptor_subtypes(gene: str) -> list[str]:
    """All OR subclasses applicable to a receptor node."""
    subs = ["ClassA_OR", "Receptor"]
    if gene.upper().startswith("OR"):
        subs.insert(0, "EctopicallyExpressedOR")
    return subs


def slug(text: str) -> str:
    """Stable id fragment from a free-text label."""
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in (text or "").strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "unknown"

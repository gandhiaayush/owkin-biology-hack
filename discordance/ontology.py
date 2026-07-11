"""Controlled vocabulary for the Discordance evidence graph.

This is the runtime ontology: shared names for node/edge kinds and allowed
direction/source values. Protégé can mirror these classes; the live system
uses this module so missing assertions stay open-world (absence ≠ false).
"""
from __future__ import annotations

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

DIRECTIONS = ("tumor_suppressive", "tumor_promoting", "neutral")
DIRECTION_CONTEXTS = ("activation_effect", "expression_pattern", "genetic_alteration")
SOURCE_TYPES = ("primary_study", "review", "preliminary", "patent", "database_derived")

# Consensus / tension display hints for Person C tension maps
STATUS_COLORS = {
    "consensus": "green",
    "contested": "red",
    "exploratory": "amber",
    "structural": "blue",
    "neutral": "gray",
}


def slug(text: str) -> str:
    """Stable id fragment from a free-text label."""
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in (text or "").strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "unknown"

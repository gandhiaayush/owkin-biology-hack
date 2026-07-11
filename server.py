"""
Discordance MCP Server — Builder and Query tools.

Builder tool: accepts a structured evidence record, writes to SQLite,
              runs contradiction detection on insert, returns result.
Query tool:   given gene + cancer_type, returns sourced confidence-weighted
              answer with explicit contestation flags. Triggers elicitation
              when evidence is deadlocked.

Run: python server.py
     or: fastmcp run server.py
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.elicitation import AcceptedElicitation

from discordance import (
    init_db, insert_record, get_records,
    detect_contradictions, compute_direction_scores, generate_rules,
    EvidenceRecord,
)
from discordance.elicitation import should_trigger_elicitation, build_elicitation_question

DB_PATH = Path("evidence.db")
init_db(DB_PATH)

mcp = FastMCP("discordance", instructions=(
    "Contradiction-aware knowledge graph for olfactory receptors in cancer. "
    "Use add_evidence to ingest evidence records, query_graph to ask questions."
))


# ── Pydantic schemas for tool I/O ──────────────────────────────────────────

class EvidenceInput(BaseModel):
    source: str = Field(description="Full citation, e.g. 'Author et al. YEAR, Journal'")
    source_type: Literal["primary_study", "review", "preliminary", "patent", "database_derived"]
    claim: str = Field(description="Single sentence, specific claim text")
    mechanism: str = Field(default="not specified", description="Pathway or molecular mechanism")
    direction: Literal["tumor_suppressive", "tumor_promoting", "neutral"]
    direction_context: Literal["activation_effect", "expression_pattern", "genetic_alteration"] = "activation_effect"
    cancer_type: str = Field(default="prostate_cancer")
    model_system: str = Field(description="e.g. LNCaP, xenograft, TCGA-PRAD")
    sample_size: Optional[int] = None
    independent_replications: Optional[int] = None
    gene: str = Field(default="OR51E2")
    confidence_note: str = Field(default="")


class ResearcherChoice(BaseModel):
    choice: Literal["A", "B", "C", "D"] = Field(
        description="A=weight suppressive, B=weight promoting, C=report both, D=request MOSAIC"
    )


# ── Builder tool ────────────────────────────────────────────────────────────

@mcp.tool()
def add_evidence(evidence: EvidenceInput) -> dict:
    """
    Ingest one evidence record into the knowledge graph.
    Runs contradiction detection immediately on insert.
    Returns the new record id and any contradictions found.
    """
    record = EvidenceRecord(
        source=evidence.source,
        source_type=evidence.source_type,
        claim=evidence.claim,
        mechanism=evidence.mechanism,
        direction=evidence.direction,
        direction_context=evidence.direction_context,
        cancer_type=evidence.cancer_type,
        model_system=evidence.model_system,
        sample_size=evidence.sample_size,
        independent_replications=evidence.independent_replications,
        gene=evidence.gene,
        confidence_note=evidence.confidence_note,
    )
    row_id = insert_record(record)

    if row_id is None:
        return {"status": "duplicate_ignored", "record_id": None, "contradiction_detected": False}

    # Run contradiction detection on the full updated record set
    all_records = get_records(evidence.gene, evidence.cancer_type)
    contradictions = detect_contradictions(all_records)
    scores = compute_direction_scores(all_records)

    contradiction_data = []
    for c in contradictions:
        contradiction_data.append({
            "suppressive_sources": [r.source for r in c.suppressive_records],
            "promoting_sources": [r.source for r in c.promoting_records],
            "same_model_system": c.same_model_system,
            "same_endpoint": c.same_endpoint,
            "divergence_hypothesis": c.divergence_hypothesis,
            "deadlock": c.deadlock,
        })

    return {
        "status": "inserted",
        "record_id": row_id,
        "contradiction_detected": bool(contradictions),
        "contradictions": contradiction_data,
        "confidence_label": scores.overall_confidence_label,
    }


# ── Query tool ──────────────────────────────────────────────────────────────

@mcp.tool()
async def query_graph(
    gene: str,
    cancer_type: str,
    ctx: Context,
    query: str = "",
) -> dict:
    """
    Query the knowledge graph for a gene in a cancer context.
    Returns sourced, confidence-weighted rules. Surfaces contradictions explicitly.
    When evidence is deadlocked, triggers MCP elicitation to ask the researcher.
    """
    records = get_records(gene, cancer_type)

    if not records:
        return {
            "gene": gene,
            "cancer_type": cancer_type,
            "query": query,
            "consensus_status": "no_data",
            "overall_confidence_label": "no evidence in graph for this gene/cancer context",
            "rules": [],
            "contradictions": [],
            "elicitation_triggered": False,
            "elicitation_response": None,
            "tension_map_data": {"nodes": [], "edges": []},
        }

    scores = compute_direction_scores(records)
    contradictions = detect_contradictions(records)
    rules = generate_rules(records)

    elicitation_triggered = False
    elicitation_response = None

    if should_trigger_elicitation(scores) and contradictions:
        elicitation_triggered = True
        question = build_elicitation_question(gene, cancer_type, contradictions[0], scores)
        result = await ctx.elicit(message=question, schema=ResearcherChoice)

        if isinstance(result, AcceptedElicitation) and result.data:
            choice = result.data.choice
            elicitation_response = (
                f"Researcher chose option {choice}: "
                + {
                    "A": "weight suppressive evidence more heavily",
                    "B": "weight promoting evidence more heavily",
                    "C": "report both directions without adjudication (recommended)",
                    "D": "request additional MOSAIC context before deciding",
                }.get(choice, "unknown")
            )
        else:
            elicitation_response = f"Researcher declined or cancelled ({result.action})"

    # Serialize rules and contradictions
    rules_data = [
        {
            "direction": r.direction,
            "claim": r.claim,
            "confidence_label": r.confidence_label,
            "sources": r.sources,
            "mechanism": r.mechanism,
            "contested": r.contested,
        }
        for r in rules
    ]

    contradiction_data = [
        {
            "suppressive_sources": [r.source for r in c.suppressive_records],
            "promoting_sources": [r.source for r in c.promoting_records],
            "same_model_system": c.same_model_system,
            "same_endpoint": c.same_endpoint,
            "divergence_hypothesis": c.divergence_hypothesis,
            "deadlock": c.deadlock,
        }
        for c in contradictions
    ]

    tension_map = _build_tension_map(gene, cancer_type, scores, contradictions)

    return {
        "gene": gene,
        "cancer_type": cancer_type,
        "query": query,
        "consensus_status": scores.consensus_status,
        "overall_confidence_label": scores.overall_confidence_label,
        "rules": rules_data,
        "contradictions": contradiction_data,
        "elicitation_triggered": elicitation_triggered,
        "elicitation_response": elicitation_response,
        "tension_map_data": tension_map,
    }


def _build_tension_map(gene, cancer_type, scores, contradictions) -> dict:
    nodes = [
        {"id": gene, "label": gene, "type": "gene", "consensus_status": scores.consensus_status},
        {"id": cancer_type, "label": cancer_type.replace("_", " ").title(), "type": "cancer_type"},
    ]
    edges = []
    is_contested = bool(contradictions)

    if scores.suppressive.records:
        nodes.append({
            "id": "tumor_suppressive", "label": "Tumor Suppressive",
            "type": "direction", "color_hint": "green",
        })
        edges.append({
            "from": gene, "to": "tumor_suppressive",
            "weight": round(scores.suppressive.score, 3),
            "contested": is_contested,
            "sources": [r.source for r in scores.suppressive.records],
            "mechanism": "; ".join(
                {r.mechanism for r in scores.suppressive.records if r.mechanism != "not specified"}
            ) or "not specified",
        })

    if scores.promoting.records:
        nodes.append({
            "id": "tumor_promoting", "label": "Tumor Promoting",
            "type": "direction", "color_hint": "red",
        })
        edges.append({
            "from": gene, "to": "tumor_promoting",
            "weight": round(scores.promoting.score, 3),
            "contested": is_contested,
            "sources": [r.source for r in scores.promoting.records],
            "mechanism": "; ".join(
                {r.mechanism for r in scores.promoting.records if r.mechanism != "not specified"}
            ) or "not specified",
        })

    edges.append({
        "from": gene, "to": cancer_type,
        "weight": 1.0, "type": "expressed_in",
    })

    return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    mcp.run()

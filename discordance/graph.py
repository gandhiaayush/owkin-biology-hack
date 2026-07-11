"""Evidence knowledge graph built from EvidenceRecord rows.

Question → match receptor/cancer → collect local claim neighborhood →
return all supporting/opposing/neutral evidence with weights and tensions.
Open-world: missing claims are not treated as false.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from .models import EvidenceRecord, ContradictionPair
from .scoring import score_record, compute_direction_scores
from .contradiction import detect_contradictions
from . import ontology as onto


@dataclass
class GraphNode:
    id: str
    type: str
    label: str
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "label": self.label, **self.meta}


@dataclass
class GraphEdge:
    id: str
    source: str  # from node id
    target: str  # to node id
    type: str
    weight: float = 1.0
    contested: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from": self.source,
            "to": self.target,
            "type": self.type,
            "weight": round(self.weight, 3),
            "contested": self.contested,
            **self.meta,
        }


@dataclass
class EvidenceGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: dict[str, GraphEdge] = field(default_factory=dict)

    def add_node(self, node: GraphNode) -> GraphNode:
        existing = self.nodes.get(node.id)
        if existing:
            existing.meta.update(node.meta)
            return existing
        self.nodes[node.id] = node
        return node

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        if edge.id in self.edges:
            return self.edges[edge.id]
        self.edges[edge.id] = edge
        return edge

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
        }

    def neighbors(self, node_id: str, edge_type: Optional[str] = None) -> list[str]:
        out = []
        for e in self.edges.values():
            if edge_type and e.type != edge_type:
                continue
            if e.source == node_id:
                out.append(e.target)
            elif e.target == node_id:
                out.append(e.source)
        return out


def _claim_id(r: EvidenceRecord) -> str:
    rid = r.id if r.id is not None else onto.slug(r.source)[:12]
    return f"claim:{r.gene}:{rid}"


def _infer_ligands(claim: str, mechanism: str) -> list[str]:
    text = f"{claim} {mechanism}".lower().replace("β", "beta").replace("α", "alpha")
    text = text.replace("-", " ")
    found = []
    mapping = (
        ("beta ionone", "β-ionone"),
        ("alpha ionone", "α-ionone"),
        ("androstenone", "androstenone"),
    )
    for needle, label in mapping:
        if needle in text and label not in found:
            found.append(label)
    return found


def build_graph(
    records: list[EvidenceRecord],
    contradictions: Optional[list[ContradictionPair]] = None,
) -> EvidenceGraph:
    """Materialize an ontology-aligned graph from evidence records."""
    g = EvidenceGraph()
    if not records:
        return g

    contradictions = contradictions if contradictions is not None else detect_contradictions(records)
    contested_sources: set[str] = set()
    for c in contradictions:
        for r in c.suppressive_records + c.promoting_records:
            contested_sources.add(r.source)

    scores = compute_direction_scores(records)

    for r in records:
        weight = score_record(r)
        gene_id = f"receptor:{onto.slug(r.gene)}"
        cancer_id = f"cancer:{onto.slug(r.cancer_type)}"
        model_id = f"model:{onto.slug(r.model_system)}"
        paper_id = f"paper:{onto.slug(r.source)[:48]}"
        claim_id = _claim_id(r)
        direction_id = f"direction:{r.direction}"
        endpoint_label = r.endpoint if getattr(r, "endpoint", "not specified") != "not specified" else None

        status = "contested" if r.source in contested_sources and r.direction in (
            "tumor_suppressive", "tumor_promoting"
        ) else (
            "structural" if r.direction_context != "activation_effect" and r.direction == "neutral"
            else "consensus" if r.direction != "neutral" else "neutral"
        )
        if r.source_type == "patent":
            status = "exploratory"
        if r.direction_context == "genetic_alteration" and "kich" in r.cancer_type.lower():
            status = "exploratory"

        g.add_node(GraphNode(gene_id, "Receptor", r.gene, {"color_hint": onto.STATUS_COLORS.get("consensus")}))
        g.add_node(GraphNode(
            cancer_id, "CancerType", r.cancer_type.replace("_", " "),
            {"color_hint": onto.STATUS_COLORS.get("neutral")},
        ))
        g.add_node(GraphNode(model_id, "ModelSystem", r.model_system))
        g.add_node(GraphNode(paper_id, "Paper", r.source, {"source_type": r.source_type}))
        g.add_node(GraphNode(
            direction_id, "Direction", r.direction.replace("_", " "),
            {
                "color_hint": "green" if r.direction == "tumor_suppressive" else (
                    "red" if r.direction == "tumor_promoting" else "gray"
                ),
            },
        ))
        g.add_node(GraphNode(
            claim_id, "Claim", r.claim[:80] + ("…" if len(r.claim) > 80 else ""),
            {
                "full_claim": r.claim,
                "direction": r.direction,
                "direction_context": r.direction_context,
                "weight": round(weight, 3),
                "source": r.source,
                "status": status,
                "color_hint": onto.STATUS_COLORS.get(status, "gray"),
                "record_id": r.id,
            },
        ))

        g.add_edge(GraphEdge(
            f"e:{claim_id}:receptor", claim_id, gene_id, "about_receptor", weight=weight,
            contested=r.source in contested_sources,
        ))
        g.add_edge(GraphEdge(
            f"e:{claim_id}:cancer", claim_id, cancer_id, "in_cancer", weight=weight,
        ))
        g.add_edge(GraphEdge(
            f"e:{claim_id}:model", claim_id, model_id, "in_model", weight=weight,
        ))
        g.add_edge(GraphEdge(
            f"e:{claim_id}:paper", claim_id, paper_id, "from_paper", weight=weight,
            meta={"source_type": r.source_type},
        ))
        g.add_edge(GraphEdge(
            f"e:{claim_id}:direction", claim_id, direction_id, "asserts_direction",
            weight=weight, contested=r.source in contested_sources,
            meta={"direction_context": r.direction_context},
        ))

        if endpoint_label:
            ep_id = f"endpoint:{onto.slug(endpoint_label)}"
            g.add_node(GraphNode(ep_id, "Endpoint", endpoint_label))
            g.add_edge(GraphEdge(
                f"e:{claim_id}:endpoint", claim_id, ep_id, "measures_endpoint", weight=weight,
            ))

        if r.mechanism and r.mechanism != "not specified":
            mech_id = f"mechanism:{onto.slug(r.mechanism)[:40]}"
            g.add_node(GraphNode(mech_id, "Mechanism", r.mechanism[:60]))
            g.add_edge(GraphEdge(
                f"e:{claim_id}:mech", claim_id, mech_id, "via_mechanism", weight=weight * 0.5,
            ))

        for lig in _infer_ligands(r.claim, r.mechanism):
            lig_id = f"ligand:{onto.slug(lig)}"
            g.add_node(GraphNode(lig_id, "Ligand", lig))
            g.add_edge(GraphEdge(
                f"e:{claim_id}:lig:{onto.slug(lig)}", claim_id, lig_id, "uses_ligand", weight=weight,
            ))

    # Tension edges between opposing activation-effect claims in same gene set
    for c in contradictions:
        for s in c.suppressive_records:
            for p in c.promoting_records:
                sid, pid = _claim_id(s), _claim_id(p)
                if sid in g.nodes and pid in g.nodes:
                    g.add_edge(GraphEdge(
                        f"tension:{sid}:{pid}",
                        sid, pid, "tension_with",
                        weight=min(score_record(s), score_record(p)),
                        contested=True,
                        meta={
                            "same_model_system": c.same_model_system,
                            "same_endpoint": getattr(c, "same_endpoint", True),
                            "hypothesis": c.divergence_hypothesis[:240],
                        },
                    ))

    # Attach score summary on receptor node
    gene = records[0].gene
    gene_id = f"receptor:{onto.slug(gene)}"
    if gene_id in g.nodes:
        g.nodes[gene_id].meta.update({
            "consensus_status": scores.consensus_status,
            "suppressive_mass": round(scores.suppressive.score, 3),
            "promoting_mass": round(scores.promoting.score, 3),
            "elicitation_needed": scores.elicitation_needed,
        })

    return g


def query_subgraph(
    records: list[EvidenceRecord],
    gene: str,
    cancer_type: Optional[str] = None,
    max_hops: int = 2,
) -> dict[str, Any]:
    """
    Search the preseeded evidence graph for a question context.

    Returns all local answers (claims + weights + tensions), not a merged verdict.
    max_hops is reserved for future expansion; current build is claim-neighborhood = 1 hop
    from receptor, which already includes papers/models/endpoints/directions.
    """
    filtered = [r for r in records if r.gene.upper() == gene.upper()]
    if cancer_type:
        filtered = [r for r in filtered if r.cancer_type == cancer_type]

    contradictions = detect_contradictions(filtered)
    scores = compute_direction_scores(filtered)
    graph = build_graph(filtered, contradictions)

    claims = [n.to_dict() for n in graph.nodes.values() if n.type == "Claim"]
    supports = [c for c in claims if c.get("direction") == "tumor_suppressive"]
    opposes = [c for c in claims if c.get("direction") == "tumor_promoting"]
    neutral = [c for c in claims if c.get("direction") == "neutral"]

    return {
        "gene": gene,
        "cancer_type": cancer_type,
        "max_hops": max_hops,
        "open_world_note": (
            "Absence of a claim is not evidence against it; only asserted edges are returned."
        ),
        "counts": {
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "claims": len(claims),
            "tumor_suppressive": len(supports),
            "tumor_promoting": len(opposes),
            "neutral": len(neutral),
        },
        "scores": {
            "tumor_suppressive_mass": round(scores.suppressive.score, 3),
            "tumor_promoting_mass": round(scores.promoting.score, 3),
            "consensus_status": scores.consensus_status,
            "elicitation_needed": scores.elicitation_needed,
            "overall_confidence_label": scores.overall_confidence_label,
        },
        "claims": {
            "tumor_suppressive": supports,
            "tumor_promoting": opposes,
            "neutral_or_context": neutral,
        },
        "tensions": [
            {
                "same_model_system": c.same_model_system,
                "same_endpoint": getattr(c, "same_endpoint", True),
                "deadlock": c.deadlock,
                "divergence_hypothesis": c.divergence_hypothesis,
                "suppressive_sources": [r.source for r in c.suppressive_records],
                "promoting_sources": [r.source for r in c.promoting_records],
            }
            for c in contradictions
        ],
        "tension_map_data": graph.to_dict(),
    }


def tension_map_from_records(records: list[EvidenceRecord]) -> dict:
    """Compatibility helper for server.query_graph tension_map_data."""
    return build_graph(records).to_dict()

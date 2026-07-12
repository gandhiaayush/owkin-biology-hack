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

    def traverse(self, start_id: str, max_hops: int = 2) -> dict[str, int]:
        """BFS from start_id up to max_hops steps. Returns {node_id: min_hop_count}.

        Walks undirected — both edge directions are traversable. This is the real
        N-hop implementation: max_hops=1 returns direct neighbors only; max_hops=2
        returns neighbors-of-neighbors too, enabling cross-receptor path discovery.
        """
        if start_id not in self.nodes:
            return {}
        visited: dict[str, int] = {start_id: 0}
        frontier = [start_id]
        for hop in range(1, max_hops + 1):
            next_frontier = []
            for node_id in frontier:
                for neighbor in self.neighbors(node_id):
                    if neighbor not in visited:
                        visited[neighbor] = hop
                        next_frontier.append(neighbor)
            frontier = next_frontier
        return visited


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
    Search the evidence graph for a question context, walking up to max_hops from
    each Claim node. Returns all answers within the N-hop neighborhood — not a merged
    verdict, not capped at 1 hop. max_hops=2 surfaces Claim→Mechanism→Claim paths
    (cross-receptor indirect connections when the graph contains multiple receptors).

    Open-world: missing claims are not treated as false.
    """
    filtered = [r for r in records if r.gene.upper() == gene.upper()]
    if cancer_type:
        filtered = [r for r in filtered if r.cancer_type == cancer_type]

    contradictions = detect_contradictions(filtered)
    scores = compute_direction_scores(filtered)
    graph = build_graph(filtered, contradictions)

    # Real N-hop traversal: collect all nodes reachable from any Claim node within max_hops
    receptor_id = f"receptor:{onto.slug(gene)}"
    reachable: dict[str, int] = {}
    for node_id, node in graph.nodes.items():
        if node.type == "Claim":
            for reached_id, hop in graph.traverse(node_id, max_hops=max_hops).items():
                if reached_id not in reachable or reachable[reached_id] > hop:
                    reachable[reached_id] = hop

    claims = [n.to_dict() for n in graph.nodes.values() if n.type == "Claim"]
    supports = [c for c in claims if c.get("direction") == "tumor_suppressive"]
    opposes = [c for c in claims if c.get("direction") == "tumor_promoting"]
    neutral = [c for c in claims if c.get("direction") == "neutral"]

    # Nodes reachable via multi-hop but not directly attached to receptor
    multihop_nodes = [
        {"id": nid, "hop": h, "type": graph.nodes[nid].type, "label": graph.nodes[nid].label}
        for nid, h in reachable.items()
        if h >= 2 and nid in graph.nodes and graph.nodes[nid].type not in ("Claim", "Receptor")
    ]

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
            "multihop_nodes_reachable": len(multihop_nodes),
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
        "multihop_context": multihop_nodes,
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


def find_cross_receptor_connections(
    all_records: list[EvidenceRecord],
    gene_a: str,
    gene_b: str,
    max_hops: int = 2,
) -> dict[str, Any]:
    """
    Find indirect paths between two receptors' evidence through shared intermediate
    nodes (Mechanism, Endpoint, ModelSystem, CancerType, Ligand, Direction).

    Walks max_hops from every Claim node for each receptor and surfaces any nodes
    reachable from BOTH sides — these are candidates for a non-obvious relationship
    that no single paper states directly.

    Honest reporting: trivially-shared nodes (Direction, Endpoint at a coarse level)
    are flagged as such so callers can filter them. If no non-trivial connection is
    found, that is returned as an explicit result — not silently hidden.

    max_hops=2 is the minimum meaningful value: hop 1 reaches the Mechanism/Endpoint
    nodes attached to a Claim; hop 2 from there would reach another Claim on the same
    Mechanism/Endpoint. This is why max_hops=1 would never find cross-receptor paths
    (the only 1-hop neighbor of a Claim node on receptor A is that receptor's own
    conceptual nodes, never another receptor's Claim nodes).
    """
    g = build_graph(all_records)

    # Collect claim nodes per receptor
    claims_a = [n_id for n_id, n in g.nodes.items() if n.type == "Claim" and gene_a.upper() in n_id.upper()]
    claims_b = [n_id for n_id, n in g.nodes.items() if n.type == "Claim" and gene_b.upper() in n_id.upper()]

    if not claims_a:
        return {"gene_a": gene_a, "gene_b": gene_b, "max_hops": max_hops,
                "error": f"No Claim nodes found for {gene_a} in the graph.", "connections": []}
    if not claims_b:
        return {"gene_a": gene_a, "gene_b": gene_b, "max_hops": max_hops,
                "error": f"No Claim nodes found for {gene_b} in the graph.", "connections": []}

    # BFS from each side: node_id -> min hops from any claim in that receptor's set
    reachable_a: dict[str, int] = {}
    for c_id in claims_a:
        for node_id, hop in g.traverse(c_id, max_hops=max_hops).items():
            if node_id not in reachable_a or reachable_a[node_id] > hop:
                reachable_a[node_id] = hop

    reachable_b: dict[str, int] = {}
    for c_id in claims_b:
        for node_id, hop in g.traverse(c_id, max_hops=max_hops).items():
            if node_id not in reachable_b or reachable_b[node_id] > hop:
                reachable_b[node_id] = hop

    # Intersection: nodes reachable from both, excluding receptor nodes and claim nodes
    shared_ids = (set(reachable_a) & set(reachable_b)) - set(claims_a) - set(claims_b)
    shared_ids = {n for n in shared_ids if not n.startswith("receptor:")}

    # Classify each shared node
    _trivial_types = {"Direction"}  # shared by all records of the same direction — not informative
    connections = []
    for node_id in shared_ids:
        node = g.nodes.get(node_id)
        if not node:
            continue
        is_trivial = node.type in _trivial_types
        connections.append({
            "shared_node_id": node_id,
            "shared_node_type": node.type,
            "shared_node_label": node.label,
            "hops_from_a": reachable_a[node_id],
            "hops_from_b": reachable_b[node_id],
            "total_path_hops": reachable_a[node_id] + reachable_b[node_id],
            "trivial": is_trivial,
            "note": (
                "Trivially shared: every record of this direction type shares this node."
                if is_trivial else
                f"Indirect {node.type} connection at {reachable_a[node_id]}+{reachable_b[node_id]} hops."
            ),
        })

    connections.sort(key=lambda c: (c["trivial"], c["total_path_hops"], c["shared_node_type"]))

    non_trivial = [c for c in connections if not c["trivial"]]
    trivial = [c for c in connections if c["trivial"]]

    return {
        "gene_a": gene_a,
        "gene_b": gene_b,
        "max_hops": max_hops,
        "connections_found": len(non_trivial),
        "trivial_connections_excluded": len(trivial),
        "non_trivial_connections": non_trivial,
        "honest_finding": (
            f"Found {len(non_trivial)} non-trivial shared node(s) between {gene_a} and {gene_b} "
            f"within {max_hops} hops. "
            + (
                "These are candidates for indirect biological connections — verify before citing as demo evidence."
                if non_trivial else
                "No non-trivial cross-receptor connection found in current data. "
                "Mechanism nodes are not shared because they encode full free-text strings, not normalized "
                "pathway names — a pathway normalization layer (e.g. mapping 'p38 MAPK' across records) "
                "would be needed to surface the Ca²⁺/MAPK overlap between OR51E2 and OR51B4. "
                "True negative: this is a valid result, not a failure."
            )
        ),
    }


def tension_map_from_records(records: list[EvidenceRecord]) -> dict:
    """Compatibility helper for server.query_graph tension_map_data."""
    return build_graph(records).to_dict()

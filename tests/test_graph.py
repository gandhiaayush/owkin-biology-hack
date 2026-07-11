"""Tests for ontology-aligned evidence graph build + query."""
import os

from discordance import (
    init_db,
    insert_record,
    get_records,
    EvidenceRecord,
    build_graph,
    query_subgraph,
    detect_contradictions,
)


def _rec(**kwargs) -> EvidenceRecord:
    defaults = dict(
        source="Test et al. 2024",
        source_type="primary_study",
        claim="test claim about β-ionone",
        mechanism="MAPK",
        direction="tumor_suppressive",
        direction_context="activation_effect",
        endpoint="proliferation",
        cancer_type="prostate_cancer",
        model_system="LNCaP",
        gene="OR51E2",
    )
    defaults.update(kwargs)
    return EvidenceRecord(**defaults)


def test_build_graph_has_ontology_node_types(tmp_path):
    os.environ["DISCORDANCE_DB"] = str(tmp_path / "g.db")
    init_db(tmp_path / "g.db")
    insert_record(_rec(source="Neuhaus 2009", direction="tumor_suppressive", endpoint="proliferation"))
    insert_record(_rec(source="Sanz 2014", direction="tumor_promoting", endpoint="invasiveness", claim="promotes invasiveness"))
    records = get_records("OR51E2", "prostate_cancer")
    g = build_graph(records)
    types = {n.type for n in g.nodes.values()}
    assert "Receptor" in types
    assert "Claim" in types
    assert "Paper" in types
    assert "Direction" in types
    assert "Endpoint" in types
    assert "Ligand" in types  # inferred from β-ionone in claim
    edge_types = {e.type for e in g.edges.values()}
    assert "about_receptor" in edge_types
    assert "asserts_direction" in edge_types
    assert "tension_with" in edge_types


def test_query_subgraph_returns_both_sides_not_merged(tmp_path):
    os.environ["DISCORDANCE_DB"] = str(tmp_path / "g.db")
    init_db(tmp_path / "g.db")
    insert_record(_rec(source="A", direction="tumor_suppressive"))
    insert_record(_rec(source="B", direction="tumor_promoting", endpoint="invasiveness"))
    records = get_records("OR51E2", "prostate_cancer")
    out = query_subgraph(records, gene="OR51E2", cancer_type="prostate_cancer")
    assert out["counts"]["tumor_suppressive"] >= 1
    assert out["counts"]["tumor_promoting"] >= 1
    assert "open_world_note" in out
    assert out["tension_map_data"]["nodes"]
    assert out["tension_map_data"]["edges"]
    assert len(out["tensions"]) == 1


def test_different_endpoints_soften_contradiction(tmp_path):
    os.environ["DISCORDANCE_DB"] = str(tmp_path / "g.db")
    init_db(tmp_path / "g.db")
    insert_record(_rec(source="Neuhaus", direction="tumor_suppressive", endpoint="proliferation"))
    insert_record(_rec(source="Sanz", direction="tumor_promoting", endpoint="invasiveness"))
    records = get_records("OR51E2", "prostate_cancer")
    c = detect_contradictions(records)[0]
    assert c.same_endpoint is False
    assert "DIFFERENT ENDPOINTS" in c.divergence_hypothesis


def test_seed_records_graph_or51e2(tmp_path):
    os.environ["DISCORDANCE_DB"] = str(tmp_path / "g.db")
    init_db(tmp_path / "g.db")
    from seed_data import SEED_RECORDS
    for r in SEED_RECORDS:
        insert_record(r)
    records = get_records("OR51E2", "prostate_cancer")
    out = query_subgraph(records, "OR51E2", "prostate_cancer")
    assert out["counts"]["claims"] == 4
    assert out["scores"]["consensus_status"] == "contested"
    assert any(e["type"] == "tension_with" for e in out["tension_map_data"]["edges"])

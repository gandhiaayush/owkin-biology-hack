"""Tests for OWL/Turtle ontology export."""
import os
from pathlib import Path

from discordance import init_db, insert_record, get_records
from discordance.owl_export import export_ontology_turtle, write_ontology_file
from discordance import ontology as onto
from seed_data import SEED_RECORDS


def test_or_subclasses_defined():
    assert "ClassA_OR" in onto.OR_SUBCLASSES["Receptor"]
    assert "BiasedAgonist" in onto.OR_SUBCLASSES["Ligand"]
    assert "ActivationEffectClaim" in onto.OR_SUBCLASSES["Claim"]


def test_classify_neuhaus_record():
    r = SEED_RECORDS[0]
    assert onto.classify_claim_subtype(r) == "ActivationEffectClaim"
    assert onto.classify_model_subtype(r.model_system) == "EndogenousReceptorModel"
    assert onto.classify_endpoint_subtype(r.endpoint) == "ProliferationEndpoint"


def test_export_contains_or_classes_and_properties():
    ttl = export_ontology_turtle()
    assert ":ClassA_OR a owl:Class" in ttl
    assert ":BiasedAgonist a owl:Class" in ttl
    assert ":tension_with a owl:ObjectProperty" in ttl
    assert ":PatentDocument a owl:Class" in ttl


def test_export_with_evidence_individuals(tmp_path):
    os.environ["DISCORDANCE_DB"] = str(tmp_path / "owl.db")
    init_db(tmp_path / "owl.db")
    for r in SEED_RECORDS:
        insert_record(r)
    records = get_records("OR51E2", "prostate_cancer")
    ttl = export_ontology_turtle(records)
    assert ":receptor_or51e2" in ttl
    assert ":uses_ligand" in ttl
    assert "Neuhaus" in ttl or "neuhaus" in ttl.lower()


def test_write_ontology_file(tmp_path):
    path = write_ontology_file(tmp_path / "discordance.ttl")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Discordance OR-in-Cancer Evidence Ontology" in text

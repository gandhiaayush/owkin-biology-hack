import pytest
from pathlib import Path
import tempfile
import os

from discordance import init_db, insert_record, get_records, detect_contradictions, EvidenceRecord


@pytest.fixture()
def db(tmp_path):
    db_file = tmp_path / "test_evidence.db"
    init_db(db_file)
    yield db_file


def _make_record(**kwargs) -> EvidenceRecord:
    defaults = dict(
        source="Test et al. 2024",
        source_type="primary_study",
        claim="test claim",
        mechanism="test mechanism",
        direction="tumor_suppressive",
        direction_context="activation_effect",
        cancer_type="prostate_cancer",
        model_system="LNCaP",
        gene="OR51E2",
    )
    defaults.update(kwargs)
    return EvidenceRecord(**defaults)


def test_no_contradiction_single_direction(db):
    os.environ["DISCORDANCE_DB"] = str(db)
    insert_record(_make_record(direction="tumor_suppressive"))
    records = get_records("OR51E2", "prostate_cancer")
    contradictions = detect_contradictions(records)
    assert contradictions == []


def test_contradiction_detected_opposing_directions(db):
    os.environ["DISCORDANCE_DB"] = str(db)
    insert_record(_make_record(source="Suppressive Study 2009", direction="tumor_suppressive"))
    insert_record(_make_record(source="Promoting Study 2014", direction="tumor_promoting"))
    records = get_records("OR51E2", "prostate_cancer")
    contradictions = detect_contradictions(records)
    assert len(contradictions) == 1
    c = contradictions[0]
    assert len(c.suppressive_records) == 1
    assert len(c.promoting_records) == 1


def test_same_model_system_detected(db):
    os.environ["DISCORDANCE_DB"] = str(db)
    # Both are LNCaP — should detect same_model_system
    insert_record(_make_record(source="Neuhaus 2009", direction="tumor_suppressive", model_system="LNCaP"))
    insert_record(_make_record(source="Sanz 2014", direction="tumor_promoting", model_system="LNCaP cells"))
    records = get_records("OR51E2", "prostate_cancer")
    contradictions = detect_contradictions(records)
    assert contradictions[0].same_model_system is True


def test_different_model_system_not_same(db):
    os.environ["DISCORDANCE_DB"] = str(db)
    insert_record(_make_record(source="Cell study", direction="tumor_suppressive", model_system="LNCaP"))
    insert_record(_make_record(source="Animal study", direction="tumor_promoting", model_system="xenograft"))
    records = get_records("OR51E2", "prostate_cancer")
    contradictions = detect_contradictions(records)
    assert contradictions[0].same_model_system is False


def test_deadlock_detected_on_balanced_evidence(db):
    os.environ["DISCORDANCE_DB"] = str(db)
    insert_record(_make_record(source="Suppressive A", direction="tumor_suppressive"))
    insert_record(_make_record(source="Promoting B", direction="tumor_promoting", model_system="xenograft"))
    records = get_records("OR51E2", "prostate_cancer")
    contradictions = detect_contradictions(records)
    assert contradictions[0].deadlock is True


def test_direction_context_filter_prevents_false_contradiction(db):
    os.environ["DISCORDANCE_DB"] = str(db)
    # A TCGA expression record (expression_pattern) should NOT collide with an activation_effect record
    insert_record(_make_record(
        source="Neuhaus functional", direction="tumor_suppressive",
        direction_context="activation_effect",
    ))
    insert_record(_make_record(
        source="TCGA KICH amplification", direction="tumor_promoting",
        direction_context="expression_pattern",
        model_system="TCGA-KICH",
    ))
    records = get_records("OR51E2", "prostate_cancer")
    # With default filter (activation_effect only), no contradiction
    contradictions = detect_contradictions(records, direction_context_filter="activation_effect")
    assert contradictions == []


def test_four_seed_records_produce_one_contradiction(db):
    """Integration: the 4 real OR51E2 records produce exactly 1 contradiction."""
    os.environ["DISCORDANCE_DB"] = str(db)
    from seed_data import SEED_RECORDS
    for r in SEED_RECORDS:
        insert_record(r)
    records = get_records("OR51E2", "prostate_cancer")
    assert len(records) == 4
    contradictions = detect_contradictions(records)
    assert len(contradictions) == 1
    c = contradictions[0]
    assert len(c.suppressive_records) == 2
    assert len(c.promoting_records) == 2
    assert c.deadlock is True

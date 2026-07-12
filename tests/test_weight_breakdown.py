"""
Task 3: Tests confirming weight breakdown fields sum to the reported total mass.

Per the prompt: "Tests required: a test confirming the weight breakdown fields sum
to the reported total mass (catches drift between the display numbers and the real
computation)."
"""
import os
import pytest

from discordance import init_db, insert_record, get_records, EvidenceRecord
from discordance.demo_contract import to_demo_contract
from discordance.scoring import score_record, score_record_with_reason
from seed_data import SEED_RECORDS


@pytest.fixture
def db(tmp_path):
    os.environ["DISCORDANCE_DB"] = str(tmp_path / "test.db")
    init_db(tmp_path / "test.db")
    for r in SEED_RECORDS:
        insert_record(r)
    yield


def test_weight_breakdown_sums_match_total_mass(db):
    """
    The individual weight contributions in weight_breakdown must sum to the
    reported tumor_suppressive_mass and tumor_promoting_mass. Any drift between
    the display numbers and the real computation should fail here.
    """
    records = get_records("OR51E2", "prostate_cancer")
    contract = to_demo_contract(records, "OR51E2", "prostate_cancer")

    scores = contract["scores"]
    breakdown = scores["weight_breakdown"]

    sup_reported = scores["tumor_suppressive_mass"]
    pro_reported = scores["tumor_promoting_mass"]

    sup_computed = round(sum(e["weight"] for e in breakdown["tumor_suppressive"]), 3)
    pro_computed = round(sum(e["weight"] for e in breakdown["tumor_promoting"]), 3)

    assert sup_computed == sup_reported, (
        f"Suppressive breakdown sum {sup_computed} != reported mass {sup_reported}"
    )
    assert pro_computed == pro_reported, (
        f"Promoting breakdown sum {pro_computed} != reported mass {pro_reported}"
    )


def test_each_evidence_entry_has_weight_reason(db):
    """Every evidence entry must carry a weight_reason field explaining its score."""
    records = get_records("OR51E2", "prostate_cancer")
    contract = to_demo_contract(records, "OR51E2", "prostate_cancer")

    all_entries = (
        contract["tumor_suppressive"]
        + contract["tumor_promoting"]
        + contract["consensus"]
        + contract["exploratory"]
    )
    for entry in all_entries:
        assert "weight_reason" in entry, f"Missing weight_reason in entry {entry.get('id')}"
        assert isinstance(entry["weight_reason"], str)
        assert len(entry["weight_reason"]) > 0


def test_weight_reason_matches_actual_score():
    """score_record_with_reason() must return the same score as score_record()."""
    r = EvidenceRecord(
        source="Test et al. 2024",
        source_type="primary_study",
        claim="test",
        gene="OR51E2",
        direction="tumor_suppressive",
        cancer_type="prostate_cancer",
        model_system="LNCaP",
        independent_replications=2,
        sample_size=100,
    )
    score = score_record(r)
    score_with_reason, reason = score_record_with_reason(r)
    assert abs(score - score_with_reason) < 1e-9, "score_record and score_record_with_reason disagree"
    assert str(round(score, 3)) in reason, "Reason string should mention the computed score"


def test_weight_breakdown_present_even_with_no_breakdown_records(db):
    """weight_breakdown is always present, even for one-sided evidence."""
    r = EvidenceRecord(
        source="Only suppressive et al. 2024",
        source_type="primary_study",
        claim="suppresses proliferation",
        gene="ORTEST",
        direction="tumor_suppressive",
        cancer_type="test_cancer",
        model_system="test_model",
    )
    records = [r]
    contract = to_demo_contract(records, "ORTEST", "test_cancer")
    assert "weight_breakdown" in contract["scores"]
    assert "tumor_suppressive" in contract["scores"]["weight_breakdown"]
    assert "tumor_promoting" in contract["scores"]["weight_breakdown"]
    assert contract["scores"]["weight_breakdown"]["tumor_promoting"] == []

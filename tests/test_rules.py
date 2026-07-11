import pytest
from discordance import generate_rules, EvidenceRecord
from seed_data import SEED_RECORDS


def _make_record(**kwargs) -> EvidenceRecord:
    defaults = dict(
        source="Test et al. 2024",
        source_type="primary_study",
        claim="test claim",
        mechanism="MAPK activation",
        direction="tumor_suppressive",
        direction_context="activation_effect",
        cancer_type="prostate_cancer",
        model_system="LNCaP",
        gene="OR51E2",
    )
    defaults.update(kwargs)
    return EvidenceRecord(**defaults)


def test_contested_produces_two_rules():
    """When evidence is split, we get one rule per direction."""
    rules = generate_rules(SEED_RECORDS)
    directions = {r.direction for r in rules}
    assert "tumor_suppressive" in directions
    assert "tumor_promoting" in directions
    assert all(r.contested for r in rules)


def test_rules_never_claim_universal_truth():
    """Single-source rules must contain qualifying language."""
    record = _make_record()
    rules = generate_rules([record])
    assert len(rules) == 1
    assert "may" in rules[0].claim or "hypothesis" in rules[0].claim or "single source" in rules[0].claim


def test_no_rules_for_empty_records():
    rules = generate_rules([])
    assert rules == []


def test_single_direction_not_contested():
    records = [
        _make_record(source="A", direction="tumor_suppressive"),
        _make_record(source="B", direction="tumor_suppressive", model_system="xenograft"),
    ]
    rules = generate_rules(records)
    assert len(rules) == 1
    assert rules[0].contested is False
    assert rules[0].direction == "tumor_suppressive"


def test_sources_present_in_rules():
    rules = generate_rules(SEED_RECORDS)
    for rule in rules:
        assert len(rule.sources) > 0

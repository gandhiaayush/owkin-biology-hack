import os
import pytest
from pathlib import Path
from discordance import (
    init_db, insert_record, get_records, compute_direction_scores,
    score_record, get_confidence_label, EvidenceRecord,
)
from discordance.scoring import score_record_with_reason


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


def test_primary_study_outweighs_patent():
    primary = _make_record(source_type="primary_study")
    patent = _make_record(source_type="patent")
    assert score_record(primary) > score_record(patent)


def test_replication_increases_score():
    no_rep = _make_record(independent_replications=0)
    replicated = _make_record(independent_replications=3)
    assert score_record(replicated) > score_record(no_rep)


def test_unknown_replication_penalized_vs_confirmed_zero():
    unknown = _make_record(independent_replications=None)
    confirmed_zero = _make_record(independent_replications=0)
    assert score_record(confirmed_zero) >= score_record(unknown)


def test_confidence_label_single_unreplicated():
    record = _make_record(independent_replications=None)
    label = get_confidence_label([record])
    assert "N=1" in label
    assert "hypothesis" in label


def test_confidence_label_converging_evidence():
    records = [
        _make_record(source="A 2020", independent_replications=None),
        _make_record(source="B 2021", independent_replications=None),
    ]
    label = get_confidence_label(records)
    assert "N=2" in label


def test_elicitation_fires_on_balanced_evidence():
    """Four seed records should produce a deadlocked score where elicitation is needed."""
    from seed_data import SEED_RECORDS
    scores = compute_direction_scores(SEED_RECORDS)
    assert scores.consensus_status == "contested"
    assert scores.elicitation_needed is True


def test_primary_studies_differentiated_by_quality_not_only_source_type():
    """Two primary studies with different rigor should not collapse to identical weights."""
    cell_line = _make_record(
        source="Cell line 2010",
        model_system="generic cell line",
        endpoint="not specified",
        mechanism="not specified",
    )
    xenograft = _make_record(
        source="Xenograft 2021",
        model_system="xenograft, mouse",
        endpoint="tumor_growth",
        mechanism="NF-kB pathway",
        claim="PSGR promotes xenograft tumor growth",
    )
    assert score_record(xenograft) > score_record(cell_line)
    assert score_record(xenograft) != score_record(cell_line)


def test_quality_bonuses_visible_in_reason_string():
    r = _make_record(
        source="Rodriguez et al. 2014",
        model_system="xenograft",
        endpoint="tumor_growth",
        mechanism="NF-kB pathway",
    )
    _, reason = score_record_with_reason(r)
    assert "in vivo/xenograft" in reason
    assert "endpoint=tumor_growth" in reason
    assert "mechanism specified" in reason


def test_patents_not_in_literature_consensus():
    records = [
        _make_record(source="Lit study", direction="tumor_suppressive", source_type="primary_study"),
        _make_record(source="Patent Corp", direction="tumor_promoting", source_type="patent"),
    ]
    scores = compute_direction_scores(records)
    # Patent should not count toward promoting score
    assert scores.promoting.score == 0.0
    assert scores.commercial_interest_score > 0.0


def test_consensus_suppressive_when_only_one_direction():
    records = [
        _make_record(source="Study A", direction="tumor_suppressive"),
        _make_record(source="Study B", direction="tumor_suppressive", model_system="xenograft"),
    ]
    scores = compute_direction_scores(records)
    assert scores.consensus_status == "consensus_suppressive"
    assert scores.elicitation_needed is False

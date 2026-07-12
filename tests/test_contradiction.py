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
    assert len(c.suppressive_records) == 1
    assert len(c.promoting_records) == 1
    assert c.deadlock is True


def test_confirmed_different_endpoints_softens_framing(db):
    """
    Neuhaus (proliferation) vs. Sanz (invasiveness): both are activation_effect,
    opposing direction, but endpoint is positively confirmed to differ. The
    hypothesis text should say so explicitly rather than reading as a flat
    same-claim contradiction, and same_endpoint should be False.
    """
    os.environ["DISCORDANCE_DB"] = str(db)
    insert_record(_make_record(
        source="Neuhaus et al. 2009", direction="tumor_suppressive",
        endpoint="proliferation",
    ))
    insert_record(_make_record(
        source="Sanz et al. 2014", direction="tumor_promoting",
        endpoint="invasiveness",
    ))
    records = get_records("OR51E2", "prostate_cancer")
    contradictions = detect_contradictions(records)
    assert len(contradictions) == 1
    c = contradictions[0]
    assert c.same_endpoint is False
    assert "CONFIRMED DIFFERENT ENDPOINTS" in c.divergence_hypothesis
    assert "proliferation" in c.divergence_hypothesis
    assert "invasiveness" in c.divergence_hypothesis


def test_unknown_endpoint_does_not_falsely_soften_framing(db):
    """
    When endpoint isn't specified on either/both records, we must NOT assume
    they differ -- that would understate a genuine contradiction based on
    missing data rather than a positive finding. same_endpoint defaults True
    (flat contradiction framing) until endpoints are positively confirmed distinct.
    """
    os.environ["DISCORDANCE_DB"] = str(db)
    insert_record(_make_record(source="Study A et al. 2020", direction="tumor_suppressive"))
    insert_record(_make_record(source="Study B et al. 2021", direction="tumor_promoting", model_system="xenograft"))
    records = get_records("OR51E2", "prostate_cancer")
    contradictions = detect_contradictions(records)
    assert contradictions[0].same_endpoint is True
    assert "CONFIRMED DIFFERENT ENDPOINTS" not in contradictions[0].divergence_hypothesis


def test_database_derived_records_not_over_collapsed(db):
    """
    Regression test: database_derived sources (TCGA API pulls) don't follow an
    'Author Year' citation format. Applying the citation-key normalization to
    them collapsed genuinely distinct cohort-specific queries (e.g. TCGA-KICH
    vs TCGA-PRAD CNV pulls) into false duplicates, silently dropping the KICH
    exploratory finding. Confirm distinct database pulls are kept distinct.
    """
    os.environ["DISCORDANCE_DB"] = str(db)
    general = insert_record(_make_record(
        source="GDC API cnvs endpoint, gene ENSG00000167332, live pull",
        source_type="database_derived", direction="neutral",
        direction_context="genetic_alteration", model_system="TCGA pan-cancer",
    ))
    kich = insert_record(_make_record(
        source="GDC API cnvs endpoint, gene ENSG00000167332, TCGA-KICH cohort, live pull",
        source_type="database_derived", direction="neutral",
        direction_context="genetic_alteration", model_system="TCGA-KICH",
    ))
    prad = insert_record(_make_record(
        source="GDC API cnvs endpoint, gene ENSG00000167332, TCGA-PRAD cohort, live pull",
        source_type="database_derived", direction="neutral",
        direction_context="genetic_alteration", model_system="TCGA-PRAD",
    ))
    assert general is not None
    assert kich is not None
    assert prad is not None
    assert len({general, kich, prad}) == 3  # all distinct row ids, none dropped as duplicate


def test_citation_key_dedup_collapses_differently_formatted_same_paper(db):
    """
    Regression test for the seed_data.py / JSON-loader duplicate bug: the same
    paper cited two different ways (short form vs. full author list) must be
    recognized as the same source and not double-inserted.
    """
    os.environ["DISCORDANCE_DB"] = str(db)
    short_form = insert_record(_make_record(
        source="Neuhaus et al. 2009, J Biol Chem", direction="tumor_suppressive",
    ))
    long_form = insert_record(_make_record(
        source=(
            "Neuhaus EM, Zhang W, Gelis L, Deng Y, Noldus J, Hatt H (2009). "
            '"Activation of an olfactory receptor inhibits proliferation of '
            'prostate cancer cells." J Biol Chem 284(24):16218-16225.'
        ),
        direction="tumor_suppressive",
    ))
    assert short_form is not None
    assert long_form is None  # recognized as a duplicate of the same paper
    records = get_records("OR51E2", "prostate_cancer")
    assert len(records) == 1

"""
Tests for discordance/scorecard.py -- the end-of-query, per-source scorecard
output. Verifies: every scorecard field is populated meaningfully (not a
placeholder), contested sources are correctly flagged and ranked first,
weak/unreplicated/preliminary sources get real limitations, and the query's
endpoint is used to distinguish "directly answers this" from "adjacent
context" sources.
"""
import pytest

from discordance import EvidenceRecord, compute_direction_scores, detect_contradictions
from discordance.scorecard import build_scorecards, infer_query_endpoint, scorecard_to_dict
from seed_data import SEED_RECORDS


def _make_record(**kwargs) -> EvidenceRecord:
    defaults = dict(
        source="Test et al. 2024",
        source_type="primary_study",
        claim="test claim",
        mechanism="MAPK activation",
        direction="tumor_suppressive",
        direction_context="activation_effect",
        endpoint="proliferation",
        cancer_type="prostate_cancer",
        model_system="LNCaP",
        gene="OR51E2",
    )
    defaults.update(kwargs)
    return EvidenceRecord(**defaults)


def _build(records, query_endpoint=None):
    scores = compute_direction_scores(records)
    contradictions = detect_contradictions(records)
    return build_scorecards(records, scores, contradictions, query_endpoint=query_endpoint)


def test_every_scorecard_has_populated_fields():
    """No scorecard should have empty strengths/limitations/best_for/selection_reason --
    build_scorecards must always produce a real assessment, never a blank stub."""
    cards = _build(SEED_RECORDS)
    assert cards
    for c in cards:
        assert c.strengths and all(isinstance(s, str) and s for s in c.strengths)
        assert c.limitations and all(isinstance(s, str) and s for s in c.limitations)
        assert c.best_for
        assert c.selection_reason
        assert c.weight_reason


def test_contested_sources_ranked_first():
    """SEED_RECORDS is a genuine 2-vs-2 contested split -- every scorecard should be
    flagged contested, and contested cards must sort ahead of non-contested ones."""
    cards = _build(SEED_RECORDS)
    assert all(c.contested for c in cards)

    contested_flags = [c.contested for c in cards]
    # once a False appears, no True should follow (contested-first invariant)
    seen_false = False
    for flag in contested_flags:
        if not flag:
            seen_false = True
        assert not (seen_false and flag)


def test_unreplicated_source_flagged_as_limitation():
    r = _make_record(source="Solo 2020", independent_replications=None, sample_size=None)
    cards = _build([r])
    assert len(cards) == 1
    assert any("unreplicated" in lim.lower() for lim in cards[0].limitations)
    assert any("sample size not reported" in lim.lower() for lim in cards[0].limitations)


def test_strongly_replicated_source_flagged_as_strength():
    r = _make_record(source="Strong 2020", independent_replications=5, sample_size=200)
    cards = _build([r])
    assert any("independently replicated" in s.lower() for s in cards[0].strengths)
    assert any("reasonably powered" in s.lower() for s in cards[0].strengths)


def test_preliminary_source_flagged_distinctly_from_primary_study():
    prelim = _make_record(source="Auto-extracted 2024", source_type="preliminary")
    primary = _make_record(source="Verified 2024", source_type="primary_study")
    cards = _build([prelim, primary])

    prelim_card = next(c for c in cards if c.source == "Auto-extracted 2024")
    primary_card = next(c for c in cards if c.source == "Verified 2024")

    assert any("not yet manually verified" in lim.lower() for lim in prelim_card.limitations)
    assert not any("not yet manually verified" in lim.lower() for lim in primary_card.limitations)
    assert any("peer-reviewed" in s.lower() for s in primary_card.strengths)


def test_patent_flagged_as_commercial_not_biological_validation():
    r = _make_record(source="US1234567", source_type="patent", direction="tumor_promoting")
    cards = _build([r])
    assert any("commercial" in lim.lower() for lim in cards[0].limitations)
    assert "commercial" in cards[0].best_for.lower()


def test_query_endpoint_distinguishes_direct_answer_from_adjacent_context():
    """A source measuring 'invasiveness' should be flagged as directly answering
    an invasiveness query, but only adjacent context for a proliferation query."""
    r = _make_record(source="Invasion 2020", endpoint="invasiveness", direction="tumor_promoting")

    direct_cards = _build([r], query_endpoint="invasiveness")
    assert "directly answers" in direct_cards[0].best_for.lower()

    adjacent_cards = _build([r], query_endpoint="proliferation")
    assert "related but distinct" in adjacent_cards[0].best_for.lower()


def test_infer_query_endpoint_matches_known_terms():
    assert infer_query_endpoint("Does it affect proliferation in LNCaP cells?") == "proliferation"
    assert infer_query_endpoint("What about invasion of prostate cells?") == "invasiveness"
    assert infer_query_endpoint("Tell me everything about OR51E2") is None


def test_scorecard_to_dict_round_trips_all_fields():
    cards = _build(SEED_RECORDS)
    d = scorecard_to_dict(cards[0])
    for key in (
        "source", "source_type", "direction", "weight", "weight_reason",
        "strengths", "limitations", "best_for", "selection_reason",
        "contested", "endpoint",
    ):
        assert key in d


def test_in_vivo_and_specificity_control_detected_in_strengths():
    r = _make_record(
        source="Xenograft 2022",
        model_system="xenograft, mouse",
        claim="siRNA knockdown of the receptor abolished the effect, confirming specificity",
    )
    cards = _build([r])
    strengths_text = " ".join(cards[0].strengths).lower()
    assert "in vivo" in strengths_text
    assert "specificity control" in strengths_text


def test_no_contradiction_ranks_by_weight_when_not_contested():
    """A single-direction, non-contested evidence set should still rank
    higher-weight sources first among themselves."""
    weak = _make_record(source="Weak 2020", independent_replications=None, sample_size=None)
    strong = _make_record(source="Strong 2020", independent_replications=5, sample_size=200)
    cards = _build([weak, strong])
    assert not any(c.contested for c in cards)
    assert cards[0].source == "Strong 2020"
    assert cards[0].weight >= cards[1].weight

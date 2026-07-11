"""
Regression tests for discordance/demo_contract.py.

Person C's frontend (demos/or51e2-tension-map.html, demos/baseline-vs-augmented.html)
was built and tested against demos/mocks/or51e2-query.json's exact shape, not against
query_graph()'s native return shape. These tests exist to catch drift between the two
early -- if someone changes to_demo_contract()'s output shape without updating the
demo pages (or vice versa), this should fail loudly instead of silently breaking the
live demo.
"""
import json
import os
from pathlib import Path

import pytest

from discordance import init_db, insert_record, get_records
from discordance.demo_contract import to_demo_contract
from seed_data import SEED_RECORDS

MOCK_PATH = Path(__file__).parent.parent / "demos" / "mocks" / "or51e2-query.json"


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    os.environ["DISCORDANCE_DB"] = str(path)
    init_db(path)
    yield path


def test_top_level_keys_match_frozen_mock(db):
    """
    The exact set of top-level keys Person C's frontend destructures must be
    present -- not a superset or subset. This is the check that would have
    caught the original query_graph-vs-mock shape mismatch immediately.
    """
    for r in SEED_RECORDS:
        insert_record(r)
    records = get_records("OR51E2", "prostate_cancer")
    contract = to_demo_contract(records, "OR51E2", "prostate_cancer")

    mock = json.loads(MOCK_PATH.read_text())
    assert set(contract.keys()) == set(mock.keys())


def test_tool_name_matches_documented_name(db):
    """
    demos/KPRO_MCP_HOOKUP.md and the mock both call this tool `query_or_graph`.
    The registered MCP tool must use this exact name or organizer/Person C
    instructions calling it by name will fail with 'tool not found'.
    """
    contract = to_demo_contract([], "OR51E2", "prostate_cancer")
    assert contract["tool"] == "query_or_graph"


def test_adjudication_shape_present_even_without_elicitation_support(db):
    """
    KPRO_MCP_HOOKUP.md's 'Elicitation note' explicitly requires: always return
    adjudication.needs_judgment + options, regardless of whether the live MCP
    elicitation call succeeds -- this is the demo's fallback path if K Pro
    doesn't support elicitation. Confirm this fallback shape is always present
    on deadlocked evidence, independent of any live ctx.elicit() call.
    """
    for r in SEED_RECORDS:
        insert_record(r)
    records = get_records("OR51E2", "prostate_cancer")
    contract = to_demo_contract(records, "OR51E2", "prostate_cancer")

    assert contract["adjudication"]["needs_judgment"] is True
    assert contract["adjudication"]["elicitation"] is not None
    assert "options" in contract["adjudication"]["elicitation"]
    assert len(contract["adjudication"]["elicitation"]["options"]) >= 2
    assert contract["adjudication"]["fallback_without_elicitation"]["return_to_client"] is True


def test_evidence_buckets_partition_by_direction(db):
    for r in SEED_RECORDS:
        insert_record(r)
    records = get_records("OR51E2", "prostate_cancer")
    contract = to_demo_contract(records, "OR51E2", "prostate_cancer")

    assert len(contract["tumor_suppressive"]) == 2
    assert len(contract["tumor_promoting"]) == 2
    for entry in contract["tumor_suppressive"]:
        assert entry["direction"] == "tumor_suppressive"
    for entry in contract["tumor_promoting"]:
        assert entry["direction"] == "tumor_promoting"


def test_empty_records_returns_valid_shape_not_error(db):
    """No data loaded yet shouldn't crash the demo -- it should return the
    same top-level shape with empty/zeroed contents, so Person C's frontend
    doesn't need a special no-data code path."""
    contract = to_demo_contract([], "OR51E2", "prostate_cancer")
    mock = json.loads(MOCK_PATH.read_text())
    assert set(contract.keys()) == set(mock.keys())
    assert contract["adjudication"]["needs_judgment"] is False


def test_balance_threshold_derived_from_real_elicitation_threshold(db):
    """
    balance_threshold must be a real function of ELICITATION_THRESHOLD, not a
    hardcoded cosmetic number copied from the mock -- otherwise it silently
    stops meaning anything the moment scoring.py's threshold changes.
    """
    from discordance.scoring import ELICITATION_THRESHOLD

    for r in SEED_RECORDS:
        insert_record(r)
    records = get_records("OR51E2", "prostate_cancer")
    contract = to_demo_contract(records, "OR51E2", "prostate_cancer")

    total_mass = (
        contract["scores"]["tumor_suppressive_mass"] + contract["scores"]["tumor_promoting_mass"]
    )
    expected = round((ELICITATION_THRESHOLD[1] - ELICITATION_THRESHOLD[0]) * total_mass, 3)
    assert contract["scores"]["balance_threshold"] == expected

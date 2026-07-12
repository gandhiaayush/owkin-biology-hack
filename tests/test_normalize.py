"""Tests for endpoint/model normalization from live MCP critique."""
import os
import pytest
from discordance import init_db, insert_record, get_records, detect_contradictions, detect_auxiliary_tensions
from discordance.normalize import endpoint_tokens, endpoints_overlap, models_overlap, cell_compartment
from seed_data import SEED_RECORDS


@pytest.fixture
def db(tmp_path):
    os.environ["DISCORDANCE_DB"] = str(tmp_path / "n.db")
    init_db(tmp_path / "n.db")
    yield


def test_endpoint_tokens_from_compound_string():
    tokens = endpoint_tokens("proliferation, migration, tumor growth, prognosis correlation")
    assert "tumor_growth" in tokens
    assert "proliferation" in tokens


def test_thomsen_and_sanz_share_tumor_growth_endpoint(db):
    """Regression: composite endpoint strings must overlap, not falsely differ."""
    for r in SEED_RECORDS:
        insert_record(r)
    # Load full OR51E2 prostate set including Thomsen/Marelli from JSON if present
    from pathlib import Path
    import json
    from scripts.load_into_discordance import convert
    data = json.loads(Path("data/receptors/or51e2.json").read_text())
    for raw in data:
        ct = (raw.get("cancer_type") or "").replace(" ", "_")
        if ct in ("prostate", "prostate_cancer", ""):
            for ev in convert(raw):
                insert_record(ev)
    records = get_records("OR51E2", "prostate_cancer")
    sup = [r for r in records if r.direction == "tumor_suppressive"]
    pro = [r for r in records if r.direction == "tumor_promoting" and cell_compartment(r) == "tumor_cell"]
    assert endpoints_overlap(sup, pro)


def test_invasion_does_not_trigger_immune_compartment():
    from discordance.models import EvidenceRecord
    r = EvidenceRecord(
        source="Sanz 2016", source_type="primary_study",
        claim="beta-ionone promotes invasiveness", gene="OR51E2",
        direction="tumor_promoting", cancer_type="prostate_cancer",
        model_system="LNCaP", mechanism="PI3K-gamma/invasion axis",
    )
    assert cell_compartment(r) == "tumor_cell"


def test_marelli_is_immune_not_tumor_cell(db):
    from pathlib import Path
    import json
    from scripts.load_into_discordance import convert
    data = json.loads(Path("data/receptors/or51e2.json").read_text())
    for raw in data:
        for ev in convert(raw):
            insert_record(ev)
    records = get_records("OR51E2", "prostate_cancer")
    marelli = [r for r in records if "Marelli" in r.source]
    assert len(marelli) == 1
    assert cell_compartment(marelli[0]) == "immune_cell"


def test_auxiliary_tensions_include_cell_compartment(db):
    from pathlib import Path
    import json
    from scripts.load_into_discordance import convert
    data = json.loads(Path("data/receptors/or51e2.json").read_text())
    for raw in data:
        for ev in convert(raw):
            insert_record(ev)
    records = get_records("OR51E2", "prostate_cancer")
    aux = detect_auxiliary_tensions(records)
    ids = {t["id"] for t in aux}
    assert "t_cell_compartment" in ids
    assert "t_ligand_validity" in ids

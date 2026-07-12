"""
Seed the evidence database with 4 verified OR51E2 mock records.
Run: python seed_data.py
Re-running is safe — duplicates are ignored via source_hash.
"""
from pathlib import Path
from discordance import init_db, insert_record, get_records, EvidenceRecord

SEED_RECORDS = [
    EvidenceRecord(
        source="Neuhaus et al. 2009, J Biol Chem",
        source_type="primary_study",
        claim="β-ionone activation of OR51E2 inhibits LNCaP cell proliferation",
        mechanism="MAPK family activation and intracellular Ca2+ increase",
        direction="tumor_suppressive",
        direction_context="activation_effect",
        endpoint="proliferation",
        cancer_type="prostate_cancer",
        model_system="LNCaP",
        sample_size=None,
        independent_replications=None,
        gene="OR51E2",
        confidence_note=(
            "Endogenous receptor (not overexpressed); "
            "first study establishing OR51E2 functional activity in prostate cancer"
        ),
    ),
    EvidenceRecord(
        source="Sanz et al. 2014, PLoS ONE",
        source_type="primary_study",
        claim=(
            "β-ionone promotes invasiveness in LNCaP cells (2.75x invasion index increase); "
            "α-ionone alone has no effect but abrogates β-ionone's pro-invasive effect when co-administered"
        ),
        mechanism="PI3K-gamma / Gbeta-gamma G-protein pathway (invasion index assay, not proliferation)",
        direction="tumor_promoting",
        direction_context="activation_effect",
        endpoint="invasiveness",
        cancer_type="prostate_cancer",
        model_system="LNCaP",
        sample_size=None,
        independent_replications=None,
        gene="OR51E2",
        confidence_note=(
            "VERIFIED (Person A, full text read): Sanz measures INVASIVENESS, not proliferation -- "
            "a different endpoint from Neuhaus's proliferation assay. The Sanz authors themselves note "
            "their beta-ionone result is 'not in agreement with' Neuhaus, but frame it as two "
            "potentially co-occurring phenotypes (reduced proliferation + increased invasiveness is a "
            "known cancer biology pattern) rather than a strict same-endpoint contradiction. See "
            "data/receptors/or51e2.json for full verification notes."
        ),
    ),
    EvidenceRecord(
        source="Rodriguez et al. 2014, Oncogenesis",
        source_type="primary_study",
        claim="PSGR (OR51E2) promotes prostatic intraepithelial neoplasia and xenograft tumor growth",
        mechanism="NF-κB pathway activation",
        direction="tumor_promoting",
        direction_context="expression_pattern",
        endpoint="tumor_growth",
        cancer_type="prostate_cancer",
        model_system="xenograft",
        sample_size=None,
        independent_replications=None,
        gene="OR51E2",
        confidence_note=(
            "In vivo xenograft; NF-κB mechanism distinct from MAPK in Neuhaus "
            "— different signaling context in vivo vs. cell culture"
        ),
    ),
    EvidenceRecord(
        source="Pronin & Slepak 2021, J Biol Chem",
        source_type="primary_study",
        claim="OR51E2 suppresses proliferation and promotes cell death in prostate cancer cells",
        mechanism="not specified",
        direction="tumor_suppressive",
        direction_context="expression_pattern",
        endpoint="proliferation",
        cancer_type="prostate_cancer",
        model_system="prostate cancer cell line",
        sample_size=None,
        independent_replications=None,
        gene="OR51E2",
        confidence_note=(
            "Paper explicitly flags field-wide controversy: some studies could not replicate "
            "β-ionone as a functional OR51E2 ligand, questioning agonism itself"
        ),
    ),
]


def main() -> None:
    db_path = Path("evidence.db")
    init_db(db_path)
    inserted = 0
    for record in SEED_RECORDS:
        row_id = insert_record(record)
        if row_id is not None:
            print(f"  Inserted: [{row_id}] {record.source[:50]}")
            inserted += 1
        else:
            print(f"  Skipped (duplicate): {record.source[:50]}")
    print(f"\nDone. {inserted}/{len(SEED_RECORDS)} records inserted.")

    records = get_records("OR51E2", "prostate_cancer")
    print(f"Verified: {len(records)} OR51E2 prostate_cancer records in DB.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Pull bioactivity/ligand-binding data for a receptor from the ChEMBL REST API
and append evidence records to data/receptors/<receptor>.json.

Receptor-agnostic by design (CLAUDE.md Section 4: Person B's logic should be
receptor-agnostic, and Person A's scripts should follow the same principle so
adding a new receptor is a data problem, not a code problem).

Usage: python3 scripts/chembl_pull.py OR51E2
       python3 scripts/chembl_pull.py OR2H1
       python3 scripts/chembl_pull.py OR51B4
"""
import json
import sys
from collections import Counter
from pathlib import Path
from urllib import request, parse

CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"
REPO_ROOT = Path(__file__).resolve().parent.parent


def chembl_get(path, params):
    url = f"{CHEMBL_API}/{path}?{parse.urlencode(params)}"
    with request.urlopen(url) as resp:
        return json.loads(resp.read().decode())


def find_target(symbol):
    data = chembl_get("target/search.json", {"q": symbol})
    hits = [t for t in data.get("targets", []) if t["organism"] == "Homo sapiens"]
    return hits[0] if hits else None


def fetch_activities(target_chembl_id):
    data = chembl_get("activity.json", {"target_chembl_id": target_chembl_id, "limit": "1000"})
    return data["activities"], data["page_meta"]["total_count"]


def fetch_molecule_names(molecule_ids):
    if not molecule_ids:
        return {}
    data = chembl_get(
        "molecule.json",
        {"molecule_chembl_id__in": ",".join(molecule_ids), "limit": str(len(molecule_ids) + 5)},
    )
    return {m["molecule_chembl_id"]: m.get("pref_name") for m in data["molecules"]}


def build_records(receptor, target, activities, total_count):
    records = []
    ec50_ic50 = [a for a in activities if a["standard_type"] in ("EC50", "IC50")]
    unique_molecules = sorted(set(a["molecule_chembl_id"] for a in activities))
    names = fetch_molecule_names([a["molecule_chembl_id"] for a in ec50_ic50])

    assay_desc_counts = Counter(a["assay_description"] for a in activities)
    top_assays = "; ".join(f"{desc[:100]} (n={n})" for desc, n in assay_desc_counts.most_common(3))

    records.append({
        "receptor": receptor,
        "source_type": "chembl",
        "citation": f"ChEMBL target {target['target_chembl_id']} ({target['pref_name']}), live API pull",
        "claim": (
            f"{total_count} bioactivity records in ChEMBL for {receptor} ({target['pref_name']}), "
            f"spanning {len(unique_molecules)} unique molecules and {len(ec50_ic50)} EC50/IC50 potency "
            f"measurements. Top assay types: {top_assays}."
        ),
        "mechanism": None,
        "direction": "unclear",
        "model_system": "ChEMBL-aggregated heterologous expression assays (multiple cell systems, see individual assay_description fields)",
        "sample_size": total_count,
        "replication_count": None,
        "cancer_type": None,
        "verified_by_person_a": True,
        "raw_excerpt_or_link": f"https://www.ebi.ac.uk/chembl/target_report_card/{target['target_chembl_id']}/",
        "verification_notes": (
            f"Live ChEMBL REST API pull (target_chembl_id={target['target_chembl_id']}). This is a "
            "ligand-binding/potency data source, not a tumor-direction claim -- grounds rule-generation "
            "claims about ligand potency in real binding data rather than inferred from paper discussion "
            "sections, per CLAUDE.md Section 8's rationale for adding ChEMBL."
        ),
    })

    for a in ec50_ic50:
        mol_id = a["molecule_chembl_id"]
        name = names.get(mol_id) or mol_id
        records.append({
            "receptor": receptor,
            "source_type": "chembl",
            "citation": f"ChEMBL activity {a['activity_id']} ({mol_id} in assay {a['assay_chembl_id']}, document {a.get('document_chembl_id')})",
            "claim": (
                f"{name} ({mol_id}) shows {a['standard_type']} = {a['standard_value']} "
                f"{a['standard_units']} at {receptor} in assay: {a['assay_description']}"
            ),
            "mechanism": None,
            "direction": "unclear",
            "model_system": a["assay_description"],
            "sample_size": None,
            "replication_count": None,
            "cancer_type": None,
            "verified_by_person_a": True,
            "raw_excerpt_or_link": f"https://www.ebi.ac.uk/chembl/compound_report_card/{mol_id}/",
            "verification_notes": (
                f"Live ChEMBL REST API pull, single assay record (activity_id={a['activity_id']}), "
                "document_year=" + str(a.get("document_year")) + ". Ligand-potency data point, not an "
                "independent claim about cancer biology direction."
            ),
        })

    return records


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/chembl_pull.py <RECEPTOR_SYMBOL>")
        sys.exit(1)
    receptor = sys.argv[1].upper()
    out_file = REPO_ROOT / "data" / "receptors" / f"{receptor.lower()}.json"

    print(f"Searching ChEMBL for target {receptor}...")
    target = find_target(receptor)
    if not target:
        print(f"  No human ChEMBL target found for {receptor} -- skipping (nothing to add).")
        return
    print(f"  Found {target['target_chembl_id']} ({target['pref_name']})")

    activities, total_count = fetch_activities(target["target_chembl_id"])
    print(f"  {total_count} total activity records ({len(activities)} fetched)")

    new_records = build_records(receptor, target, activities, total_count)

    existing = json.loads(out_file.read_text()) if out_file.exists() else []
    existing = [r for r in existing if r.get("source_type") != "chembl"]
    existing.extend(new_records)
    out_file.write_text(json.dumps(existing, indent=2) + "\n")
    print(f"Wrote {len(new_records)} ChEMBL records to {out_file} (total {len(existing)} records)")


if __name__ == "__main__":
    main()

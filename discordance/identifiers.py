"""Manual external ID lookup table for demo receptors.

Lightweight v1 — no API calls at runtime. O(1) dict lookup, zero efficiency concern
for hackathon scale (3 receptors, <100 records).
"""
from __future__ import annotations

# gene symbol → external identifiers
RECEPTOR_IDS: dict[str, dict[str, str]] = {
    "OR51E2": {
        "hgnc": "HGNC:8125",
        "ensembl": "ENSG00000167332",
        "uniprot": "Q8NGK8",
        "chembl": "CHEMBL4523454",
        "aliases": "PSGR",
        "pdb": "8F76",
    },
    "OR2H1": {
        "hgnc": "HGNC:8251",
        "ensembl": "ENSG00000173295",
        "uniprot": "Q96R48",
    },
    "OR51B4": {
        "hgnc": "HGNC:8122",
        "ensembl": "ENSG00000176971",
        "uniprot": "Q9H255",
    },
}

# cancer_type slug → disease ontology IDs (best-effort for pitch)
CANCER_IDS: dict[str, dict[str, str]] = {
    "prostate_cancer": {"mondo": "MONDO:0008315", "label": "prostate cancer"},
    "colorectal_cancer": {"mondo": "MONDO:0005575", "label": "colorectal cancer"},
    "lung_cancer": {"mondo": "MONDO:0008903", "label": "lung cancer"},
    "kich": {"mondo": "MONDO:0004974", "label": "kidney chromophobe carcinoma"},
}

# common ligands in OR51E2 evidence
LIGAND_IDS: dict[str, dict[str, str]] = {
    "β-ionone": {"chebi": "CHEBI:48911", "or_subtype": "BiasedAgonist"},
    "beta-ionone": {"chebi": "CHEBI:48911", "or_subtype": "BiasedAgonist"},
    "α-ionone": {"chebi": "CHEBI:48910", "or_subtype": "BiasedAgonist"},
    "androstenone": {"chebi": "CHEBI:15994", "or_subtype": "OdorantLigand"},
    "propionate": {"chebi": "CHEBI:17272", "or_subtype": "MetaboliteLigand"},
}


def receptor_external_ids(gene: str) -> dict[str, str]:
    return RECEPTOR_IDS.get(gene.upper(), {"hgnc": None, "label": gene})


def cancer_external_ids(cancer_type: str) -> dict[str, str]:
    key = cancer_type.lower().replace(" ", "_")
    return CANCER_IDS.get(key, {"label": cancer_type.replace("_", " ")})


def ligand_external_ids(name: str) -> dict[str, str]:
    return LIGAND_IDS.get(name, {"label": name})

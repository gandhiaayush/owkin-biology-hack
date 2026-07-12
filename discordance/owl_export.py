"""Export Discordance runtime ontology to OWL/Turtle for Protégé.

The export mirrors discordance/ontology.py class and property definitions.
Evidence individuals can be included from live EvidenceRecord rows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from . import ontology as onto
from .models import EvidenceRecord

OWL_PREFIX = "http://owkin.com/discordance/ontology#"
OWL_HEADER = f"""@prefix : <{OWL_PREFIX}> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<{OWL_PREFIX}> a owl:Ontology ;
    rdfs:label "Discordance OR-in-Cancer Evidence Ontology" ;
    rdfs:comment "Contradiction-aware evidence graph for olfactory receptors in cancer." .
"""


def _class_axioms() -> list[str]:
    lines = []
    for node in onto.NODE_TYPES:
        lines.append(f":{node} a owl:Class ; rdfs:label \"{node}\" .")
    for parent, children in onto.OR_SUBCLASSES.items():
        for child in children:
            lines.append(
                f":{child} a owl:Class ; rdfs:subClassOf :{parent} ; rdfs:label \"{child}\" ."
            )
    return lines


def _property_axioms() -> list[str]:
    lines = []
    for edge in onto.EDGE_TYPES:
        domain, ranges = onto.OR_EDGE_SEMANTICS[edge]
        range_str = ", ".join(f":{r}" for r in ranges)
        lines.append(
            f":{edge} a owl:ObjectProperty ; rdfs:label \"{edge}\" ; "
            f"rdfs:domain :{domain} ; rdfs:range [ owl:unionOf ({range_str}) ] ."
        )
    for prop, label in onto.DATA_PROPERTIES.items():
        lines.append(f":{prop} a owl:DatatypeProperty ; rdfs:label \"{label}\" .")
    return lines


def _individual_from_record(r: EvidenceRecord, idx: int) -> list[str]:
    claim_id = f"claim_{r.id or idx}"
    paper_id = f"paper_{onto.slug(r.source)[:32]}"
    receptor_id = f"receptor_{onto.slug(r.gene)}"
    lines = [
        f":{receptor_id} a :ClassA_OR, :Receptor ; rdfs:label \"{r.gene}\" .",
        f":{paper_id} a :{onto.classify_paper_subtype(r.source_type)} ; rdfs:label \"{r.source[:80]}\" .",
        f":{claim_id} a :{onto.classify_claim_subtype(r)} ;",
        f"    :from_paper :{paper_id} ;",
        f"    :about_receptor :{receptor_id} ;",
        f"    :hasDirection \"{r.direction}\" ;",
        f"    :hasDirectionContext \"{r.direction_context}\" ;",
        f"    :hasSourceType \"{r.source_type}\" ;",
        f"    rdfs:label \"{r.claim[:120].replace(chr(34), chr(39))}\" .",
    ]
    ligand = onto.infer_ligand_subtype(r.claim, r.mechanism)
    if ligand:
        lig_id = f"ligand_{onto.slug(ligand)}"
        lines.insert(1, f":{lig_id} a :OdorantLigand, :Ligand ; rdfs:label \"{ligand}\" .")
        lines.append(f":{claim_id} :uses_ligand :{lig_id} .")
    model_subtype = onto.classify_model_subtype(r.model_system)
    model_id = f"model_{onto.slug(r.model_system)}"
    lines.insert(2, f":{model_id} a :{model_subtype}, :ModelSystem ; rdfs:label \"{r.model_system}\" .")
    lines.append(f":{claim_id} :in_model :{model_id} .")
    if r.endpoint and r.endpoint != "not specified":
        ep_subtype = onto.classify_endpoint_subtype(r.endpoint)
        ep_id = f"endpoint_{onto.slug(r.endpoint)}"
        lines.insert(3, f":{ep_id} a :{ep_subtype}, :Endpoint ; rdfs:label \"{r.endpoint}\" .")
        lines.append(f":{claim_id} :measures_endpoint :{ep_id} .")
    return lines


def export_ontology_turtle(
    records: Optional[Iterable[EvidenceRecord]] = None,
) -> str:
    """Return full Turtle document. Optionally embed evidence individuals."""
    parts = [OWL_HEADER, "", "# ── Classes ──", *_class_axioms(), "", "# ── Properties ──", *_property_axioms()]
    if records:
        parts.extend(["", "# ── Evidence individuals (sample) ──"])
        for idx, r in enumerate(records):
            parts.extend(_individual_from_record(r, idx))
    return "\n".join(parts) + "\n"


def write_ontology_file(
    path: Path,
    records: Optional[Iterable[EvidenceRecord]] = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(export_ontology_turtle(records), encoding="utf-8")
    return path

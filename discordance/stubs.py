"""
Stubs for Person A's extraction pipeline.
Replace these with real implementations when Person A's pipeline is ready.
The interface contract: these functions accept raw text/metadata and return
a dict matching the EvidenceRecord schema expected by the Builder MCP tool.
"""
from __future__ import annotations


def mock_person_a_extract(raw_text: str, metadata: dict) -> dict:
    """
    Stub — returns a placeholder evidence record.
    Person A's real pipeline replaces this function.
    Output must conform to the Builder tool's input schema.
    """
    return {
        "source": metadata.get("citation", "Unknown source"),
        "source_type": metadata.get("source_type", "primary_study"),
        "claim": raw_text[:200],
        "mechanism": metadata.get("mechanism", "not specified"),
        "direction": metadata.get("direction", "neutral"),
        "direction_context": metadata.get("direction_context", "activation_effect"),
        "cancer_type": metadata.get("cancer_type", "prostate_cancer"),
        "model_system": metadata.get("model_system", "unknown"),
        "sample_size": metadata.get("sample_size"),
        "independent_replications": metadata.get("independent_replications"),
        "gene": metadata.get("gene", "OR51E2"),
        "confidence_note": metadata.get("confidence_note", ""),
    }

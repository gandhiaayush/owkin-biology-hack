# Discordance

Contradiction-aware evidence **knowledge graph** for olfactory receptors in cancer — MCP tools for Owkin K Pro.

## What it does

Question → search a preseeded evidence graph → return **all** weighted answers (support, oppose, context) → flag tensions → elicit when deadlocked.

Open-world: missing claims are not treated as false.

## Quick start

```bash
pip install -r requirements.txt
rm -f evidence.db
python scripts/load_into_discordance.py          # load data/receptors/*.json
# or: python seed_data.py                        # 4 OR51E2 demo records only
pytest tests/ -v
python server.py                                 # MCP: add_evidence, query_graph, get_tension_map
```

## Graph system

| Module | Role |
|---|---|
| `discordance/ontology.py` | Controlled vocab (node/edge types) |
| `discordance/graph.py` | Build/query evidence graph + tension map JSON |
| `discordance/contradiction.py` | Opposing directions; softens if endpoints differ |
| `discordance/scoring.py` | Evidence weights + elicitation threshold |
| `discordance/rules.py` | Confidence-qualified rules |
| `server.py` | FastMCP tools |

Node types: `Receptor`, `Claim`, `Paper`, `ModelSystem`, `Endpoint`, `Direction`, `Ligand`, `Mechanism`, `CancerType`.

## MCP tools

- `add_evidence` — ingest one record; returns contradictions on insert
- `query_graph` — rules + contradictions + `subgraph` + `tension_map_data` (+ elicitation on deadlock)
- `get_tension_map` — graph JSON for Person C visualization

## Data

Person A writes `data/receptors/<gene>.json` (see `data/schema.md`).  
`scripts/load_into_discordance.py` adapts into SQLite `EvidenceRecord`s and infers endpoints for known demo papers when missing.

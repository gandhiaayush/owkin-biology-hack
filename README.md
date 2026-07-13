# Discordance

**🥈 2nd Place — Owkin Rewiring Biology Hackathon, July 2026**

A contradiction-aware knowledge graph for olfactory receptors in cancer, delivered as an MCP tool suite for Owkin K Pro. Instead of collapsing conflicting evidence into a single hedge, Discordance explicitly flags contradictions between sources, weights evidence by strength, generates confidence-qualified rules, and uses MCP elicitation to ask the researcher for judgment when it genuinely cannot resolve a deadlock.

---

## The Problem

Olfactory receptors (ORs) are ectopically expressed across multiple cancer types and represent a largely unexplored class of therapeutic targets. Owkin had **no existing infrastructure for OR-specific evidence** prior to this project. Standard LLM responses to questions about ORs in cancer either produce falsely confident single-direction answers or useless hedges — neither surfaces the real methodological disputes in the primary literature.

---

## What Discordance Does Differently

### 1. Contradiction detection
When two sources make opposing claims about the same receptor/pathway/outcome, the system flags this explicitly rather than merging them into a narrative. It identifies both claims, their sources, and — where evidence allows — a mechanistic hypothesis for why they diverge (different cell line, different assay, different endpoint, different ligand).

**The primary demo case:** OR51E2 / PSGR in prostate cancer. Neuhaus 2009 shows β-ionone *suppresses proliferation* in LNCaP cells. Sanz 2014 shows β-ionone *promotes invasiveness* in the same LNCaP cells. Both are real. Both can be simultaneously true. The system says this explicitly (`same_endpoint: false`) rather than picking a winner.

### 2. Evidence weighting
Every edge in the graph carries a strength score based on: source type (primary study > review > preliminary), number of independent replications, sample size, and model system. Patents are tracked as evidence of commercial interest, not biological validation — they appear in a distinct `commercial_interest` block and never enter the directional mass score.

### 3. Confidence-qualified rules
Given a query, the system returns claims with attached confidence levels: `"high confidence, N=3 independent studies"` vs `"unreplicated, N=1, treat as hypothesis"`. Never asserts a rule as universally true off a single paper.

### 4. MCP elicitation on deadlock
When the adjudication logic finds a contradiction it cannot confidently resolve (evidence masses are balanced, or replication count and sample size point in opposite directions), the tool pauses and asks the researcher a structured question via MCP elicitation rather than guessing. This is the feature that only works as a live MCP tool, not a static report.

### 5. Open-world assumption
Missing claims are not treated as false. A TCGA CNV amplification signal in kidney chromophobe carcinoma (KICH) with no functional literature is surfaced explicitly as an unexplored connection labeled low-confidence — not silently ignored.

---

## Receptors Covered

| Receptor | Cancer types | Key finding | Records |
|---|---|---|---|
| OR51E2 / PSGR | Prostate (primary), colorectal, melanoma, KICH exploratory | Contested activation outcome in prostate; consensus-suppressive in colorectal (2 independent 2025 papers) | ~90 |
| OR2H1 | Lung, ovarian, cholangiocarcinoma | CAR-T target; ectopic surface expression across epithelial tumors (Martin 2022) | ~15 |
| OR51B4 | Colorectal | Activation suppresses proliferation via PLC/p38/Akt (Weber 2017) | ~10 |

---

## Architecture

```
data/receptors/*.json            ← structured evidence records (Person A verified)
scripts/load_into_discordance.py ← ingests JSON → SQLite evidence.db
discordance/
  db.py                          ← EvidenceRecord model, SQLite I/O
  scoring.py                     ← evidence weights, activation mass pool, elicitation threshold
  contradiction.py               ← detect opposing directional claims, endpoint comparison
  normalize.py                   ← citation dedup, endpoint tokenization, model-system families
  demo_contract.py               ← structured query_or_graph payload (all buckets)
  graph.py                       ← ontology-aligned graph for tension map visualization
  rules.py                       ← confidence-qualified rule generation
  scorecard.py                   ← per-source scorecards with weight breakdown
  elicitation.py                 ← MCP elicitation question builder
  ontology.py                    ← controlled vocabulary (node/edge types)
  owl_export.py                  ← OWL/RDF export for downstream ontology tooling
server.py                        ← FastMCP server (query_or_graph, add_evidence, get_tension_map)
```

### Evidence buckets in every response

| Bucket | Contents | Enters mass score? |
|---|---|---|
| `tumor_suppressive` | Activation-effect, primary/review, tumor-cell intrinsic, verified | ✅ |
| `tumor_promoting` | Same criteria, opposite direction | ✅ |
| `exploratory` | Expression-pattern, genetic-alteration, immune/TME compartment, preliminary, patents | ❌ (kept, not dropped) |
| `consensus` | Uncontested directional claims | ✅ |

The `exploratory` bucket is not filler. A Marelli 2025 finding that OR51E2 on tumor-associated macrophages drives immunosuppressive M2 polarization belongs there — it is a real finding with a different causal structure than the tumor-cell activation claims.

---

## Data Sources

| Source | What it provides |
|---|---|
| Primary literature | Verified claims, mechanism, model system, endpoint, replication count |
| TCGA (GDC API) | Expression, CNV, somatic mutation across 48 cancer projects |
| PDB (REST API) | Solved structures — OR51E2 → 8F76 |
| ChEMBL (EBI API) | 26 unique validated molecules with EC50/IC50 at OR51E2 |
| Patents (USPTO) | Commercial interest signal — US10588884B2 (Duke, 28 compounds) |
| MOSAIC | Via K Pro native session — not built as a separate integration |

---

## Quickstart

```bash
# Install
pip install -r requirements.txt

# Build the evidence database
rm -f evidence.db
python seed_data.py                                # 4 core verified seed records
python scripts/load_into_discordance.py --all      # full load: verified + candidates + expansion

# Run tests
pytest tests/ -v                                   # 95 tests

# Start the MCP server
python server.py                                   # stdio mode (Claude Desktop)
python server.py --http                            # HTTP mode (claude.ai, K Pro via tunnel)
```

### Connect to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "discordance": {
      "command": "/path/to/python",
      "args": ["server.py"],
      "cwd": "/path/to/oslo"
    }
  }
}
```

### Connect to claude.ai / K Pro

```bash
python server.py --http          # starts on port 8000
ngrok http 8000                  # get a public HTTPS URL
# add https://<your-subdomain>.ngrok-free.dev/mcp as the connector URL
```

---

## MCP Tools

### `query_or_graph(gene, cancer_type, query)`
The primary research tool. Returns a structured contract with:
- `tumor_suppressive` / `tumor_promoting` — weighted, deduplicated primary evidence
- `named_exploratory_findings` — Rodriguez 2014, Thomsen 2025, Marelli 2025 explicitly called out
- `therapeutic_analysis` — pre-computed go/no-go, endpoint comparison, evidence strength, and α-ionone assessment grounded only in graph data
- `tensions` — contested claims with endpoint comparison and divergence hypothesis
- `adjudication` — verdict, elicitation options on deadlock
- `ligand_grounding` — 26 ChEMBL-validated OR51E2 ligands with EC50/IC50
- `scorecards_markdown` — per-source weight breakdown ready to paste into a report

### `add_evidence(gene, citation, claim, direction, ...)`
Ingest a new evidence record. Returns any new contradictions detected on insert.

### `get_tension_map(gene, cancer_type)`
Returns graph JSON for visualization (tension map). Use for rendering — not for re-adjudication.

---

## Hallucination Prevention

Repeated live testing caught specific fabrications. Countermeasures are now baked in at multiple layers:

| Fabrication caught | Where fixed |
|---|---|
| "Golgi-localized Gβγ-PI3Kγ-ARF1 pathway" invented twice | `CRITICAL` block in `query_or_graph` docstring |
| Fake citation "Xu et al. 2022" | Listed in `check_response.py` known-fabrications |
| Fake paper "Sanz 2017" | Listed in `check_response.py` |
| Patent described as having 144 compounds | ChEMBL claim rewritten to distinguish 144 raw assay entries / 26 unique molecules / 28 patent compounds; `must_not_do` in `client_instructions` |
| Exploratory bucket silently dropped | `named_exploratory_findings` field + `must_do` enforcement |

```bash
# Run after every live demo session
python3 scripts/check_response.py < claude_response.txt
```

---

## Eval

```bash
python scripts/eval_query_accuracy.py
```

6 golden queries, 27 rubric points, currently passing at **100%**:

| Query | Score |
|---|---|
| OR51E2 / prostate — contested, different endpoints | 6/6 |
| OR51E2 / colorectal — consensus suppressive | 4/4 |
| OR51E2 / KICH — CNV signal, no functional literature | 4/4 |
| OR2H1 / lung — CAR-T single verified paper | 4/4 |
| OR51E2 / melanoma — suppressive, no tension | 5/5 |
| OR51B4 / colorectal — single source | 4/4 |

---

## Key Files

| File | Purpose |
|---|---|
| `CLAUDE.md` | Full project spec, team roles, receptor coverage plan |
| `DEMO.md` | 5-minute demo runbook with judge Q&A prep |
| `scripts/check_response.py` | Post-run fabrication checker |
| `scripts/eval_query_accuracy.py` | Ground-truth accuracy eval |
| `data/receptors/or51e2.json` | Primary evidence dataset (~90 records, fully annotated) |
| `demos/mocks/or51e2-query.json` | Frozen contract shape for frontend testing |

---

## Team

Built at the Owkin Rewiring Biology Hackathon, July 11–12, 2026.

- **Shivansh Bansal** — Evidence pipeline: literature extraction, TCGA/PDB/ChEMBL/patent pulls, claim verification against full text
- **Aayush Gandhi** — Graph logic, MCP tools, contradiction detection, scoring, elicitation, demo contract

---

*Discordance is an honest knowledge graph: it tells you what the evidence actually says, flags where it disagrees with itself, and asks rather than guesses when it is genuinely uncertain.*

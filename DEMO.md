# Discordance — Demo Runbook
### Owkin Rewiring Biology Hackathon, July 12, 2026

---

## Setup (do before demo)

```bash
# From the oslo/ directory:
python seed_data.py                    # inserts the 4 verified seed records
python scripts/load_into_discordance.py  # loads all 64 records (OR51E2/OR2H1/OR51B4)
python server.py                       # starts the MCP server
```

Confirm the server is running before wiring into K Pro.

---

## The Demo Sequence (5 minutes)

### Step 1 — The baseline question (30 sec)

Ask plain K Pro:

> "What is the role of OR51E2 in cancer? Is activating this receptor good or bad therapeutically?"

Expected K Pro response: either a confident single-direction answer (wrong) or a vague hedge ("may have context-dependent effects"). Either way, it won't cite specific sources or flag that there's a real methodological controversy in the field.

---

### Step 2 — The augmented answer (90 sec)

With K Pro + Discordance, call:

```json
query_graph(gene="OR51E2", cancer_type="prostate_cancer")
```

What to point out in the response:

**1. `consensus_status: "contested"`** — the system doesn't pick a winner. It reports both directions.

**2. The contradiction:**
```
same_model_system: true    ← same cell line (LNCaP)
same_endpoint: false       ← Neuhaus measured proliferation, Sanz measured invasiveness
```
This is the key nuance. These aren't flat contradictions — they're different endpoints. Anti-proliferative AND pro-invasive could both be true simultaneously. The system says this explicitly instead of merging into a hedge.

**3. `elicitation_triggered: true`** — because the score ratio is exactly 0.5 (2 suppressive papers vs 2 promoting papers, equal weight). The tool pauses and asks the researcher:
> "Deadlock detected. Would you like to: A) weight suppressive evidence, B) weight promoting evidence, C) report both without adjudication (recommended), D) request MOSAIC context"

This is the moment that only works as a live MCP tool. Say out loud: **"This is the system knowing what it doesn't know and asking rather than guessing."**

**4. Confidence-qualified rules** — the output includes:
- `"unreplicated (N=2 sources) — treat as hypothesis"` for both sides (replication_count=0 for all papers)
- Never asserts "always true" off any single paper

---

### Step 3 — The new finding (60 sec)

Call:

```json
query_graph(gene="OR51E2", cancer_type="colorectal_cancer")
```

Response: `consensus_status: "consensus_suppressive"`, 2 converging 2025 papers (Kim et al., both independent groups):
- β-ionone → Ca²⁺ → MEK/ERK inhibition → suppresses proliferation + induces apoptosis (confirmed in xenograft)
- Propionate → Or51e2 → cAMP → MEK/ERK suppression (confirmed: no effect in Or51e2-KO mice)

Say: **"Two independent 2025 papers, neither in Owkin's existing OR infrastructure, surfaced by the graph. This is the kind of non-obvious connection the Context Award is looking for."**

---

### Step 4 — The KICH exploratory finding (30 sec, if time)

```json
query_graph(gene="OR51E2", cancer_type="KICH")
```

Response: TCGA CNV amplification signal (10 cases in a ~66-case cohort), no functional literature. `consensus_status: "single_source"`, `confidence: "low"`.

Say: **"The system flags an unexplored connection rather than silently ignoring it. Under open world assumption — absence of evidence is not evidence of absence."**

---

### Step 5 — Generalization (30 sec)

Switch to OR2H1:

```json
query_graph(gene="OR2H1", cancer_type="lung_cancer")
```

Response: clean `consensus_suppressive` / `consensus_promoting` — a different evidence pattern than OR51E2's contested picture. Say: **"One receptor is deeply contested, another has clear directionality. The system handles both correctly."**

---

## The Three Judging Track Hooks

**Best AI Scientist MCP:**
- Live MCP tool, wired directly into K Pro
- Elicitation demonstrates going beyond simple tool-calling
- 64 verified/preliminary records across 3 receptors, growing

**Context Award:**
- Tension map shows contested (red) vs. consensus (green) by visual inspection
- KICH CNV finding = surfacing a non-obvious connection, explicitly labeled low-confidence
- Colorectal finding = two 2025 papers that no existing Owkin OR infrastructure would have surfaced

**Frontier Award:**
- Elicitation: the tool knows what it doesn't know and asks
- Open world assumption: absence of evidence ≠ absence of effect, shown concretely on KICH
- Owkin currently has zero OR-specific infrastructure; we're handing over a working starting point

---

## If Challenged by a Sharp Judge

**"Sanz and Neuhaus aren't really contradictory — they measure different endpoints."**
→ Correct. The system already says this. `same_endpoint: false`, `divergence_hypothesis: "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness..."`. The system is more honest than a naive contradiction detector — this is a feature, not a bug.

**"Your confidence scores are just record counts, not real statistics."**
→ True — `independent_replications=0` for all papers so the scoring is source-type-weighted, not replication-count-weighted. The correct response: "this is exactly why we built the schema to accommodate replication counts — as more data comes in, the weights will become meaningful. Right now they correctly label everything as unreplicated rather than overstating confidence."

**"Why should I trust the extraction pipeline?"**
→ Pull up the benchmark: direction accuracy 100% on 5 verified papers, endpoint accuracy clear on the Sanz test case (the hardest case). AND: Person A verified all core records against full text, so the primary demo data isn't automated-extraction-dependent.

---

## Backup Evidence

If the primary OR51E2/prostate contradiction gets challenged:
1. **Colorectal story** — two 2025 papers, consensus-suppressive, KO mouse validation (strongest mechanistic evidence in the set)
2. **OR2H1 CAR-T** — clean single-direction story, different evidence pattern, shows generalization
3. **KICH CNV** — exploratory finding, clearly labeled low-confidence, demonstrates OWA behavior

---

## Current Graph State

| Receptor | Records | Verified | Primary demo use |
|---|---|---|---|
| OR51E2 | 42 JSON / 40 in DB | 6 literature fully verified by Person A | Primary demo (prostate contested, colorectal consensus) |
| OR2H1 | 10 | 1 literature | Generalization story (CAR-T) |
| OR51B4 | 8 | 1 literature | Backup only |

Total in evidence.db: **64 records** across 3 receptors + source types (literature, TCGA, PDB, ChEMBL, patent, preliminary).

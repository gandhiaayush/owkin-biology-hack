# Claude Connector — Discordance MCP (no K Pro required)

Use this path to benchmark **plain Claude** vs **Claude + Discordance MCP** on the frozen OR51E2 question.

---

## What you're comparing

| | Plain Claude | Claude + Discordance |
|---|---|---|
| **Input** | Natural-language question only | Same question + `query_or_graph` tool call |
| **Output** | Prose synthesis (may merge tensions) | Structured JSON: weighted evidence buckets, tensions, `needs_judgment` |
| **Baseline file** | `demos/mocks/baseline-claude.txt` (you capture) | `demos/mocks/augmented-live-snapshot.json` (from graph) |
| **K Pro baseline** | `demos/mocks/baseline-kpro.txt` (already captured) | same augmented snapshot |

---

## Step 1 — Server

```bash
cd /Users/aayushg/Downloads/BioHack
.venv/bin/python scripts/load_into_discordance.py   # if DB empty
.venv/bin/python server.py --http                     # streamable-http on :8000
```

Local MCP endpoint: `http://127.0.0.1:8000/mcp`

Verify tools (optional):

```bash
npx -y @modelcontextprotocol/inspector http://127.0.0.1:8000/mcp
```

You should see: `query_or_graph`, `query_graph`, `add_evidence`, `get_tension_map`, `cross_receptor_connections`.

---

## Step 2 — HTTPS tunnel (required for Claude.ai)

Claude custom connectors need a **public HTTPS** URL.

**Terminal 2** (keep server running in Terminal 1):

```bash
# Option A — Cloudflare (no account needed for quick tunnel)
cloudflared tunnel --url http://127.0.0.1:8000

# Option B — ngrok
ngrok http 8000
```

Copy the HTTPS URL and append `/mcp`, e.g.:

```text
https://abc123.trycloudflare.com/mcp
```

---

## Step 3 — Add Claude custom connector

1. Open [claude.ai](https://claude.ai) → **Settings** → **Connectors** → **Add custom connector**
2. Name: `Discordance`
3. URL: `https://<your-tunnel>/mcp`
4. OAuth fields: leave empty
5. **Connect** → approve tool access

Refs:
- [Claude custom connectors](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)

---

## Step 4 — Capture baseline (plain Claude, no connector)

**New chat. Discordance connector OFF.**

Paste exactly:

```text
Does activating OR51E2 / PSGR suppress or promote prostate cancer
phenotypes? Summarize the evidence for LNCaP / prostate models, including β-ionone studies.
```

Save the full reply to:

```text
demos/mocks/baseline-claude.txt
```

Header to include:

```text
PLAIN CLAUDE BASELINE — captured YYYY-MM-DD
Frozen question: [same question]
Connector: none
```

---

## Step 5 — Augmented benchmark (Discordance connected)

**New chat. Discordance connector ON.**

Paste:

```text
Using the Discordance tools only, call query_or_graph with:
  gene=OR51E2
  cancer_type=prostate_cancer
  query="Does activating OR51E2 / PSGR suppress or promote prostate cancer phenotypes? Summarize the evidence for LNCaP / prostate models, including β-ionone studies."

Return tensions and adjudication. Do not merge opposing claims into one bottom line.
If needs_judgment is true, present the elicitation options and wait for my choice.
```

**Pass criteria:**
- Tool call to `query_or_graph` (not just prose)
- Neuhaus/Pronin vs Sanz/Rodriguez surfaced as separate weighted entries
- `adjudication.needs_judgment: true` or explicit deadlock
- Endpoint difference called out (proliferation vs invasiveness)

**Offline snapshot** (what the tool should return):

```bash
.venv/bin/python scripts/capture_augmented_snapshot.py
# → demos/mocks/augmented-live-snapshot.json
```

Open side-by-side UI:

```bash
open demos/baseline-vs-augmented.html
open demos/or51e2-tension-map.html
```

---

## Step 6 — What the LLM actually receives from `query_or_graph`

The tool does **not** return a merged paragraph. It returns a **demo contract** the model can cite structurally:

```json
{
  "tumor_suppressive": [ { "claim", "weight", "source", "endpoint", "ligand" }, ... ],
  "tumor_promoting":  [ ... ],
  "tensions": [ { "left", "right", "same_endpoint", "deadlock", "hypotheses" } ],
  "scores": { "tumor_suppressive_mass", "tumor_promoting_mass", "balance_abs_delta" },
  "adjudication": { "status": "deadlock", "needs_judgment": true, "elicitation": { "options": [...] } },
  "rules": [ { "text", "confidence", "qualification": "Contested -- do not treat as settled" } ],
  "baseline_contrast": { "plain_k_pro_expected", "augmented_expected" }
}
```

Claude's job after the tool call: **narrate the structure**, not collapse it.

---

## Multimodal instance (parallel work)

Your other instance (image → understand → graph) would feed **new `EvidenceRecord`s** via `add_evidence` or `data/receptors/*.json` → `load_into_discordance.py`. Same graph pipeline; different ingestion path. The query contract shape stays identical.

---

## TCGA / ontology tests

```bash
# Ontology-aligned graph (Protégé-style vocab, Python runtime)
.venv/bin/python -m pytest tests/test_graph.py tests/test_demo_contract.py -v

# TCGA live validation (needs network + SSL certs on macOS)
SSL_CERT_FILE=$(.venv/bin/python -c "import certifi; print(certifi.where())") \
  .venv/bin/python -m pytest tests/test_tcga_validation.py -v -s
```

If TCGA tests fail with `CERTIFICATE_VERIFY_FAILED`, run:

```bash
/Applications/Python\ 3.14/Install\ Certificates.command
```

(or use the `SSL_CERT_FILE` line above)

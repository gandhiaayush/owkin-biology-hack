# Discordance: An Opinionated, Contradiction-Aware Knowledge Graph for Olfactory Receptors in Cancer
### Team reference doc — Owkin Rewiring Biology Hackathon, July 11–12, 2026
### v2 — scoped to depth-first, incremental receptor coverage

---

## 1. The One-Paragraph Pitch

We're building an MCP tool suite that gives Owkin's K Pro a persistent, queryable knowledge
graph centered on olfactory receptors (ORs) in cancer — a domain K Pro currently has no
infrastructure for. The graph is built from literature, TCGA, PDB, ChEMBL, and patents
(MOSAIC accessed natively through K Pro itself, not built separately). Instead of aggregating
everything into one falsely-confident answer, the system explicitly flags contradictions between
sources, weights evidence by strength, generates confidence-qualified rules (not "always true"
claims), and uses MCP elicitation to ask a researcher for judgment when it genuinely can't
resolve something. Rather than trying to cover the whole OR family, we're going deep on a
small, deliberately incremental set of receptors — starting with one (OR51E2), verified and
demoable on its own, then adding a second and third only if time allows — because a smaller
system that definitely works beats a broader one that's half-verified by pitch time.

---

## 2. Why This Project (context for anyone joining mid-build)

Two separate conversations with Owkin people shaped this:

1. **First biologist**: told us to "have an opinion" — build something opinionated and narrow,
   not a generic top-down graph. Warned that MOSAIC Window may not be exportable (it's
   inside K only). Suggested bringing in PDB and weighting by literature strength/consensus.
   Suggested picking a specific niche (a cancer type, a receptor) rather than trying to be
   generic across all of biology.

2. **Second biologist**: pointed out Owkin has **no existing infrastructure for olfactory
   receptors**, and said a knowledge graph specifically for ORs in cancer would be genuinely
   useful to hand off as a pre-built MCP tool — not just a hackathon demo. He also suggested
   the **rule-generation** feature: given a sub-query (a pathway, a receptor, a ligand), return a
   set of claims that hold across the evidence, with the important caveat (ours, added after
   discussion) that these must be **confidence-qualified**, not asserted as universally true,
   because we already found real cases where "always true" would have been wrong.

**Resolved decision (updated):** rather than building broad coverage across the whole OR
family, we're going **depth-first and incremental**. Receptor #1 (OR51E2) is the fully verified
demo centerpiece and must work end-to-end on its own — contradiction detection, evidence
weighting, rule generation, tension map, the works. Receptor #2 and #3 are added only after
#1 is solid, using the same pipeline, to demonstrate the system generalizes without needing to
prove it across the entire family. This is a more honest claim than "we built infrastructure for
all olfactory receptors" and a much lower-risk one given the time we have.

MOSAIC is accessed through K Pro's native session, not built as a separate integration.

---

## 3. The Core Mechanism (what makes this more than "a knowledge graph")

Don't skip this section — it's the actual differentiator and everyone on the team should be able
to explain it in one breath if a judge asks.

1. **Contradiction detection.** When two sources make opposing claims about the same
   receptor/pathway/outcome, the system flags this explicitly instead of merging them into a
   single hedge ("may have context-dependent effects"). It states both claims, their sources,
   and — where possible — a hypothesis for why they diverge (different cell line, different assay,
   different ligand purity, different endpoint measured).

2. **Evidence weighting.** Every edge in the graph carries a strength score based on: number
   of independent replications, sample size (for TCGA-derived claims), and source type
   (peer-reviewed primary data > review article > single preliminary study > patent claim).
   Patents are evidence of *commercial interest*, not biological validation — weight them as a
   distinct edge type, not folded into "literature consensus."

3. **Confidence-qualified rule generation.** Given a sub-query (e.g. "what pathway does
   ligand X activate on receptor Y"), return a rule with an attached confidence level based on
   replication count — "high confidence, N=3 independent studies" vs. "unreplicated, N=1, treat
   as hypothesis." Never assert a rule as universally true off a single paper. We already have a
   real example (OR51E2 in prostate cancer, see Section 6) where doing so would have been
   wrong.

4. **Elicitation on genuine deadlock.** When the adjudication logic finds a contradiction it
   can't confidently resolve (evidence strength roughly balanced, or replication count and
   sample size point in opposite directions), the tool pauses mid-session and asks the
   researcher a structured question via MCP elicitation, instead of guessing. This is the part
   that only works as a live MCP tool, not a static report — it's our answer to the brief's call to
   go beyond simple tool-calling.

---

## 4. Team Roles

Split by **vertical slice**, not by layer — each person can work mostly independently end-to-end
on their piece, so nobody sits blocked waiting on someone else for more than an hour or two.
Sync points are listed in Section 8. Roles are unchanged from the original plan — the scope
change affects *how much* Person A ingests, not the role structure itself.

### Person A — Evidence Pipeline (Shivansh)
**Owns: is the data trustworthy.**

Responsibilities:
- Literature ingestion and extraction, **receptor by receptor, in strict priority order**:
  OR51E2 first, fully verified, before touching receptor #2. Extract
  claim/mechanism/direction/model-system/sample-size into structured records.
- TCGA queries (expression, mutation, CNV) for each receptor as it's added
- PDB structural lookups where solved structures exist (OR51E2 → 8F76 confirmed)
- ChEMBL bioactivity/ligand-binding pulls
- Patent search — scoped to whichever receptors actually get built (start with just OR51E2),
  using your ISEF-era patent-mining experience
- Personally spot-checking extracted claims against source papers — this is the step an
  LLM-only pipeline can get subtly wrong (see Section 6 for what "getting it wrong" looks
  like in practice — the Neuhaus/Sanz case)

**Hard rule: do not start receptor #2's literature pull until receptor #1's evidence set is fully
verified and in the graph.** This is the discipline that makes "incremental" actually work
instead of quietly turning back into "broad and shallow."

Output format: structured evidence records written to the graph store (see Section 7 for
schema).

### Person B — Graph Logic + MCP Tools
**Owns: does the reasoning actually work.**

Responsibilities:
- Graph store setup (schema in Section 7)
- Contradiction detection logic
- Evidence weighting / confidence scoring
- Rule generation with confidence qualification
- The Builder MCP tool (ingest → extract → write, calling Person A's pipeline)
- The Query MCP tool (K Pro asks the graph a question, gets back a sourced, weighted,
  possibly-flagged-as-contested answer)
- Elicitation trigger logic (the confidence-balance check that decides when to stop and ask)

Can and should start immediately with a small hand-written fake dataset (3–4 mock evidence
records) rather than waiting on Person A's real pipeline — swap in real data once it exists.
Because the receptor count is small, this logic should be built to be receptor-agnostic from
the start (don't hardcode anything specific to OR51E2), so adding receptor #2 and #3 is a data
problem, not a code problem.

### Person C — Demo Surface
**Owns: does this convince a judge in five minutes.**

Responsibilities:
- Tension map visualization (nodes/edges color-coded by consensus vs. contested — see
  Section 9)
- Wiring the MCP tool suite into a live K Pro session
- The baseline-vs-augmented comparison: same question to plain K Pro vs. K Pro + our tool
- Rehearsing the demo, timing it, preparing a backup contradiction in case the primary one
  gets challenged
- Slide/pitch materials mapping the build to the three judging tracks (Section 10)

Can build against mocked graph query responses early, same reasoning as Person B. Design
the tension map to look complete and intentional even with only 1–3 receptors in it — a
tightly-scoped, dense graph on one receptor reads as "deliberate," not "unfinished."

---

## 5. Explicitly Not Building

Naming constraints up front is a strength, not a hedge — say this part out loud in the pitch.

- **No coverage of the full OR family.** One receptor, fully verified, is the baseline
  commitment. A second and third are stretch goals, not promises.
- **No fully autonomous multi-agent system.** One tool suite, human-in-the-loop via elicitation
  when needed.
- **No background server-side re-sampling.**
- **No separately-built MOSAIC integration.** Access it through K Pro's native session, not a
  custom pipeline.
- **No claim of "always true" rules without confidence qualification.** This was a real design
  correction — see Section 6.

---

## 6. The Core Verified Contradiction — OR51E2 / PSGR in Prostate Cancer

This is receptor #1 and your primary demo case. It's real, citable, and already checked — use
it first, use it confidently. Do not move to receptor #2 until this is fully solid.

**The setup:** OR51E2 (aka PSGR — Prostate-Specific G-protein-coupled Receptor) is the
most-studied olfactory receptor in cancer. It has ectopic expression in prostate tissue, is
upregulated in prostate cancer, and has a solved PDB structure (8F76).

**The contradiction:** whether *activating* OR51E2 is tumor-suppressive or tumor-promoting
is genuinely split in the primary literature — in the *same cell line* (LNCaP), not just
different tissue contexts.

| Source | Claim | Mechanism | Direction | Model system |
|---|---|---|---|---|
| Neuhaus et al. 2009, *J Biol Chem* | β-ionone activation of OR51E2 inhibits proliferation | MAPK family activation, intracellular Ca²⁺ increase | **Tumor-suppressive** | LNCaP cells (endogenous receptor) |
| Sanz et al. 2014, *PLoS ONE* | β-ionone promotes invasiveness; α-ionone sustains LNCaP growth | Not fully specified from abstract alone — **pull full text before final build** | **Tumor-promoting** | LNCaP cells |
| Rodriguez et al. 2014, *Oncogenesis* | PSGR promotes prostatic intraepithelial neoplasia and xenograft tumor growth | NF-κB pathway | **Tumor-promoting** | Xenograft model |
| Pronin & Slepak 2021, *J Biol Chem* | OR51E1/OR51E2 suppress proliferation, promote cell death | Explicitly notes field-wide controversy on β-ionone agonism itself — some studies couldn't replicate β-ionone as a real OR51E2 ligand | **Tumor-suppressive**, flags controversy directly | Prostate cancer cell line |

**Why this is a strong demo case, not a manufactured one:**
- Same receptor, same cell line (LNCaP), overlapping ligand (β-ionone) — this isn't
  "different tissue, so maybe expected," it's a direct same-system disagreement.
- A 2021 paper in the set *explicitly states* the field has this controversy and attributes it to
  methodology (detection method, endogenous vs. overexpressed receptor, ligand purity) —
  you don't have to argue this is a real contradiction, a published paper already argues it for
  you.
- **Open item before final build**: read Sanz et al. 2014 full text, not just the abstract. The
  α-ionone/β-ionone distinction might mean Sanz is measuring *invasiveness* while Neuhaus
  measures *proliferation* — these could both be true simultaneously (reduced proliferation,
  increased invasiveness is a known cancer biology pattern) rather than a true contradiction.
  **Person A: this is the single most important verification task before the demo is final,
  and it should happen before any work starts on receptor #2.** If it turns out not to be a
  true contradiction, the elicitation/confidence-scoring framing still works ("evidence is
  nuanced, not simply contradictory, here's why") — just don't present it as a clean
  contradiction if the full text doesn't support that.

**The rule-generation lesson this taught us:** if we'd generated an "always true" rule off
Neuhaus alone ("OR51E2 activation is tumor-suppressive in prostate cancer"), it would have
been wrong given Sanz and Rodriguez. This is the concrete example to cite when explaining
why rules must be confidence-qualified rather than asserted as universal.

**A secondary, exploratory extension (not your primary demo):** no literature currently
connects OR51E2 to kidney chromophobe carcinoma (TCGA-KICH), despite that cancer type
showing the highest CNV amplification signal for OR51E2 across all 48 TCGA projects checked.
Frame this as "the graph flags an unexplored connection," clearly labeled low-confidence — a
good example of "surfacing non-obvious connections" for the Context Award.

---

## 7. Receptors #2 and #3 — Only After #1 Is Solid

Do not pick these until OR51E2 is fully verified, in the graph, contradiction-detection working
on it, and Sanz et al. full text resolved. When you do pick #2 and #3, prioritize receptors you
(Shivansh) already have real literature on from your ISEF review, so verification is fast rather
than starting cold. Good candidates already in your existing lit review, roughly in order of how
much material you already have:

- **OR2H1** — CAR-T target across multiple epithelial tumors (lung, ovarian,
  cholangiocarcinoma); you have detailed methodology notes on this one already
- **OR51B4** — colorectal cancer, activation inhibits proliferation via PLC/p38/Akt signaling
  (note: this is a *different* receptor from OR51E2, don't conflate them)
- **OR2C3** — melanoma-exclusive expression, a clean single-cancer-type story if you want
  something with less complexity than the OR51E2 contradiction

Whichever two you pick, run the same rigor as OR51E2: structured evidence table, personally
verified, at least a working hypothesis about whether there's a real tension or just single-paper
coverage (in which case the honest output is a confidence-qualified single-source claim, not a
forced contradiction).

---

## 8. Data Sources — Priority and Integration Notes

### Tier 1 — build these first, they gate the demo
- **Literature** (manual + search-assisted extraction) — primary evidence type
- **TCGA** (public, GDC API confirmed working — we already pulled real expression/CNV/
  mutation data for OR51E2) — expression, mutation, CNV
- **PDB** (public, REST API) — structural cross-checks; OR51E2 → 8F76 confirmed available
- **MOSAIC** — via K Pro's native session access, not a separate build

### Tier 2 — add if Tier 1 is solid ahead of schedule
- **ChEMBL** (EBI, public REST API) — bioactivity/ligand-binding data; this is what makes
  rule-generation claims like "X ligand activates Y at Z potency" grounded in real binding
  data instead of inferred from a paper's discussion section
- **One expression baseline — pick ONE of:**
  - **Human Protein Atlas** — IHC-based protein expression, normal vs. cancer tissue,
    visual (stained tissue images), useful for the tension map
  - **GTEx** — normal tissue RNA expression baseline, quantitative fold-change claims
  - *(Don't build both — redundant coverage of the same claim type isn't worth two
    integrations under time pressure.)*
- **Patents** (Google Patents public API or USPTO full-text search) — scoped to whichever
  receptors actually get built. Distinctive source — almost no other team will think to
  include this.
- **CIViC** — low-effort add since it's already linked from GDC gene pages; not a priority
  build, just a quick check if time allows.

### Explicitly skipped — don't build these
- **GEO** — too raw/heterogeneous to clean up in this timeframe; TCGA already covers
  curated cancer expression data
- **COSMIC** — redundant with TCGA, which is already confirmed working
- **STRING** — genuinely interesting for future work, but a fundamentally different
  evidence type (interaction networks) that needs its own schema thinking we don't have
  time for

---

## 9. Timeline and Checkpoints

Hold each other to these — if you're meaningfully behind at a checkpoint, that's the signal to
cut scope (elicitation first, then stop at 1 receptor instead of adding #2/#3), not push through
silently.

**Tonight (Day 1):**
- MOSAIC-through-K-Pro access confirmed working
- Sanz et al. full text read and the invasiveness-vs-proliferation question resolved one way
  or the other
- OR51E2 evidence set (Section 6) fully in the graph, contradiction detection demonstrably
  working on that one case
- **Checkpoint decision point: is receptor #1 fully solid? If not, do not start #2 — spend the
  rest of tonight finishing #1 instead.**

**Tomorrow morning (Day 2, early):**
- If #1 is solid: begin receptor #2 (pick from Section 7 list)
- Rule generation producing confidence-qualified output (not "always true" claims) on
  receptor #1 at minimum
- Elicitation triggering correctly at least once in a test run

**Tomorrow midday:**
- Receptor #3 only if #2 went smoothly and there's clear time to spare — otherwise stop at 2
- Tension map visualization finalized

**Tomorrow early afternoon:**
- Demo fully rehearsed
- Backup contradiction identified and verified in case the primary one gets challenged live
- Pitch mapped explicitly to all three judging tracks (Section 10)

---

## 10. The Demo

**Centerpiece: baseline-vs-augmented comparison.** Ask the same research question about
OR51E2 in prostate cancer to plain K Pro and to K Pro + our tool suite. Plain K Pro likely
gives a generic or falsely-confident answer. Our tool surfaces the real Neuhaus-vs-Sanz(-vs-
Rodriguez) split explicitly, with sources, mechanisms, and a confidence-qualified read on
what's actually established vs. contested.

**Visual: tension map.** Graph visualization where nodes/edges are color-coded by
consensus (green) vs. contested (red). The OR51E2 prostate cluster should visibly show as
contested — this is the "hero shot" of the demo, the moment that shows the team thought
about epistemic honesty rather than just building a bigger database. If receptors #2/#3 made
it in, the map should visually show the system handling different evidence patterns (one
contested, one clean-consensus, one single-source-unreplicated) — that variety is a better
proof of generalization than raw receptor count would be.

**Fallback:** have the KICH/CNV exploratory finding (Section 6) or receptor #2's evidence set
ready in case the primary example gets challenged by a sharp judge as a known confound.

---

## 11. Judging Fit

- **Best AI Scientist MCP** — the tool suite is directly integrable into K Pro, the
  contradiction-detection pattern generalizes across disease areas (demonstrated on a small,
  deliberately verified set rather than claimed broadly), and it demonstrates real depth of
  biomedical reasoning through evidence weighting rather than naive aggregation.
- **Context Award** — the entire premise is grounding reasoning in the right evidence at the
  right moment; the tension map is a direct visualization of relevance and precision in
  knowledge grounding; the KICH exploratory finding demonstrates surfacing non-obvious
  connections.
- **Frontier Award** — the elicitation step (the tool knowing what it doesn't know and asking
  rather than guessing) is the clearest "this feels like the future" moment in the system; the
  fact that Owkin currently has zero OR-specific infrastructure and we're handing over a
  working, honestly-scoped starting point strengthens the "genuinely new capability" case.

---

## 12. Open Questions / Risks to Track

- **Sanz et al. full text** — does it actually contradict Neuhaus, or measure a different
  endpoint? (Person A, highest priority, blocks starting receptor #2)
- **MOSAIC-through-K-Pro** — confirm this actually works before building anything that
  assumes it does
- **Sample sizes / replication counts** for each OR51E2 paper — needed for evidence
  weighting to be more than a vibe-based number
- **Discipline risk**: the temptation to start receptor #2 before #1 is truly finished is the
  most likely way this project quietly drifts back into "broad and shallow." Treat the Section
  9 checkpoint as a hard gate.
- **Elicitation UX** — none of us have built with MCP elicitation before; test it in isolation
  early rather than discovering it's flaky during final integration

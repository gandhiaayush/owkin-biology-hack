# Person C — Demo Surface Runbook

Aligned to `CLAUDE.md` §§4, 6, 10, 11.

## Owns
- Tension map (hero visual)
- Baseline vs augmented comparison script
- Pitch timing + judging-track mapping
- Backup contradiction / fallback

## Open locally
```bash
open demos/or51e2-tension-map.html
# or: xdg-open demos/or51e2-tension-map.html
```

---

## 5-minute demo script

### 0:00–0:40 — Problem
K Pro aggregates evidence well. It is not built to notice when evidence disagrees.
Olfactory receptors in cancer are a real gap: Owkin has no OR-specific infrastructure.

### 0:40–1:30 — What we built (one sentence)
An MCP tool suite over a small, verified OR knowledge graph that **flags contradictions**, **weights evidence**, returns **confidence-qualified rules**, and **asks the researcher** when it cannot adjudicate.

### 1:30–3:00 — Centerpiece: baseline vs augmented
**Same question to both systems:**

> Does activating OR51E2 (PSGR) suppress or promote prostate cancer phenotypes in LNCaP / prostate models?

| System | Expected behavior |
|---|---|
| Plain K Pro | Smooth / hedged / falsely confident single narrative |
| K Pro + Discordance | Surfaces Neuhaus (↓ proliferation) vs Sanz (↑ invasiveness) vs Rodriguez (↑ growth), with sources + weights |

Show tension map (`demos/or51e2-tension-map.html`):
1. Filter **Consensus** — expression / structure stay green
2. Filter **Contested** — activation→outcome split lights up
3. Click Sanz vs Neuhaus edges — same receptor, same cell-line family, opposing directions
4. Call out deadlock → elicitation question

### 3:00–3:40 — Why MCP (not a PDF)
Elicitation only works live:
> Evidence is balanced. Prioritize proliferation endpoint, invasiveness endpoint, or keep as contested?

### 3:40–4:20 — Scope honesty
One receptor fully verified (OR51E2). #2/#3 only if time. No fake “whole OR family” claim.

### 4:20–5:00 — Judging map + ask
Map to awards (below). Offer handoff as pre-built OR MCP tool for K Pro.

---

## Backup if primary contradiction is challenged
1. **Endpoint nuance framing** (still strong): Sanz may measure invasiveness while Neuhaus measures proliferation — both can be true; silent merge still wrong; elicitation still needed.
2. **TCGA-KICH exploratory**: highest OR51E2 CNV amp across checked TCGA projects, no lit link — Context Award “non-obvious connection,” labeled low confidence.
3. If Person A verified a clean contradiction on receptor #2, swap that in.

---

## Judging-track mapping (say these words)

### Best AI Scientist MCP
Integrable tool suite; contradiction pattern is domain-agnostic; depth via weighting + qualified rules, not bigger database.

### Context Award
Tension map = right evidence at the right moment. Contested vs consensus is visible. KICH finding = non-obvious connection.

### Frontier Award
Elicitation: the tool knows when not to know. Feels like the future of AI scientists.

---

## Wiring checklist (Day 2)
- [ ] Mock Query MCP responses match tension-map cards (can demo UI before live graph)
- [ ] Live K Pro session has Discordance tools connected
- [ ] Baseline question saved as a paste-ready prompt
- [ ] Elicitation path tested once (or fallback: tool returns `needs_judgment` options)
- [ ] Full run timed ≤ 5 minutes twice

## Paste-ready baseline prompt
```
Does activating OR51E2 / PSGR suppress or promote prostate cancer
phenotypes? Summarize the evidence for LNCaP / prostate models,
including β-ionone studies.
```

## Paste-ready augmented follow-up
```
Using Discordance, query OR51E2 activation outcomes in prostate cancer.
Return weighted evidence, flag contradictions, and do not merge opposing claims.
```

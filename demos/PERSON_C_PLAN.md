# Person C Plan — What Needs To Be Done

Owner: **Person C (Demo Surface)**  
Goal: make a judge believe this in **5 minutes**.  
Source of truth: `CLAUDE.md` §§4, 6, 9–11.

---

## North star

Same research question → **plain K Pro** vs **K Pro + Discordance** → tension map shows the OR51E2 split → elicitation (or fallback) when masses are balanced.

If that loop works with **one receptor**, we win the demo even if receptors #2/#3 never ship.

---

## Status right now

| Item | Status |
|---|---|
| OR51E2 tension map (`demos/or51e2-tension-map.html`) | Done (mocked data) |
| 5-min runbook + award lines (`demos/PERSON_C_RUNBOOK.md`) | Done |
| Live K Pro + MCP wiring | Not started (needs tools from B) |
| Baseline vs augmented live capture | Not started |
| Pitch slides / 1-pager | Not started |
| Timed rehearsal (×2) | Not started |
| Backup path verified with Person A | Blocked on Sanz full-text call |

---

## Dependencies (don’t get blocked)

```text
Person A                Person B                 Person C
────────                ────────                 ────────
Verify OR51E2 lit  ──►  Query MCP returns   ──►  Wire into K Pro
(Sanz full text)        weighted + contested     Run baseline vs augmented
                        + elicitation trigger    Polish tension map to live JSON
                        Mock responses early ──► Build UI against mocks NOW
```

**You can work now without A/B finishing** by using mocked query JSON that matches the tension map cards. Swap to live responses when B’s Query tool exists.

---

## Priority ordered backlog

### P0 — Must ship for pitch (do these first)

1. **Freeze the demo question**
   - Use the paste-ready prompt in `PERSON_C_RUNBOOK.md`
   - No wording changes after first successful live run

2. **Mock Query API contract with Person B (30 min sync)**
   - Agree JSON shape for:
     - `supports[]` / `opposes[]` (source, weight, claim, model, endpoint)
     - `tensions[]` (why contested)
     - `needs_judgment` + elicitation options
   - You build the UI/demo against this mock tonight

3. **Connect tension map to that JSON**
   - Today: hardcoded OR51E2 edges (OK)
   - Next: load from `demos/mocks/or51e2-query.json` so live MCP output can drop in later

4. **Baseline vs augmented dry run**
   - Run plain K Pro on the frozen question → screenshot/save answer
   - Run augmented path (mock OK at first) → show contested split
   - Put both side-by-side in pitch (slide or browser tabs)

5. **Elicitation path**
   - Preferred: real MCP elicitation mid-tool
   - Fallback (ship this if elicitation flaky): tool returns `needs_judgment: true` + 3 options; next user message continues
   - Demo must not die if K Pro lacks elicitation support

6. **Two timed rehearsals ≤ 5:00**
   - Rehearsal 1: find cuts
   - Rehearsal 2: final cadence
   - Roles: you drive UI; someone else watches time / asks hostile Qs

### P1 — Makes it feel finished

7. **Pitch surface (pick one, don’t overbuild)**
   - Option A: 4–5 slides max
   - Option B: one HTML “pitch board” with problem → demo → awards
   - Must include explicit award mapping (Best MCP / Context / Frontier)

8. **Backup pack ready**
   - Card 1: “endpoint nuance” framing (proliferation vs invasion)
   - Card 2: TCGA-KICH exploratory CNV (low confidence)
   - Card 3: receptor #2 only if A/B actually verified it

9. **Live K Pro wiring checklist**
   - Tools visible in session
   - One successful `query_or_graph` (or whatever B names it) call
   - Tension map opens in <5 seconds during pitch
   - Offline fallback: local HTML + saved baseline screenshot

### P2 — Only if P0/P1 green

10. Second receptor on the map (visual variety: contested vs consensus vs single-source)
11. Fancy motion / polish beyond what judges can see in 10 seconds
12. Extra slides, logos, or “platform” narrative

---

## Day-by-day for Person C

### Tonight (Day 1)
- [ ] Sync 15 min with B on Query JSON + tool names
- [ ] Sync 10 min with A: is Neuhaus vs Sanz still “contradiction” or “endpoint nuance”?
- [ ] Export mock `or51e2-query.json` matching Section 6 papers
- [ ] Point tension map at the mock (or keep hardcoded if time-crunched — both OK)
- [ ] Capture plain K Pro baseline answer for the frozen question
- [ ] Write award 1-liners on a single slide / section (already drafted in runbook)

**Exit criterion tonight:** you can demo the tension map + explain the contradiction without anyone else’s laptop.

### Tomorrow morning (Day 2)
- [ ] Plug into B’s real Query MCP (swap mock → live)
- [ ] Test elicitation OR fallback once
- [ ] First full baseline-vs-augmented run timed

**Exit criterion morning:** live augmented answer shows contested OR51E2 split with sources.

### Tomorrow midday
- [ ] Finalize tension map styling (dense on 1 receptor = deliberate)
- [ ] Pitch deck / pitch board locked
- [ ] Backup cards printed or one-click ready

### Tomorrow early afternoon
- [ ] Rehearsal #1 + cuts
- [ ] Rehearsal #2
- [ ] Freeze demo; no new features

---

## Cut order if behind (from CLAUDE.md spirit)

1. Drop receptor #2/#3 from *your* visuals (A/B problem anyway)
2. Drop fancy elicitation UX → use `needs_judgment` fallback
3. Drop live K Pro wiring → local HTML + recorded/saved baseline comparison
4. Never drop: OR51E2 contested story + tension map + “we don’t silently merge”

---

## Sync questions to ask A/B today

**To Person A**
- Sanz full text: contradiction or different endpoint?
- Final weights / N for Neuhaus, Sanz, Rodriguez, Pronin?
- Is KICH exploratory approved as backup?

**To Person B**
- Exact MCP tool names + input schema?
- Does Query return graph-ready nodes/edges or only text cards?
- When does elicitation fire (`|support - oppose| < τ`)? What’s τ?

---

## Definition of done (Person C)

- [ ] Judge sees contested OR51E2 cluster in < 30 seconds of the visual
- [ ] Baseline vs augmented difference is obvious without explanation
- [ ] You can say in one breath why this needed MCP (elicitation / no silent merge)
- [ ] Backup path ready if a biologist challenges the primary contradiction
- [ ] Pitch explicitly maps to all three award tracks
- [ ] Timed run ≤ 5 minutes, twice

---

## Suggested next action (right now)

1. Message B: “send me the Query mock JSON schema — I’ll bind the tension map tonight.”  
2. Message A: “Sanz call — contradiction or nuance? I need the pitch line.”  
3. Capture baseline K Pro answer for the frozen question while waiting.

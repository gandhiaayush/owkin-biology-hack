# Evidence record schema

Every evidence record — regardless of source — is a JSON object with this shape, stored as an
array under `data/receptors/<receptor>.json`.

```json
{
  "receptor": "OR51E2",
  "source_type": "literature | tcga | pdb | chembl | patent | unpublished_primary",
  "citation": "Neuhaus et al. 2009, J Biol Chem",
  "claim": "Free-text statement of what the source claims",
  "mechanism": "Free-text mechanism, or null if not applicable/not yet known",
  "direction": "tumor-suppressive | tumor-promoting | neutral | unclear",
  "model_system": "e.g. LNCaP cells (endogenous receptor)",
  "endpoint": "e.g. 'proliferation', 'invasiveness', 'apoptosis', 'migration' -- optional, default 'not specified'",
  "sample_size": null,
  "replication_count": null,
  "cancer_type": "prostate",
  "verified_by_person_a": false,
  "verification_notes": "What was checked, against what, and any caveats",
  "raw_excerpt_or_link": "Quote, DOI, or file path this was extracted from"
}
```

## Field notes

- `source_type` — five categories. `patent` is evidence of commercial interest, not biological
  validation — never fold into literature consensus when weighting. `unpublished_primary` is for
  unpublished/unreplicated primary data (e.g. a collaborator's own wet-lab assay) — kept distinct
  from `literature` so it isn't weighted as peer-reviewed consensus.
- `direction` — `neutral`/`unclear` are valid; don't force a binary read on a source that hasn't
  established one (e.g. a structural or expression-only record with no explicit tumor-direction
  claim).
- `sample_size` / `replication_count` — required for evidence weighting (more independent
  replications and larger cohorts = higher confidence). Use `null` only when genuinely unknown
  (e.g. sample size not reported in a paper's abstract) — don't guess.
- `verified_by_person_a` — only set `true` after manually checking the record against the primary
  source (source paper full text, or actual API response), not from a bare citation match.
- `cancer_type` — use `null` for non-cancer model systems (e.g. RPE cells) that are still relevant
  context for interpreting a ligand's mechanism.
- `endpoint` — the actual biological outcome measured (proliferation, invasiveness, …). Two
  activation-effect claims can still fail as a *same-endpoint* contradiction if they measured
  different things (Neuhaus vs Sanz). Leave `"not specified"` when unclear; contradiction logic
  only softens framing when endpoints are positively confirmed to differ.

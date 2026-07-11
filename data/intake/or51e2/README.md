# Intake: Saanvi Gudisay / Shivansh Bansal ISEF-ACSEF-IFoRE research

Source project: "Allosteric Regulation of Ectopically Expressed Olfactory Receptors in Tumor
Cells: Ligand-Receptor Topology and Deep Learning-Assisted Drug Discovery" (Dublin High
School; ISEF 2025 CBIO034T, ACSEF HS-BCOM-296-T2, IFoRE 2025).

Files copied here from the original source at `~/Downloads/Science Fairs/`.

## What was pulled into `data/receptors/or51e2.json`

- Two new literature records: Gelis et al. 2017 (melanoma) and Jovancevic et al. 2017 (RPE,
  non-cancer) — both extracted from `Literature Review.docx`.
- One `unpublished_primary` record: the dual-luciferase reporter assay from `firefly.xlsx` /
  `nano-luc.xlsx`, with ratios independently recomputed (see that record's `verification_notes`
  for a data-quality caveat — the raw numbers do not cleanly support the "2 of 4 ligands
  activated" claim in the ISEF video script).
- Neuhaus et al. 2009's mechanism field was enriched using this review's more detailed summary.

## What was explicitly NOT pulled in (and why)

- **`OR+Ligand list.docx`'s OR51E2 row (nonanoic acid, residues H108/I206/S111/Y254)** — the
  document itself labels this row **"OR51E1"**, not OR51E2. Confirmed by direct text extraction.
  Do not attribute this ligand/residue data to OR51E2 without further verification against the
  original AlphaFold3/docking output.
- **Sanz et al. 2014** is NOT in these materials. A similarly-titled paper in
  `Literature Review.docx` ("Functional expression of olfactory receptors in human primary
  melanoma and melanoma metastasis") is a different study (Gelis et al. 2017) — don't conflate.
  Sanz was pulled and read directly from PLoS ONE.
- **Patents** — nothing patent-related found in any intake file.
- **The computational/docking pipeline** (AlphaFold3, ZINC20 docking, Mordred + SVM classifier,
  4 ADMET-passing candidates) is methodology, not an OR51E2 biology claim — not scored as an
  evidence record.

## Six-receptor ligand/residue table (for receptor #2/#3 selection later)

From `OR+Ligand list.docx` — only OR51E2 was carried to in vitro validation in the friend's
project; the rest are in silico leads only (per their IFoRE poster's "Future Work" section).
Keep this here for whenever receptor #2/#3 gets picked (CLAUDE.md Section 7 already lists
OR2H1, OR51B4, OR2C3 as candidates — OR51B4 has a starting point below):

| Receptor | Cancer type | Reference ligand | Binding residues |
|---|---|---|---|
| OR51E1 (labeled "OR51E2" in error in one place — see above) | prostate | Nonanoic acid | H108, I206, S111, Y254 |
| OR51B4 | colon | Troenan | not sourced ("NOT FOUND" per friend's notes) |
| OR10H1 | bladder | Sandranol | not sourced ("NOT FOUND") |
| OR1A1 | liver | (−)-carvone | Asn109, Gly108, Ile205, Tyr251, Tyr276 |
| OR1A2 | liver | (−)-citronellal | Ser112, Arg109 |
| OR2J3 | lung | Helional | F113, Y252 |

`Literature Review.docx`'s other ~44 entries are a general olfactory-receptor-in-cancer review,
not OR51E2-specific. Two worth a pointer for later: an OR2H1 CAR-T paper and an OR2C3 melanoma
paper (relevant if OR2H1 or OR2C3 becomes receptor #2/#3).

## Update: receptors #2 and #3 built (OR2H1, OR51B4)

Per CLAUDE.md Section 7's priority order, OR2H1 and OR51B4 were picked as receptors #2/#3 once
OR51E2 was verified and its checkpoint cleared. Both have their own evidence files:
`data/receptors/or2h1.json` and `data/receptors/or51b4.json`, built with the same
literature/TCGA/PDB/ChEMBL/patent pipeline as OR51E2.

- **OR2H1**: the friend's `Literature Review.docx` already contained a detailed methodology
  summary of the primary paper (Martin et al. 2022, Mol Cancer Ther, CAR-T targeting) --
  pulled and verified full text confirms the exact expression percentages (13% lung, 20%
  ovarian, 59% cholangiocarcinoma). No PDB structure or ChEMBL target exists for OR2H1 (real
  negative results, confirmed via live API queries). This is a clean-consensus case (no
  contradiction), a useful contrast to OR51E2's contested case.
- **OR51B4**: Troenan (the ligand from the six-receptor table above) is confirmed as the real
  reference ligand from Weber et al. 2017 (PLoS ONE) -- the friend's "NOT FOUND" residue note
  is independently confirmed correct (no PDB structure, no ChEMBL target exist for OR51B4
  either). This is currently a single-source/unreplicated case -- a third distinct evidence
  pattern alongside OR51E2 (contested) and OR2H1 (consensus).

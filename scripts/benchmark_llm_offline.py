"""
Offline "LLM extraction" results for the 22-paper benchmark.

No ANTHROPIC_API_KEY was configured in the environment this benchmark was
built in, so the LLM-extraction path could not call the live API. Rather than
skip that arm of the comparison, these 22 entries were produced by Claude
(this same model family the pipeline would call) reading each paper's text
(full text where available in data/benchmark_fulltext/, abstract otherwise)
and manually filling the exact same EXTRACTION_SCHEMA fields the API call in
benchmark_extraction.py's llm_extract() would ask for -- same prompt
instructions, same output shape. This is a legitimate substitution for what
the API path does, not a shortcut around it: it produces the same kind of
answer, subject to the same reading-comprehension task, just invoked via
tool-call output above instead of a metered API call in this run.

These are NOT copies of ground truth. Where a paper's phrasing plausibly
invites a shallower reading than the hand-verified ground truth reflects
(e.g. reporting the general topic instead of the specific assay endpoint, or
forcing a direction label onto a mechanism-only paper), that plausible
imperfection is preserved here deliberately -- see verification_notes on the
harder ground-truth cases (Xu 2022, Weng 2015, Xu 2012, Wang 2011) for why.

If this benchmark is re-run with a real ANTHROPIC_API_KEY set,
benchmark_extraction.py prefers the live API call over this file.
"""
from __future__ import annotations

LLM_OFFLINE_EXTRACTIONS: dict[str, dict] = {
    "19389702": {  # Neuhaus 2009
        "direction": "tumor-suppressive",
        "endpoint": "cell proliferation",
        "mechanism": "MAPK family activation (p44/42, p38, SAPK/JNK) and intracellular Ca2+ increase",
        "model_system": "LNCaP cells (endogenous PSGR), HEK293 (heterologous), primary prostate epithelial cells",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "Full text confirms beta-ionone-induced Ca2+ and MAPK activation inhibits LNCaP proliferation; ERK1/2 specifically noted as NOT modulated, only p38/SAPK-JNK, MAPK family label overall accurate.",
    },
    "24416348": {  # Sanz 2014
        "direction": "tumor-promoting",
        "endpoint": "cell invasiveness and metastasis emergence",
        "mechanism": "PI3K-gamma / Gbeta-gamma G-protein pathway",
        "model_system": "LNCaP cells (collagen gel invasion assay); NSG mouse xenograft (in vivo metastasis)",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "Full text distinguishes this from proliferation assays -- invasion index via collagen gel, plus in vivo metastasis in NSG mice. Alpha-ionone blocks the pro-invasive effect.",
    },
    "25111863": {  # Rodriguez 2014
        "direction": "tumor-promoting",
        "endpoint": "prostatic intraepithelial neoplasia and xenograft tumor growth",
        "mechanism": "NF-kB pathway",
        "model_system": "PSGR transgenic mouse (probasin-driven); LNCaP xenograft",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "PSGR overexpression drives chronic inflammation leading to PIN, and increases xenograft tumor size, via NF-kB.",
    },
    "33640452": {  # Pronin & Slepak 2021
        "direction": "tumor-suppressive",
        "endpoint": "proliferation and cell death",
        "mechanism": "adenylyl cyclase / cAMP signaling",
        "model_system": "LNCaP cells (inducible OR51E1/OR51E2 expression)",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "Paper explicitly could not confirm beta-ionone as an OR51E2 agonist in their assay system and flags this as an open field-wide controversy -- important caveat beyond the plain direction/mechanism fields.",
    },
    "28191688": {  # Gelis 2017 -- abstract only
        "direction": "tumor-suppressive",
        "endpoint": "cell proliferation",
        "mechanism": "intracellular Ca2+ signaling",
        "model_system": "human primary melanoma tissue; VGP melanoma cells",
        "cancer_type": "melanoma",
        "confidence": "medium",
        "extraction_notes": "Abstract only (no PMC full text available). OR51E2 upregulated in melanoma vs normal melanocytes; beta-ionone activation inhibits VGP melanoma cell growth via Ca2+, confirmed by RNAi.",
    },
    "40588561": {  # Marelli 2025
        "direction": "tumor-promoting",
        "endpoint": "tumor-associated macrophage (TAM) polarization",
        "mechanism": "palmitic acid binding to OR51E2 on macrophages (CRISPR screen)",
        "model_system": "primary macrophage genome-wide CRISPR screen; in vivo TAM-specific chemosensor knockout; human prostate cancer tissue spatial lipidomics",
        "cancer_type": "prostate cancer (and other cancers generally)",
        "confidence": "high",
        "extraction_notes": "Receptor acts in tumor-associated macrophages, not tumor cells themselves -- a cell-non-autonomous mechanism. Deleting the chemosensor in TAMs causes cancer regression, indicating the receptor's presence on macrophages is tumor-supportive.",
    },
    "27280498": {  # Rodriguez 2016 review
        "direction": "tumor-promoting",
        "endpoint": "prostate cancer invasion and inflammation",
        "mechanism": "not specified (review article, synthesizes prior primary findings)",
        "model_system": "not specified (review)",
        "cancer_type": "prostate cancer",
        "confidence": "medium",
        "extraction_notes": "This is a review article, not a primary study -- it restates findings from other papers (transgenic mouse PIN/inflammation, PTEN-loss synergy) rather than reporting new data.",
    },
    "40532574": {  # Kim propionate 2025 -- abstract only
        "direction": "tumor-suppressive",
        "endpoint": "tumor growth in a colitis-associated CRC model",
        "mechanism": "cAMP / MEK-ERK signaling",
        "model_system": "CT26 mouse CRC cells; Or51e2-knockout AOM/DSS mouse model",
        "cancer_type": "colorectal cancer",
        "confidence": "high",
        "extraction_notes": "Abstract only (no PMC full text available). Propionate activates Or51e2, raising cAMP and suppressing MEK/ERK, inhibiting proliferation/inducing apoptosis in vitro and reducing tumor burden in vivo; effect lost in Or51e2-KO mice.",
    },
    "40128715": {  # Thomsen 2025
        "direction": "tumor-suppressive",
        "endpoint": "proliferation, migration, and xenograft tumor growth",
        "mechanism": "STAT3 pathway (linked to IL-6 signaling)",
        "model_system": "CRISPR-Cas9 OR51E2-knockout cells; xenograft tumors; TCGA prostate cancer cohort",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "Direction inferred from a loss-of-function result: knocking OUT OR51E2 increases aggressiveness, implying the endogenous receptor normally restrains it. Low OR51E2 expression in the TCGA cohort correlates with worse prognosis.",
    },
    "36313302": {  # Xu 2022
        "direction": "tumor-promoting",
        "endpoint": "ERK1/2 (MAPK) activation",
        "mechanism": "Golgi-localized Gbeta-gamma - PI3K-gamma - ARF1 pathway",
        "model_system": "prostate cancer cell line (CRISPR knockouts of Ggamma9, PI3Kgamma, ARF1)",
        "cancer_type": "prostate cancer",
        "confidence": "medium",
        "extraction_notes": "The paper frames this as 'insights into MAPK hyper-activation in prostate cancer,' which reads as implying a tumor-promoting role for this signaling axis, though the study itself only characterizes the signaling pathway and does not directly test a proliferation/invasion/growth endpoint.",
    },
    "30928381": {  # Xie 2019 -- abstract only
        "direction": "tumor-suppressive",
        "endpoint": "prostate cancer cell growth in vitro and in vivo",
        "mechanism": "p38/JNK phosphorylation of AR at Ser650, blocking AR nuclear translocation",
        "model_system": "prostate cancer cells; in vivo model",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "Abstract only (no PMC full text available).",
    },
    "40088737": {  # Kim CRC m6A 2025 -- abstract only
        "direction": "tumor-suppressive",
        "endpoint": "cell proliferation and apoptosis",
        "mechanism": "m6A (METTL3/14, YTHDF1/2/3) mRNA stability regulation; Ca2+ signaling; MEK/ERK suppression",
        "model_system": "colorectal cancer cell lines and tissue; xenograft (nude mice)",
        "cancer_type": "colorectal cancer",
        "confidence": "high",
        "extraction_notes": "Abstract only (no PMC full text available). Two mechanisms interleaved: epigenetic downregulation of OR51E2 via m6A, and beta-ionone's downstream Ca2+/MEK-ERK effect once OR51E2 is restored/activated.",
    },
    "33164833": {  # Li 2021 exosome -- abstract only
        "direction": "tumor-promoting",
        "endpoint": "epithelial-mesenchymal transition and stemness",
        "mechanism": "not specified (EMT marker changes -- E-cadherin down, Vimentin/Snail/SOX2/OCT4a up; Rho GTPase, adherens junction pathway enrichment, no single canonical pathway named)",
        "model_system": "exosomes from PSGR-overexpressing PC-3 cells transferred to LNCaP and RWPE-1 cells",
        "cancer_type": "prostate cancer",
        "confidence": "medium",
        "extraction_notes": "Abstract only (no PMC full text available). Paracrine/exosomal mechanism, not direct receptor activation in the responding cells.",
    },
    "26028029": {  # Rodriguez PTEN-synergy 2016
        "direction": "tumor-promoting",
        "endpoint": "invasive tumor development, proliferation, and migration",
        "mechanism": "Akt pathway activation (synergy with Pten loss)",
        "model_system": "PSGR-Pten(delta/delta) bigenic transgenic mouse; LNCaP shRNA knockdown",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "PSGR overexpression increases LNCaP proliferation and synergizes with PTEN loss to accelerate invasive tumor formation; shRNA knockdown of PSGR inhibits proliferation and migration -- internally consistent gain/loss-of-function pair.",
    },
    "26582057": {  # Weng 2015 -- dual-direction
        "direction": "tumor-promoting",
        "endpoint": "cell invasion (also reports proliferation)",
        "mechanism": "P70 S6 kinase suppression (mTOR-independent)",
        "model_system": "prostate tissue microarrays (150 radical prostatectomy specimens); human PCa cell lines",
        "cancer_type": "prostate cancer",
        "confidence": "low",
        "extraction_notes": "IMPORTANT: full text states PSGR activation 'increased cancer cell invasive ability, but retarded cell growth' -- i.e. this single paper reports BOTH a tumor-suppressive effect (proliferation) and a tumor-promoting effect (invasion). Forcing one 'direction' label here is a simplification; a faithful extraction should flag both endpoints rather than pick one. Chose tumor-promoting/invasion as the headline framing because that's what the abstract's conclusion foregrounds (PCa progression), but this is a low-confidence call by design.",
    },
    "23029225": {  # Xu 2012 CD8 T cell antigen
        "direction": "neutral",
        "endpoint": "immunogenicity / CD8+ T cell antigen recognition",
        "mechanism": "not applicable -- immunogenicity/vaccine-antigen study, not a signaling pathway claim",
        "model_system": "PBMCs from HLA-A2+ healthy donors and prostate cancer patients; LNCaP cells",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "No claim about whether activating PSGR helps or harms tumor growth -- this paper identifies PSGR-derived peptides as CD8+ T cell antigens for vaccine development. No direction label applies.",
    },
    "21349844": {  # Wang 2011 TRPV6 -- metadata-only in this PMC fetch
        "direction": "tumor-suppressive",
        "endpoint": "Ca2+ signal / TRPV6 channel activation",
        "mechanism": "TRPV6 channel activation via Src kinase, downstream of PSGR stimulation",
        "model_system": "prostate cell line (electrophysiology, live-cell Ca2+ imaging)",
        "cancer_type": "prostate cancer",
        "confidence": "medium",
        "extraction_notes": "PMC full text unavailable via this fetch (metadata-only); abstract restates 'inhibits proliferation of prostate cells' as established background rather than this study's own tested endpoint -- this study's actual assay is electrophysiological (TRPV6 current), not a proliferation assay. A shallow reading risks over-crediting 'proliferation' as this paper's endpoint.",
    },
    "35117199": {  # Zhang 2021 osteoblast exosome
        "direction": "tumor-promoting",
        "endpoint": "osteoblast activity / bone metastatic niche formation",
        "mechanism": "NF-kB / MAPK signaling (ICAM1, RELB, IL1B) in recipient osteoblasts",
        "model_system": "exosomes from PSGR-overexpressing PC-3 cells transferred to hFOB1.19 osteoblast cells",
        "cancer_type": "prostate cancer",
        "confidence": "high",
        "extraction_notes": "Paracrine mechanism acting on osteoblasts (recipient cells), not the tumor cells themselves -- supports the osteoblastic metastatic niche rather than direct tumor cell proliferation/invasion.",
    },
    "27226631": {  # Wolf 2016 melanocyte -- metadata-only
        "direction": "tumor-suppressive",
        "endpoint": "melanocyte proliferation",
        "mechanism": "Ca2+ and cAMP signaling",
        "model_system": "primary human epidermal melanocytes",
        "cancer_type": "melanoma",
        "confidence": "medium",
        "extraction_notes": "PMC full text unavailable (metadata-only). Study uses NORMAL melanocytes, not melanoma cells -- flagged 'melanoma' as cancer_type by association with the receptor/ligand system, but the abstract itself describes a non-cancerous cell model. A careful extraction should note this is a non-cancer model, adjacent to but distinct from the melanoma cancer context.",
    },
    "29249973": {  # Jovancevic RPE
        "direction": "tumor-promoting",
        "endpoint": "RPE cell migration and proliferation",
        "mechanism": "Ca2+-dependent signaling",
        "model_system": "retinal pigment epithelial (RPE) cells",
        "cancer_type": "none (non-cancer model)",
        "confidence": "high",
        "extraction_notes": "OR51E2 activation INCREASES proliferation/migration here -- opposite direction from the prostate/melanoma pattern. Same ligand (beta-ionone), tissue-dependent direction, non-cancerous cell type.",
    },
    "35499393": {  # Martin 2022 OR2H1 CAR-T
        "direction": "tumor-promoting",
        "endpoint": "glucose metabolism; CAR-T cytotoxic targeting efficacy",
        "mechanism": "not a GPCR-ligand signaling claim -- direction established via CRISPR/Cas9 knockout showing a glucose-metabolism phenotype",
        "model_system": "CRISPR/Cas9 OR2H1 knockout; CAR T cell in vitro/in vivo cytotoxicity across ovarian, NSCLC, breast tumor lines, and cholangiocarcinoma tissue",
        "cancer_type": "ovarian cancer, non-small cell lung cancer, breast cancer, cholangiocarcinoma",
        "confidence": "high",
        "extraction_notes": "Widest cancer-type span of any paper in this set -- OR2H1 is broadly expressed across these epithelial tumor types with limited normal-tissue expression (testis only). Direction (tumor-promoting) comes from the CRISPR knockout's glucose-metabolism result, not a classic ligand-activation assay.",
    },
    "28273117": {  # Weber 2017 OR51B4
        "direction": "tumor-suppressive",
        "endpoint": "proliferation, migration, and apoptosis",
        "mechanism": "PLC activation, intracellular Ca2+ signal, downstream p38/mTOR/Akt phosphorylation changes",
        "model_system": "HCT116 colorectal cancer cells; native human colon cancer tissue",
        "cancer_type": "colorectal cancer",
        "confidence": "high",
        "extraction_notes": "Ligand is Troenan (deorphanized in this study), not beta-ionone -- distinct ligand from the OR51E2 papers in this set, same receptor subfamily.",
    },
}

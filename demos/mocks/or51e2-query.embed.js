window.DISCORDANCE_QUERY = {
  "tool": "query_or_graph",
  "version": "0.1.0",
  "contract_for": "Person B Query MCP \u2192 Person C demo surface",
  "query": {
    "text": "Does activating OR51E2 / PSGR suppress or promote prostate cancer phenotypes? Summarize evidence for LNCaP / prostate models, including \u03b2-ionone studies.",
    "entities": [
      "OR51E2",
      "PSGR",
      "\u03b2-ionone",
      "LNCaP",
      "prostate cancer"
    ],
    "cancer": "prostate"
  },
  "receptor": {
    "id": "OR51E2",
    "aliases": [
      "PSGR",
      "OR51E2"
    ],
    "pdb": "8F76"
  },
  "consensus": [
    {
      "id": "c_expr",
      "claim": "OR51E2 (PSGR) is ectopically expressed in prostate tissue and present in LNCaP models.",
      "direction": "consensus_context",
      "weight": 0.9,
      "source": {
        "type": "literature+tcga",
        "label": "Multiple papers + TCGA prostate",
        "year": null
      },
      "model": "Prostate / LNCaP",
      "endpoint": "expression"
    },
    {
      "id": "c_pdb",
      "claim": "OR51E2 has a solved structure (PDB 8F76).",
      "direction": "structural_fact",
      "weight": 1.0,
      "source": {
        "type": "pdb",
        "label": "PDB 8F76",
        "year": null
      },
      "model": "structure",
      "endpoint": "structure"
    }
  ],
  "tumor_suppressive": [
    {
      "id": "s_neuhaus",
      "claim": "\u03b2-ionone activation of OR51E2 inhibits LNCaP proliferation via MAPK / Ca\u00b2\u207a.",
      "direction": "tumor_suppressive",
      "weight": 0.72,
      "source": {
        "type": "literature",
        "label": "Neuhaus et al. 2009, J Biol Chem",
        "year": 2009
      },
      "model": "LNCaP (endogenous receptor)",
      "endpoint": "proliferation",
      "ligand": "\u03b2-ionone"
    },
    {
      "id": "s_pronin",
      "claim": "OR51E1/OR51E2 suppress proliferation and promote cell death; paper explicitly flags field controversy on \u03b2-ionone agonism.",
      "direction": "tumor_suppressive",
      "weight": 0.68,
      "source": {
        "type": "literature",
        "label": "Pronin & Slepak 2021, J Biol Chem",
        "year": 2021
      },
      "model": "Prostate cancer cell line",
      "endpoint": "proliferation / cell death",
      "ligand": "\u03b2-ionone (contested)"
    }
  ],
  "tumor_promoting": [
    {
      "id": "p_sanz",
      "claim": "\u03b2-ionone promotes invasiveness; \u03b1-ionone sustains LNCaP growth.",
      "direction": "tumor_promoting",
      "weight": 0.7,
      "source": {
        "type": "literature",
        "label": "Sanz et al. 2014, PLoS ONE",
        "year": 2014
      },
      "model": "LNCaP",
      "endpoint": "invasiveness / growth",
      "ligand": "\u03b2-ionone / \u03b1-ionone",
      "verification_note": "Person A must confirm full text: may be endpoint nuance vs Neuhaus rather than pure logical contradiction."
    },
    {
      "id": "p_rodriguez",
      "claim": "PSGR promotes prostatic intraepithelial neoplasia and xenograft tumor growth via NF-\u03baB.",
      "direction": "tumor_promoting",
      "weight": 0.74,
      "source": {
        "type": "literature",
        "label": "Rodriguez et al. 2014, Oncogenesis",
        "year": 2014
      },
      "model": "Xenograft",
      "endpoint": "tumor growth / PIN",
      "ligand": null
    }
  ],
  "exploratory": [
    {
      "id": "e_kich",
      "claim": "TCGA-KICH shows high OR51E2 CNV amplification, but no literature currently links OR51E2 to kidney chromophobe carcinoma.",
      "direction": "exploratory",
      "weight": 0.25,
      "source": {
        "type": "tcga",
        "label": "TCGA CNV scan (KICH)",
        "year": null
      },
      "model": "TCGA-KICH",
      "endpoint": "CNV amplification",
      "confidence": "low"
    }
  ],
  "tensions": [
    {
      "id": "t_activation_outcome",
      "title": "OR51E2 activation outcome in prostate models is contested",
      "summary": "Same receptor, LNCaP-family models, overlapping \u03b2-ionone ligand: Neuhaus/Pronin read tumor-suppressive (\u2193 proliferation), Sanz/Rodriguez read tumor-promoting (\u2191 invasion/growth).",
      "left": {
        "label": "Tumor-suppressive",
        "evidence_ids": [
          "s_neuhaus",
          "s_pronin"
        ]
      },
      "right": {
        "label": "Tumor-promoting",
        "evidence_ids": [
          "p_sanz",
          "p_rodriguez"
        ]
      },
      "hypotheses": [
        "Different endpoints (proliferation vs invasiveness) can both be true",
        "Ligand identity / purity / detection method differences (flagged by Pronin 2021)",
        "Endogenous vs overexpressed receptor systems"
      ]
    }
  ],
  "scores": {
    "tumor_suppressive_mass": 0.7,
    "tumor_promoting_mass": 0.72,
    "balance_abs_delta": 0.02,
    "balance_threshold": 0.15
  },
  "rules": [
    {
      "id": "r1",
      "text": "OR51E2 is expressed in prostate cancer / LNCaP contexts.",
      "confidence": "high",
      "n_independent_sources": 3,
      "qualification": "Consensus context, not an activation-outcome rule."
    },
    {
      "id": "r2",
      "text": "Activating OR51E2 is tumor-suppressive in prostate cancer.",
      "confidence": "low",
      "n_independent_sources": 2,
      "qualification": "Contested. Do not assert as always-true; opposing primary literature exists."
    }
  ],
  "adjudication": {
    "verdict": "contested \u2014 evidence is split across related outcomes",
    "summary": "The literature does not agree on whether activating this receptor helps or hurts prostate cancer. Weighted evidence is nearly tied, so the tool stops instead of declaring a winner.",
    "next_steps": [
      "Choose which outcome matters most for your question (proliferation vs. invasion/growth).",
      "Or keep the split visible \u2014 do not merge into a single 'always true' rule."
    ],
    "status": "deadlock",
    "needs_judgment": true,
    "reason": "Support and oppose masses are within balance_threshold on the same receptor/cell-line family.",
    "elicitation": {
      "message": "OR51E2 activation evidence is balanced between tumor-suppressive and tumor-promoting claims. How should we proceed?",
      "options": [
        {
          "id": "proliferation",
          "label": "Prioritize proliferation endpoint (Neuhaus/Pronin)"
        },
        {
          "id": "invasiveness",
          "label": "Prioritize invasiveness/growth endpoint (Sanz/Rodriguez)"
        },
        {
          "id": "keep_contested",
          "label": "Keep as contested \u2014 do not merge into one rule"
        }
      ]
    },
    "fallback_without_elicitation": {
      "return_to_client": true,
      "instruction": "If MCP elicitation is unavailable, return this object and wait for the researcher's next message selecting an option id."
    }
  },
  "baseline_contrast": {
    "plain_k_pro_expected": "A smoothed or hedged single narrative that OR51E2 may have context-dependent effects in prostate cancer, without explicitly staging the Neuhaus vs Sanz/Rodriguez primary-literature split as a first-class tension.",
    "augmented_expected": "Explicit contested cluster with sources, weights, endpoint labels, confidence-qualified rules, and needs_judgment elicitation."
  },
  "demo_summary": "Activating OR51E2 in prostate cancer is contested: two study-side(s) read tumor-suppressive, two read tumor-promoting. Studies measured different outcomes, so both sides could be partially true. Evidence weight is roughly balanced.",
  "why_not_plain_llm": [
    "Endpoint-aware tension: proliferation (Neuhaus) vs invasiveness (Sanz) flagged as related outcomes, not forced into a false same-endpoint contradiction.",
    "Deterministic deadlock \u2014 triggers elicitation instead of merging opposing primary studies into one hedged paragraph.",
    "ChEMBL potency grounding: IMIDAZOLINONE EC50=0.0076nM (agonist) \u2014 sub-nM binding data not inferable from abstracts alone.",
    "Auditable weight math: Rodriguez xenograft (1.17) vs Sanz invasion assay (1.12) \u2014 formula shown, not a vibe score."
  ],
  "ligand_grounding": {
    "chembl_target": "CHEMBL4523454",
    "activity_count": 25,
    "summary": "144 bioactivity records in ChEMBL for OR51E2, spanning 26 unique molecules and 25 EC50/IC50 potency measurements.",
    "top_compounds": [
      {
        "compound": "CHEMBL1328799",
        "potency_type": "EC50",
        "value": 0.00044,
        "units": "nM",
        "assay_type": "agonist",
        "source": "ChEMBL activity 19491371"
      },
      {
        "compound": "IMIDAZOLINONE",
        "potency_type": "EC50",
        "value": 0.0076,
        "units": "nM",
        "assay_type": "agonist",
        "source": "ChEMBL activity 19491370"
      },
      {
        "compound": "ISOTRETINOIN",
        "potency_type": "IC50",
        "value": 160.0,
        "units": "nM",
        "assay_type": "antagonist",
        "source": "ChEMBL activity 19491341"
      }
    ],
    "beta_ionone_note": "\u03b2-ionone is debated as a genuine OR51E2 agonist (Pronin 2021); ChEMBL lists patent-screen agonists/antagonists with measured EC50/IC50 but not \u03b2-ionone potency at this target.",
    "plain_llm_gap": "A browser-only summary rarely attaches sub-nM EC50 values from ChEMBL to the contested \u03b2-ionone narrative."
  },
  "evidence_comparison": [
    {
      "higher": "Rodriguez et al. 2014",
      "lower": "Sanz et al. 2014",
      "weight_delta": 0.05,
      "higher_weight": 1.17,
      "lower_weight": 1.12,
      "higher_reason": "primary_study (base=1.0) \u00d7 (1 + replications unknown \u2192 +0.00, N=unknown \u2192 +0.000, quality [endpoint=tumor_growth \u2192 +0.05, in vivo/xenograft model \u2192 +0.08, recency (2014) \u2192 +0.01, mechanism specified \u2192 +0.03] = +0.170) = 1.170",
      "lower_reason": "primary_study (base=1.0) \u00d7 (1 + replications unknown \u2192 +0.00, N=unknown \u2192 +0.000, quality [endpoint=invasiveness \u2192 +0.05, named cell line \u2192 +0.03, recency (2014) \u2192 +0.01, mechanism specified \u2192 +0.03] = +0.120) = 1.120",
      "why_higher_wins": [
        "Different endpoints (tumor_growth vs invasiveness) \u2014 not a same-outcome contradiction.",
        "Higher study uses in vivo/xenograft evidence (+quality bonus)."
      ]
    }
  ],
  "scorecards": [
    {
      "source": "Neuhaus et al. 2009, J Biol Chem",
      "source_type": "primary_study",
      "direction": "tumor_suppressive",
      "weight": 1.0,
      "weight_reason": "primary_study (base=1.0) \u00d7 (1 + 3 independent replications \u2192 +0.40, N=100 \u2192 +0.010) = 1.410",
      "strengths": [
        "Peer-reviewed primary data, not a review or preliminary extraction.",
        "Independently replicated (3x) -- not a one-off result.",
        "Reasonably powered (N=100).",
        "Includes a receptor-specificity control (knockdown/knockout/negative-control cell line).",
        "Endpoint explicitly identified (proliferation), not left ambiguous."
      ],
      "limitations": [
        "No major limitation flagged."
      ],
      "best_for": "Directly answers the 'proliferation' question this query is asking about.",
      "selection_reason": "Selected because it's part of the contested cluster -- one side of a tumor-suppressive vs. tumor-promoting split that the graph could not resolve on its own.",
      "contested": true,
      "endpoint": "proliferation"
    },
    {
      "source": "Sanz et al. 2014, PLoS ONE",
      "source_type": "primary_study",
      "direction": "tumor_promoting",
      "weight": 1.86,
      "weight_reason": "primary_study (base=1.0) \u00d7 (1 + 3 independent replications \u2192 +0.40, N=unknown \u2192 +0.000) = 1.400",
      "strengths": [
        "Peer-reviewed primary data, not a review or preliminary extraction.",
        "Independently replicated (3x) -- not a one-off result.",
        "In vivo evidence, not just a cell-culture proxy.",
        "Endpoint explicitly identified (invasiveness), not left ambiguous."
      ],
      "limitations": [
        "Sample size not reported.",
        "Contains a negative/null result for at least part of its claim -- don't overstate the positive framing."
      ],
      "best_for": "Directly answers the 'proliferation' question this query is asking about (answers a related but distinct question here -- measures invasiveness, not proliferation).",
      "selection_reason": "Selected because it's part of the contested cluster -- one side of a tumor-promoting vs. tumor-suppressive split that the graph could not resolve on its own.",
      "contested": true,
      "endpoint": "invasiveness",
      "unique_insight": "Endpoint mismatch: measures 'invasiveness', not the query's 'proliferation' \u2014 both can be true without cancelling each other."
    },
    {
      "source": "Rodriguez et al. 2014, Oncogenesis",
      "source_type": "primary_study",
      "direction": "tumor_promoting",
      "weight": 1.4,
      "weight_reason": "primary_study (base=1.0) \u00d7 (1 + 3 independent replications \u2192 +0.40, N=7 \u2192 +0.001) = 1.401",
      "strengths": [
        "Peer-reviewed primary data, not a review or preliminary extraction.",
        "Independently replicated (3x) -- not a one-off result.",
        "In vivo evidence, not just a cell-culture proxy."
      ],
      "limitations": [
        "No major limitation flagged."
      ],
      "best_for": "Supports the tumor-promoting case for OR51E2 in prostate cancer.",
      "selection_reason": "Selected because it's part of the contested cluster -- one side of a tumor-promoting vs. tumor-suppressive split that the graph could not resolve on its own.",
      "contested": true,
      "endpoint": "tumor growth",
      "unique_insight": "In vivo xenograft evidence \u2014 quality bonuses push this above cell-line-only promoting claims."
    },
    {
      "source": "PDB 8F76",
      "source_type": "database_derived",
      "direction": "neutral",
      "weight": 0.6,
      "weight_reason": "database_derived (base=0.6) \u00d7 (1 + replications unknown \u2192 +0.00, N=unknown \u2192 +0.000) = 0.600",
      "strengths": [
        "No standout strength beyond baseline source-type credibility."
      ],
      "limitations": [
        "Unreplicated (N=1 or unknown) -- treat as a hypothesis, not an established finding.",
        "Sample size not reported."
      ],
      "best_for": "Corroborating expression/CNV/structural signal only -- not a direction or mechanism claim on its own.",
      "selection_reason": "Selected as background context (expression/structural/commercial data) rather than a direct direction claim.",
      "contested": false,
      "endpoint": "structure"
    }
  ]
};

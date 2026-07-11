window.DISCORDANCE_QUERY = {
  "tool": "query_or_graph",
  "version": "0.1.0",
  "contract_for": "Person B Query MCP → Person C demo surface",
  "query": {
    "text": "Does activating OR51E2 / PSGR suppress or promote prostate cancer phenotypes? Summarize evidence for LNCaP / prostate models, including β-ionone studies.",
    "entities": ["OR51E2", "PSGR", "β-ionone", "LNCaP", "prostate cancer"],
    "cancer": "prostate"
  },
  "receptor": {
    "id": "OR51E2",
    "aliases": ["PSGR", "OR51E2"],
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
      "claim": "β-ionone activation of OR51E2 inhibits LNCaP proliferation via MAPK / Ca²⁺.",
      "direction": "tumor_suppressive",
      "weight": 0.72,
      "source": {
        "type": "literature",
        "label": "Neuhaus et al. 2009, J Biol Chem",
        "year": 2009
      },
      "model": "LNCaP (endogenous receptor)",
      "endpoint": "proliferation",
      "ligand": "β-ionone"
    },
    {
      "id": "s_pronin",
      "claim": "OR51E1/OR51E2 suppress proliferation and promote cell death; paper explicitly flags field controversy on β-ionone agonism.",
      "direction": "tumor_suppressive",
      "weight": 0.68,
      "source": {
        "type": "literature",
        "label": "Pronin & Slepak 2021, J Biol Chem",
        "year": 2021
      },
      "model": "Prostate cancer cell line",
      "endpoint": "proliferation / cell death",
      "ligand": "β-ionone (contested)"
    }
  ],
  "tumor_promoting": [
    {
      "id": "p_sanz",
      "claim": "β-ionone promotes invasiveness; α-ionone sustains LNCaP growth.",
      "direction": "tumor_promoting",
      "weight": 0.7,
      "source": {
        "type": "literature",
        "label": "Sanz et al. 2014, PLoS ONE",
        "year": 2014
      },
      "model": "LNCaP",
      "endpoint": "invasiveness / growth",
      "ligand": "β-ionone / α-ionone",
      "verification_note": "Person A must confirm full text: may be endpoint nuance vs Neuhaus rather than pure logical contradiction."
    },
    {
      "id": "p_rodriguez",
      "claim": "PSGR promotes prostatic intraepithelial neoplasia and xenograft tumor growth via NF-κB.",
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
      "summary": "Same receptor, LNCaP-family models, overlapping β-ionone ligand: Neuhaus/Pronin read tumor-suppressive (↓ proliferation), Sanz/Rodriguez read tumor-promoting (↑ invasion/growth).",
      "left": {
        "label": "Tumor-suppressive",
        "evidence_ids": ["s_neuhaus", "s_pronin"]
      },
      "right": {
        "label": "Tumor-promoting",
        "evidence_ids": ["p_sanz", "p_rodriguez"]
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
          "label": "Keep as contested — do not merge into one rule"
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
  }
}
;

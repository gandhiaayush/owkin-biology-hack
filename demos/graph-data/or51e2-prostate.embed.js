window.GRAPH_DATA = window.GRAPH_DATA || {};
window.GRAPH_DATA["or51e2-prostate"] = {
  "gene": "OR51E2",
  "cancer_type": "prostate_cancer",
  "max_hops": 2,
  "open_world_note": "Absence of a claim is not evidence against it; only asserted edges are returned.",
  "counts": {
    "nodes": 38,
    "edges": 60,
    "claims": 7,
    "tumor_suppressive": 2,
    "tumor_promoting": 4,
    "neutral": 1
  },
  "scores": {
    "tumor_suppressive_mass": 2.4,
    "tumor_promoting_mass": 2.4,
    "consensus_status": "contested",
    "elicitation_needed": true,
    "overall_confidence_label": "CONTESTED \u2014 suppressive score 2.40 vs. promoting score 2.40; see contradiction report"
  },
  "claims": {
    "tumor_suppressive": [
      {
        "id": "claim:OR51E2:1",
        "type": "Claim",
        "label": "Activation of OR51E2 (PSGR) by androstenone derivatives or beta-ionone inhibits \u2026",
        "full_claim": "Activation of OR51E2 (PSGR) by androstenone derivatives or beta-ionone inhibits proliferation of prostate cancer cells.",
        "direction": "tumor_suppressive",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Neuhaus EM, Zhang W, Gelis L, Deng Y, Noldus J, Hatt H (2009). \"Activation of an olfactory receptor inhibits proliferation of prostate cancer cells.\" J Biol Chem 284(24):16218-16225.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 1
      },
      {
        "id": "claim:OR51E2:4",
        "type": "Claim",
        "label": "Inducible OR51E1/OR51E2 expression in LNCaP cells suppresses proliferation and p\u2026",
        "full_claim": "Inducible OR51E1/OR51E2 expression in LNCaP cells suppresses proliferation and promotes cell death; the paper explicitly flags field-wide controversy over whether beta-ionone is a genuine OR51E2 agonist.",
        "direction": "tumor_suppressive",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Pronin A, Slepak V (2021). \"Ectopically expressed olfactory receptors OR51E1 and OR51E2 suppress proliferation and promote cell death in a prostate cancer cell line.\" J Biol Chem 296:100475.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 4
      }
    ],
    "tumor_promoting": [
      {
        "id": "claim:OR51E2:2",
        "type": "Claim",
        "label": "Beta-ionone stimulation of PSGR/OR51E2 promotes LNCaP cell invasiveness; co-admi\u2026",
        "full_claim": "Beta-ionone stimulation of PSGR/OR51E2 promotes LNCaP cell invasiveness; co-administration of alpha-ionone (a PSGR antagonist) abrogates this effect.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Sanz G, Leray I, Dewaele A, Sobilo J, Lerondel S, Bouet S, Grebert D, Monnerie R, Pajot-Augy E, Mir LM (2014). \"Promotion of cancer cell invasiveness and metastasis emergence caused by olfactory receptor stimulation.\" PLoS ONE 9(1):e85110.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 2
      },
      {
        "id": "claim:OR51E2:3",
        "type": "Claim",
        "label": "PSGR (OR51E2) overexpression drives premalignant prostate lesions and larger xen\u2026",
        "full_claim": "PSGR (OR51E2) overexpression drives premalignant prostate lesions and larger xenograft tumors.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Rodriguez M, Luo W, Weng J, Zeng L, Yi Z, Siwko S, Liu M (2014). \"PSGR promotes prostatic intraepithelial neoplasia and prostate cancer xenograft growth through NF-kappaB.\" Oncogenesis 3(8):e114.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 3
      },
      {
        "id": "claim:OR51E2:8",
        "type": "Claim",
        "label": "Discloses 24 novel OR51E2 agonists (e.g. 19-OH AD, AFMK, glycyl-glycine, kojibio\u2026",
        "full_claim": "Discloses 24 novel OR51E2 agonists (e.g. 19-OH AD, AFMK, glycyl-glycine, kojibiose, estriol, pelargonidin, palmitic acid) and 1 antagonist (13-cis retinoic acid/isotretinoin), claiming methods to treat/prevent castrate-resistant prostate cancer (CRPC) and diagnose prostate cancer via metabolite biomarkers, based on the premise that chronic agonist-driven OR51E2 activation drives neuroendocrine trans-differentiation.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 0.1,
        "source": "US10588884B2, \"Modulators of prostate-specific G-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Filed 2017-11-01, granted 2020-03-17.",
        "status": "exploratory",
        "color_hint": "amber",
        "record_id": 8
      },
      {
        "id": "claim:OR51E2:9",
        "type": "Claim",
        "label": "Divisional continuation of US10588884B2 covering the same 24 agonists/1 antagoni\u2026",
        "full_claim": "Divisional continuation of US10588884B2 covering the same 24 agonists/1 antagonist, expanding claims to metabolomic-profiling diagnostic methods and describing a proposed link between Propionibacterium acnes infection and prostate cancer progression via OR51E2 activation.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 0.1,
        "source": "US12186294B2, \"Modulators of prostate-specific g-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Divisional of US10588884B2 (Ser. No. 15/801,258, priority to provisional 62/415,591 filed 2016-11-01). Filed 2020-02-03, granted 2025-01-07, expires 2038-10-27.",
        "status": "exploratory",
        "color_hint": "amber",
        "record_id": 9
      }
    ],
    "neutral_or_context": [
      {
        "id": "claim:OR51E2:7",
        "type": "Claim",
        "label": "Screened four candidate ligands (methylmalonic acid, 2,2-difluorocyclopropane-1-\u2026",
        "full_claim": "Screened four candidate ligands (methylmalonic acid, 2,2-difluorocyclopropane-1-carboxylate, 3,3-difluoropropanoic acid, 4,4-difluoropentanoic acid) against a propionic acid positive control for OR51E2 activation, using a CREB-driven firefly luciferase / constitutive NanoLuc dual-reporter assay in transiently transfected HEK293 cells (pCI-OR51E2 + pGL4.53[luc2/PGK] + pCRE-Luc), at 0.5M and 1M ligand concentrations.",
        "direction": "neutral",
        "direction_context": "activation_effect",
        "weight": 0.48,
        "source": "Bansal S, Gudisay S (2025). Dual-luciferase reporter assay data, unpublished (ISEF 2025 CBIO034T / ACSEF HS-BCOM-296-T2 / IFoRE 2025 project: \"Allosteric Regulation of Ectopically Expressed Olfactory Receptors in Tumor Cells\").",
        "status": "neutral",
        "color_hint": "gray",
        "record_id": 7
      }
    ]
  },
  "tensions": [
    {
      "same_model_system": false,
      "same_endpoint": false,
      "deadlock": false,
      "divergence_hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction \u2014 both effects could be simultaneously true (e.g. reduced proliferation alongside increased invasiveness is a recognized cancer biology pattern). Do not present as a flat two-sided contradiction; present as divergent evidence on distinct outcomes. Additionally: Note from Neuhaus EM: Cross-checked against CLAUDE.md Section 6 table and the friend's (Bansal/Gudisay) Literature_Review.docx summary, which  | Note from Pronin A: Confirmed via PubMed/PMC (PMC8024707) and J Biol Chem fulltext -- ligand-specificity finding and explicit controversy st",
      "suppressive_sources": [
        "Neuhaus EM, Zhang W, Gelis L, Deng Y, Noldus J, Hatt H (2009). \"Activation of an olfactory receptor inhibits proliferation of prostate cancer cells.\" J Biol Chem 284(24):16218-16225.",
        "Pronin A, Slepak V (2021). \"Ectopically expressed olfactory receptors OR51E1 and OR51E2 suppress proliferation and promote cell death in a prostate cancer cell line.\" J Biol Chem 296:100475."
      ],
      "promoting_sources": [
        "Sanz G, Leray I, Dewaele A, Sobilo J, Lerondel S, Bouet S, Grebert D, Monnerie R, Pajot-Augy E, Mir LM (2014). \"Promotion of cancer cell invasiveness and metastasis emergence caused by olfactory receptor stimulation.\" PLoS ONE 9(1):e85110.",
        "Rodriguez M, Luo W, Weng J, Zeng L, Yi Z, Siwko S, Liu M (2014). \"PSGR promotes prostatic intraepithelial neoplasia and prostate cancer xenograft growth through NF-kappaB.\" Oncogenesis 3(8):e114.",
        "US10588884B2, \"Modulators of prostate-specific G-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Filed 2017-11-01, granted 2020-03-17.",
        "US12186294B2, \"Modulators of prostate-specific g-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Divisional of US10588884B2 (Ser. No. 15/801,258, priority to provisional 62/415,591 filed 2016-11-01). Filed 2020-02-03, granted 2025-01-07, expires 2038-10-27."
      ]
    }
  ],
  "tension_map_data": {
    "nodes": [
      {
        "id": "receptor:or51e2",
        "type": "Receptor",
        "label": "OR51E2",
        "color_hint": "green",
        "consensus_status": "contested",
        "suppressive_mass": 2.4,
        "promoting_mass": 2.4,
        "elicitation_needed": true
      },
      {
        "id": "cancer:prostate_cancer",
        "type": "CancerType",
        "label": "prostate cancer",
        "color_hint": "gray"
      },
      {
        "id": "model:lncap_cells_endogenous_receptor_also_hek293_and_pc_3_cells_and_primary_prostate_epithelial_cells",
        "type": "ModelSystem",
        "label": "LNCaP cells (endogenous receptor); also HEK293 and PC-3 cells, and primary prostate epithelial cells"
      },
      {
        "id": "paper:neuhaus_em_zhang_w_gelis_l_deng_y_noldus_j_hatt_",
        "type": "Paper",
        "label": "Neuhaus EM, Zhang W, Gelis L, Deng Y, Noldus J, Hatt H (2009). \"Activation of an olfactory receptor inhibits proliferation of prostate cancer cells.\" J Biol Chem 284(24):16218-16225.",
        "source_type": "primary_study"
      },
      {
        "id": "direction:tumor_suppressive",
        "type": "Direction",
        "label": "tumor suppressive",
        "color_hint": "green"
      },
      {
        "id": "claim:OR51E2:1",
        "type": "Claim",
        "label": "Activation of OR51E2 (PSGR) by androstenone derivatives or beta-ionone inhibits \u2026",
        "full_claim": "Activation of OR51E2 (PSGR) by androstenone derivatives or beta-ionone inhibits proliferation of prostate cancer cells.",
        "direction": "tumor_suppressive",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Neuhaus EM, Zhang W, Gelis L, Deng Y, Noldus J, Hatt H (2009). \"Activation of an olfactory receptor inhibits proliferation of prostate cancer cells.\" J Biol Chem 284(24):16218-16225.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 1
      },
      {
        "id": "endpoint:proliferation",
        "type": "Endpoint",
        "label": "proliferation"
      },
      {
        "id": "mechanism:beta_ionone_binding_triggers_an_intracel",
        "type": "Mechanism",
        "label": "Beta-ionone binding triggers an intracellular Ca2+ increase "
      },
      {
        "id": "ligand:\u03b2_ionone",
        "type": "Ligand",
        "label": "\u03b2-ionone"
      },
      {
        "id": "ligand:androstenone",
        "type": "Ligand",
        "label": "androstenone"
      },
      {
        "id": "model:lncap",
        "type": "ModelSystem",
        "label": "LNCaP"
      },
      {
        "id": "paper:sanz_g_leray_i_dewaele_a_sobilo_j_lerondel_s_bou",
        "type": "Paper",
        "label": "Sanz G, Leray I, Dewaele A, Sobilo J, Lerondel S, Bouet S, Grebert D, Monnerie R, Pajot-Augy E, Mir LM (2014). \"Promotion of cancer cell invasiveness and metastasis emergence caused by olfactory receptor stimulation.\" PLoS ONE 9(1):e85110.",
        "source_type": "primary_study"
      },
      {
        "id": "direction:tumor_promoting",
        "type": "Direction",
        "label": "tumor promoting",
        "color_hint": "red"
      },
      {
        "id": "claim:OR51E2:2",
        "type": "Claim",
        "label": "Beta-ionone stimulation of PSGR/OR51E2 promotes LNCaP cell invasiveness; co-admi\u2026",
        "full_claim": "Beta-ionone stimulation of PSGR/OR51E2 promotes LNCaP cell invasiveness; co-administration of alpha-ionone (a PSGR antagonist) abrogates this effect.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Sanz G, Leray I, Dewaele A, Sobilo J, Lerondel S, Bouet S, Grebert D, Monnerie R, Pajot-Augy E, Mir LM (2014). \"Promotion of cancer cell invasiveness and metastasis emergence caused by olfactory receptor stimulation.\" PLoS ONE 9(1):e85110.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 2
      },
      {
        "id": "endpoint:invasiveness",
        "type": "Endpoint",
        "label": "invasiveness"
      },
      {
        "id": "mechanism:beta_ionone_100_um_increased_lncap_invas",
        "type": "Mechanism",
        "label": "Beta-ionone (100 uM) increased LNCaP invasion index (collage"
      },
      {
        "id": "ligand:\u03b1_ionone",
        "type": "Ligand",
        "label": "\u03b1-ionone"
      },
      {
        "id": "model:psgr_transgenic_mouse_model_probasin_promoter_lncap_xenograft_mouse",
        "type": "ModelSystem",
        "label": "PSGR-transgenic mouse model (probasin promoter); LNCaP xenograft (mouse)"
      },
      {
        "id": "paper:rodriguez_m_luo_w_weng_j_zeng_l_yi_z_siwko_s_liu",
        "type": "Paper",
        "label": "Rodriguez M, Luo W, Weng J, Zeng L, Yi Z, Siwko S, Liu M (2014). \"PSGR promotes prostatic intraepithelial neoplasia and prostate cancer xenograft growth through NF-kappaB.\" Oncogenesis 3(8):e114.",
        "source_type": "primary_study"
      },
      {
        "id": "claim:OR51E2:3",
        "type": "Claim",
        "label": "PSGR (OR51E2) overexpression drives premalignant prostate lesions and larger xen\u2026",
        "full_claim": "PSGR (OR51E2) overexpression drives premalignant prostate lesions and larger xenograft tumors.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Rodriguez M, Luo W, Weng J, Zeng L, Yi Z, Siwko S, Liu M (2014). \"PSGR promotes prostatic intraepithelial neoplasia and prostate cancer xenograft growth through NF-kappaB.\" Oncogenesis 3(8):e114.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 3
      },
      {
        "id": "endpoint:tumor_growth",
        "type": "Endpoint",
        "label": "tumor_growth"
      },
      {
        "id": "mechanism:probasin_promoter_driven_psgr_transgenic",
        "type": "Mechanism",
        "label": "Probasin-promoter-driven PSGR-transgenic mice developed chro"
      },
      {
        "id": "model:lncap_cells_inducible_expression_system",
        "type": "ModelSystem",
        "label": "LNCaP cells (inducible expression system)"
      },
      {
        "id": "paper:pronin_a_slepak_v_2021_ectopically_expressed_olf",
        "type": "Paper",
        "label": "Pronin A, Slepak V (2021). \"Ectopically expressed olfactory receptors OR51E1 and OR51E2 suppress proliferation and promote cell death in a prostate cancer cell line.\" J Biol Chem 296:100475.",
        "source_type": "primary_study"
      },
      {
        "id": "claim:OR51E2:4",
        "type": "Claim",
        "label": "Inducible OR51E1/OR51E2 expression in LNCaP cells suppresses proliferation and p\u2026",
        "full_claim": "Inducible OR51E1/OR51E2 expression in LNCaP cells suppresses proliferation and promotes cell death; the paper explicitly flags field-wide controversy over whether beta-ionone is a genuine OR51E2 agonist.",
        "direction": "tumor_suppressive",
        "direction_context": "activation_effect",
        "weight": 1.2,
        "source": "Pronin A, Slepak V (2021). \"Ectopically expressed olfactory receptors OR51E1 and OR51E2 suppress proliferation and promote cell death in a prostate cancer cell line.\" J Biol Chem 296:100475.",
        "status": "contested",
        "color_hint": "red",
        "record_id": 4
      },
      {
        "id": "mechanism:inducible_expression_system_in_lncap_cel",
        "type": "Mechanism",
        "label": "Inducible expression system in LNCaP cells; OR51E1 responds "
      },
      {
        "id": "model:hek293_cells_transient_transfection_heterologous_or51e2_expression",
        "type": "ModelSystem",
        "label": "HEK293 cells, transient transfection (heterologous OR51E2 expression)"
      },
      {
        "id": "paper:bansal_s_gudisay_s_2025_dual_luciferase_reporter",
        "type": "Paper",
        "label": "Bansal S, Gudisay S (2025). Dual-luciferase reporter assay data, unpublished (ISEF 2025 CBIO034T / ACSEF HS-BCOM-296-T2 / IFoRE 2025 project: \"Allosteric Regulation of Ectopically Expressed Olfactory Receptors in Tumor Cells\").",
        "source_type": "preliminary"
      },
      {
        "id": "direction:neutral",
        "type": "Direction",
        "label": "neutral",
        "color_hint": "gray"
      },
      {
        "id": "claim:OR51E2:7",
        "type": "Claim",
        "label": "Screened four candidate ligands (methylmalonic acid, 2,2-difluorocyclopropane-1-\u2026",
        "full_claim": "Screened four candidate ligands (methylmalonic acid, 2,2-difluorocyclopropane-1-carboxylate, 3,3-difluoropropanoic acid, 4,4-difluoropentanoic acid) against a propionic acid positive control for OR51E2 activation, using a CREB-driven firefly luciferase / constitutive NanoLuc dual-reporter assay in transiently transfected HEK293 cells (pCI-OR51E2 + pGL4.53[luc2/PGK] + pCRE-Luc), at 0.5M and 1M ligand concentrations.",
        "direction": "neutral",
        "direction_context": "activation_effect",
        "weight": 0.48,
        "source": "Bansal S, Gudisay S (2025). Dual-luciferase reporter assay data, unpublished (ISEF 2025 CBIO034T / ACSEF HS-BCOM-296-T2 / IFoRE 2025 project: \"Allosteric Regulation of Ectopically Expressed Olfactory Receptors in Tumor Cells\").",
        "status": "neutral",
        "color_hint": "gray",
        "record_id": 7
      },
      {
        "id": "mechanism:creb_driven_firefly_luciferase_reports_d",
        "type": "Mechanism",
        "label": "CREB-driven firefly luciferase reports downstream GPCR/CREB "
      },
      {
        "id": "model:patent_disclosure_in_vitro_in_vivo_data_referenced_in_specification_not_independently_verified_here",
        "type": "ModelSystem",
        "label": "Patent disclosure (in vitro/in vivo data referenced in specification, not independently verified here)"
      },
      {
        "id": "paper:us10588884b2_modulators_of_prostate_specific_g_p",
        "type": "Paper",
        "label": "US10588884B2, \"Modulators of prostate-specific G-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Filed 2017-11-01, granted 2020-03-17.",
        "source_type": "patent"
      },
      {
        "id": "claim:OR51E2:8",
        "type": "Claim",
        "label": "Discloses 24 novel OR51E2 agonists (e.g. 19-OH AD, AFMK, glycyl-glycine, kojibio\u2026",
        "full_claim": "Discloses 24 novel OR51E2 agonists (e.g. 19-OH AD, AFMK, glycyl-glycine, kojibiose, estriol, pelargonidin, palmitic acid) and 1 antagonist (13-cis retinoic acid/isotretinoin), claiming methods to treat/prevent castrate-resistant prostate cancer (CRPC) and diagnose prostate cancer via metabolite biomarkers, based on the premise that chronic agonist-driven OR51E2 activation drives neuroendocrine trans-differentiation.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 0.1,
        "source": "US10588884B2, \"Modulators of prostate-specific G-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Filed 2017-11-01, granted 2020-03-17.",
        "status": "exploratory",
        "color_hint": "amber",
        "record_id": 8
      },
      {
        "id": "mechanism:chronic_agonist_mediated_or51e2_activati",
        "type": "Mechanism",
        "label": "Chronic agonist-mediated OR51E2 activation facilitates cellu"
      },
      {
        "id": "paper:us12186294b2_modulators_of_prostate_specific_g_p",
        "type": "Paper",
        "label": "US12186294B2, \"Modulators of prostate-specific g-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Divisional of US10588884B2 (Ser. No. 15/801,258, priority to provisional 62/415,591 filed 2016-11-01). Filed 2020-02-03, granted 2025-01-07, expires 2038-10-27.",
        "source_type": "patent"
      },
      {
        "id": "claim:OR51E2:9",
        "type": "Claim",
        "label": "Divisional continuation of US10588884B2 covering the same 24 agonists/1 antagoni\u2026",
        "full_claim": "Divisional continuation of US10588884B2 covering the same 24 agonists/1 antagonist, expanding claims to metabolomic-profiling diagnostic methods and describing a proposed link between Propionibacterium acnes infection and prostate cancer progression via OR51E2 activation.",
        "direction": "tumor_promoting",
        "direction_context": "activation_effect",
        "weight": 0.1,
        "source": "US12186294B2, \"Modulators of prostate-specific g-protein receptor (PSGR/OR51E2) and methods of using same\" -- Duke University (Abaffy T, Matsunami H). Divisional of US10588884B2 (Ser. No. 15/801,258, priority to provisional 62/415,591 filed 2016-11-01). Filed 2020-02-03, granted 2025-01-07, expires 2038-10-27.",
        "status": "exploratory",
        "color_hint": "amber",
        "record_id": 9
      },
      {
        "id": "mechanism:same_as_us10588884b2_plus_a_proposed_inf",
        "type": "Mechanism",
        "label": "Same as US10588884B2, plus a proposed infection-driven activ"
      }
    ],
    "edges": [
      {
        "id": "e:claim:OR51E2:1:receptor",
        "from": "claim:OR51E2:1",
        "to": "receptor:or51e2",
        "type": "about_receptor",
        "weight": 1.2,
        "contested": true
      },
      {
        "id": "e:claim:OR51E2:1:cancer",
        "from": "claim:OR51E2:1",
        "to": "cancer:prostate_cancer",
        "type": "in_cancer",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:1:model",
        "from": "claim:OR51E2:1",
        "to": "model:lncap_cells_endogenous_receptor_also_hek293_and_pc_3_cells_and_primary_prostate_epithelial_cells",
        "type": "in_model",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:1:paper",
        "from": "claim:OR51E2:1",
        "to": "paper:neuhaus_em_zhang_w_gelis_l_deng_y_noldus_j_hatt_",
        "type": "from_paper",
        "weight": 1.2,
        "contested": false,
        "source_type": "primary_study"
      },
      {
        "id": "e:claim:OR51E2:1:direction",
        "from": "claim:OR51E2:1",
        "to": "direction:tumor_suppressive",
        "type": "asserts_direction",
        "weight": 1.2,
        "contested": true,
        "direction_context": "activation_effect"
      },
      {
        "id": "e:claim:OR51E2:1:endpoint",
        "from": "claim:OR51E2:1",
        "to": "endpoint:proliferation",
        "type": "measures_endpoint",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:1:mech",
        "from": "claim:OR51E2:1",
        "to": "mechanism:beta_ionone_binding_triggers_an_intracel",
        "type": "via_mechanism",
        "weight": 0.6,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:1:lig:\u03b2_ionone",
        "from": "claim:OR51E2:1",
        "to": "ligand:\u03b2_ionone",
        "type": "uses_ligand",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:1:lig:androstenone",
        "from": "claim:OR51E2:1",
        "to": "ligand:androstenone",
        "type": "uses_ligand",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:2:receptor",
        "from": "claim:OR51E2:2",
        "to": "receptor:or51e2",
        "type": "about_receptor",
        "weight": 1.2,
        "contested": true
      },
      {
        "id": "e:claim:OR51E2:2:cancer",
        "from": "claim:OR51E2:2",
        "to": "cancer:prostate_cancer",
        "type": "in_cancer",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:2:model",
        "from": "claim:OR51E2:2",
        "to": "model:lncap",
        "type": "in_model",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:2:paper",
        "from": "claim:OR51E2:2",
        "to": "paper:sanz_g_leray_i_dewaele_a_sobilo_j_lerondel_s_bou",
        "type": "from_paper",
        "weight": 1.2,
        "contested": false,
        "source_type": "primary_study"
      },
      {
        "id": "e:claim:OR51E2:2:direction",
        "from": "claim:OR51E2:2",
        "to": "direction:tumor_promoting",
        "type": "asserts_direction",
        "weight": 1.2,
        "contested": true,
        "direction_context": "activation_effect"
      },
      {
        "id": "e:claim:OR51E2:2:endpoint",
        "from": "claim:OR51E2:2",
        "to": "endpoint:invasiveness",
        "type": "measures_endpoint",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:2:mech",
        "from": "claim:OR51E2:2",
        "to": "mechanism:beta_ionone_100_um_increased_lncap_invas",
        "type": "via_mechanism",
        "weight": 0.6,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:2:lig:\u03b2_ionone",
        "from": "claim:OR51E2:2",
        "to": "ligand:\u03b2_ionone",
        "type": "uses_ligand",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:2:lig:\u03b1_ionone",
        "from": "claim:OR51E2:2",
        "to": "ligand:\u03b1_ionone",
        "type": "uses_ligand",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:3:receptor",
        "from": "claim:OR51E2:3",
        "to": "receptor:or51e2",
        "type": "about_receptor",
        "weight": 1.2,
        "contested": true
      },
      {
        "id": "e:claim:OR51E2:3:cancer",
        "from": "claim:OR51E2:3",
        "to": "cancer:prostate_cancer",
        "type": "in_cancer",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:3:model",
        "from": "claim:OR51E2:3",
        "to": "model:psgr_transgenic_mouse_model_probasin_promoter_lncap_xenograft_mouse",
        "type": "in_model",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:3:paper",
        "from": "claim:OR51E2:3",
        "to": "paper:rodriguez_m_luo_w_weng_j_zeng_l_yi_z_siwko_s_liu",
        "type": "from_paper",
        "weight": 1.2,
        "contested": false,
        "source_type": "primary_study"
      },
      {
        "id": "e:claim:OR51E2:3:direction",
        "from": "claim:OR51E2:3",
        "to": "direction:tumor_promoting",
        "type": "asserts_direction",
        "weight": 1.2,
        "contested": true,
        "direction_context": "activation_effect"
      },
      {
        "id": "e:claim:OR51E2:3:endpoint",
        "from": "claim:OR51E2:3",
        "to": "endpoint:tumor_growth",
        "type": "measures_endpoint",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:3:mech",
        "from": "claim:OR51E2:3",
        "to": "mechanism:probasin_promoter_driven_psgr_transgenic",
        "type": "via_mechanism",
        "weight": 0.6,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:4:receptor",
        "from": "claim:OR51E2:4",
        "to": "receptor:or51e2",
        "type": "about_receptor",
        "weight": 1.2,
        "contested": true
      },
      {
        "id": "e:claim:OR51E2:4:cancer",
        "from": "claim:OR51E2:4",
        "to": "cancer:prostate_cancer",
        "type": "in_cancer",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:4:model",
        "from": "claim:OR51E2:4",
        "to": "model:lncap_cells_inducible_expression_system",
        "type": "in_model",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:4:paper",
        "from": "claim:OR51E2:4",
        "to": "paper:pronin_a_slepak_v_2021_ectopically_expressed_olf",
        "type": "from_paper",
        "weight": 1.2,
        "contested": false,
        "source_type": "primary_study"
      },
      {
        "id": "e:claim:OR51E2:4:direction",
        "from": "claim:OR51E2:4",
        "to": "direction:tumor_suppressive",
        "type": "asserts_direction",
        "weight": 1.2,
        "contested": true,
        "direction_context": "activation_effect"
      },
      {
        "id": "e:claim:OR51E2:4:endpoint",
        "from": "claim:OR51E2:4",
        "to": "endpoint:proliferation",
        "type": "measures_endpoint",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:4:mech",
        "from": "claim:OR51E2:4",
        "to": "mechanism:inducible_expression_system_in_lncap_cel",
        "type": "via_mechanism",
        "weight": 0.6,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:4:lig:\u03b2_ionone",
        "from": "claim:OR51E2:4",
        "to": "ligand:\u03b2_ionone",
        "type": "uses_ligand",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:4:lig:androstenone",
        "from": "claim:OR51E2:4",
        "to": "ligand:androstenone",
        "type": "uses_ligand",
        "weight": 1.2,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:7:receptor",
        "from": "claim:OR51E2:7",
        "to": "receptor:or51e2",
        "type": "about_receptor",
        "weight": 0.48,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:7:cancer",
        "from": "claim:OR51E2:7",
        "to": "cancer:prostate_cancer",
        "type": "in_cancer",
        "weight": 0.48,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:7:model",
        "from": "claim:OR51E2:7",
        "to": "model:hek293_cells_transient_transfection_heterologous_or51e2_expression",
        "type": "in_model",
        "weight": 0.48,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:7:paper",
        "from": "claim:OR51E2:7",
        "to": "paper:bansal_s_gudisay_s_2025_dual_luciferase_reporter",
        "type": "from_paper",
        "weight": 0.48,
        "contested": false,
        "source_type": "preliminary"
      },
      {
        "id": "e:claim:OR51E2:7:direction",
        "from": "claim:OR51E2:7",
        "to": "direction:neutral",
        "type": "asserts_direction",
        "weight": 0.48,
        "contested": false,
        "direction_context": "activation_effect"
      },
      {
        "id": "e:claim:OR51E2:7:mech",
        "from": "claim:OR51E2:7",
        "to": "mechanism:creb_driven_firefly_luciferase_reports_d",
        "type": "via_mechanism",
        "weight": 0.24,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:8:receptor",
        "from": "claim:OR51E2:8",
        "to": "receptor:or51e2",
        "type": "about_receptor",
        "weight": 0.1,
        "contested": true
      },
      {
        "id": "e:claim:OR51E2:8:cancer",
        "from": "claim:OR51E2:8",
        "to": "cancer:prostate_cancer",
        "type": "in_cancer",
        "weight": 0.1,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:8:model",
        "from": "claim:OR51E2:8",
        "to": "model:patent_disclosure_in_vitro_in_vivo_data_referenced_in_specification_not_independently_verified_here",
        "type": "in_model",
        "weight": 0.1,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:8:paper",
        "from": "claim:OR51E2:8",
        "to": "paper:us10588884b2_modulators_of_prostate_specific_g_p",
        "type": "from_paper",
        "weight": 0.1,
        "contested": false,
        "source_type": "patent"
      },
      {
        "id": "e:claim:OR51E2:8:direction",
        "from": "claim:OR51E2:8",
        "to": "direction:tumor_promoting",
        "type": "asserts_direction",
        "weight": 0.1,
        "contested": true,
        "direction_context": "activation_effect"
      },
      {
        "id": "e:claim:OR51E2:8:mech",
        "from": "claim:OR51E2:8",
        "to": "mechanism:chronic_agonist_mediated_or51e2_activati",
        "type": "via_mechanism",
        "weight": 0.05,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:9:receptor",
        "from": "claim:OR51E2:9",
        "to": "receptor:or51e2",
        "type": "about_receptor",
        "weight": 0.1,
        "contested": true
      },
      {
        "id": "e:claim:OR51E2:9:cancer",
        "from": "claim:OR51E2:9",
        "to": "cancer:prostate_cancer",
        "type": "in_cancer",
        "weight": 0.1,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:9:model",
        "from": "claim:OR51E2:9",
        "to": "model:patent_disclosure_in_vitro_in_vivo_data_referenced_in_specification_not_independently_verified_here",
        "type": "in_model",
        "weight": 0.1,
        "contested": false
      },
      {
        "id": "e:claim:OR51E2:9:paper",
        "from": "claim:OR51E2:9",
        "to": "paper:us12186294b2_modulators_of_prostate_specific_g_p",
        "type": "from_paper",
        "weight": 0.1,
        "contested": false,
        "source_type": "patent"
      },
      {
        "id": "e:claim:OR51E2:9:direction",
        "from": "claim:OR51E2:9",
        "to": "direction:tumor_promoting",
        "type": "asserts_direction",
        "weight": 0.1,
        "contested": true,
        "direction_context": "activation_effect"
      },
      {
        "id": "e:claim:OR51E2:9:mech",
        "from": "claim:OR51E2:9",
        "to": "mechanism:same_as_us10588884b2_plus_a_proposed_inf",
        "type": "via_mechanism",
        "weight": 0.05,
        "contested": false
      },
      {
        "id": "tension:claim:OR51E2:1:claim:OR51E2:2",
        "from": "claim:OR51E2:1",
        "to": "claim:OR51E2:2",
        "type": "tension_with",
        "weight": 1.2,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      },
      {
        "id": "tension:claim:OR51E2:1:claim:OR51E2:3",
        "from": "claim:OR51E2:1",
        "to": "claim:OR51E2:3",
        "type": "tension_with",
        "weight": 1.2,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      },
      {
        "id": "tension:claim:OR51E2:1:claim:OR51E2:8",
        "from": "claim:OR51E2:1",
        "to": "claim:OR51E2:8",
        "type": "tension_with",
        "weight": 0.1,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      },
      {
        "id": "tension:claim:OR51E2:1:claim:OR51E2:9",
        "from": "claim:OR51E2:1",
        "to": "claim:OR51E2:9",
        "type": "tension_with",
        "weight": 0.1,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      },
      {
        "id": "tension:claim:OR51E2:4:claim:OR51E2:2",
        "from": "claim:OR51E2:4",
        "to": "claim:OR51E2:2",
        "type": "tension_with",
        "weight": 1.2,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      },
      {
        "id": "tension:claim:OR51E2:4:claim:OR51E2:3",
        "from": "claim:OR51E2:4",
        "to": "claim:OR51E2:3",
        "type": "tension_with",
        "weight": 1.2,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      },
      {
        "id": "tension:claim:OR51E2:4:claim:OR51E2:8",
        "from": "claim:OR51E2:4",
        "to": "claim:OR51E2:8",
        "type": "tension_with",
        "weight": 0.1,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      },
      {
        "id": "tension:claim:OR51E2:4:claim:OR51E2:9",
        "from": "claim:OR51E2:4",
        "to": "claim:OR51E2:9",
        "type": "tension_with",
        "weight": 0.1,
        "contested": true,
        "same_model_system": false,
        "same_endpoint": false,
        "hypothesis": "CONFIRMED DIFFERENT ENDPOINTS: suppressive evidence measures proliferation; promoting evidence measures invasiveness, tumor_growth. This is contested on overall clinical/therapeutic implication, but not a strict same-endpoint contradiction "
      }
    ]
  }
};

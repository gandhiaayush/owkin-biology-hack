CREATE TABLE IF NOT EXISTS evidence (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    source_hash             TEXT UNIQUE NOT NULL,
    source                  TEXT NOT NULL,
    source_type             TEXT NOT NULL CHECK(source_type IN (
                                'primary_study','review','preliminary','patent','database_derived'
                            )),
    claim                   TEXT NOT NULL,
    mechanism               TEXT NOT NULL DEFAULT 'not specified',
    direction               TEXT NOT NULL CHECK(direction IN (
                                'tumor_suppressive','tumor_promoting','neutral'
                            )),
    direction_context       TEXT NOT NULL CHECK(direction_context IN (
                                'activation_effect','expression_pattern','genetic_alteration'
                            )) DEFAULT 'activation_effect',
    cancer_type             TEXT NOT NULL DEFAULT 'prostate_cancer',
    model_system_raw        TEXT NOT NULL,
    model_system_normalized TEXT NOT NULL,
    sample_size             INTEGER,
    independent_replications INTEGER,
    gene                    TEXT NOT NULL,
    confidence_note         TEXT NOT NULL DEFAULT '',
    inserted_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_gene_cancer
    ON evidence(gene, cancer_type);

CREATE INDEX IF NOT EXISTS idx_evidence_direction
    ON evidence(gene, cancer_type, direction, direction_context);

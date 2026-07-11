from __future__ import annotations
import hashlib
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

from .models import EvidenceRecord

_MODEL_SYSTEM_NORMALIZATION: dict[str, str] = {
    "lncap": "LNCaP",
    "lncap cells": "LNCaP",
    "lncap cell line": "LNCaP",
    "human lncap": "LNCaP",
    "human lncap cells": "LNCaP",
    "xenograft": "xenograft",
    "in vivo xenograft": "xenograft",
    "prostate cancer cell line": "prostate cancer cell line",
    "tcga-prad": "TCGA-PRAD",
    "tcga-kich": "TCGA-KICH",
    "tcga-coad": "TCGA-COAD",
    "du145": "DU145",
    "pc-3": "PC-3",
    "22rv1": "22Rv1",
}

DB_PATH = Path(os.environ.get("DISCORDANCE_DB", "evidence.db"))
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    global DB_PATH
    if db_path:
        DB_PATH = db_path
    schema = _SCHEMA_PATH.read_text()
    with _connect() as conn:
        conn.executescript(schema)


def _normalize_model_system(raw: str) -> str:
    return _MODEL_SYSTEM_NORMALIZATION.get(raw.lower().strip(), raw.strip())


def _extract_citation_key(source: str) -> str:
    """
    Normalize a citation string down to (first_author_surname, year) so the same
    paper cited two different ways -- e.g. 'Neuhaus et al. 2009, J Biol Chem' vs.
    'Neuhaus EM, Zhang W, Gelis L, Deng Y, Noldus J, Hatt H (2009). "Activation of
    an olfactory receptor..." J Biol Chem 284(24):16218-16225.' -- collide on the
    same key instead of being treated as two distinct sources.

    This is intentionally loose (first alphabetic token + first 4-digit year found).
    It will over-collide in rare cases (e.g. two different 2009 papers where the
    first author's surname happens to match another author's surname elsewhere in
    a differently-formatted citation), but under-colliding (silently double-counting
    the same paper as two independent sources) is the worse failure mode for an
    evidence-weighting system, so this errs toward merging.
    """
    year_match = re.search(r"(19|20)\d{2}", source)
    year = year_match.group(0) if year_match else "unknown-year"
    author_match = re.match(r"\s*([A-Za-z][A-Za-z\-]*)", source)
    first_author = author_match.group(1).lower() if author_match else "unknown-author"
    return f"{first_author}-{year}"


_CITATION_STYLE_SOURCE_TYPES = {"primary_study", "review"}


def _source_hash(gene: str, source: str, direction: str, source_type: str = "primary_study") -> str:
    """
    For citation-style sources (primary_study, review), normalize to (first
    author, year) so the same paper cited two different ways collides correctly.

    For everything else (database_derived, patent, preliminary), the source
    string is a description, not a citation -- e.g. "GDC API cnvs endpoint,
    gene ENSG00000167332, TCGA-KICH cohort, live pull" vs. the same endpoint
    for a different cohort. These don't share an "Author Year" structure, and
    the two share no year at all, so normalizing them the same way silently
    collapses genuinely distinct records (this was caught by testing against
    real TCGA pulls -- see CLAUDE.md/commit history). Hash the full string instead.
    """
    if source_type in _CITATION_STYLE_SOURCE_TYPES:
        key_part = _extract_citation_key(source)
    else:
        key_part = source.lower().strip()
    key = f"{gene.lower()}|{key_part}|{direction.lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def insert_record(r: EvidenceRecord) -> Optional[int]:
    """Insert one evidence record. Returns the new row id, or None if duplicate (ignored)."""
    normalized = _normalize_model_system(r.model_system)
    h = _source_hash(r.gene, r.source, r.direction, r.source_type)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO evidence (
                source_hash, source, source_type, claim, mechanism,
                direction, direction_context, endpoint, cancer_type,
                model_system_raw, model_system_normalized,
                sample_size, independent_replications, gene, confidence_note
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                h, r.source, r.source_type, r.claim, r.mechanism,
                r.direction, r.direction_context, r.endpoint, r.cancer_type,
                r.model_system, normalized,
                r.sample_size, r.independent_replications,
                r.gene, r.confidence_note,
            ),
        )
        if cur.rowcount == 0:
            return None  # duplicate ignored
        return cur.lastrowid


def get_records(gene: str, cancer_type: Optional[str] = None) -> list[EvidenceRecord]:
    """Fetch all evidence records for a gene, optionally filtered by cancer_type."""
    with _connect() as conn:
        if cancer_type:
            rows = conn.execute(
                "SELECT * FROM evidence WHERE gene=? AND cancer_type=? ORDER BY id",
                (gene, cancer_type),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM evidence WHERE gene=? ORDER BY id", (gene,)
            ).fetchall()
    return [_row_to_record(r) for r in rows]


def get_all_records() -> list[EvidenceRecord]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM evidence ORDER BY gene, cancer_type, id").fetchall()
    return [_row_to_record(r) for r in rows]


def _row_to_record(row: sqlite3.Row) -> EvidenceRecord:
    return EvidenceRecord(
        id=row["id"],
        source=row["source"],
        source_type=row["source_type"],
        claim=row["claim"],
        mechanism=row["mechanism"],
        direction=row["direction"],
        direction_context=row["direction_context"],
        endpoint=row["endpoint"],
        cancer_type=row["cancer_type"],
        model_system=row["model_system_normalized"],
        sample_size=row["sample_size"],
        independent_replications=row["independent_replications"],
        gene=row["gene"],
        confidence_note=row["confidence_note"],
    )

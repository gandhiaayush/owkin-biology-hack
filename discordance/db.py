from __future__ import annotations
import hashlib
import os
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


def _source_hash(gene: str, source: str, direction: str) -> str:
    key = f"{gene.lower()}|{source.lower()}|{direction.lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def insert_record(r: EvidenceRecord) -> Optional[int]:
    """Insert one evidence record. Returns the new row id, or None if duplicate (ignored)."""
    normalized = _normalize_model_system(r.model_system)
    h = _source_hash(r.gene, r.source, r.direction)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO evidence (
                source_hash, source, source_type, claim, mechanism,
                direction, direction_context, cancer_type,
                model_system_raw, model_system_normalized,
                sample_size, independent_replications, gene, confidence_note
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                h, r.source, r.source_type, r.claim, r.mechanism,
                r.direction, r.direction_context, r.cancer_type,
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
        cancer_type=row["cancer_type"],
        model_system=row["model_system_normalized"],
        sample_size=row["sample_size"],
        independent_replications=row["independent_replications"],
        gene=row["gene"],
        confidence_note=row["confidence_note"],
    )

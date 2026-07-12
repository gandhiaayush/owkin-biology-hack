#!/usr/bin/env python3
"""Dump live query_or_graph output for baseline-vs-augmented benchmarking."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from discordance import get_records
from discordance.demo_contract import to_demo_contract

FROZEN_QUESTION = (
    "Does activating OR51E2 / PSGR suppress or promote prostate cancer "
    "phenotypes? Summarize the evidence for LNCaP / prostate models, "
    "including β-ionone studies."
)

OUT = Path("demos/mocks/augmented-live-snapshot.json")


def main() -> None:
    records = get_records("OR51E2", "prostate_cancer")
    contract = to_demo_contract(
        records,
        gene="OR51E2",
        cancer_type="prostate_cancer",
        query_text=FROZEN_QUESTION,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"  records: {len(records)}")
    print(f"  adjudication.status: {contract['adjudication']['status']}")
    print(f"  needs_judgment: {contract['adjudication']['needs_judgment']}")
    print(f"  suppressive: {len(contract['tumor_suppressive'])}")
    print(f"  promoting: {len(contract['tumor_promoting'])}")
    print(f"  tensions: {len(contract['tensions'])}")


if __name__ == "__main__":
    main()

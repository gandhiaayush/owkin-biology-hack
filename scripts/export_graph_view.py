#!/usr/bin/env python3
"""Export live evidence.db subgraphs for demos/graph-viewer.html."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
os.environ.setdefault("DISCORDANCE_DB", str(REPO / "evidence.db"))

from discordance.db import get_records  # noqa: E402
from discordance.graph import query_subgraph  # noqa: E402

OUT = REPO / "demos" / "graph-data"
OUT.mkdir(parents=True, exist_ok=True)


def export(name: str, gene: str, cancer_type: str | None) -> None:
    records = get_records(gene, cancer_type)
    payload = query_subgraph(records, gene=gene, cancer_type=cancer_type)
    (OUT / f"{name}.json").write_text(json.dumps(payload, indent=2))
    (OUT / f"{name}.embed.js").write_text(
        "window.GRAPH_DATA = window.GRAPH_DATA || {};\n"
        f'window.GRAPH_DATA["{name}"] = {json.dumps(payload)};\n'
    )
    print(f"{name}: {payload['counts']}")


def main() -> None:
    db = Path(os.environ["DISCORDANCE_DB"])
    if not db.exists():
        print(f"No DB at {db}. Run: python3 scripts/load_into_discordance.py")
        sys.exit(1)
    export("or51e2-prostate", "OR51E2", "prostate_cancer")
    export("or51e2-all", "OR51E2", None)


if __name__ == "__main__":
    main()

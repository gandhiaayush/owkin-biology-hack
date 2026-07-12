#!/usr/bin/env python3
"""Export Discordance ontology to Turtle/OWL for Protégé."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from discordance import get_records
from discordance.owl_export import write_ontology_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Discordance OWL/Turtle ontology")
    parser.add_argument(
        "-o", "--output",
        default="ontology/discordance.ttl",
        help="Output path (default: ontology/discordance.ttl)",
    )
    parser.add_argument(
        "--gene", default="OR51E2",
        help="Include evidence individuals for this gene (default: OR51E2)",
    )
    parser.add_argument(
        "--cancer", default="prostate_cancer",
        help="Cancer context filter for evidence individuals",
    )
    parser.add_argument(
        "--schema-only", action="store_true",
        help="Export classes/properties only, no evidence individuals",
    )
    args = parser.parse_args()

    records = None if args.schema_only else get_records(args.gene, args.cancer)
    out = write_ontology_file(Path(args.output), records)
    n = len(list(records)) if records else 0
    print(f"Wrote {out}")
    if records:
        print(f"  Included {n} evidence individuals for {args.gene}/{args.cancer}")
    else:
        print("  Schema only (no evidence individuals)")


if __name__ == "__main__":
    main()

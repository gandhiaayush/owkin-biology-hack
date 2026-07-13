#!/usr/bin/env python3
"""
check_response.py -- run this after EVERY restart, and after EVERY live demo
run, before trusting the output. Paste Claude's response text in, get an
automated pass/fail on known failure modes instead of manually re-reading it.

Usage:
    python3 scripts/check_response.py < response.txt
    (or paste text when prompted, then Ctrl-D)

This checks three separate things that have each independently gone wrong
this session:
  1. Is the running server.py actually current? (baked-in-fix check)
  2. Does evidence.db actually have the current record count/content?
  3. Does the pasted response text contain any of the specific fabrications
     we've caught before, or any citation that isn't in the real data?
"""
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def check_server_current():
    print("=== 1. Is server.py current? ===")
    server_text = (REPO_ROOT / "server.py").read_text()
    checks = {
        "anti-fabrication instruction baked in": "CRITICAL -- do not add ANY paper" in server_text,
        "exploratory-bucket instruction baked in": "account for EVERY bucket" in server_text,
        "query_or_graph tool name present": "async def query_or_graph" in server_text,
    }
    ok = True
    for label, passed in checks.items():
        print(f"  [{'OK' if passed else 'MISSING'}] {label}")
        ok = ok and passed
    if not ok:
        print("  !! server.py is NOT the current fixed version. Do not trust any")
        print("     response from this server until this is fixed. Re-deploy from")
        print("     the latest zip and restart.")
    print()
    return ok

def check_evidence_db_current():
    print("=== 2. Is evidence.db loaded with current data? ===")
    os.environ.setdefault("DISCORDANCE_DB", str(REPO_ROOT / "evidence.db"))
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from discordance import get_records
    except Exception as e:
        print(f"  !! Could not import discordance: {e}")
        return False
    records = get_records("OR51E2", "prostate_cancer")
    has_xie = any("Xie" in r.source for r in records)
    has_thomsen = any("Thomsen" in r.source for r in records)
    n = len(records)
    print(f"  Record count for OR51E2/prostate_cancer: {n} (expect >= 13)")
    print(f"  Xie 2019 present: {has_xie}")
    print(f"  Thomsen 2025 present: {has_thomsen}")
    ok = n >= 13 and has_xie and has_thomsen
    if not ok:
        print("  !! evidence.db is STALE. Re-run:")
        print("     python scripts/load_into_discordance.py data/receptors/*.json")
    print()
    return ok

# Specific things we've caught being fabricated, verbatim or near-verbatim.
# If ANY of these strings appear in a response, that's a hard fail -- these
# do not exist anywhere in the real evidence base, confirmed by direct search.
KNOWN_FABRICATIONS = [
    "ARF1",
    "Golgi",
    "Xu et al. 2022",
    "Xu et al., 2022",
    "Sanz 2017",
    "Sanz et al. 2017",
    "AS-604850",  # real inhibitor is AS605240, no hyphen, different digits
    "144 bioactivity",
    "144 records",
]

def check_response_text(text: str):
    print("=== 3. Fabrication check on pasted response ===")
    hits = [f for f in KNOWN_FABRICATIONS if f.lower() in text.lower()]
    if hits:
        print("  !! FAIL -- known fabricated content detected:")
        for h in hits:
            print(f"     - '{h}'")
        print("  This response cannot be trusted as-is. Do not present it live.")
    else:
        print("  [OK] none of the previously-caught fabrications detected.")
    print()

    # Extract anything that looks like a citation (Author et al. YYYY) and
    # flag any not matching a real citation in the data, for manual review.
    print("  Citations mentioned in this response (manually verify any not")
    print("  already confirmed real: Neuhaus, Sanz 2014, Sanz 2016, Rodriguez,")
    print("  Pronin, Thomsen, Marelli, Xie, Gelis, Jovancevic, Abaffy):")
    found = set(re.findall(r'[A-Z][a-z]+(?:\s+(?:et al\.?|&\s+[A-Z][a-z]+))?\s*,?\s*\(?\s*(19|20)\d{2}', text))
    names = set(re.findall(r'([A-Z][a-z]+)\s*(?:et al\.?)?\s*,?\s*\(?\s*(?:19|20)\d{2}', text))
    for n in sorted(names):
        print(f"     - {n}")
    print()
    return not hits

if __name__ == "__main__":
    print("Discordance response checker\n")
    server_ok = check_server_current()
    db_ok = check_evidence_db_current()

    print("Paste the response text to check, then press Ctrl-D (or Ctrl-Z on Windows):")
    text = sys.stdin.read()
    text_ok = check_response_text(text) if text.strip() else True

    print("=== SUMMARY ===")
    print(f"  server.py current:   {'PASS' if server_ok else 'FAIL'}")
    print(f"  evidence.db current: {'PASS' if db_ok else 'FAIL'}")
    print(f"  no known fabrication:{'PASS' if text_ok else 'FAIL'}")
    if server_ok and db_ok and text_ok:
        print("\n  All checks passed. Still manually skim for NEW fabrications --")
        print("  this only catches ones we've already seen before.")
    else:
        print("\n  DO NOT present this live until failing checks above are fixed.")

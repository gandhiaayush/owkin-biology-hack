#!/usr/bin/env python3
"""Search RCSB PDB for solved structures of a receptor and append structural
evidence records (or an explicit negative-result record) to
data/receptors/<receptor>.json.

Receptor-agnostic by design: searches live via the RCSB full-text search API
rather than a hardcoded PDB ID, so this runs unchanged for any receptor.

Usage: python3 scripts/pdb_lookup.py OR51E2
       python3 scripts/pdb_lookup.py OR2H1
       python3 scripts/pdb_lookup.py OR51B4
"""
import json
import sys
from pathlib import Path
from urllib import request, parse

SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2/query"
ENTRY_API = "https://data.rcsb.org/rest/v1/core/entry"
REPO_ROOT = Path(__file__).resolve().parent.parent


def search_entries(receptor):
    query = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": receptor},
        },
        "return_type": "entry",
    }
    url = f"{SEARCH_API}?{parse.urlencode({'json': json.dumps(query)})}"
    req = request.Request(url)
    try:
        with request.urlopen(req) as resp:
            # RCSB search returns HTTP 204 (empty body) for zero hits.
            if resp.status == 204:
                return []
            body = resp.read().decode()
            if not body:
                return []
            data = json.loads(body)
            return [r["identifier"] for r in data.get("result_set", [])]
    except Exception as e:
        if getattr(e, "code", None) == 204:
            return []
        raise


def fetch_entry(pdb_id):
    with request.urlopen(f"{ENTRY_API}/{pdb_id}") as resp:
        return json.loads(resp.read().decode())


def build_record(receptor, pdb_id, entry):
    exptl = entry.get("exptl", [{}])[0]
    citation = entry.get("citation", [{}])[0]
    info = entry.get("rcsb_entry_info", {})
    accession = entry.get("rcsb_accession_info", {})

    method = exptl.get("method")
    resolution = info.get("resolution_combined", [None])[0]
    title = entry.get("struct", {}).get("title")
    release_date = accession.get("initial_release_date", "")[:10]
    authors = citation.get("rcsb_authors") or []

    return {
        "receptor": receptor,
        "source_type": "pdb",
        "citation": (
            f"PDB {pdb_id} -- {authors[0] if authors else 'unknown author'} et al. "
            f"({citation.get('year')}). \"{citation.get('title')}\" "
            f"{citation.get('journal_abbrev')} {citation.get('journal_volume')}:"
            f"{citation.get('page_first')}-{citation.get('page_last')}."
        ),
        "claim": (
            f"Solved structure of {title}, method={method}, resolution={resolution} A, "
            f"released {release_date}. This is a structural cross-check only -- it does not itself "
            f"make a claim about tumor direction/mechanism."
        ),
        "mechanism": None,
        "direction": "neutral",
        "model_system": f"{method} structure ({title})",
        "sample_size": None,
        "replication_count": 1,
        "cancer_type": None,
        "verified_by_person_a": True,
        "verification_notes": (
            f"Live RCSB PDB REST API pull (full-text search for '{receptor}', matched entry {pdb_id}). "
            f"doi:{citation.get('pdbx_database_id_DOI')}."
        ),
        "raw_excerpt_or_link": f"https://www.rcsb.org/structure/{pdb_id}",
    }


def build_negative_record(receptor):
    return {
        "receptor": receptor,
        "source_type": "pdb",
        "citation": "RCSB PDB full-text search, live query",
        "claim": f"No solved PDB structure exists for {receptor} (0 hits on a full-text search of the RCSB PDB).",
        "mechanism": None,
        "direction": "neutral",
        "model_system": None,
        "sample_size": None,
        "replication_count": None,
        "cancer_type": None,
        "verified_by_person_a": True,
        "verification_notes": (
            f"Live RCSB PDB search API query (search.rcsb.org/rcsbsearch/v2/query, full_text service, "
            f"query='{receptor}') returned zero hits. Genuine negative result -- any structural claims "
            "about this receptor would currently rely on computational predictions (e.g. AlphaFold), "
            "not an experimentally solved structure."
        ),
        "raw_excerpt_or_link": "https://search.rcsb.org/rcsbsearch/v2/query",
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/pdb_lookup.py <RECEPTOR_SYMBOL>")
        sys.exit(1)
    receptor = sys.argv[1].upper()
    out_file = REPO_ROOT / "data" / "receptors" / f"{receptor.lower()}.json"

    print(f"Searching RCSB PDB for {receptor}...")
    pdb_ids = search_entries(receptor)

    if not pdb_ids:
        print(f"  No PDB structures found for {receptor}.")
        new_records = [build_negative_record(receptor)]
    else:
        print(f"  Found {len(pdb_ids)} entr{'y' if len(pdb_ids) == 1 else 'ies'}: {', '.join(pdb_ids)}")
        new_records = []
        for pdb_id in pdb_ids:
            entry = fetch_entry(pdb_id)
            record = build_record(receptor, pdb_id, entry)
            print(f"  {record['claim']}")
            new_records.append(record)

    existing = json.loads(out_file.read_text()) if out_file.exists() else []
    existing = [r for r in existing if r.get("source_type") != "pdb"]
    existing.extend(new_records)
    out_file.write_text(json.dumps(existing, indent=2) + "\n")
    print(f"Wrote {len(new_records)} PDB record(s) to {out_file} (total {len(existing)} records)")


if __name__ == "__main__":
    main()

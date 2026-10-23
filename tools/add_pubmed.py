#!/usr/bin/env python3
"""Add a paper to data/publications.json from its PubMed ID.

    python tools/add_pubmed.py 39941897 clinical
    python tools/add_pubmed.py 38452385 cbct method

Tags are optional; see TAG_LABELS in build.py for the ones the site knows.
Uses curl for the download so it works behind the UCLA proxy.
"""
import json
import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "publications.json"


def fetch(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    cmd = ["curl", "-sS", "-G", url, "--data-urlencode", "db=pubmed", "--data-urlencode", f"id={pmid}",
           "--data-urlencode", "retmode=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
    r = json.loads(result.stdout)["result"][pmid]
    doi = next((a["value"] for a in r.get("articleids", []) if a.get("idtype") == "doi"), "")
    return {"pmid": pmid, "doi": doi, "year": int(r["pubdate"][:4]), "title": r["title"].strip().rstrip("."),
            "authors": [a["name"] for a in r.get("authors", [])], "journal": r.get("source", ""),
            "volume": r.get("volume", ""), "issue": r.get("issue", ""), "pages": r.get("pages", "")}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pmid, tags = sys.argv[1], sys.argv[2:]
    pubs = json.loads(DATA.read_text(encoding="utf-8"))
    if any(p.get("pmid") == pmid for p in pubs):
        sys.exit(f"PMID {pmid} is already listed.")
    entry = fetch(pmid)
    entry["tags"] = tags
    pubs.append(entry)
    pubs.sort(key=lambda p: (-p["year"], p["title"].lower()))
    DATA.write_text(json.dumps(pubs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("added:", entry["year"], entry["title"])


if __name__ == "__main__":
    main()

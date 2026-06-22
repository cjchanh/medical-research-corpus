#!/usr/bin/env python3
"""ClinicalTrials.gov v2 lane — pull trials per condition, append to corpus.json (dedup by NCT).

Run AFTER europepmc_client.py.  python3 clinicaltrials_client.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus" / "corpus.json"
API = "https://clinicaltrials.gov/api/v2/studies"
UA = "CDS-Archivist-medcorpus/0.3"

# Short topical terms — the full boolean EPMC queries are too complex for the CT query parser.
TERMS = {
    "hEDS": "hypermobile Ehlers-Danlos syndrome",
    "POTS_exercise": "postural orthostatic tachycardia exercise",
    "POTS_treatment": "postural orthostatic tachycardia syndrome treatment",
    "MCAS": "mast cell activation syndrome",
    "OSA": "obstructive sleep apnea CPAP",
    "ADHD_guanfacine": "guanfacine ADHD",
    "OCD_ERP": "obsessive compulsive disorder exposure response prevention",
    "Hashimoto": "Hashimoto thyroiditis",
    "collagen_loading": "tendon collagen loading",
    "neuroconnective": "joint hypermobility autonomic",
}


def pull(term: str, n: int = 12) -> list[dict]:
    url = f"{API}?{urllib.parse.urlencode({'query.term': term, 'pageSize': str(n)})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp).get("studies", [])
    except Exception as exc:
        print(f"[ERR] {term}: {exc}", file=sys.stderr)
        return []


def normalize(study: dict, condition: str) -> dict:
    p = study.get("protocolSection", {})
    idm = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    desc = p.get("descriptionModule", {})
    nct = idm.get("nctId")
    year = (status.get("startDateStruct", {}) or {}).get("date", "")[:4]
    return {
        "condition": condition, "id": nct, "source": "CT",
        "pmid": None, "pmcid": None, "doi": None,
        "title": idm.get("briefTitle"),
        "authors": (idm.get("organization", {}) or {}).get("fullName"),
        "journal": "ClinicalTrials.gov", "year": year or None,
        "pub_type": status.get("overallStatus"),
        "is_oa": False, "is_preprint": False, "is_trial": True, "cited_by": 0,
        "abstract": desc.get("briefSummary"), "fulltext": None,
        "url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
    }


def main() -> int:
    if not CORPUS.exists():
        print("Run europepmc_client.py first.", file=sys.stderr)
        return 1
    docs = {(d.get("doi") or d.get("id")): d for d in json.loads(CORPUS.read_text())}
    added = 0
    for cond, term in TERMS.items():
        studies = pull(term)
        for s in studies:
            d = normalize(s, cond)
            if d["id"] and d["id"] not in docs:
                docs[d["id"]] = d
                added += 1
        print(f"[CT]  {cond:18s} {len(studies)}")
        time.sleep(0.3)
    CORPUS.write_text(json.dumps(list(docs.values()), indent=1, ensure_ascii=False))
    print(f"[DONE] +{added} trials -> {len(docs)} total docs -> {CORPUS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

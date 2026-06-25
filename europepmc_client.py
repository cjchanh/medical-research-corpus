#!/usr/bin/env python3
"""Europe PMC client — articles + preprints (medRxiv/bioRxiv via SRC:PPR) + BioC full text.

P1/P2 of the Medical Research Corpus. Stdlib only, no API key.
Run:  python3 europepmc_client.py        (FETCH_FULLTEXT=0 to skip full text)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
BIOC = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmcid}/unicode"
HERE = Path(__file__).resolve().parent
CORPUS_DIR = HERE / "corpus"
UA = "medical-research-corpus/0.3 (local research client)"


def search(query: str, page_size: int = 30) -> list[dict]:
    params = {"query": query, "format": "json", "pageSize": str(page_size), "resultType": "core"}
    req = urllib.request.Request(f"{BASE}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp).get("resultList", {}).get("result", [])
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == 2:
                raise RuntimeError(f"EPMC failed: {exc}") from exc
            time.sleep(1.5)
    return []


def search_paged(query: str, target: int, page_size: int = 100) -> list[dict]:
    """Page through Europe PMC via cursorMark up to ~`target` results (lifts the old 30-row cap)."""
    out: list[dict] = []
    cursor = "*"
    page_size = min(page_size, 1000)
    while len(out) < target:
        params = {
            "query": query, "format": "json", "resultType": "core",
            "pageSize": str(min(page_size, target - len(out))), "cursorMark": cursor,
        }
        req = urllib.request.Request(f"{BASE}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if not out:
                raise RuntimeError(f"EPMC failed: {exc}") from exc
            break  # partial results are still useful
        batch = data.get("resultList", {}).get("result", [])
        out.extend(batch)
        nxt = data.get("nextCursorMark")
        if not batch or not nxt or nxt == cursor:
            break
        cursor = nxt
        time.sleep(0.2)
    return out


def fetch_fulltext(pmcid: str) -> str | None:
    """Pull OA full text via NCBI BioC JSON and join passage text. None if unavailable."""
    req = urllib.request.Request(BIOC.format(pmcid=pmcid), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except Exception:
        return None
    texts: list[str] = []
    for coll in (data if isinstance(data, list) else [data]):
        for doc in coll.get("documents", []):
            for passage in doc.get("passages", []):
                if passage.get("text"):
                    texts.append(passage["text"])
    full = re.sub(r"\s+", " ", " ".join(texts)).strip()
    return full or None


def normalize(rec: dict, condition: str) -> dict:
    src, rid = rec.get("source"), rec.get("id")
    return {
        "condition": condition, "id": rid, "source": src,
        "pmid": rec.get("pmid"), "pmcid": rec.get("pmcid"), "doi": rec.get("doi"),
        "title": rec.get("title"), "authors": rec.get("authorString"),
        "journal": rec.get("journalTitle"), "year": rec.get("pubYear"),
        "pub_type": rec.get("pubType"),
        "is_oa": rec.get("isOpenAccess") == "Y",
        "is_preprint": src == "PPR",
        "is_trial": False,
        "cited_by": rec.get("citedByCount"),
        "abstract": rec.get("abstractText"), "fulltext": None,
        "url": f"https://europepmc.org/article/{src}/{rid}" if src and rid else None,
    }


def main() -> int:
    seeds: dict[str, str] = json.loads((HERE / "seed_queries.json").read_text())
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    per = int(os.environ.get("EPMC_PER_QUERY", "100"))        # was a hard 30 — now configurable
    ppr = int(os.environ.get("EPMC_PPR_PER_QUERY", "30"))     # was a hard 10
    deduped: dict[str, dict] = {}

    for cond, query in seeds.items():
        try:
            recs = search_paged(query, per)
        except RuntimeError as exc:
            print(f"[ERR] {cond}: {exc}", file=sys.stderr)
            continue
        for d in (normalize(r, cond) for r in recs):
            key = d["doi"] or d["id"]
            if key and key not in deduped:
                deduped[key] = d
        print(f"[ART] {cond:18s} {len(recs)}")
        time.sleep(0.3)

    for cond, query in seeds.items():  # preprint (medRxiv/bioRxiv) lane
        try:
            recs = search_paged(f"({query}) AND (SRC:PPR)", ppr)
        except RuntimeError:
            recs = []
        for d in (normalize(r, cond) for r in recs):
            key = d["doi"] or d["id"]
            if key and key not in deduped:
                deduped[key] = d
        print(f"[PPR] {cond:18s} {len(recs)}")
        time.sleep(0.3)

    if not deduped:
        print("[FAIL] 0 results — check query/params or network. Corpus untouched.", file=sys.stderr)
        return 2

    if os.environ.get("FETCH_FULLTEXT", "1") != "0":
        oa = [d for d in deduped.values() if d.get("is_oa") and d.get("pmcid")]
        print(f"[FT]  BioC full text for {len(oa)} OA papers…")
        ok = 0
        for d in oa:
            text = fetch_fulltext(d["pmcid"])
            if text:
                d["fulltext"] = text[:8000]
                ok += 1
            time.sleep(0.2)
        print(f"[FT]  stored {ok}/{len(oa)}")

    out = CORPUS_DIR / "corpus.json"
    out.write_text(json.dumps(list(deduped.values()), indent=1, ensure_ascii=False))
    arts = sum(1 for d in deduped.values() if not d["is_preprint"])
    pps = sum(1 for d in deduped.values() if d["is_preprint"])
    print(f"[DONE] {len(deduped)} unique: {arts} articles + {pps} preprints -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

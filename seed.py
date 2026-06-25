#!/usr/bin/env python3
"""seed.py — build or EXTEND the local corpus for ANY condition, in one command.

    python3 seed.py "long covid"
    python3 seed.py "atrial fibrillation" --per 200
    python3 seed.py "rheumatoid arthritis" --no-trials --no-embed

Pulls Europe PMC articles + preprints (+ ClinicalTrials.gov trials), dedups into
corpus/corpus.json (extends an existing corpus, never clobbers), then embeds locally
via Ollama. Sovereign: the only thing that leaves your machine is the public-literature
API query itself — no account, no key, and your data never goes to a cloud model.

Stdlib only; the embed step needs a running Ollama (`ollama pull nomic-embed-text`).
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import clinicaltrials_client as ct
import embeddings as emb
import europepmc_client as epmc

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus" / "corpus.json"


def load_corpus() -> dict[str, dict]:
    if CORPUS.exists():
        return {(d.get("doi") or d.get("id")): d for d in json.loads(CORPUS.read_text())}
    return {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build/extend the local corpus for one condition.")
    ap.add_argument("condition", help='free-text condition, e.g. "long covid"')
    ap.add_argument("--per", type=int, default=int(os.environ.get("SEED_PER", "120")),
                    help="target articles to pull from Europe PMC (default 120)")
    ap.add_argument("--no-trials", action="store_true", help="skip the ClinicalTrials.gov lane")
    ap.add_argument("--no-fulltext", action="store_true", help="skip BioC full-text fetch")
    ap.add_argument("--no-embed", action="store_true", help="skip the local embedding step")
    args = ap.parse_args(argv)

    cond = args.condition.strip()
    if not cond:
        ap.error("condition must not be empty")
    tag = cond.lower().replace(" ", "_")[:40]
    CORPUS.parent.mkdir(parents=True, exist_ok=True)
    docs = load_corpus()
    before = len(docs)

    # Europe PMC: peer-reviewed articles + preprints. Free-text condition as the query.
    arts = epmc.search_paged(cond, args.per)
    pps = epmc.search_paged(f"({cond}) AND (SRC:PPR)", max(args.per // 4, 20))
    for rec in arts + pps:
        d = epmc.normalize(rec, tag)
        key = d["doi"] or d["id"]
        if key and key not in docs:
            docs[key] = d
    print(f"[EPMC] {cond!r}: {len(arts)} articles + {len(pps)} preprints")

    # BioC full text for newly-added OA papers lacking it
    if not args.no_fulltext:
        oa = [d for d in docs.values() if d.get("is_oa") and d.get("pmcid") and d.get("fulltext") is None]
        ok = 0
        for d in oa:
            text = epmc.fetch_fulltext(d["pmcid"])
            if text:
                d["fulltext"] = text[:8000]
                ok += 1
            time.sleep(0.2)
        print(f"[FT]   +{ok} full texts")

    # ClinicalTrials.gov
    if not args.no_trials:
        added = 0
        for study in ct.pull(cond, max(args.per // 3, 20)):
            d = ct.normalize(study, tag)
            if d["id"] and d["id"] not in docs:
                docs[d["id"]] = d
                added += 1
        print(f"[CT]   +{added} trials")

    CORPUS.write_text(json.dumps(list(docs.values()), indent=1, ensure_ascii=False))
    print(f"[CORPUS] {before} -> {len(docs)} docs (+{len(docs) - before}) -> {CORPUS}")

    if args.no_embed:
        print("[EMBED] skipped — run `python3 embeddings.py` before querying.")
        return 0
    print("[EMBED] local embeddings (Ollama nomic-embed-text)…")
    return emb.main()


if __name__ == "__main__":
    raise SystemExit(main())

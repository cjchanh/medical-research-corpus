#!/usr/bin/env python3
"""First grounded query over the pulled Europe PMC corpus.

Cited results, ABSTAIN when nothing matches. Stdlib only. This is the minimal
"testify" retrieval: every returned claim resolves to a specific paper
(DOI / PMID / OA link). Real ranking moves into Archivist's semantic layer at P3.

Run:  python3 grounded_query.py "<question>" [topN]
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus" / "corpus.json"
STOP = {"the", "and", "for", "with", "what", "does", "are", "how", "vs", "from", "that", "this"}


def tokens(text: str | None) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 2 and t not in STOP]


def build_idf(docs: list[dict]) -> dict[str, float]:
    """Inverse document frequency over the corpus — rare, specific terms outweigh common ones."""
    n = len(docs)
    df: Counter = Counter()
    for d in docs:
        for t in set(tokens(d.get("title")) + tokens(d.get("abstract"))):
            df[t] += 1
    return {t: math.log(n / (1 + c)) + 1.0 for t, c in df.items()}


def score(doc: dict, qterms: list[str], idf: dict[str, float]) -> float:
    body = Counter(tokens(doc.get("title")) + tokens(doc.get("abstract")))
    if not body:
        return 0.0
    s = sum(body.get(t, 0) * idf.get(t, 1.0) for t in qterms)  # TF-IDF: specific terms dominate
    title = set(tokens(doc.get("title")))
    s += 2.0 * sum(idf.get(t, 1.0) for t in qterms if t in title)  # title hits weigh more
    return s


def citation(doc: dict) -> str:
    ids = []
    if doc.get("doi"):
        ids.append(f"doi:{doc['doi']}")
    if doc.get("pmid"):
        ids.append(f"PMID:{doc['pmid']}")
    if doc.get("is_oa"):
        ids.append("OA")
    return " · ".join(ids) or "(no id)"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: grounded_query.py '<question>' [topN]")
        return 1
    if not CORPUS.exists():
        print("ABSTAIN — no corpus yet. Run europepmc_client.py first (needs network).")
        return 0

    question = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    docs: list[dict] = json.loads(CORPUS.read_text())
    qterms = tokens(question)
    idf = build_idf(docs)

    scored = [(score(d, qterms, idf), d) for d in docs]
    hits = sorted((p for p in scored if p[0] > 0), key=lambda p: p[0], reverse=True)[:top_n]

    print(f"\nQ: {question}\nCorpus: {len(docs)} papers (Europe PMC)\n" + "=" * 64)
    if not hits:
        print("ABSTAIN — no paper in the local corpus matches. Widen the pull or rephrase.")
        return 0

    for rank, (sc, d) in enumerate(hits, 1):
        title = (d.get("title") or "(no title)").strip()
        meta = f"{(d.get('authors') or '')[:55]}… {d.get('journal') or ''} {d.get('year') or ''}".strip()
        print(f"\n[{rank}] {title}")
        print(f"    {meta}")
        print(f"    {citation(d)}   score={sc:.1f}   {d.get('url') or ''}")
        abstract = re.sub(r"<[^>]+>", " ", d.get("abstract") or "").strip().replace("\n", " ")
        if abstract:
            print(f'    "{abstract[:280]}{"…" if len(abstract) > 280 else ""}"')

    print("\n" + "=" * 64)
    print(f"{len(hits)} cited results. Every claim resolves to a paper.  (testify)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

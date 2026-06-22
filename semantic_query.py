#!/usr/bin/env python3
"""P3 — semantic query over the corpus via local nomic-embed-text + cosine.

Ranks by meaning, not keyword overlap. Cited results, ABSTAIN if corpus/embeddings
are missing. Fully sovereign (Ollama localhost). Stdlib only.

Run:  python3 semantic_query.py "<question>" [topN]
"""
from __future__ import annotations

import json
import math
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus" / "corpus.json"
EMB = HERE / "corpus" / "embeddings.json"
OLLAMA = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"


def embed(text: str) -> list[float]:
    body = json.dumps({"model": MODEL, "prompt": text}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp).get("embedding")


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def cite(d: dict) -> str:
    ids = []
    if d.get("doi"):
        ids.append(f"doi:{d['doi']}")
    if d.get("pmid"):
        ids.append(f"PMID:{d['pmid']}")
    if d.get("is_oa"):
        ids.append("OA+fulltext" if d.get("fulltext") else "OA")
    return " · ".join(ids) or "(no id)"


def rank(question: str, top_n: int = 5) -> list[tuple[float, dict]]:
    docs = {(d.get("doi") or d.get("id")): d for d in json.loads(CORPUS.read_text())}
    vecs = json.loads(EMB.read_text())
    qv = embed(question)
    scored = [(cosine(qv, v), docs.get(k, {})) for k, v in vecs.items()]
    return sorted(scored, key=lambda p: p[0], reverse=True)[:top_n]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: semantic_query.py '<question>' [topN]")
        return 1
    if not (CORPUS.exists() and EMB.exists()):
        print("ABSTAIN — run europepmc_client.py then embeddings.py first.")
        return 0

    question = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    hits = rank(question, top_n)

    print(f"\nQ (semantic): {question}\nCorpus: {len(json.loads(EMB.read_text()))} embedded papers (nomic-embed-text)\n" + "=" * 64)
    for i, (sc, d) in enumerate(hits, 1):
        title = (d.get("title") or "(no title)").strip()
        meta = f"{(d.get('authors') or '')[:55]}… {d.get('journal') or ''} {d.get('year') or ''}".strip()
        ab = re.sub(r"<[^>]+>", " ", d.get("abstract") or "").strip().replace("\n", " ")
        print(f"\n[{i}] {title}")
        print(f"    {meta}")
        print(f"    {cite(d)}   cos={sc:.3f}   {d.get('url') or ''}")
        if ab:
            print(f'    "{ab[:260]}{"…" if len(ab) > 260 else ""}"')
    print("\n" + "=" * 64)
    print("Semantic rank (meaning, not keywords). Every claim resolves to a paper.  (testify)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Grounded retrieval — compile-conformant entrypoint (P4).

Semantic rank (local nomic-embed) -> record-authority re-rank -> ABSTAIN gate.
Emits a compile-style verdict (ANSWER / ABSTAIN) with authority-labelled, cited
evidence. Sovereign (Ollama localhost). The ranking is exposed as grounded_rank()
so other surfaces (cross_query) reuse the same authority+ABSTAIN logic. Stdlib only.

Run:  python3 grounded.py "<question>" [topN]
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import urllib.request
from pathlib import Path

from authority import authority_tier

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus" / "corpus.json"
EMB = HERE / "corpus" / "embeddings.json"
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/embeddings"
MODEL = "nomic-embed-text"
ABSTAIN_COS = 0.62  # calibrated: on-topic POTS scored 0.78, off-topic retinopathy 0.56 -> abstain


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


def ids_of(d: dict) -> str:
    out = []
    if d.get("doi"):
        out.append(f"doi:{d['doi']}")
    if d.get("pmid"):
        out.append(f"PMID:{d['pmid']}")
    if (d.get("id") or "").startswith("NCT"):
        out.append(d["id"])
    if d.get("is_oa"):
        out.append("OA+ft" if d.get("fulltext") else "OA")
    return " · ".join(out) or "(no id)"


def grounded_rank(question: str, top_n: int = 5, *, corpus_path=CORPUS,
                  embeddings_path=EMB, embed_fn=embed) -> tuple[str, float, list]:
    """Shared ranking. Returns (verdict, top_cosine, results).

    results = [(cosine, doc, (tier, label)), …] ranked by evidence-authority then
    relevance; [] when verdict is ABSTAIN. corpus_path / embeddings_path / embed_fn
    are injectable for offline tests; CLI behavior is unchanged (module defaults).
    """
    docs = {(d.get("doi") or d.get("id")): d for d in json.loads(corpus_path.read_text())}
    vecs = json.loads(embeddings_path.read_text())
    qv = embed_fn(question)
    ranked = sorted(((cosine(qv, v), k) for k, v in vecs.items()), reverse=True)
    top_cos = ranked[0][0] if ranked else 0.0
    if top_cos < ABSTAIN_COS:
        return ("ABSTAIN", top_cos, [])
    k = max(top_n * 3, 12)
    cands = [(c, docs.get(key, {}), authority_tier(docs.get(key, {}))) for c, key in ranked[:k]]
    cands.sort(key=lambda t: (t[2][0], -t[0]))  # strongest evidence first, then relevance
    return ("ANSWER", top_cos, cands[:top_n])


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: grounded.py '<question>' [topN]")
        return 1
    if not (CORPUS.exists() and EMB.exists()):
        print('{"verdict":"ABSTAIN","reason":"no corpus/embeddings — run client + embeddings first"}')
        return 0

    question = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    verdict, top_cos, results = grounded_rank(question, top_n)

    n_docs = len(json.loads(CORPUS.read_text()))
    print("\n" + "=" * 70)
    print(f"GROUNDED  q: {question}")
    print(f"corpus: {n_docs} docs | top cosine {top_cos:.3f}")
    print("=" * 70)

    if verdict == "ABSTAIN":
        print(f"\nverdict: ABSTAIN  — top cosine {top_cos:.3f} < {ABSTAIN_COS}.")
        print("The corpus has nothing relevant to this question. Not fabricating an answer.")
        print("\n→ Pull sources for this topic and re-ask in one line:")
        print(f'    python3 seed.py "{question}" && python3 grounded.py "{question}"')
        print("  (shorten the seed term to the core condition for broader recall.)")
        print("=" * 70)
        return 0

    print("\nverdict: ANSWER  | ranked by evidence-authority within the semantic matches\n")
    for i, (cos_s, d, (tier, label)) in enumerate(results, 1):
        ab = re.sub(r"<[^>]+>", " ", d.get("abstract") or "").strip().replace("\n", " ")
        print(f"[{i}] «{label}»  {(d.get('title') or '(no title)').strip()}")
        print(f"    {(d.get('authors') or '')[:48]} {d.get('year') or ''} | {ids_of(d)} | cos={cos_s:.3f}")
        print(f"    {d.get('url') or ''}")
        if ab:
            print(f'    "{ab[:240]}{"…" if len(ab) > 240 else ""}"')
        print()
    print("=" * 70)
    print("compile-conformant: verdict + authority-ranked, cited evidence; ABSTAIN-gated. (testify)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

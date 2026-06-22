#!/usr/bin/env python3
"""P3 — embed the corpus with a local sovereign model (Ollama nomic-embed-text, 768-d).

No cloud. Vectors cached to corpus/embeddings.json keyed by DOI/id, so re-runs
only embed new papers. Stdlib only.

Run:  python3 embeddings.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus" / "corpus.json"
EMB = HERE / "corpus" / "embeddings.json"
OLLAMA = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"
DIM = 768


def embed(text: str) -> list[float] | None:
    body = json.dumps({"model": MODEL, "prompt": text[:8000]}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp).get("embedding")


def doc_text(d: dict) -> str:
    parts = [d.get("title") or "", d.get("abstract") or ""]
    if d.get("fulltext"):
        parts.append(d["fulltext"][:4000])
    return "\n".join(parts).strip()


def main() -> int:
    if not CORPUS.exists():
        print("No corpus — run europepmc_client.py first.", file=sys.stderr)
        return 1
    docs = json.loads(CORPUS.read_text())
    cache: dict[str, list[float]] = json.loads(EMB.read_text()) if EMB.exists() else {}
    out: dict[str, list[float]] = {}
    new = 0
    for d in docs:
        key = d.get("doi") or d.get("id")
        if not key:
            continue
        if len(cache.get(key, [])) == DIM:
            out[key] = cache[key]
            continue
        text = doc_text(d)
        if not text:
            continue
        try:
            vec = embed(text)
        except Exception as exc:
            print(f"[ERR] {key}: {exc}", file=sys.stderr)
            continue
        if vec and len(vec) == DIM:
            out[key] = vec
            new += 1
            if new % 25 == 0:
                print(f"  embedded {new} new…")
                EMB.write_text(json.dumps(out))  # incremental save — timeout-safe
    EMB.write_text(json.dumps(out))
    print(f"[DONE] {len(out)} doc vectors ({DIM}-d, {MODEL}) -> {EMB}  (+{new} new)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

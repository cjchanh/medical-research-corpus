#!/usr/bin/env python3
"""Cross-corpus join — the prize, now authority+ABSTAIN aware.

Literature side uses grounded_rank() (record-authority ranking + ABSTAIN gate),
put side by side with the user's verified personal signals (Garmin / clinical) for the
same question. One engine, two corpora, every literature claim cited. Stdlib only.

Run:  python3 cross_query.py "<question>" [topN]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from grounded import grounded_rank, ids_of

HERE = Path(__file__).resolve().parent
SIGNALS = HERE / "personal_signals.json"


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def match_signals(question: str, lit_titles: list[str], top: int = 4) -> list[dict]:
    sigs = json.loads(SIGNALS.read_text())
    qtok = tokens(question) | tokens(" ".join(lit_titles))
    scored = [(len(set(s["tags"]) & qtok), s) for s in sigs]
    return [s for n, s in sorted(scored, key=lambda p: p[0], reverse=True) if n > 0][:top]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: cross_query.py '<question>' [topN]")
        return 1
    question = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    verdict, top_cos, results = grounded_rank(question, top_n)

    print("\n" + "#" * 68)
    print(f"CROSS-CORPUS:  {question}")
    print("#" * 68)

    print("\n--- WHAT THE LITERATURE SAYS (Europe PMC, authority-ranked + ABSTAIN) ---")
    titles: list[str] = []
    if verdict == "ABSTAIN":
        print(f"  verdict: ABSTAIN (top cos {top_cos:.3f}) — no relevant paper in corpus; not fabricating.")
    else:
        for i, (cos_s, d, (tier, label)) in enumerate(results, 1):
            titles.append(d.get("title", ""))
            ab = re.sub(r"<[^>]+>", " ", d.get("abstract") or "").strip().replace("\n", " ")
            print(f"\n[{i}] «{label}»  {(d.get('title') or '').strip()}  (cos={cos_s:.3f})")
            print(f"    {ids_of(d)}  {d.get('url') or ''}")
            if ab:
                print(f'    "{ab[:200]}{"…" if len(ab) > 200 else ""}"')

    print("\n--- WHAT YOUR DATA SHOWS (verified personal signals) ---")
    sigs = match_signals(question, titles)
    if not sigs:
        print("  (no personal signal tagged to this question)")
    for s in sigs:
        print(f"  • {s['metric']}: {s['value']}")
        print(f"      ^ {s['source']}")

    print("\n--- CROSS ---")
    print("  Hold the literature's strongest evidence against your numbers above.")
    print("  Two corpora, authority-ranked, ABSTAIN-gated, every literature claim cited.  (testify)")
    print("#" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

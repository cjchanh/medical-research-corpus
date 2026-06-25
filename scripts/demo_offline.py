#!/usr/bin/env python3
"""Deterministic offline demo — NO Ollama, NO network. Runs the real grounded_rank
against tiny committed fixtures using precomputed query vectors, so anyone can see a
cited ANSWER and a fail-closed ABSTAIN without building a corpus.

    python3 scripts/demo_offline.py "Does CPAP reduce cardiovascular risk in OSA?"   # -> ANSWER
    python3 scripts/demo_offline.py "What is the best programming language?"          # -> ABSTAIN
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path for CLI use
import grounded  # noqa: E402

EX = Path(__file__).resolve().parent.parent / "examples"
_ANSWER_VEC = [1.0, 0.0, 0.0]   # aligns with the in-corpus fixtures
_ABSTAIN_VEC = [0.0, 0.0, 1.0]  # orthogonal -> below threshold
_ON_TOPIC = ("cpap", "osa", "apnea", "cardiovascular", "oxygen", "hypoxem")


def _query_vec(question: str) -> list[float]:
    ql = question.lower()
    return _ANSWER_VEC if any(w in ql for w in _ON_TOPIC) else _ABSTAIN_VEC


def main() -> int:
    q = sys.argv[1] if len(sys.argv) > 1 else "Does CPAP reduce cardiovascular risk in OSA?"
    verdict, cos, res = grounded.grounded_rank(
        q, corpus_path=EX / "mini_corpus.json", embeddings_path=EX / "mini_embeddings.json",
        embed_fn=_query_vec)
    print(f"\nq: {q}\nverdict: {verdict}  (top cosine {cos:.3f})")
    for i, (c, d, (_tier, label)) in enumerate(res, 1):
        print(f"  [{i}] «{label}» {d.get('title')}  (cos {c:.3f})  {grounded.ids_of(d)}")
    if verdict == "ABSTAIN":
        print("  (nothing relevant in the demo fixtures — fail-closed, not fabricating)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

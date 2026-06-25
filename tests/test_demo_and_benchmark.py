"""Deterministic demo fixtures + ABSTAIN calibration benchmark. Fully offline."""
import json
from pathlib import Path

import benchmark_abstain
import grounded

EX = Path(__file__).resolve().parent.parent / "examples"
FIX = Path(__file__).resolve().parent / "fixtures"


def test_demo_fixtures_answer_ranks_systematic_review_first():
    verdict, _cos, res = grounded.grounded_rank(
        "cpap", corpus_path=EX / "mini_corpus.json", embeddings_path=EX / "mini_embeddings.json",
        embed_fn=lambda _q: [1.0, 0.0, 0.0])
    assert verdict == "ANSWER" and res
    assert res[0][2][1] == "systematic-review"  # authority re-rank puts the SR on top


def test_demo_fixtures_abstain():
    verdict, _cos, res = grounded.grounded_rank(
        "off topic", corpus_path=EX / "mini_corpus.json", embeddings_path=EX / "mini_embeddings.json",
        embed_fn=lambda _q: [0.0, 0.0, 1.0])
    assert verdict == "ABSTAIN" and res == []


def test_calibration_cases_classify_correctly():
    cases = json.loads((FIX / "calibration_cases.json").read_text())
    for c in cases:
        assert benchmark_abstain.classify(c["top_cosine"]) == c["expected"], c

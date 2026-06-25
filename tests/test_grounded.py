"""Core retrieval behavior: cosine, ids_of, and the ABSTAIN gate. Fully offline
(injects a fake embed_fn + tmp corpus/embeddings via grounded_rank's seams)."""
import json

import grounded


def _fixtures(tmp_path, corpus, embs):
    cp = tmp_path / "corpus.json"
    ep = tmp_path / "embeddings.json"
    cp.write_text(json.dumps(corpus))
    ep.write_text(json.dumps(embs))
    return cp, ep


def test_cosine_zero_and_identical():
    assert grounded.cosine([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]) == 0.0   # zero vector -> 0, no crash
    assert grounded.cosine([1.0, 0.0], [1.0, 0.0]) == 1.0             # identical -> 1
    assert grounded.cosine([1.0, 0.0], [0.0, 1.0]) == 0.0             # orthogonal -> 0


def test_ids_of_emits_resolvable_labels():
    s = grounded.ids_of({"doi": "10.1/x", "pmid": "123", "is_oa": True, "fulltext": "body"})
    assert "doi:10.1/x" in s and "PMID:123" in s and "OA+ft" in s
    assert "NCT001" in grounded.ids_of({"id": "NCT001"})
    assert grounded.ids_of({"is_oa": True}) == "OA"
    assert grounded.ids_of({}) == "(no id)"


def test_abstain_below_threshold(tmp_path):
    corpus = [{"doi": "d1", "title": "x"}]
    embs = {"d1": [0.0, 1.0]}  # orthogonal to query [1,0] -> cosine 0.0 < 0.62
    cp, ep = _fixtures(tmp_path, corpus, embs)
    verdict, cos, res = grounded.grounded_rank(
        "q", corpus_path=cp, embeddings_path=ep, embed_fn=lambda _q: [1.0, 0.0])
    assert verdict == "ABSTAIN"
    assert cos < grounded.ABSTAIN_COS
    assert res == []


def test_answer_above_threshold(tmp_path):
    corpus = [{"doi": "d1", "title": "systematic review of x"}]
    embs = {"d1": [1.0, 0.0]}  # identical to query -> cosine 1.0 >= 0.62
    cp, ep = _fixtures(tmp_path, corpus, embs)
    verdict, cos, res = grounded.grounded_rank(
        "q", corpus_path=cp, embeddings_path=ep, embed_fn=lambda _q: [1.0, 0.0])
    assert verdict == "ANSWER"
    assert cos >= grounded.ABSTAIN_COS
    assert len(res) == 1 and res[0][1]["doi"] == "d1"


def test_empty_embeddings_abstain_no_crash(tmp_path):
    cp, ep = _fixtures(tmp_path, [], {})
    verdict, cos, res = grounded.grounded_rank(
        "q", corpus_path=cp, embeddings_path=ep, embed_fn=lambda _q: [1.0, 0.0])
    assert verdict == "ABSTAIN" and cos == 0.0 and res == []


def test_authority_beats_raw_cosine(tmp_path):
    # A: higher cosine but preprint (tier 5); B: lower cosine but systematic review (tier 1).
    corpus = [
        {"doi": "A", "title": "x", "is_preprint": True},
        {"doi": "B", "title": "systematic review of x"},
    ]
    embs = {"A": [1.0, 0.0], "B": [0.9, 0.2]}  # both cosine >= 0.62 vs query [1,0]
    cp, ep = _fixtures(tmp_path, corpus, embs)
    verdict, _cos, res = grounded.grounded_rank(
        "q", top_n=2, corpus_path=cp, embeddings_path=ep, embed_fn=lambda _q: [1.0, 0.0])
    assert verdict == "ANSWER"
    assert res[0][1]["doi"] == "B"  # stronger evidence tier wins despite A's higher cosine

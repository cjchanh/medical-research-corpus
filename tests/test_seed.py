"""seed.py: extends + dedups the corpus, and --no-embed skips Ollama. Offline
(monkeypatches the client functions + redirects CORPUS to a temp path)."""
import json

import seed


def test_seed_extends_and_dedups(monkeypatch, tmp_path):
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([{"doi": "d1", "id": "x1", "title": "existing"}]))
    monkeypatch.setattr(seed, "CORPUS", corpus)
    # one genuinely new article + skip preprint lane; no trials
    monkeypatch.setattr(seed.epmc, "search_paged",
                        lambda q, n: [] if "SRC:PPR" in q else [{"source": "MED", "id": "n1", "doi": "d2", "title": "new"}])
    monkeypatch.setattr(seed.epmc, "fetch_fulltext", lambda _pmcid: None)
    monkeypatch.setattr(seed.ct, "pull", lambda _term, _n: [])
    embed_called = {"v": False}
    monkeypatch.setattr(seed.emb, "main", lambda: embed_called.__setitem__("v", True) or 0)

    rc = seed.main(["new condition"])
    assert rc == 0

    keys = {(d.get("doi") or d.get("id")) for d in json.loads(corpus.read_text())}
    assert "d1" in keys and "d2" in keys      # pre-existing kept (extend, not clobber) + new added
    assert embed_called["v"] is True          # embed step ran by default


def test_seed_no_embed_skips_ollama(monkeypatch, tmp_path):
    corpus = tmp_path / "corpus.json"
    monkeypatch.setattr(seed, "CORPUS", corpus)
    monkeypatch.setattr(seed.epmc, "search_paged", lambda q, n: [])
    monkeypatch.setattr(seed.epmc, "fetch_fulltext", lambda _pmcid: None)
    monkeypatch.setattr(seed.ct, "pull", lambda _term, _n: [])
    embed_called = {"v": False}
    monkeypatch.setattr(seed.emb, "main", lambda: embed_called.__setitem__("v", True) or 0)

    rc = seed.main(["cond", "--no-embed", "--no-trials"])
    assert rc == 0
    assert embed_called["v"] is False         # --no-embed must never touch Ollama

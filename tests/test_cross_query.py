"""cross_query: missing personal_signals.json must fail closed (empty), not crash."""
import json

import cross_query


def test_match_signals_no_file_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(cross_query, "SIGNALS", tmp_path / "absent.json")
    assert cross_query.match_signals("any question", ["a title"]) == []


def test_match_signals_tags_match(monkeypatch, tmp_path):
    sig = tmp_path / "signals.json"
    sig.write_text(json.dumps([{"metric": "SpO2", "value": "x", "tags": ["oxygen", "sleep"], "source": "wearable"}]))
    monkeypatch.setattr(cross_query, "SIGNALS", sig)
    hits = cross_query.match_signals("overnight oxygen desaturation", [""])
    assert hits and hits[0]["metric"] == "SpO2"

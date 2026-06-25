"""ClinicalTrials.gov client: nextPageToken pagination + normalization. Offline."""
import json

import clinicaltrials_client as ct


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, *a):
        return self._b


def _urlopen_serving(pages):
    it = iter(pages)

    def fake(_req, timeout=None):
        return _Resp(next(it))

    return fake


def test_pull_paginates_until_no_token(monkeypatch):
    pages = [{"studies": [{"a": 1}], "nextPageToken": "t1"}, {"studies": [{"a": 2}]}]  # no token -> stop
    monkeypatch.setattr(ct.urllib.request, "urlopen", _urlopen_serving(pages))
    monkeypatch.setattr(ct.time, "sleep", lambda *_a: None)
    out = ct.pull("term", target=100)
    assert out == [{"a": 1}, {"a": 2}]


def test_pull_respects_target(monkeypatch):
    pages = [{"studies": [{"a": i}], "nextPageToken": "t"} for i in range(10)]
    monkeypatch.setattr(ct.urllib.request, "urlopen", _urlopen_serving(pages))
    monkeypatch.setattr(ct.time, "sleep", lambda *_a: None)
    out = ct.pull("term", target=3, page_size=1)
    assert len(out) >= 3  # stops once target reached


def test_normalize_resolvable_url():
    study = {"protocolSection": {
        "identificationModule": {"nctId": "NCT99", "briefTitle": "T"},
        "statusModule": {}, "descriptionModule": {}}}
    d = ct.normalize(study, "cond")
    assert d["url"] == "https://clinicaltrials.gov/study/NCT99"
    assert d["is_trial"] is True and d["id"] == "NCT99"

# Contributing

Thanks for your interest. This is a sovereign, local-first medical-evidence engine — contributions
should preserve that posture.

## Principles

- **Local-first, keyless.** No cloud calls at query time; no API keys. Don't add a hosted dependency.
- **Fail-closed.** When evidence is insufficient, the engine ABSTAINs — never fabricate an answer.
- **Never commit private/generated data.** The public-boundary gate enforces this; see below.
- **Not medical advice.** Keep all framing methodological, not clinical.

## Dev setup

```
pip install -r requirements.txt pytest
ollama pull nomic-embed-text     # only needed to build/query a real corpus
python3 -m pytest -q             # tests are fully offline (no network, no Ollama)
```

## Before you open a PR

```
python3 -m pytest -q                          # all tests pass
python3 -m compileall -q .                    # everything compiles
python3 scripts/verify_public_boundary.py     # no private/secret file is tracked
```

- New behavior needs a test (the suite is offline — use the fakes/seams in `tests/`).
- Keep `seed_queries.json` topic-only; never add personal data or a real export to the repo.
- Run `python3 scripts/demo_offline.py "<q>"` to sanity-check ranking/ABSTAIN without a corpus.

CI runs the same three gates on Python 3.10–3.12.

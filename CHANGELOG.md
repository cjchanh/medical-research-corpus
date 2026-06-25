# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions are date-tagged.

## [Unreleased]

### Added
- `seed.py "<condition>"` one-liner to build/extend a cited corpus for any condition.
- Paginated, env-configurable acquisition (Europe PMC `cursorMark`, ClinicalTrials `nextPageToken`).
- One-command Docker stack (`ollama` + `engine`) and a Colab "reproduce in 5 cells" notebook.
- Offline pytest suite (ABSTAIN gate, authority ordering, cosine, ids, client pagination/dedup,
  seed extend/dedup, missing-`personal_signals` guard) + GitHub Actions CI (3.10–3.12).
- `scripts/verify_public_boundary.py` public/private boundary gate (CI-enforced).
- Deterministic offline demo (`scripts/demo_offline.py` + `examples/mini_*.json`).
- ABSTAIN calibration benchmark + `docs/` method card, limitations, and calibration report.
- ABSTAIN now suggests a one-line `seed.py … && grounded.py …` to pull sources and re-ask.

### Changed
- `OLLAMA_URL` is now configurable across all embed paths (default `localhost`).

### Security
- `.gitignore` guards secret-file patterns (`.env`, `*.key`, `*.pem`, `*.p12`).

## [0.1.0] - 2026-06-24
- Initial public release: sovereign, local-first, authority-ranked, ABSTAIN-gated medical-evidence
  engine (Europe PMC + ClinicalTrials + local Ollama embeddings). MIT licensed.

# Security & Privacy

## Design posture

- **Keyless + local-first.** The engine uses no API keys and makes no cloud calls at query time;
  embeddings run locally via Ollama. The only egress is the public-literature API queries.
- **Trust-domain separation.** Personal/clinical data (`personal_signals.json`, the wearable export,
  the generated `corpus/`) is gitignored and never committed. `cross_query.py` fails closed (empty)
  when no personal layer is present.
- **Enforced boundary.** `scripts/verify_public_boundary.py` (run in CI) fails the build if any
  private/generated/secret file becomes tracked: `corpus/`, `personal_signals.json`,
  `paper/evidence_table.md`, `paper/figure_spo2.png`, `.env*`, `*.key`, `*.pem`, `*.p12`.

## Reporting

Found a vulnerability or a privacy-boundary gap (e.g. a way private data could be committed or
exfiltrated)? Please open a **private** report via GitHub Security Advisories on this repository
rather than a public issue. We'll respond as promptly as a small project can.

Do **not** include real personal health data, keys, or exports in any issue or PR.

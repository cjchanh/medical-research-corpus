<!-- Do not include real personal health data, keys, or exports in this PR. -->

## What this changes

## Checklist
- [ ] `python3 -m pytest -q` passes (tests are offline — no network/Ollama)
- [ ] `python3 -m compileall -q .` clean
- [ ] `python3 scripts/verify_public_boundary.py` passes (no private/secret file tracked)
- [ ] New behavior has a test
- [ ] Preserves the local-first, keyless, fail-closed posture (no cloud at query time)
- [ ] No personal data / real export / secret added

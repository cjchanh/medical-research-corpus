# Release & Reproducibility

The large, user-built `corpus/` is **never** committed (it's gitignored and regenerable). For
deterministic reproduction we ship a tiny demo corpus as a release asset, not in git.

## Cut a release

1. Update `CHANGELOG.md` (move Unreleased → a dated version).
2. Package the deterministic demo corpus + checksums:

   ```
   python3 scripts/package_demo_corpus.py
   shasum -a 256 dist/*            # matches dist/SHA256SUMS
   ```
3. Create the GitHub release and attach `dist/demo-corpus.tar.gz` + `dist/SHA256SUMS`.
4. Anyone can then verify and run the deterministic demo without crawling the live APIs:

   ```
   shasum -a 256 -c SHA256SUMS
   python3 scripts/demo_offline.py "Does CPAP reduce cardiovascular risk in OSA?"
   ```

## Runtime pinning

`docker-compose.yml` uses `ollama/ollama:latest` for ease of first use. For a reproducible build,
pin a specific Ollama image tag and record the `nomic-embed-text` model digest in the release notes.

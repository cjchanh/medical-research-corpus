# Method Card — Medical Research Corpus

**What it is.** A sovereign, local-first medical-evidence retrieval engine. It builds a local
corpus from public literature, embeds it on-device, and answers condition questions with
authority-ranked, cited, ABSTAIN-gated retrieval — or declines.

## Pipeline

1. **Acquire** — Europe PMC (peer-reviewed articles + `SRC:PPR` preprints, with NCBI BioC
   full text for open-access papers) and ClinicalTrials.gov v2. Keyless. Paginated
   (Europe PMC `cursorMark`, ClinicalTrials `nextPageToken`); per-query caps configurable.
2. **Dedup** — by DOI, else source id (NCT for trials). Corpus is *extended*, never clobbered.
3. **Embed** — locally via Ollama `nomic-embed-text` (768-d). Vectors cached by key; re-runs
   embed only new docs. No cloud at query time.
4. **Rank** — cosine similarity (query × corpus) for the semantic candidate window, then a
   **record-authority re-rank** (`authority.py`): systematic-review/meta-analysis (1) >
   RCT / scoping-review (2) > cohort / review / research-article (3) > trial-registry /
   case-report (4) > preprint (5). A strong source is not beaten by a weak one on relevance alone.
5. **Gate** — if top cosine `< ABSTAIN_COS` (0.62), return **ABSTAIN** and suggest pulling more
   sources, rather than fabricate. See `ABSTAIN_CALIBRATION.md`.
6. **Cite** — every returned claim carries a resolvable id (DOI / PMID / NCT) + URL.

## Provenance & trust domains

External public literature is kept **separate** from any personal/clinical data
(`personal_signals.json`, gitignored). `cross_query.py` joins them at query time without
merging indexes; it fails closed (empty) when no personal layer is present.

## What it is not

Not a diagnostic tool, not medical advice, not an exhaustive corpus (it indexes what you seed),
and not a novel-physiology claim. It is a *method* for grounded, cited, fail-closed retrieval.
See `LIMITATIONS.md`.

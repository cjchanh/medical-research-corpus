# Limitations

Honest scope. This engine is a grounded-retrieval *method*, not a clinical product.

- **Not medical advice.** Outputs are literature pointers, not diagnosis or treatment guidance.
- **Corpus = what you seed.** Coverage is only as broad as the seed queries you run; it is not an
  exhaustive index of the literature. Answers can be incomplete if the corpus is thin for a topic.
- **Single embedder, fixed threshold.** Ranking uses one local model (`nomic-embed-text`) and a
  single cosine ABSTAIN threshold (0.62). Both are reasonable defaults, not exhaustively tuned;
  see `ABSTAIN_CALIBRATION.md`.
- **Authority hierarchy is a heuristic.** Tiers are inferred from `pub_type` + title keywords, which
  are coarse; a mislabeled title can mis-tier a document.
- **Retrieval, not synthesis.** It cites the strongest relevant sources; it does not read, reconcile,
  or adjudicate their findings for you.
- **Recency / full-text gaps.** The NCBI BioC full-text endpoint 404s some very recent papers, so a
  fraction of open-access docs carry abstract-only text.
- **No clinical validation.** Thresholds and tiers have not been validated against clinical outcomes.
- **ABSTAIN is conservative by design.** It will decline borderline questions rather than stretch —
  that is the intended fail-closed behavior, not a bug.

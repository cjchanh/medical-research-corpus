# Medical Research Corpus

Sovereign, local-first medical-evidence engine. Pulls peer-reviewed literature,
preprints, and trials into a local corpus and answers condition questions with
**authority-ranked, cited, ABSTAIN-gated** retrieval — fully on-device (Ollama
embeddings, no cloud at query time). Built 2026-06-22. **Not medical advice.**

## Why this exists

Most medical AI answers fluently and can't show its work: it fabricates citations and
never says "I don't know." This engine takes the opposite stance — it retrieves real
literature (peer-reviewed articles, preprints, registered trials), ranks it by evidence
tier, cites every claim to a resolvable source, and **abstains** when nothing in the corpus
is relevant enough, rather than inventing an answer. It runs fully on-device: local corpus,
local embeddings (Ollama), nothing leaves the machine at query time.

The design principle is one line: **a system shouldn't answer — it should testify.** Every
output is grounded, cited, and auditable, or it declines. Demonstrated here on personal-health
questions — the data layer stays private and gitignored; only the engine and method are public
— the same sovereign, cited, fail-closed pattern applies anywhere evidence must be traceable
and the source data must stay on-premise.

## Quick start
```
python3 europepmc_client.py         # pull articles + preprints (+ BioC full text)
python3 clinicaltrials_client.py    # add ClinicalTrials.gov trials
python3 embeddings.py               # embed corpus locally (nomic-embed-text, 768-d)
python3 grounded.py  "<question>"   # authority-ranked, ABSTAIN-gated, cited answer
python3 cross_query.py "<question>" # literature × your verified personal signals
```

## Example outputs

On-topic question → **authority-ranked, cited** answer (real run against the 468-doc corpus):

```
$ python3 grounded.py "Does CPAP adherence reduce cardiovascular risk in obstructive sleep apnea?"

GROUNDED  corpus: 468 docs | top cosine 0.825
verdict: ANSWER  | ranked by evidence-authority within the semantic matches

[1] «research-article» Long-term effect of CPAP on cardiovascular outcomes after acute myocardial
    infarction in obstructive sleep apnea patients.  2026 | doi:10.1007/s11325-026-03642-x
    PMID:41896434 | cos=0.825   https://europepmc.org/article/MED/41896434
[2] «research-article» CPAP therapy for patients with OSA and coronary artery disease.
    2025 | PMID:41181658 · OA+full-text | cos=0.804
[3] «research-article» Obstructive Sleep Apnea and Coronary Artery Disease: an overlooked
    cardiovascular risk factor.  2026 | PMID:41898162 · OA+full-text | cos=0.800
    ... every ranked claim cites a resolvable Europe PMC / DOI / PMID source.
```

Off-topic question → **ABSTAIN** (fail-closed — it refuses rather than fabricate):

```
$ python3 grounded.py "What is the best programming language for building a web app?"

GROUNDED  corpus: 468 docs | top cosine 0.461
verdict: ABSTAIN  — top cosine 0.461 < 0.62.
The corpus has nothing relevant to this question. Not fabricating an answer.
```

## Corpus (2026-06-22)
**468 docs** = 277 peer-reviewed articles + 84 preprints (medRxiv/bioRxiv) + 107 trials.
198 OA papers carry full-text bodies. 468 local embeddings. DOI/NCT-deduped.

## Sources
- **Europe PMC** — articles + OA full text (via NCBI BioC JSON). No API key.
- **Europe PMC `SRC:PPR`** — medRxiv/bioRxiv preprints (flagged lower-authority).
- **ClinicalTrials.gov v2** — registered trials.

Authority hierarchy (`authority.py`): systematic-review > RCT / scoping-review >
cohort / research-article > trial-registry > preprint. ABSTAIN below cosine 0.62
(calibrated: on-topic ≈0.78, off-topic ≈0.56).

## Files
| File | Role |
|---|---|
| `seed_queries.json` | condition seed queries |
| `europepmc_client.py` | articles + preprints + BioC full text |
| `clinicaltrials_client.py` | trials lane |
| `embeddings.py` | local Ollama embeddings (incremental cache) |
| `authority.py` | evidence-tier hierarchy |
| `grounded.py` | compile-conformant retrieval (verdict / authority / ABSTAIN); exposes `grounded_rank()` |
| `semantic_query.py` | plain semantic search |
| `cross_query.py` | literature × personal-data join (uses `grounded_rank`) |
| `personal_signals.json` | verified Garmin / clinical signals |
| `corpus/corpus.json`, `corpus/embeddings.json` | the corpus + vectors |

## Architecture decision (2026-06-22) — ADJACENT, not ingested into Archivist core
**DELIBERATE (operator decision, Path A).** This corpus is kept **separate** from the
Archivist personal core — not ingested. Rationale:
- **Trust-domain separation.** The personal core testifies about the user (their own
  record: messages, health records, wearables). This corpus is **external, cloud-sourced
  public literature.** Provenance must stay distinct.

> **Privacy / two-layer split:** personal data — `personal_signals.json`, the wearable
> export, generated `corpus/`, and the filled paper draft — is **gitignored** and never
> committed. Copy `personal_signals.template.json` to provide your own; the engine and
> method are the shareable layer.
- **The cross-join (`cross_query.py`) IS the integration** — one engine, two corpora,
  without merging indexes.
- Ingestion into core would be a **governed spec-grade source-adapter** build
  (`investigator/ingestion/importer.py` + `CORPUS_IMPORT_AUDIT_VERIFICATION_PLAN.md`),
  not a JSON dump — out of scope by choice.

**Future option (Path B):** if this should become a first-class governed corpus
retrievable via `cds_compile_query` / `archivist-search`, spec a conforming
source-adapter via `/spec-drafter` → recursive engine, tagged so literature stays
distinct from personal data. Not an oversight — a parked choice.

## Not done (by choice)
- Full text is default-on, but the BioC endpoint 404s some very recent papers
  (~99% OA success on this pull).
- P5 refresh cron (re-pull new papers since last run) — not wired.

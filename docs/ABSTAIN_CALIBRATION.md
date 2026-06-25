# ABSTAIN Calibration

The engine answers only when the top query-to-corpus cosine clears a threshold; otherwise it
**abstains** rather than fabricate.

```
ABSTAIN_COS = 0.62   # grounded.py
```

## How it was set

Calibrated on observed query/corpus cosines: on-topic, well-represented questions land high;
off-topic or off-corpus questions land low. Measured cases (`tests/fixtures/calibration_cases.json`):

| Question | Top cosine | Verdict |
|---|---:|---|
| CPAP → cardiovascular risk in OSA (matched corpus) | 0.825 | ANSWER |
| Cardiovascular/autonomic complications of long COVID | 0.757 | ANSWER |
| OSA/CPAP question asked against a *long-COVID* corpus | 0.581 | ABSTAIN |
| "Best programming language for a web app" | 0.445 | ABSTAIN |

0.62 sits in the gap between the on-topic cluster (~0.75–0.83) and the off-topic/off-corpus
cluster (~0.45–0.58), so a corpus/question mismatch correctly abstains instead of stretching.

Re-check anytime: `python3 scripts/benchmark_abstain.py --fixtures tests/fixtures/calibration_cases.json`

## Tuning

- **Raise** the threshold → fewer, higher-confidence answers, more ABSTAINs (safer).
- **Lower** it → more answers, higher risk of a weakly-grounded one.
- Calibration is corpus- and embedder-specific. If you change the embed model or your corpus is
  consistently thin, re-measure with `benchmark_abstain.py` and adjust. Prefer ABSTAIN on doubt —
  the engine's value is that it declines rather than guesses.

#!/usr/bin/env python3
"""Report how the ABSTAIN threshold classifies fixture cases — calibration check.

Each fixture case carries a real top-cosine (measured on actual runs) and the
expected verdict; this applies the live ABSTAIN_COS and reports correctness. Offline.

    python3 scripts/benchmark_abstain.py --fixtures tests/fixtures/calibration_cases.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from grounded import ABSTAIN_COS  # noqa: E402


def classify(top_cosine: float) -> str:
    return "ANSWER" if top_cosine >= ABSTAIN_COS else "ABSTAIN"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ABSTAIN threshold calibration report")
    ap.add_argument("--fixtures", default="tests/fixtures/calibration_cases.json")
    args = ap.parse_args(argv)
    cases = json.loads(Path(args.fixtures).read_text())
    ok = 0
    print(f"ABSTAIN threshold = {ABSTAIN_COS}\n")
    for c in cases:
        got = classify(c["top_cosine"])
        good = got == c["expected"]
        ok += good
        print(f"  [{'PASS' if good else 'FAIL'}] cos={c['top_cosine']:.3f} -> {got} "
              f"(expected {c['expected']}) — {c.get('note', '')}")
    print(f"\n{ok}/{len(cases)} cases correctly classified at threshold {ABSTAIN_COS}")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())

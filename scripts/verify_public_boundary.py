#!/usr/bin/env python3
"""Public-boundary gate: fail if any private / generated / secret file is tracked.

Run in CI and before any push. Exit 1 (with the offending paths) on violation.
"""
from __future__ import annotations

import re
import subprocess
import sys

FORBIDDEN = [
    r"^corpus/",
    r"(^|/)personal_signals\.json$",
    r"^paper/evidence_table\.md$",
    r"^paper/figure_spo2\.png$",
    r"(^|/)\.env($|\.)",
    r"\.key$",
    r"\.pem$",
    r"\.p12$",
]


def main() -> int:
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    pats = [re.compile(p) for p in FORBIDDEN]
    bad = [f for f in tracked if any(p.search(f) for p in pats)]
    if bad:
        print("PUBLIC BOUNDARY VIOLATION — these must never be tracked:", file=sys.stderr)
        for f in bad:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"public boundary OK — {len(tracked)} tracked files, 0 private/generated/secret")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Package the tiny deterministic demo corpus into a release asset + checksum.

The large user-built corpus stays out of git; this ships only the committed demo fixtures
so a release asset lets anyone reproduce a deterministic ANSWER/ABSTAIN offline. Output to
dist/ (gitignored).
"""
import hashlib
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
DIST = ROOT / "dist"


def main() -> int:
    DIST.mkdir(exist_ok=True)
    asset = DIST / "demo-corpus.tar.gz"
    with tarfile.open(asset, "w:gz") as tar:
        for name in ("mini_corpus.json", "mini_embeddings.json"):
            tar.add(EXAMPLES / name, arcname=name)
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    (DIST / "SHA256SUMS").write_text(f"{digest}  {asset.name}\n")
    print(f"[packaged] {asset}")
    print(f"[sha256]   {digest}  {asset.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

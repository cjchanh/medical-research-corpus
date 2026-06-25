"""Make the repo-root engine modules + scripts/ importable from tests/."""
import pathlib
import sys

_root = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "scripts"))

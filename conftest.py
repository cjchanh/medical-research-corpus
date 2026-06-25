"""Make the repo-root engine modules importable from tests/ (they live at the root)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

"""Build notebooks/*.ipynb from the cell lists in src/nb*.py.

Usage: python scripts/build_notebooks.py
"""

import importlib
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def build(module_name: str) -> Path:
    """Write one notebook from src/<module_name>.py and return its path."""
    module = importlib.import_module(module_name)
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["colab"] = {"provenance": []}
    for kind, text in module.CELLS:
        cell = nbformat.v4.new_markdown_cell(text) if kind == "markdown" else nbformat.v4.new_code_cell(text)
        nb.cells.append(cell)
    out = ROOT / "notebooks" / module.FILENAME
    nbformat.write(nb, out)
    return out


def main() -> None:
    for path in sorted((ROOT / "src").glob("nb[0-9]*.py")):
        print("built", build(path.stem).relative_to(ROOT))


if __name__ == "__main__":
    main()

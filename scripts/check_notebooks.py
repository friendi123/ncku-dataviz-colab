"""Execute every notebook against local data and check content and format rules.

Usage: python scripts/check_notebooks.py [--online]
  --online  use the published GitHub data URLs instead of local files
Spec: docs/specs/2026-10-02-colab-notebooks-design.md (course project)
"""

import re
import shutil
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
DATA = ROOT / "data"
CACHE = ROOT / "cache"

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
ONLINE = "--online" in sys.argv


# ---------- helpers ----------

def code_cells(nb) -> list[str]:
    return [c.source for c in nb.cells if c.cell_type == "code"]


def md_cells(nb) -> list[str]:
    return [c.source for c in nb.cells if c.cell_type == "markdown"]


def all_text(nb) -> str:
    return "\n".join(c.source for c in nb.cells)


def outputs_text(nb) -> str:
    parts = []
    for c in nb.cells:
        for out in c.get("outputs", []):
            if out.get("output_type") == "stream":
                parts.append(out.get("text", ""))
            elif "data" in out and "text/plain" in out["data"]:
                parts.append(out["data"]["text/plain"])
            elif out.get("output_type") == "error":
                parts.append("ERROR " + out.get("ename", "") + ": " + out.get("evalue", ""))
    return "\n".join(parts)


def require(text: str, phrases: list[str], where: str) -> None:
    missing = [p for p in phrases if p not in text]
    assert not missing, f"{where}: missing {missing}"


# ---------- format rules (all notebooks) ----------

def check_format(nb_path: Path) -> None:
    nb = nbformat.read(nb_path, as_version=4)
    name = nb_path.name
    text = all_text(nb)
    assert not EMOJI.findall(text), f"{name}: emoji present"
    first_md = md_cells(nb)[0]
    require(first_md, ["What you will learn", "Why this matters to you"], f"{name} top block")
    assert any("Try it with AI" in m for m in md_cells(nb)), f"{name}: no 'Try it with AI' box"
    codes = code_cells(nb)
    assert "__version__" in codes[-1], f"{name}: last code cell must print versions"
    assert "CHECK PASSED" in codes[-2], f"{name}: second-to-last code cell must be the verify cell"
    for i, src in enumerate(codes):
        lines = src.splitlines()
        for j, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            inline = "  #" in line
            above = j > 0 and lines[j - 1].strip().startswith("#")
            continuation = j > 0 and lines[j - 1].rstrip().endswith(("(", "[", "{", ",", "\\"))
            closer = stripped in (")", "]", "}", "})", "])", "),")
            assert inline or above or continuation or closer, f"{name} code cell {i}: uncommented line {line!r}"
        for line in lines:
            if "http" in line and not re.match(r"\s*[A-Z_]+\s*=\s*\"http", line):
                raise AssertionError(f"{name}: URL outside a settings constant: {line!r}")


# ---------- execution ----------

def with_overrides(nb, overrides: dict[str, str]):
    """Replace 'NAME = ...' settings lines in code cells with local values."""
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        lines = cell.source.splitlines()
        for k, line in enumerate(lines):
            for var, value in overrides.items():
                if re.match(rf"{var}\s*=", line):
                    lines[k] = f"{var} = {value!r}  # local test override"
        cell.source = "\n".join(lines)
    return nb


def execute(nb_path: Path, overrides: dict[str, str]):
    """Run a temporary copy of the notebook; return the executed notebook."""
    nb = nbformat.read(nb_path, as_version=4)
    nb = with_overrides(nb, overrides)
    workdir = Path(tempfile.mkdtemp(prefix="nbcheck_"))
    client = NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(workdir)}})
    client.execute()
    nb.metadata["_workdir"] = str(workdir)
    return nb


def local_data() -> dict[str, str]:
    return {} if ONLINE else {"DATA_BASE": DATA.as_posix() + "/"}


# ---------- main ----------

def main() -> None:
    notebooks = sorted(NOTEBOOKS.glob("*.ipynb"))
    assert notebooks, "no notebooks found; run scripts/build_notebooks.py"
    for path in notebooks:
        check_format(path)
        print(f"PASS format {path.name}")
    checks = [obj for name, obj in globals().items() if name.startswith("check_nb") and callable(obj)]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")


if __name__ == "__main__":
    main()

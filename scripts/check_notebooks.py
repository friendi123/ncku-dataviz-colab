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


def statements(src: str) -> list[tuple[int, int]]:
    """(first line, last line) of every logical statement in a code cell."""
    import io
    import tokenize

    spans, first = [], None
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
            continue
        if first is None:
            first = tok.start[0]
        if tok.type == tokenize.NEWLINE:
            spans.append((first, tok.start[0]))
            first = None
    return spans


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
        for first, last in statements(src):
            span = lines[first - 1 : last]
            above = first > 1 and lines[first - 2].strip().startswith("#")
            commented = any(re.search(r"(^|\s)#", ln) for ln in span)
            assert commented or above, f"{name} code cell {i}: statement without a comment: {span[0]!r}"
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


def execute(nb_path: Path, overrides: dict[str, str], allow_errors: bool = False):
    """Run a temporary copy of the notebook; return the executed notebook."""
    nb = nbformat.read(nb_path, as_version=4)
    nb = with_overrides(nb, overrides)
    workdir = Path(tempfile.mkdtemp(prefix="nbcheck_"))
    client = NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(workdir)}}, allow_errors=allow_errors)
    client.execute()
    nb.metadata["_workdir"] = str(workdir)
    return nb


def local_data() -> dict[str, str]:
    return {} if ONLINE else {"DATA_BASE": DATA.as_posix() + "/"}


# ---------- per-notebook checks ----------

def run_twice(nb_path: Path, overrides: dict[str, str]) -> str:
    """Execute twice in a row (students rerun cells); both must pass. Return output of run 2."""
    first = outputs_text(execute(nb_path, overrides))
    assert "CHECK PASSED" in first, f"{nb_path.name} run 1 did not pass:\n{first[-1500:]}"
    second = outputs_text(execute(nb_path, overrides))
    assert "CHECK PASSED" in second, f"{nb_path.name} run 2 did not pass:\n{second[-1500:]}"
    assert "ERROR" not in second, f"{nb_path.name}: error in output"
    return second


def check_nb01() -> None:
    nb_path = NOTEBOOKS / "01_profile_airbnb.ipynb"
    out = run_twice(nb_path, local_data())
    require(out, ["30,259 rows", "90 columns", "Missing price: 29", "Duplicate listing IDs: 0"], "nb01 output")
    nb = nbformat.read(nb_path, as_version=4)
    require(all_text(nb), ["Check:", "problems found"], "nb01 text")


CLEAN_CSV = "nyc_listings_clean_2026-06-14.csv"
LONG_CSV = "nyc_review_scores_long_2026-06-14.csv"


def check_nb02() -> None:
    nb_path = NOTEBOOKS / "02_clean_airbnb.ipynb"
    out = run_twice(nb_path, local_data())
    moves = re.findall(r"Move (\d+) .*rows before: ([\d,]+) \| rows after: ([\d,]+)", out)
    assert sorted({int(m[0]) for m in moves}) == list(range(1, 11)), f"moves reported: {moves}"
    import pandas as pd

    workdir = Path(re.search(r"Saved to (.+)", out).group(1).strip()).parent
    made = pd.read_csv(workdir / CLEAN_CSV)
    assert len(made) == 30259, f"clean file has {len(made)} rows"
    assert pd.api.types.is_numeric_dtype(made["price"]), "price is not numeric"
    assert made["reviews_per_month"].isna().sum() == 0, "reviews_per_month still has gaps"
    for col in ["bathrooms_count", "bathroom_shared", "has_wifi", "price_missing", "price_outlier", "area_label"]:
        assert col in made.columns, f"missing column {col}"
    stored = DATA / CLEAN_CSV
    assert stored.exists(), "copy the generated clean CSV into data/"
    assert (workdir / CLEAN_CSV).read_bytes() == stored.read_bytes(), "data/ clean CSV differs from notebook output"
    assert (workdir / LONG_CSV).read_bytes() == (DATA / LONG_CSV).read_bytes(), "data/ long CSV differs"


FIVE_BLOCKS = ["Research question", "Why a t-test fits", "Hypotheses", "Look first", "How to report it"]


def fmt_p(p: float) -> str:
    """Same p-value format the notebook uses."""
    return "< 0.001" if p < 0.001 else f"= {p:.3f}"


def check_nb03() -> None:
    import numpy as np
    import pandas as pd
    from scipy import stats

    nb_path = NOTEBOOKS / "03_ttest_airbnb.ipynb"
    nb = nbformat.read(nb_path, as_version=4)
    text = all_text(nb)
    require(text, ["Stats in 5 minutes", "Choosing a test", "Going further", "p-value (p 值)", "Cohen's d"], "nb03 text")
    parts = re.split(r"\n## Part ", "\n" + "\n".join(md_cells(nb)))
    core = {int(p[0]): p for p in parts[1:] if p[0] in "1234"}
    assert sorted(core) == [1, 2, 3, 4], f"core parts found: {sorted(core)}"
    for n in (1, 3, 4):
        require(core[n], FIVE_BLOCKS + ["You are here", "Stuck?"], f"nb03 Part {n}")
    require(core[2], ["Research question", "You are here", "Stuck?"], "nb03 Part 2")
    verify = code_cells(nb)[-2]
    assert "mannwhitney" not in verify.lower() and "wilcoxon" not in verify.lower(), "verify cell must cover core only"

    out = run_twice(nb_path, local_data())

    # Independent recomputation from the stored clean file
    d = pd.read_csv(DATA / CLEAN_CSV)
    p = d[d["price"].notna() & d["host_is_superhost"].notna()]
    sh, other = p.loc[p.host_is_superhost == "t", "price"], p.loc[p.host_is_superhost == "f", "price"]
    t1 = stats.ttest_ind(sh, other, equal_var=False)
    assert t1.pvalue < 0.05 and other.mean() > sh.mean(), "Part 1 expectation changed"
    q = p[~p["price_outlier"]]
    t2 = stats.ttest_ind(q.loc[q.host_is_superhost == "t", "price"], q.loc[q.host_is_superhost == "f", "price"], equal_var=False)
    assert t2.pvalue > 0.05, "Part 2 expectation changed (ledger: p = 0.638)"
    r = d.dropna(subset=["review_scores_cleanliness", "review_scores_location"])
    diff = r.review_scores_cleanliness - r.review_scores_location
    t3 = stats.ttest_rel(r.review_scores_cleanliness, r.review_scores_location)
    d3 = diff.mean() / diff.std(ddof=1)
    assert t3.pvalue < 0.001 and abs(d3) < 0.2, "Part 3 expectation changed"
    s = d.review_scores_rating.dropna()
    t4 = stats.ttest_1samp(s, 4.8)
    assert s.mean() < 4.8 and t4.pvalue < 0.001, "Part 4 expectation changed"
    for label, pv in [("Part 1", t1.pvalue), ("Part 2", t2.pvalue), ("Part 3", t3.pvalue), ("Part 4", t4.pvalue)]:
        assert f"p {fmt_p(pv)}" in out, f"{label}: notebook output lacks 'p {fmt_p(pv)}'"
    require(out, [f"{len(sh):,}", f"{len(other):,}", f"{len(r):,}", f"{len(s):,}"], "nb03 sample sizes")


BIKE_CASES = {
    "YouBike": {"CITY": "YouBike", "MONTH": "2026-07", "WEEK_START": "2026-07-06",
                "YOUBIKE_URL_TEMPLATE": (CACHE / "youbike_202607.zip").as_posix(),
                "YOUBIKE_STATIONS_URL": (CACHE / "youbike_stations.json").as_posix()},
    "Bluebikes": {"CITY": "Bluebikes", "MONTH": "2026-08", "WEEK_START": "2026-08-03",
                  "BLUEBIKES_URL_TEMPLATE": (CACHE / "bluebikes_202608.zip").as_posix()},
}
BIKE_WEEK_TOTALS = {"YouBike": 1338920, "Bluebikes": 124721}  # verified in Task 2 (data/README.md)
FAIL_MESSAGE = "The download failed. Try again, or ask your instructor for the backup file."


def check_nb04() -> None:
    import pandas as pd

    nb_path = NOTEBOOKS / "04_bike_week.ipynb"
    nb = nbformat.read(nb_path, as_version=4)
    text = all_text(nb)
    for banned in ["Airbnb", "Week 4", "Week 5", "Week 6", "Notebook 0"]:
        assert banned not in text, f"nb04 must be stand-alone: found {banned!r}"
    require(text, ["Assignment brief", "Deliverables", "Rubric", "For instructors", "aggregated"], "nb04 text")
    for city, overrides in BIKE_CASES.items():
        out = run_twice(nb_path, overrides)
        total = BIKE_WEEK_TOTALS[city]
        require(out, [f"Trips in the chosen week: {total:,}"], f"nb04 {city}")
        workdir = Path(re.search(r"Saved to (.+)", out).group(1).strip()).parent
        hourly = pd.read_csv(next(workdir.glob("*_station_hour.csv")))
        pairs = pd.read_csv(next(workdir.glob("*_station_pairs.csv")))
        assert hourly["trips"].sum() == total, f"{city}: station-hour table sums to {hourly['trips'].sum()}"
        assert pairs["trips"].sum() == total, f"{city}: station-pairs table sums to {pairs['trips'].sum()}"
        for col in ["start_lat", "start_lng", "end_lat", "end_lng"]:
            assert col in pairs.columns, f"{city}: pairs table lacks {col}"
        if city == "YouBike":
            assert hourly["station"].str.contains("捷運").any(), "YouBike station names garbled"
    bad = dict(BIKE_CASES["Bluebikes"], BLUEBIKES_URL_TEMPLATE="https://invalid.invalid/none.zip")
    failed = execute(nb_path, bad, allow_errors=True)
    errors = [o for c in failed.cells for o in c.get("outputs", []) if o.get("output_type") == "error"]
    assert errors and errors[0]["ename"] == "SystemExit", f"bad download should stop with SystemExit, got {errors[:1]}"
    assert FAIL_MESSAGE in outputs_text(failed), "friendly download message missing"


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

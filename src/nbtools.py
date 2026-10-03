"""Small helpers for authoring notebooks as Python cell lists."""

DATA_BASE = "https://raw.githubusercontent.com/friendi123/ncku-dataviz-colab/main/data/"

ATTRIBUTION = "Data: Inside Airbnb (insideairbnb.com), NYC snapshot 2026-06-14, CC BY 4.0."


def md(text: str) -> tuple[str, str]:
    """A markdown cell; leading/trailing blank lines removed."""
    return ("markdown", text.strip("\n"))


def code(text: str) -> tuple[str, str]:
    """A code cell; leading/trailing blank lines removed."""
    return ("code", text.strip("\n"))


VERSIONS_CELL = code(
    """
# Print the software versions used, so problems can be traced later
import sys, pandas, numpy, scipy, matplotlib, seaborn  # load the libraries to read their versions
print("Python", sys.version.split()[0])  # Python version
for lib in (pandas, numpy, scipy, matplotlib, seaborn):  # each library in turn
    print(lib.__name__, lib.__version__)  # library name and version
"""
)

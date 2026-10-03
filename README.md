# Data Visualization with Excel, Tableau, and AI: Colab Notebooks

Classroom notebooks for an 8-week, English-medium course at National Cheng Kung University (NCKU).
Students run them in Google Colab. No installation and no coding experience are needed.

**How to use:**

1. Click an **Open in Colab** badge below. Sign in with your Google account if asked.
2. Choose **File > Save a copy in Drive**. Work in your copy; otherwise your changes are lost when you close the tab.
3. Run the notebook: **Runtime > Run all**, or one cell at a time with **Shift + Enter**.
   If Colab warns that the notebook was not authored by Google, click **Run anyway**.
4. Scroll to the end. The last check cell prints **CHECK PASSED** when everything worked.

## The notebooks

| Notebook | What students do | Open |
|---|---|---|
| 01 Profile the Airbnb data | Find every data problem at once: size, types, missing values, duplicates. | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/friendi123/ncku-dataviz-colab/blob/main/notebooks/01_profile_airbnb.ipynb) |
| 02 Clean the Airbnb data | The 10 cleaning moves (split, trim, fill, sort and filter, merge, replace, format, remove duplicates, unpivot, extract), each with a row-count log. | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/friendi123/ncku-dataviz-colab/blob/main/notebooks/02_clean_airbnb.ipynb) |
| 03 Are these differences real? | T-tests in plain English: independent, paired, and one-sample. Each part starts with a research question and explains why a t-test fits. | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/friendi123/ncku-dataviz-colab/blob/main/notebooks/03_ttest_airbnb.ipynb) |
| 04 One week of bike-share trips | **Stand-alone assignment** for any course: turn millions of Taipei YouBike or Boston Bluebikes trips into two map-ready tables. Includes an assignment brief and rubric. | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/friendi123/ncku-dataviz-colab/blob/main/notebooks/04_bike_week.ipynb) |

## Using Notebook 04 in another course

Notebook 04 does not depend on the other notebooks.
Change the city, month, and week in Step 1; everything else updates.
It downloads data directly from the official sources and publishes only aggregated tables.
Facts about the source files (columns, sizes, licences) are in [`data/README.md`](data/README.md).

## Data and licences

- **NYC Airbnb:** Inside Airbnb (insideairbnb.com), NYC snapshot 2026-06-14, CC BY 4.0. A copy and the cleaned version are in `data/`.
- **Taipei YouBike 2.0:** Taipei City Government, Department of Transportation (data.taipei), Open Government Data License, version 1.0. Downloaded by Notebook 04; not stored here.
- **Boston Bluebikes:** Bluebikes System Data, Bluebikes Data License Agreement. Downloaded by Notebook 04; not stored here. Publish aggregated data only.

Code in this repository is released under the MIT License (see `LICENSE`).

## Acknowledgement

The order of topics in Notebook 03 was inspired by Todd M. Gureckis,
"The Ultimate (Concise) Guide to t-test type things in Python" (NYU Lab in Cognition).
All code and text here are original.

## For maintainers

- Notebook content lives in `src/nbXX_*.py`. Build with `python scripts/build_notebooks.py`.
- Test with `python scripts/check_notebooks.py`. It runs every notebook twice against local data and recomputes the key statistics.
  The bike checks need one month of each city in `cache/` (see `data/README.md`).

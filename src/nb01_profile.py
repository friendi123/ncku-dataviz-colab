"""Notebook 01: profile the raw NYC Airbnb file (find every problem at once)."""

from nbtools import ATTRIBUTION, DATA_BASE, VERSIONS_CELL, code, md

FILENAME = "01_profile_airbnb.ipynb"

CELLS = [
    md(
        f"""
# Notebook 01: Profile the Airbnb data

Before you clean data, you need to know what is wrong with it.
This notebook checks the whole file in a few seconds.
This is called **data profiling (資料剖析)**.

**What you will learn**

- How big the file is (rows and columns).
- Which columns are stored as the wrong type, such as prices stored as text.
- How much data is missing, and where.

**Why this matters to you:** In Excel, finding these problems takes a long time.
Here, a few lines of Python show every problem at once.
Analysts use this step at the start of almost every project.

**How to use this notebook:** Click a code cell, then press **Shift + Enter** to run it.
Read the result. Then answer the **Check:** question in your head or in your notes.
You do not need to write any code.

{ATTRIBUTION}
"""
    ),
    md(
        """
## Step 1: Load the data

We load the tools we need and read the Airbnb file from the course website.
The file has one row per listing (one home or room for rent).
"""
    ),
    code(
        f"""
import pandas as pd  # pandas: the main tool for tables in Python
import matplotlib.pyplot as plt  # matplotlib: draws charts

# Where the course data lives (a settings value; do not change it)
DATA_BASE = "{DATA_BASE}"

# Read the raw Airbnb file into a table called df (short for "data frame")
df = pd.read_csv(DATA_BASE + "nyc_listings_raw_2026-06-14.csv.gz")
print("Loaded the Airbnb file.")  # confirm that loading worked
"""
    ),
    md(
        """
## Step 2: How big is the file?

`df.shape` gives two numbers: rows, then columns.
"""
    ),
    code(
        """
rows, columns = df.shape  # count rows and columns
print(f"The file has {rows:,} rows and {columns} columns.")  # show both numbers
"""
    ),
    md(
        """
**Check:** How many listings (rows) are in the file? Is that more than you could check by hand?
"""
    ),
    md(
        """
## Step 3: What type is each column?

Every column has a **data type (資料型態)**: number, text, or date.
If a number is stored as text, you cannot add it up or take an average.
"""
    ),
    code(
        """
# Show the first 3 prices and the type Python gives the price column
print(df["price"].head(3))  # the first three prices
print("Type of the price column:", df["price"].dtype)  # 'object' or 'str' both mean text
"""
    ),
    md(
        """
**Check:** The prices look like numbers, but Python says they are text.
Why? Look for the `$` sign and the comma in prices over $1,000.
We fix this in Notebook 02.
"""
    ),
    md(
        """
## Step 4: Where is data missing?

A **missing value (缺失值)** is an empty cell.
We count the share of empty cells in each column and chart the 15 worst columns.
"""
    ),
    code(
        """
missing_share = df.isna().mean().sort_values(ascending=False)  # share of empty cells per column, worst first
top15 = missing_share.head(15)  # keep the 15 columns with the most missing data

ax = top15.sort_values().plot(kind="barh", figsize=(7, 5), color="#4C72B0")  # horizontal bar chart
ax.set_xlabel("Share of listings with no value")  # label the x-axis in plain words
ax.set_title("The 15 columns with the most missing data")  # chart title
plt.tight_layout()  # keep labels inside the picture
plt.show()  # draw the chart

print(f"Missing price: {df['price'].isna().mean():.0%} of listings")  # the one number we care about most
"""
    ),
    md(
        """
**Check:** About how many listings have no price?
Compare this with what you saw in Power Query. The numbers should match.
"""
    ),
    md(
        """
## Step 5: Summary statistics

`describe()` gives the count, mean (平均數), minimum, maximum, and quartiles for number columns.
Look for values that seem impossible.
"""
    ),
    code(
        """
# Summary statistics for four number columns
cols = ["accommodates", "minimum_nights", "number_of_reviews", "review_scores_rating"]  # columns to describe
print(df[cols].describe().round(2))  # rounded to 2 decimals so it is easy to read
"""
    ),
    md(
        """
**Check:** Look at the maximum of `minimum_nights`. Would a guest really book a stay that long?
Price is not in this table. Why not? (Hint: Step 3.)
"""
    ),
    md(
        """
## Step 6: Duplicate listings?

Each listing should appear once. We count listing IDs that appear more than once.
"""
    ),
    code(
        """
duplicates = df["id"].duplicated().sum()  # count IDs that appear more than once
print(f"Duplicate listing IDs: {duplicates}")  # zero is a good result; write it in your log
"""
    ),
    md(
        """
## Step 7: The problems found

This table is your to-do list for Notebook 02.
"""
    ),
    code(
        """
problems = [  # each row: (problem, how many listings)
    ("Price stored as text ($ and commas)", f"{len(df):,} listings"),
    ("Listings with no price", f"{df['price'].isna().sum():,} listings"),
    ("Listings with no reviews per month", f"{df['reviews_per_month'].isna().sum():,} listings"),
    ("Bathrooms stored as text (e.g. '1 shared bath')", f"{df['bathrooms_text'].notna().sum():,} listings"),
    ("Duplicate listing IDs", f"{duplicates}"),
]
for problem, how_many in problems:  # go through the list one row at a time
    print(f"{problem}: {how_many}")  # print the problem and its count
"""
    ),
    md(
        """
### Try it with AI

Copy this prompt into an AI tool. Paste the output of Step 3 after it.

> "Here are the first rows and the type of one column from my data. Explain in two simple sentences
> why this column is stored as text, and give me one line of pandas code to turn it into numbers."

Then check: does the AI code remove both the `$` sign and the comma?
"""
    ),
    md(
        """
## Final check

Run this cell. If everything is right, it prints **CHECK PASSED**.
"""
    ),
    code(
        """
# Verify the key numbers; a message explains what to rerun if something is wrong
assert len(df) == 30259, "The file should have 30,259 rows. Rerun Step 1."  # row count
assert df.shape[1] == 90, "The file should have 90 columns. Rerun Step 1."  # column count
assert round(df["price"].isna().mean() * 100) == 29, "Missing price should be about 29%. Rerun Step 4."  # missing share
print(f"{len(df):,} rows, {df.shape[1]} columns checked.")  # what was checked
print("CHECK PASSED")  # all checks passed
"""
    ),
    VERSIONS_CELL,
]

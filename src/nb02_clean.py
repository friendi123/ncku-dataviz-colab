"""Notebook 02: the 10 cleaning moves on the raw NYC Airbnb file."""

from nbtools import ATTRIBUTION, DATA_BASE, VERSIONS_CELL, code, md

FILENAME = "02_clean_airbnb.ipynb"


def move(number: int, name: str, why: str, body: str, check: str) -> list:
    """One cleaning move: explanation, code that logs rows before and after, and a Check question."""
    return [
        md(f"## Move {number}: {name}\n\n{why}"),
        code(
            "before = len(df)  # rows before this move\n"
            + body.strip("\n")
            + f'\nprint(f"Move {number} ({name}): rows before: {{before:,}} | rows after: {{len(df):,}}")  # log the row counts'
        ),
        md(f"**Check:** {check}"),
    ]


CELLS = [
    md(
        f"""
# Notebook 02: Clean the Airbnb data

In Notebook 01 we found the problems. Now we fix them.
This is the **Transform (轉換)** step of ETL.

**What you will learn**

- The 10 cleaning moves, done in Python.
- How to log every change with the number of rows before and after.
- Why we **flag** strange values instead of deleting them.

**Why this matters to you:** Clean data is the base of every trustworthy chart.
Doing the same moves in Excel and in Python shows you that the skill is the same in any tool.

**Compare with Power Query:** Your instructor will ask you to compare 4 moves (1, 3, 6, and 8) with your Power Query result.
The row counts must match.

**Golden rule:** Never change data silently. Every move below prints the rows before and after.

{ATTRIBUTION}
"""
    ),
    md("## Step 0: Load the raw file and keep the useful columns"),
    code(
        f"""
import os  # os: helps us show where a file is saved
import sys  # sys: tells us if we are running inside Google Colab
import pandas as pd  # pandas: the main tool for tables

# Where the course data lives (a settings value; do not change it)
DATA_BASE = "{DATA_BASE}"

raw = pd.read_csv(DATA_BASE + "nyc_listings_raw_2026-06-14.csv.gz")  # read the raw file

# The columns we keep (the same idea as removing columns in Power Query)
KEEP = [
    "id", "name", "host_id", "host_name", "host_since", "host_is_superhost",
    "neighbourhood_cleansed", "neighbourhood_group_cleansed", "latitude", "longitude",
    "property_type", "room_type", "accommodates", "bathrooms_text", "bedrooms", "beds",
    "amenities", "price", "minimum_nights", "availability_365", "number_of_reviews",
    "last_review", "reviews_per_month", "review_scores_rating", "review_scores_accuracy",
    "review_scores_cleanliness", "review_scores_checkin", "review_scores_communication",
    "review_scores_location", "review_scores_value",
]
df = raw[KEEP].copy()  # a working copy with only these columns
print(f"Kept {{df.shape[1]}} of {{raw.shape[1]}} columns and all {{len(df):,}} rows.")  # confirm
"""
    ),
    *move(
        1,
        "Split",
        'The column `bathrooms_text` mixes a number and a word, for example "1 shared bath".\n'
        "We split it into a number (`bathrooms_count`) and a yes/no column (`bathroom_shared`).",
        """
text = df["bathrooms_text"].str.lower()  # lower case makes matching easier
number = text.str.extract(r"(\\d+\\.?\\d*)")[0].astype(float)  # the first number in the text
number = number.where(~text.str.contains("half", na=False) | number.notna(), 0.5)  # "Half-bath" has no digit: count it as 0.5
df["bathrooms_count"] = number  # new number column
df["bathroom_shared"] = text.str.contains("shared", na=False)  # True if the bathroom is shared
""",
        'Pick one row with "shared" in `bathrooms_text`. Is `bathroom_shared` True for it?',
    ),
    *move(
        2,
        "Trim",
        "Some names have extra spaces at the start, at the end, or in the middle. We remove them.",
        """
for col in ["name", "host_name"]:  # the two name columns
    df[col] = df[col].str.strip().str.replace(r"\\s+", " ", regex=True)  # trim ends; turn many spaces into one
""",
        "Why do extra spaces matter? (Hint: \"Anna \" and \"Anna\" look the same but count as two different names.)",
    ),
    *move(
        3,
        "Fill",
        "Many listings have no value in `reviews_per_month`.\n"
        "We first check why. If a listing has zero reviews, its reviews per month is truly 0.",
        """
gaps = df["reviews_per_month"].isna()  # rows with no value
print(f"Empty cells: {gaps.sum():,}")  # how many gaps
print(f"Of these, listings with zero reviews: {(gaps & (df['number_of_reviews'] == 0)).sum():,}")  # the reason
df["reviews_per_month"] = df["reviews_per_month"].fillna(0)  # fill the gaps with 0 (the true value)
""",
        "Are the two numbers above the same? If yes, filling with 0 is correct, not a guess.",
    ),
    *move(
        4,
        "Sort and filter",
        "Some listings have no price. We do **not** delete them. We add a flag column `price_missing`.\n"
        "Then we sort to see the most-reviewed listings first.",
        """
df["price_missing"] = df["price"].isna()  # True if the listing has no price
df = df.sort_values("number_of_reviews", ascending=False)  # most-reviewed listings first
print(f"Listings flagged with no price: {df['price_missing'].sum():,}")  # how many flags
""",
        "Why is flagging safer than deleting? Who might still need the listings with no price?",
    ),
    *move(
        5,
        "Merge",
        "We join the neighborhood and the borough into one label, such as \"Harlem, Manhattan\".\n"
        "This makes map labels and tooltips clearer.",
        """
df["area_label"] = df["neighbourhood_cleansed"] + ", " + df["neighbourhood_group_cleansed"]  # join two columns
print(df["area_label"].head(3).to_string(index=False))  # show three examples
""",
        "Why might two different boroughs have a neighborhood with a similar name?",
    ),
    *move(
        6,
        "Replace",
        'Price is stored as text, like "$1,234.00". We remove "$" and "," and turn it into a number.',
        """
df["price"] = df["price"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float)  # text to number
print(df["price"].describe().round(2))  # now we can compute statistics on price
""",
        "What are the minimum and maximum prices? Does the maximum look real?",
    ),
    *move(
        7,
        "Format",
        "Dates are stored as text. We turn them into real dates, so we can sort them and count days.",
        """
for col in ["host_since", "last_review"]:  # the two date columns
    df[col] = pd.to_datetime(df[col], errors="coerce")  # text to date; bad values become empty
print(df[["host_since", "last_review"]].dtypes)  # both should now be dates
""",
        "What is the earliest `host_since` date? How long has that host been on Airbnb?",
    ),
    *move(
        8,
        "Remove duplicates",
        "Each listing ID should appear once. We count duplicates, then remove any we find.",
        """
print(f"Duplicate listing IDs found: {df['id'].duplicated().sum()}")  # count duplicates
df = df.drop_duplicates(subset="id")  # keep the first copy of each ID
""",
        "Zero duplicates is a valid result. Write it in your cleaning log.",
    ),
    *move(
        9,
        "Unpivot",
        "The 7 review-score columns are wide: one column per score type.\n"
        "Tableau often works better with a long table: one row per listing and score type.\n"
        "We save the long table as a separate file. The main table keeps its rows.",
        """
score_cols = [c for c in df.columns if c.startswith("review_scores_")]  # the 7 score columns
scores_long = df.melt(id_vars="id", value_vars=score_cols, var_name="score_type", value_name="score")  # wide to long
scores_long["score_type"] = scores_long["score_type"].str.replace("review_scores_", "", regex=False)  # shorter names
print(f"Long table: {len(scores_long):,} rows = {len(df):,} listings x {len(score_cols)} score types")  # size check
""",
        "Why does the long table have 7 times as many rows as the main table?",
    ),
    *move(
        10,
        "Extract",
        "The `amenities` column is a long list in one cell. We extract one yes/no column: does the listing have Wifi?",
        """
df["has_wifi"] = df["amenities"].str.contains("wifi", case=False, na=False)  # True if "wifi" appears anywhere
df = df.drop(columns="amenities")  # drop the long list to keep the file small
print(f"Listings with Wifi: {df['has_wifi'].mean():.0%}")  # share with Wifi
""",
        "Is the share with Wifi higher or lower than you expected?",
    ),
    md(
        """
## Extra: flag price outliers

An **outlier (離群值)** is a value far from the others.
We use a standard rule: a price is an outlier if it is above the upper quartile plus 3 times the
**interquartile range (IQR, 四分位距)**. We flag outliers. We do not delete them.
"""
    ),
    code(
        """
q1, q3 = df["price"].quantile([0.25, 0.75])  # the lower and upper quartiles of price
limit = q3 + 3 * (q3 - q1)  # the outlier limit
df["price_outlier"] = df["price"] > limit  # True if the price is above the limit
print(f"Outlier limit: ${limit:,.2f} per night")  # show the limit
print(f"Listings flagged as outliers: {df['price_outlier'].sum():,}")  # how many flags
"""
    ),
    md("**Check:** Look at the limit. Would you call a listing above it unusual? Write down your choice and reason."),
    md("## Save the clean files"),
    code(
        """
df = df.sort_values("id").reset_index(drop=True)  # put rows back in ID order before saving
df.to_csv("nyc_listings_clean_2026-06-14.csv", index=False)  # save the main clean table
scores_long.sort_values(["id", "score_type"]).to_csv("nyc_review_scores_long_2026-06-14.csv", index=False)  # save the long table
print("Saved to", os.path.abspath("nyc_listings_clean_2026-06-14.csv"))  # where the file is
if "google.colab" in sys.modules:  # only inside Google Colab
    from google.colab import files  # Colab's download helper
    files.download("nyc_listings_clean_2026-06-14.csv")  # download the file to your computer
"""
    ),
    md(
        """
### Try it with AI

Copy this prompt into an AI tool:

> "I have a pandas column called `amenities` that holds a list of features as text.
> Write one line of code that makes a True/False column for whether the text contains 'Air conditioning'."

Run the code in a new cell. Then check: compare the share of True values with the share you expect.
"""
    ),
    md("## Final check\n\nRun this cell. If everything is right, it prints **CHECK PASSED**."),
    code(
        """
# Verify the clean table; a message explains what to rerun if something is wrong
assert len(df) == 30259, "The clean table should still have 30,259 rows. Rerun from Step 0."  # no rows lost
assert pd.api.types.is_numeric_dtype(df["price"]), "Price should be a number. Rerun Move 6."  # price fixed
assert df["reviews_per_month"].isna().sum() == 0, "Reviews per month still has gaps. Rerun Move 3."  # gaps filled
assert df["id"].is_unique, "Listing IDs should be unique. Rerun Move 8."  # no duplicates
print(f"{len(df):,} rows and {df.shape[1]} columns checked.")  # what was checked
print("CHECK PASSED")  # all checks passed
"""
    ),
    VERSIONS_CELL,
]

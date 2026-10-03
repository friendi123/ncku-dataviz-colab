"""Notebook 03: Are these differences real? T-tests on the clean NYC Airbnb file."""

from nbtools import ATTRIBUTION, DATA_BASE, VERSIONS_CELL, code, md

FILENAME = "03_ttest_airbnb.ipynb"

CELLS = [
    md(
        f"""
# Notebook 03: Are these differences real?

Your pivot table showed that some groups have different average prices.
But is a difference **real**, or could it be **chance**?
A **t-test (t 檢定)** helps you answer that question.

**What you will learn**

- How to turn a business question into a research question and two hypotheses.
- When a t-test fits a question, and which kind of t-test to use.
- How to read and report a p-value, an effect size, and a confidence interval in plain English.

**Why this matters to you:** Managers often ask, "Is this difference real?"
A t-test gives you an honest answer. Knowing how to explain it makes your analysis trustworthy.

**How this notebook works**

- Parts 1-5 are the **core track**. Everyone does them.
- Part 6, **Going further**, is optional and not graded. It is for students who know more statistics.
- Each part starts with "You are here". If you feel lost, read the **Stuck?** tip at the end of the part.

{ATTRIBUTION}
"""
    ),
    md("## Step 0: Load the clean data and the helper tools"),
    code(
        f"""
import numpy as np  # numpy: math tools
import pandas as pd  # pandas: tables
import matplotlib.pyplot as plt  # matplotlib: charts
import seaborn as sns  # seaborn: nicer charts
from scipy import stats  # scipy.stats: the t-tests

# Where the course data lives (a settings value; do not change it)
DATA_BASE = "{DATA_BASE}"

df = pd.read_csv(DATA_BASE + "nyc_listings_clean_2026-06-14.csv")  # the file you cleaned in Notebook 02
df["host_type"] = df["host_is_superhost"].map({{"t": "Superhost", "f": "Other host"}})  # readable group names
sns.set_theme(style="whitegrid", palette="colorblind")  # a clean, colour-blind-safe chart style
print(f"Loaded {{len(df):,}} listings.")  # confirm loading worked
"""
    ),
    md(
        """
The next cell defines small helper tools. You do not need to understand every line.
Each tool runs a test and prints the results in plain English.
"""
    ),
    code(
        """
def fmt_p(p):  # write a p-value the way reports usually do
    return "< 0.001" if p < 0.001 else f"= {p:.3f}"  # very small values are shown as < 0.001


def size_label(d):  # turn Cohen's d into words
    d = abs(d)  # the sign only shows direction, so we use the size
    return "tiny" if d < 0.2 else "small" if d < 0.5 else "medium" if d < 0.8 else "large"  # traffic-light reading


def independent_test(a, b, name_a, name_b):  # Welch's t-test for two separate groups
    a, b = a.dropna(), b.dropna()  # ignore empty cells
    result = stats.ttest_ind(a, b, equal_var=False)  # Welch's version: does not assume equal spread
    diff = a.mean() - b.mean()  # difference in averages
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)  # squared standard errors
    dof = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))  # Welch degrees of freedom
    margin = stats.t.ppf(0.975, dof) * np.sqrt(va + vb)  # 95% margin of error
    d = diff / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)  # Cohen's d
    print(f"{name_a}: n = {len(a):,}, mean = {a.mean():,.2f}")  # group A summary
    print(f"{name_b}: n = {len(b):,}, mean = {b.mean():,.2f}")  # group B summary
    print(f"Difference = {diff:,.2f}, t = {result.statistic:.2f}, p {fmt_p(result.pvalue)}")  # the test
    print(f"Cohen's d = {d:.3f} ({size_label(d)}), 95% CI of the difference: {diff - margin:,.2f} to {diff + margin:,.2f}")  # size and range
    return {"diff": diff, "p": result.pvalue, "d": d, "low": diff - margin, "high": diff + margin}  # keep the numbers


def paired_test(x, y, name_x, name_y):  # paired t-test for two scores from the same listings
    pair = pd.concat([x, y], axis=1).dropna()  # keep listings that have both scores
    x, y = pair.iloc[:, 0], pair.iloc[:, 1]  # the two columns again
    diff = x - y  # one difference per listing
    result = stats.ttest_rel(x, y)  # the paired t-test
    margin = stats.t.ppf(0.975, len(diff) - 1) * diff.std(ddof=1) / np.sqrt(len(diff))  # 95% margin of error
    d = diff.mean() / diff.std(ddof=1)  # Cohen's d for paired data
    print(f"Listings with both scores: n = {len(diff):,}")  # sample size
    print(f"{name_x} mean = {x.mean():.3f}, {name_y} mean = {y.mean():.3f}")  # the two averages
    print(f"Mean difference = {diff.mean():.3f}, t = {result.statistic:.2f}, p {fmt_p(result.pvalue)}")  # the test
    print(f"Cohen's d = {d:.3f} ({size_label(d)}), 95% CI: {diff.mean() - margin:.3f} to {diff.mean() + margin:.3f}")  # size and range
    return {"diff": diff.mean(), "p": result.pvalue, "d": d, "low": diff.mean() - margin, "high": diff.mean() + margin}  # keep the numbers


def one_sample_test(x, target, name):  # one-sample t-test against a fixed number
    x = x.dropna()  # ignore empty cells
    result = stats.ttest_1samp(x, target)  # compare the average with the target
    margin = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))  # 95% margin of error
    d = (x.mean() - target) / x.std(ddof=1)  # Cohen's d
    print(f"{name}: n = {len(x):,}, mean = {x.mean():.3f}, target = {target}")  # summary
    print(f"Difference from target = {x.mean() - target:.3f}, t = {result.statistic:.2f}, p {fmt_p(result.pvalue)}")  # the test
    print(f"Cohen's d = {d:.3f} ({size_label(d)}), 95% CI of the mean: {x.mean() - margin:.3f} to {x.mean() + margin:.3f}")  # size and range
    return {"mean": x.mean(), "p": result.pvalue, "d": d, "low": x.mean() - margin, "high": x.mean() + margin}  # keep the numbers


print("Helper tools are ready.")  # confirm the tools loaded
"""
    ),
    md(
        """
## Stats in 5 minutes

Read this once. Come back to it whenever you need it.

| Term | Plain English | Airbnb example |
|---|---|---|
| **Mean (平均數)** | The average. Add all values and divide by how many there are. | The average nightly price. |
| **Median (中位數)** | The middle value when you sort from low to high. Extreme values do not move it much. | Half of listings cost less than the median price. |
| **Sample (樣本)** | The data we have. We use it to learn about a bigger group. | These listings stand for NYC Airbnb listings in general. |
| **Hypothesis (假設)** | A claim we test. H0 (null) says "no difference". H1 says "there is a difference". | H0: superhosts and other hosts charge the same on average. |
| **p-value (p 值)** | If there were really no difference, how surprising would our result be? A small p (below 0.05) means "probably a real difference". | p = 0.30: not surprising, no evidence of a difference. p < 0.001: very surprising, a real difference is likely. |
| **Effect size, Cohen's d (效果量)** | How big the difference is, in standard units. Read it like a traffic light: under 0.2 tiny, about 0.5 medium, 0.8 or more large. | d = 0.05: the groups are almost the same, even if p is small. |
| **95% confidence interval (95% 信賴區間)** | The likely range for the true difference. | "Between $2 and $9 more per night." |

**Two rules to remember**

1. A small p-value says a difference is probably **real**. It does not say the difference is **big**.
2. Always report the effect size next to the p-value.
"""
    ),
    md(
        """
## Choosing a test

Start from your question, not from the test.

| Ask yourself | If the answer is... | Use |
|---|---|---|
| Is my outcome a number (price, score)? | Yes | A t-test can fit. (If it is a category, such as yes/no, use a different test.) |
| How many groups do I compare? | Two separate groups (each listing is in one group only) | **Independent t-test** (Part 1) |
| | Two scores from the **same** listings | **Paired t-test** (Part 3) |
| | One group against a fixed target number | **One-sample t-test** (Part 4) |
| Do a few extreme values dominate? | Yes | Check the medians and rerun without the outliers (Part 2). |
"""
    ),
    # ---------------- Part 1 ----------------
    md(
        """
## Part 1: Do superhosts charge a different price?

*You are here: Part 1 of 5 (core).*

### Research question

Airbnb gives the **superhost (超讚房東)** badge to experienced, highly rated hosts.
Pricing question: **Do superhosts charge a different nightly price from other hosts?**
If they do, the badge may support a price premium.

### Why a t-test fits

- The outcome is a **number**: nightly price.
- There are **two separate groups**: each host is either a superhost or not.
- We compare the **averages** of the two groups.

So we use an **independent-samples t-test**.
We use **Welch's version**, the safe default, because the two groups have different sizes and spreads.

### Hypotheses

- **H0:** Superhosts and other hosts charge the same average price.
- **H1:** Superhosts and other hosts charge different average prices.

### Look first

Always look at the data before you test it.
"""
    ),
    code(
        """
priced = df[df["price"].notna() & df["host_type"].notna()]  # listings with a price and a known host type
ax = sns.boxplot(data=priced, x="host_type", y="price")  # one box per group
ax.set_yscale("log")  # log scale, so very high prices do not squash the boxes
ax.set_xlabel("")  # the group names are enough
ax.set_ylabel("Nightly price (USD, log scale)")  # plain-English axis label
ax.set_title("Nightly price by host type")  # chart title
plt.show()  # draw the chart
print(priced.groupby("host_type")["price"].agg(["count", "mean", "median"]).round(2))  # the numbers behind the chart
"""
    ),
    md("**Check:** Look at the means and the medians. Which one shows a bigger gap between the groups?"),
    md("### Run the test"),
    code(
        """
part1 = independent_test(  # run Welch's t-test
    priced.loc[priced["host_type"] == "Superhost", "price"],
    priced.loc[priced["host_type"] == "Other host", "price"],
    "Superhosts",
    "Other hosts",
)
"""
    ),
    md("### How to report it\n\nThe next cell writes the report sentence from your numbers."),
    code(
        """
direction = "more" if part1["diff"] > 0 else "less"  # are superhosts higher or lower?
verdict = "a statistically significant" if part1["p"] < 0.05 else "no statistically significant"  # significant or not
print(  # print the report sentence
    f"Superhosts charged ${abs(part1['diff']):,.2f} {direction} per night than other hosts on average. "
    f"Welch's t-test found {verdict} difference (p {fmt_p(part1['p'])}). "
    f"The effect was {size_label(part1['d'])} (Cohen's d = {part1['d']:.2f})."
)
"""
    ),
    md(
        """
**Stuck?** Reread "Stats in 5 minutes". Or ask an AI tool:
"Explain this result to a first-year student in three sentences:" and paste the output above.
"""
    ),
    # ---------------- Part 2 ----------------
    md(
        """
## Part 2: Is that difference real, or caused by a few extreme listings?

*You are here: Part 2 of 5 (core).*

### Research question

**Is the price difference in Part 1 real, or is it caused by a few listings with extreme prices?**

In Notebook 02 we flagged price **outliers (離群值)**.
An average can move a lot because of a few extreme values. A median does not.
So we use two simple checks. No new test is needed:

1. Compare the **medians** of the two groups.
2. Run the **same** t-test again **without** the flagged outliers.
"""
    ),
    code(
        """
print(priced.groupby("host_type")["price"].median().round(2))  # the middle price in each group
print(f"Listings flagged as outliers: {priced['price_outlier'].sum():,}")  # how many we set aside
"""
    ),
    md("Now the same t-test, without the outliers:"),
    code(
        """
typical = priced[~priced["price_outlier"]]  # keep listings that are not outliers
part2 = independent_test(  # the same Welch's t-test as Part 1
    typical.loc[typical["host_type"] == "Superhost", "price"],
    typical.loc[typical["host_type"] == "Other host", "price"],
    "Superhosts (no outliers)",
    "Other hosts (no outliers)",
)
"""
    ),
    md("### How to report it"),
    code(
        """
if part1["p"] < 0.05 and part2["p"] >= 0.05:  # significant with outliers, not without
    print(  # explain what changed
        f"With all listings, the difference looked significant (p {fmt_p(part1['p'])}). "
        f"Without the {priced['price_outlier'].sum():,} outliers, it was not (p {fmt_p(part2['p'])}). "
        "A few extreme prices created the difference. Typical superhosts and other hosts charge about the same."
    )
else:  # any other combination
    print(f"With all listings: p {fmt_p(part1['p'])}. Without outliers: p {fmt_p(part2['p'])}. Compare the two and explain.")  # neutral wording
"""
    ),
    md(
        """
**Lesson:** Outliers can fool a t-test. Always look at the data and the medians before you trust a p-value.

**Stuck?** Think of ten friends with similar incomes, and one billionaire joining the group.
The average income jumps. The median hardly moves.
"""
    ),
    # ---------------- Part 3 ----------------
    md(
        """
## Part 3: Do guests rate cleanliness differently from location?

*You are here: Part 3 of 5 (core).*

### Research question

Service-quality question: **For the same listing, do guests rate cleanliness differently from location?**
If cleanliness scores are lower, hosts know where to improve.

### Why a t-test fits

- The outcome is a **number**: a review score from 1 to 5.
- The two scores come from the **same listing**, so they are linked in pairs.
- We compare the **average difference** within each pair.

So we use a **paired t-test**.

### Hypotheses

- **H0:** On average, cleanliness and location scores are the same.
- **H1:** On average, they are different.

### Look first
"""
    ),
    code(
        """
pairs = df[["review_scores_cleanliness", "review_scores_location"]].dropna()  # listings with both scores
gap = pairs["review_scores_cleanliness"] - pairs["review_scores_location"]  # one difference per listing
ax = gap.plot(kind="hist", bins=40, figsize=(7, 4))  # how the differences are spread
ax.axvline(0, color="black", linestyle="--")  # zero means "the same score"
ax.set_xlabel("Cleanliness score minus location score")  # plain-English axis label
ax.set_title("Most listings get similar scores for both")  # chart title
plt.show()  # draw the chart
"""
    ),
    md("### Run the test"),
    code(
        """
part3 = paired_test(df["review_scores_cleanliness"], df["review_scores_location"], "Cleanliness", "Location")  # paired t-test
"""
    ),
    md("### How to report it"),
    code(
        """
print(  # print the report sentence
    f"Across {len(pairs):,} listings, cleanliness scores were {abs(part3['diff']):.3f} points "
    f"{'lower' if part3['diff'] < 0 else 'higher'} than location scores on average "
    f"(paired t-test, p {fmt_p(part3['p'])}). "
    f"But the effect was {size_label(part3['d'])} (Cohen's d = {part3['d']:.2f})."
)
"""
    ),
    md(
        """
**Lesson:** With more than 20,000 listings, even a very small difference becomes "significant".
**Significant does not mean important.** The effect size tells you whether it matters.

**Stuck?** A p-value answers "Is it real?". Cohen's d answers "Is it big?". You need both answers.
"""
    ),
    # ---------------- Part 4 ----------------
    md(
        """
## Part 4: Is the average listing below the superhost standard?

*You are here: Part 4 of 5 (core).*

### Research question

Benchmarking question: superhosts are expected to keep an overall rating of at least 4.8.
**Is the average NYC listing rated below 4.8?**

### Why a t-test fits

- The outcome is a **number**: the overall rating.
- We have **one group** (all rated listings) and **one fixed target** (4.8).

So we use a **one-sample t-test**.

### Hypotheses

- **H0:** The average rating equals 4.8.
- **H1:** The average rating is different from 4.8.

### Look first
"""
    ),
    code(
        """
ratings = df["review_scores_rating"].dropna()  # listings with a rating
ax = ratings.plot(kind="hist", bins=40, figsize=(7, 4))  # how ratings are spread
ax.axvline(4.8, color="black", linestyle="--", label="Superhost standard (4.8)")  # the target
ax.set_xlabel("Overall rating")  # axis label
ax.set_title("Overall ratings of NYC listings")  # chart title
ax.legend()  # show the label for the dashed line
plt.show()  # draw the chart
"""
    ),
    md("### Run the test"),
    code(
        """
part4 = one_sample_test(df["review_scores_rating"], 4.8, "Overall rating")  # one-sample t-test
"""
    ),
    md("### How to report it"),
    code(
        """
print(  # print the report sentence
    f"The average rating was {part4['mean']:.2f} (95% CI {part4['low']:.2f} to {part4['high']:.2f}), "
    f"{'below' if part4['mean'] < 4.8 else 'above'} the superhost standard of 4.8 "
    f"(one-sample t-test, p {fmt_p(part4['p'])}; Cohen's d = {part4['d']:.2f}, {size_label(part4['d'])})."
)
"""
    ),
    md(
        """
**Stuck?** The confidence interval is the likely range for the true average.
If 4.8 is outside that range, the average is probably different from 4.8.
"""
    ),
    # ---------------- Part 5 ----------------
    md(
        """
## Part 5: Your turn

*You are here: Part 5 of 5 (core).*

Question to explore: entire homes and private rooms. Which one costs more **per guest**?

Before you run the code, write these in your notes:

1. **Research question:** ______________________________
2. **Why a t-test fits:** Is the outcome a number? Are the groups separate or paired?
3. **Hypotheses:** H0: ______________________ H1: ______________________

Then run the cell, and write the report sentence yourself.
"""
    ),
    code(
        """
homes = df[df["price"].notna() & ~df["price_outlier"]].copy()  # priced listings, outliers set aside
homes["price_per_guest"] = homes["price"] / homes["accommodates"]  # nightly price divided by number of guests
part5 = independent_test(  # Welch's t-test, as in Part 1
    homes.loc[homes["room_type"] == "Entire home/apt", "price_per_guest"],
    homes.loc[homes["room_type"] == "Private room", "price_per_guest"],
    "Entire homes",
    "Private rooms",
)
"""
    ),
    md(
        """
**Stuck?** Copy the Part 1 report sentence and change the names and numbers.
Remember: report the difference, the p-value, and the effect size.
"""
    ),
    # ---------------- Part 6 ----------------
    md(
        """
## Part 6: Going further (optional)

*You are here: optional extra. Not graded. Skip it if you like.*

**Rank-based tests.** The Mann-Whitney and Wilcoxon tests compare which group **tends to be higher**,
using ranks instead of averages. Use them when extreme values dominate.

- **Mann-Whitney**: two separate groups (like Part 1).
- **Wilcoxon**: paired scores (like Part 3).
"""
    ),
    code(
        """
mw = stats.mannwhitneyu(  # Mann-Whitney test on all priced listings (outliers included)
    priced.loc[priced["host_type"] == "Superhost", "price"],
    priced.loc[priced["host_type"] == "Other host", "price"],
)
print(f"Mann-Whitney (Part 1 groups): p {fmt_p(mw.pvalue)}")  # compare with Part 1
wx = stats.wilcoxon(pairs["review_scores_cleanliness"], pairs["review_scores_location"])  # Wilcoxon on the Part 3 pairs
print(f"Wilcoxon (Part 3 pairs): p {fmt_p(wx.pvalue)}")  # compare with Part 3
"""
    ),
    md(
        """
**Log price and Student's t-test.** Taking the logarithm of price pulls extreme values in.
Student's t-test assumes both groups have the same spread. Welch's does not, so Welch's is the safer default.
"""
    ),
    code(
        """
log_sh = np.log(priced.loc[priced["host_type"] == "Superhost", "price"])  # log price, superhosts
log_ot = np.log(priced.loc[priced["host_type"] == "Other host", "price"])  # log price, other hosts
print(f"Welch's t-test on log price: p {fmt_p(stats.ttest_ind(log_sh, log_ot, equal_var=False).pvalue)}")  # log scale
student = stats.ttest_ind(  # Student's t-test (assumes equal spread)
    priced.loc[priced["host_type"] == "Superhost", "price"],
    priced.loc[priced["host_type"] == "Other host", "price"],
    equal_var=True,
)
print(f"Student's t-test on price: p {fmt_p(student.pvalue)}")  # compare with Welch's in Part 1
"""
    ),
    md(
        """
### Try it with AI

Copy this prompt into an AI tool, and paste your Part 1 output after it:

> "Here is a Welch's t-test result. Explain it to a marketing manager in three short sentences.
> Mention the p-value and the effect size, and say whether the difference matters in practice."

Then check: did the AI mention the effect size? Did it say "significant" means "big"? (It should not.)
"""
    ),
    md("## Final check\n\nRun this cell. It checks the core track (Parts 1-5)."),
    code(
        """
# Verify the core results; a message explains what to rerun if something is wrong
assert len(df) == 30259, "The data should have 30,259 listings. Rerun Step 0."  # data loaded
assert part1["p"] < 0.05, "Part 1 should show p below 0.05. Rerun Part 1."  # Part 1 result
assert part2["p"] >= 0.05, "Part 2 should show p of 0.05 or more. Rerun Part 2."  # Part 2 result
assert part3["p"] < 0.001 and abs(part3["d"]) < 0.2, "Part 3: p below 0.001 with a tiny effect. Rerun Part 3."  # Part 3
assert part4["mean"] < 4.8 and part4["p"] < 0.001, "Part 4: average below 4.8, p below 0.001. Rerun Part 4."  # Part 4
assert "p" in part5, "Run Part 5 before this check."  # Part 5 ran
print("Core track checked: Parts 1-5.")  # what was checked
print("CHECK PASSED")  # all checks passed
"""
    ),
    VERSIONS_CELL,
]

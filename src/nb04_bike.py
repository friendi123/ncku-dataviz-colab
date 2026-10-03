"""Notebook 04: one week of bike-share trips (stand-alone assignment, reusable in any course)."""

from nbtools import VERSIONS_CELL, code, md

FILENAME = "04_bike_week.ipynb"

CELLS = [
    md(
        """
# One Week of Bike-Share Trips: From Millions of Rows to a Map

City bike-share systems publish every trip. One month can hold millions of rows,
which is far more than Excel can open (its limit is 1,048,576 rows).
In this assignment, you use Python to turn one week of trips into two small tables
that are ready for a map in Tableau Public or any other visualization tool.

You can choose one of two cities:

- **Taipei, YouBike 2.0 (臺北市 YouBike 2.0)**
- **Boston, Bluebikes**

**What you will learn**

- How to download and read a very large open-data file in Python.
- How to filter one week and count trips by station, day, and hour.
- How to add station locations, so trips can be drawn on a map as points and lines.

**Why this matters to you:** Real-world data is often too big for a spreadsheet.
Turning big data into a small, accurate summary is a core analyst skill, and a strong portfolio piece.

**How to use this notebook:** Click a code cell, then press **Shift + Enter** to run it.
Read each result and answer the **Check:** question. You only change the settings in Step 1.
"""
    ),
    md(
        """
## Assignment brief

**Task.** Pick a city and one week. Use this notebook to build two tables.
Then build a dashboard that answers this question:
**"Where and when do people ride, and where do they go?"**

**Deliverables**

1. The two CSV files from this notebook:
   - trips by station, day, and hour (`..._station_hour.csv`);
   - trips by start station and end station (`..._station_pairs.csv`).
2. A dashboard with at least:
   - a map of stations sized by number of trips;
   - a chart of trips by hour of the day;
   - a flow map of the busiest station-to-station routes.
3. A short write-up (about 150 words): your three main findings, and one limitation of the data.
4. A source line on the dashboard (see Step 9).

**Rubric**

| Criterion | Strong (3) | Getting there (2) | Not yet (1) |
|---|---|---|---|
| Accuracy | Totals match the notebook. Choices (city, week) are stated. | Small errors that do not change the findings. | Errors that change the findings. |
| Insight | Three clear findings, supported by the charts. | Findings are present but vague. | Charts without findings. |
| Design | Clear titles, readable map, simple charts. | Readable but cluttered in places. | Hard to read. |
| Responsible use | Source line present. Only aggregated data is published. | Source line incomplete. | No source line, or raw trip data published. |

**For instructors:** Change the city, month, and week in Step 1. Everything else updates.
The notebook stops with a plain-English message if a download fails.
Facts about the source files (columns, sizes, licences) are in `data/README.md` in this repository.
"""
    ),
    md(
        """
## Step 1: Choose your city and week

Change only the three settings below.

- `CITY`: `"YouBike"` (Taipei) or `"Bluebikes"` (Boston).
- `MONTH`: the month of data, as `"YYYY-MM"`.
- `WEEK_START`: the first day of your week, as `"YYYY-MM-DD"`. It must be inside `MONTH`, at least 6 days before the month ends.

Example for Boston: `CITY = "Bluebikes"`, `MONTH = "2026-08"`, `WEEK_START = "2026-08-03"`.
"""
    ),
    code(
        """
CITY = "YouBike"  # "YouBike" (Taipei) or "Bluebikes" (Boston)
MONTH = "2026-07"  # the month of trips to download, "YYYY-MM"
WEEK_START = "2026-07-06"  # the first day of your week, "YYYY-MM-DD"

# Official download addresses (settings values; do not change them)
YOUBIKE_URL_TEMPLATE = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike_second_ticket_opendata/{year}/{year}-{month}/{year}{month}_YouBike2.0票證刷卡資料.zip"  # YouBike monthly trips
YOUBIKE_STATIONS_URL = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"  # YouBike station list
BLUEBIKES_URL_TEMPLATE = "https://s3.amazonaws.com/hubway-data/{year}{month}-bluebikes-tripdata.zip"  # Bluebikes monthly trips

assert CITY in ("YouBike", "Bluebikes"), 'CITY must be "YouBike" or "Bluebikes".'  # catch typos early
print(f"City: {CITY}. Month: {MONTH}. Week starts: {WEEK_START}.")  # confirm the settings
"""
    ),
    md(
        """
## Step 2: Download one month of trips

This can take a minute. The YouBike file is about 133 MB; the Bluebikes file is about 22 MB.
"""
    ),
    code(
        """
import os  # os: checks whether a file exists
import sys  # sys: tells us if we are running inside Google Colab
import json  # json: reads the YouBike station list
import zipfile  # zipfile: opens .zip files
import urllib.parse  # urllib.parse: makes web addresses safe to request
import urllib.request  # urllib.request: downloads files
import pandas as pd  # pandas: tables
import matplotlib.pyplot as plt  # matplotlib: charts

DOWNLOAD_FAILED = "The download failed. Try again, or ask your instructor for the backup file."  # plain-English message


def fetch(source, target):  # get a file from the web (or use a local copy if the source is a file)
    if os.path.exists(source):  # a local file: nothing to download
        return source  # use it directly
    safe = urllib.parse.quote(source, safe=":/")  # encode Chinese characters in the address
    for attempt in (1, 2):  # try twice
        try:  # a download can fail for network reasons
            urllib.request.urlretrieve(safe, target)  # save the file
            return target  # success
        except Exception as problem:  # report the problem in plain English
            print(f"Attempt {attempt} did not work ({type(problem).__name__}).")  # say what happened
    print(DOWNLOAD_FAILED)  # both attempts failed
    raise SystemExit(DOWNLOAD_FAILED)  # stop here with a short message


year, month = MONTH.split("-")  # split "2026-07" into "2026" and "07"
template = YOUBIKE_URL_TEMPLATE if CITY == "YouBike" else BLUEBIKES_URL_TEMPLATE  # the right address for the city
zip_path = fetch(template.format(year=year, month=month), f"{CITY}_{MONTH}.zip")  # download the month
print("Downloaded:", zip_path)  # confirm
"""
    ),
    md(
        """
## Step 3: Read the trips and keep your week

The file is too big to read in one go on a free computer, so we read it in **chunks (分批)**
of one million rows, and keep only the trips in your week.

The two cities use different column names. We rename them to the same three names:
`start_time`, `start_station`, `end_station`.
"""
    ),
    code(
        """
week = pd.date_range(WEEK_START, periods=7).strftime("%Y-%m-%d")  # the 7 dates in your week
if CITY == "YouBike":  # Taipei column names
    columns = {"rent_time": "start_time", "rent_station": "start_station", "return_station": "end_station"}  # old -> new
else:  # Boston column names
    columns = {"started_at": "start_time", "start_station_name": "start_station", "end_station_name": "end_station",
               "start_lat": "start_lat", "start_lng": "start_lng"}  # Bluebikes also has coordinates

archive = zipfile.ZipFile(zip_path)  # open the zip file
csv_name = [n for n in archive.namelist() if n.endswith(".csv") and not n.startswith("__MACOSX")][0]  # the trip file
month_total, kept = 0, []  # counters
for chunk in pd.read_csv(archive.open(csv_name), usecols=list(columns), chunksize=1_000_000, encoding="utf-8"):  # one million rows at a time
    month_total += len(chunk)  # count every trip in the month
    chunk = chunk.rename(columns=columns)  # use the shared column names
    kept.append(chunk[chunk["start_time"].str[:10].isin(week)])  # keep trips that start in your week
trips = pd.concat(kept, ignore_index=True)  # join the kept pieces into one table
trips["start_time"] = pd.to_datetime(trips["start_time"])  # text to date and time

print(f"Trips in the month: {month_total:,}")  # the whole month
print(f"Trips in the chosen week: {len(trips):,}")  # your week
"""
    ),
    md(
        """
**Check:** Is one week of trips still more than Excel's limit of 1,048,576 rows?
For YouBike, note that rental times are rounded to the hour in the source data, for privacy.
"""
    ),
    md(
        """
## Step 4: Missing station names

A few trips have no station name. We do **not** delete them.
We label them "(unknown station)", so every trip is still counted.
"""
    ),
    code(
        """
for col in ["start_station", "end_station"]:  # both station columns
    print(f"{col}: {trips[col].isna().sum():,} trips with no name")  # how many are missing
    trips[col] = trips[col].fillna("(unknown station)")  # keep the trip, with a clear label
"""
    ),
    md(
        """
## Step 5: Count trips by station, day, and hour

This is the first table for your dashboard.
"""
    ),
    code(
        """
trips["date"] = trips["start_time"].dt.strftime("%Y-%m-%d")  # the day of each trip
trips["weekday"] = trips["start_time"].dt.day_name()  # Monday, Tuesday, ...
trips["hour"] = trips["start_time"].dt.hour  # 0 to 23
hourly = (  # count trips for each station, day, and hour
    trips.groupby(["start_station", "date", "weekday", "hour"]).size().reset_index(name="trips")
    .rename(columns={"start_station": "station"})
)
print(f"Rows in the station-hour table: {len(hourly):,}")  # much smaller than the trip table
print(hourly.sort_values("trips", ascending=False).head(5).to_string(index=False))  # the five busiest station-hours
"""
    ),
    code(
        """
by_hour = trips.groupby("hour").size()  # trips in each hour of the day, all stations together
ax = by_hour.plot(kind="bar", figsize=(8, 3.5), color="#4C72B0")  # a bar for each hour
ax.set_xlabel("Hour of the day")  # axis label
ax.set_ylabel("Trips")  # axis label
ax.set_title(f"{CITY}: trips by hour, week of {WEEK_START}")  # chart title
plt.tight_layout()  # keep labels inside the picture
plt.show()  # draw the chart
"""
    ),
    md("**Check:** When are the two busiest times of day? What might explain them?"),
    md(
        """
## Step 6: Add station locations

A map needs latitude and longitude for each station.

- **YouBike:** the trip file has no coordinates. We download the official station list
  and match stations by name. The station list also gives English names.
- **Bluebikes:** the trip file already has coordinates. We take the middle value for each station.
"""
    ),
    code(
        """
if CITY == "YouBike":  # Taipei: use the official station list
    stations_file = fetch(YOUBIKE_STATIONS_URL, "youbike_stations.json")  # download the station list
    with open(stations_file, encoding="utf-8") as f:  # open it as text
        stations = pd.DataFrame(json.load(f))  # turn the list into a table
    stations["station"] = stations["sna"].str.replace("YouBike2.0_", "", regex=False)  # same names as the trip file
    stations["station_en"] = stations["snaen"].str.replace("YouBike2.0_", "", regex=False)  # English names
    stations = stations.rename(columns={"latitude": "lat", "longitude": "lng"})[["station", "station_en", "lat", "lng"]]  # keep what we need
else:  # Boston: coordinates are in the trip file
    stations = (  # middle coordinates for each station
        trips.groupby("start_station")[["start_lat", "start_lng"]].median().reset_index()
        .rename(columns={"start_station": "station", "start_lat": "lat", "start_lng": "lng"})
    )
    stations["station_en"] = stations["station"]  # names are already in English
stations = stations.drop_duplicates(subset="station")  # one row per station

matched = trips["start_station"].isin(stations["station"]).mean()  # share of trips whose station has a location
print(f"Stations with a location: {len(stations):,}")  # how many stations
print(f"Trips with a matched start station: {matched:.1%}")  # how many trips can go on the map
"""
    ),
    md(
        """
**Check:** Not every trip matches. For YouBike, a few station names lost a rare Chinese character
at the source (shown as `?`). Why is it important to report the match rate instead of hiding it?
"""
    ),
    md(
        """
## Step 7: Count trips from each station to each other station

This is the second table. It lets you draw **flow lines (流向線)** from start to end.
In Tableau, use `MAKELINE(MAKEPOINT([start_lat], [start_lng]), MAKEPOINT([end_lat], [end_lng]))`.
"""
    ),
    code(
        """
pairs = trips.groupby(["start_station", "end_station"]).size().reset_index(name="trips")  # trips for each route
pairs = pairs.merge(  # add start coordinates
    stations.rename(columns={"station": "start_station", "station_en": "start_station_en", "lat": "start_lat", "lng": "start_lng"}),
    on="start_station", how="left",
)
pairs = pairs.merge(  # add end coordinates
    stations.rename(columns={"station": "end_station", "station_en": "end_station_en", "lat": "end_lat", "lng": "end_lng"}),
    on="end_station", how="left",
)
hourly = hourly.merge(stations, on="station", how="left")  # add coordinates to the first table too
print(f"Routes: {len(pairs):,}")  # how many start-end combinations
print(pairs.sort_values("trips", ascending=False).head(5)[["start_station", "end_station", "trips"]].to_string(index=False))  # busiest routes
"""
    ),
    md("**Check:** Are the busiest routes short trips or long trips? What does that suggest about how people use the bikes?"),
    md(
        """
## Step 8: Save the two tables

These tables are **aggregated (彙總)**: they hold counts, not individual trips.
Publish only aggregated tables. The Bluebikes licence does not allow republishing the raw trip data.
"""
    ),
    code(
        """
label = f"{CITY.lower()}_{WEEK_START}"  # e.g. youbike_2026-07-06
hourly.to_csv(f"{label}_station_hour.csv", index=False, encoding="utf-8-sig")  # utf-8-sig keeps Chinese readable in Excel
pairs.to_csv(f"{label}_station_pairs.csv", index=False, encoding="utf-8-sig")  # the route table
print("Saved to", os.path.abspath(f"{label}_station_hour.csv"))  # where the files are
if "google.colab" in sys.modules:  # only inside Google Colab
    from google.colab import files  # Colab's download helper
    files.download(f"{label}_station_hour.csv")  # download table 1
    files.download(f"{label}_station_pairs.csv")  # download table 2
"""
    ),
    md(
        """
## Step 9: Source line for your dashboard

Copy the line for your city onto your dashboard:

- **YouBike:** "Data: Taipei City Government, Department of Transportation (data.taipei), Open Government Data License, version 1.0. Aggregated by the author."
- **Bluebikes:** "Data: Bluebikes System Data (bluebikes.com/system-data). Aggregated by the author."

Do not suggest that the city or the bike company supports your work.
"""
    ),
    md(
        """
### Try it with AI

Copy this prompt into an AI tool:

> "I have a pandas table called `trips` with columns `start_time` (datetime) and `start_station`.
> Write code that counts trips on weekdays versus weekends for each station."

Run the code in a new cell. Then check: do the weekday and weekend counts add up to the week total?
"""
    ),
    md("## Final check\n\nRun this cell. If everything is right, it prints **CHECK PASSED**."),
    code(
        """
# Verify that nothing was lost; a message explains what to rerun if something is wrong
assert hourly["trips"].sum() == len(trips), "The station-hour table does not add up to the week. Rerun Steps 4-5."  # table 1
assert pairs["trips"].sum() == len(trips), "The route table does not add up to the week. Rerun Step 7."  # table 2
assert len(trips) > 0, "No trips in your week. Check WEEK_START in Step 1."  # the week is not empty
print(f"Both tables add up to {len(trips):,} trips.")  # what was checked
print("CHECK PASSED")  # all checks passed
"""
    ),
    VERSIONS_CELL,
]

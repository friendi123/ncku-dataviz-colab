# Data

## NYC Airbnb (stored here)

| File | What it is |
|---|---|
| `nyc_listings_raw_2026-06-14.csv.gz` | Inside Airbnb detailed listings for New York City, snapshot 2026-06-14, unchanged. 30,259 rows, 90 columns. |
| `nyc_listings_clean_2026-06-14.csv` | The same listings after the 10 cleaning moves in Notebook 02. Same 30,259 rows. |
| `nyc_review_scores_long_2026-06-14.csv` | The 7 review-score columns reshaped to long format (Notebook 02, move 9). |

Source: Inside Airbnb (insideairbnb.com). Licence: Creative Commons Attribution 4.0 International (CC BY 4.0).
We keep a copy because Inside Airbnb removes older snapshots from its download page.
The cleaned files are derived work by the course instructor, shared under the same licence.

## Bike-share data (not stored here)

Notebook 04 downloads one month directly from the official source.
We do not store bike data in this repository: the Bluebikes licence does not allow republishing the raw data.

Facts checked on 2026-10-03:

| | Taipei YouBike 2.0 | Boston Bluebikes |
|---|---|---|
| Example month | July 2026 | August 2026 |
| Download | 133 MB zip | 22 MB zip |
| Inside the zip | one CSV, 886 MB | one CSV, 139 MB (plus a `__MACOSX` folder to ignore) |
| Text encoding | UTF-8 | UTF-8 |
| Trips in the month | 7,596,992 | 582,663 |
| Trips in one week | 1,338,920 (6-12 July 2026) | 124,721 (3-9 August 2026) |
| Columns | `rent_time, rent_station, return_time, return_station, rent, bike_type, infodate` | `ride_id, rideable_type, started_at, ended_at, start_station_name, start_station_id, end_station_name, end_station_id, start_lat, start_lng, end_lat, end_lng, member_casual` |
| Time detail | Rental and return times are rounded to the hour | Exact to the millisecond |
| Station coordinates | Not in the trip file. Join `rent_station` to the station feed (`sna` without the `YouBike2.0_` prefix): 99.8% of trips match. | In the trip file (`start_lat`, `start_lng`) |
| Licence | Open Government Data License, version 1.0 (Taipei City Government, Department of Transportation) | Bluebikes Data License Agreement: analysis and sharing findings allowed; no republishing of raw data |

Notes:

- The YouBike **file index** (the list of monthly download links) is Big5-encoded. The monthly trip files are UTF-8.
- About 0.2% of YouBike trips use station names where a rare Chinese character was lost at the source (shown as `?`).
- One week of YouBike trips is still larger than Excel's limit of 1,048,576 rows. That is why we count trips in Python first.

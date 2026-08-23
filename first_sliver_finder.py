"""
generate_jewish_new_moon_timings.py

Reads:
    new_moon.csv     - astronomical new moon dates/times (UT)
    sunset_times.csv - sunset times for Jerusalem (UT)

Both input files must sit in the same directory as this script.

Writes:
    jewish_new_moon_timings.csv - also written to that same directory.

Output columns:
    1. ID                        - sequential ID starting at 1
    2. New Moon Date             - date of the astronomical new moon
    3. New Moon Time (UT)        - time of the astronomical new moon
    4. Sunset Date               - date of the next sunset at/after the new moon
    5. Sunset Time (UT)          - time of that sunset
    6. First Sliver Date         - date exactly 18 hours after col. 2/3
    7. First Sliver Time (UT)    - time exactly 18 hours after col. 2/3
    8. JNM Observed Date         - date the first sliver would first be
                                    visible (same day as col. 6 if it falls
                                    before that day's sunset, otherwise the
                                    following day). Jewish New Moon!

Rules used to build the file (confirmed with the user):
    - If a new moon (or first sliver) moment falls exactly ON that day's
      sunset time, it is treated as being BEFORE sunset (i.e. same day).
    - Rows for which the required sunset data isn't available (new moon
      dates outside/too close to the edges of sunset_times.csv's date
      range) are skipped entirely, and a summary count is printed at the
      end.
    - Dates are written in ISO format (YYYY-MM-DD).
"""

import csv
import os
from datetime import datetime, timedelta, date, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_MOON_FILE = "./parsed/new_moon.csv"
SUNSET_FILE = "./parsed/sunset_times.csv"
OUTPUT_FILE = "./processed/jewish_new_moon_timings.csv"

DATE_OUT_FMT = "%Y-%m-%d"


def load_sunset_lookup(path):
    """Return dict: date -> datetime.time (sunset time, UT)."""
    lookup = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = row["Year"].strip()
            month = row["Month"].strip()
            day = row["Day"].strip()
            set_time = row["Set (UT)"].strip()
            if not (year and month and day and set_time):
                continue
            try:
                d = datetime.strptime(f"{year} {month} {day}", "%Y %b %d").date()
                t = datetime.strptime(set_time, "%H:%M").time()
            except ValueError:
                continue
            lookup[d] = t
    return lookup


def load_new_moons(path):
    """Return list of (date, time) tuples for each valid new moon row, in order."""
    moons = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row["New Moon Date"].strip()
            time_str = row["New Moon Time (UT)"].strip()
            if not date_str or not time_str:
                continue
            try:
                d = datetime.strptime(date_str, "%b %d %Y").date()
                t = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                continue
            moons.append((d, t))
    return moons


def find_next_sunset(nm_dt, sunset_lookup):
    """
    Given a new-moon datetime, find the date/time of the "next known sunset":
    - if the new moon occurs at/before that day's sunset, use that same day
    - otherwise, use the following day's sunset
    Returns (sunset_date, sunset_time) or (None, None) if data is missing.
    """
    nm_date = nm_dt.date()
    nm_time = nm_dt.time()

    same_day_sunset = sunset_lookup.get(nm_date)
    if same_day_sunset is not None and nm_time <= same_day_sunset:
        return nm_date, same_day_sunset

    next_date = nm_date + timedelta(days=1)
    next_day_sunset = sunset_lookup.get(next_date)
    if next_day_sunset is not None:
        return next_date, next_day_sunset

    return None, None


def find_observed_date(fs_dt, sunset_lookup):
    """
    Given the first-sliver datetime, determine the date it would first be
    observed: same day if before/at that day's sunset, else the next day.
    Returns a date, or None if data is missing.
    """
    fs_date = fs_dt.date()
    fs_time = fs_dt.time()

    sunset_that_day = sunset_lookup.get(fs_date)
    if sunset_that_day is None:
        return None

    if fs_time <= sunset_that_day:
        return fs_date
    return fs_date + timedelta(days=1)


def main():
    sunset_lookup = load_sunset_lookup(SUNSET_FILE)
    new_moons = load_new_moons(NEW_MOON_FILE)

    rows_out = []
    skipped = 0
    next_id = 1

    for nm_date, nm_time in new_moons:
        nm_dt = datetime.combine(nm_date, nm_time)

        sunset_date, sunset_time = find_next_sunset(nm_dt, sunset_lookup)
        if sunset_date is None:
            skipped += 1
            continue

        fs_dt = nm_dt + timedelta(hours=18)
        fs_date = fs_dt.date()
        fs_time = fs_dt.time()

        observed_date = find_observed_date(fs_dt, sunset_lookup)
        if observed_date is None:
            skipped += 1
            continue

        rows_out.append([
            next_id,
            nm_date.strftime(DATE_OUT_FMT),
            nm_time.strftime("%H:%M"),
            sunset_date.strftime(DATE_OUT_FMT),
            sunset_time.strftime("%H:%M"),
            fs_date.strftime(DATE_OUT_FMT),
            fs_time.strftime("%H:%M"),
            observed_date.strftime(DATE_OUT_FMT),
        ])
        next_id += 1

    header = [
        "ID",
        "New Moon Date",
        "New Moon Time (UT)",
        "Sunset Date",
        "Sunset Time (UT)",
        "First Sliver Date",
        "First Sliver Time (UT)",
        "JNM Observed Date",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows_out)

    print(f"Wrote {len(rows_out)} rows to {OUTPUT_FILE}")
    if skipped:
        print(f"Skipped {skipped} new moon row(s) due to missing sunset data "
              f"(outside sunset_times.csv's date range).")


if __name__ == "__main__":
    main()
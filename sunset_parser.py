#!/usr/bin/env python3
"""
Extract USNO "Table of Sunrise/Sunset, Moonrise/Moonset, or Twilight Times
for an Entire Year" data from a series of yearly HTML files and combine
them into a single CSV.

By default, looks for files named 2024.html, 2025.html, ... 2099.html in
the input directory (any files that don't exist are simply skipped), and
writes one combined CSV with a row per (year, month, day).

Usage:
    python3 extract_sun_times.py [--dir INPUT_DIR] [--start 2024] [--end 2099] [--out sun_times.csv]
"""

import os
import re
import csv
import argparse
from bs4 import BeautifulSoup

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# Each data line looks like:
# "01  0439 1446  0433 1513  0406 1537  ...  0421 1435"
#  ^^                 <- day, 2 chars (positions 0:2)
#    ^^^^^^^^^^^      <- 11-char block per month, repeated 12x, starting at position 2
# Within each 11-char block: 2 spaces, 4-char rise, 1 space, 4-char set
DAY_WIDTH = 2
BLOCK_WIDTH = 11
RISE_OFFSET = (2, 6)   # slice within a block
SET_OFFSET = (7, 11)   # slice within a block

DAY_LINE_RE = re.compile(r"^\d{2}\s")


def parse_header(text):
    """Pull Location, coordinates, body (Sun/Moon), and Year out of the header lines."""
    lines = text.split("\n")
    info = {"Location": "", "Longitude": "", "Latitude": "", "Body": "", "Year": ""}

    for line in lines[:10]:
        # Location name is the standalone all-caps token on the very top line,
        # e.g. "...  JERUSALEM  ... Astronomical Applications Dept."
        if "Astronomical Applications Dept." in line:
            tokens = [t for t in re.split(r"\s{2,}", line.strip()) if t]
            # Name is whichever token isn't the degree/comma markers or the dept label
            for tok in tokens:
                if tok not in ("o", ",") and "Astronomical" not in tok:
                    info["Location"] = tok

        m = re.search(r"Location:\s*([EW]\d+\s*\d+),\s*([NS]\d+\s*\d+)", line)
        if m:
            info["Longitude"], info["Latitude"] = m.group(1), m.group(2)

        m = re.search(r"Rise and Set for the (\w+) for (\d{4})", line)
        if m:
            info["Body"], info["Year"] = m.group(1), m.group(2)

    return info


def parse_pre_block(text):
    """Parse the fixed-width day/month rise-set grid from the <pre> block text."""
    header = parse_header(text)
    year = header["Year"]

    rows = []
    for line in text.split("\n"):
        if not DAY_LINE_RE.match(line):
            continue
        day = line[0:DAY_WIDTH].strip()
        if not day.isdigit():
            continue
        day = int(day)

        for month_idx in range(12):
            start = DAY_WIDTH + month_idx * BLOCK_WIDTH
            block = line[start:start + BLOCK_WIDTH]
            if len(block) < BLOCK_WIDTH:
                block = block.ljust(BLOCK_WIDTH)

            rise = block[RISE_OFFSET[0]:RISE_OFFSET[1]].strip()
            setv = block[SET_OFFSET[0]:SET_OFFSET[1]].strip()

            if not rise and not setv:
                # No such calendar day (e.g. Feb 30) or no data for this cell
                continue

            rise_fmt = f"{rise[:2]}:{rise[2:]}" if len(rise) == 4 else rise
            set_fmt = f"{setv[:2]}:{setv[2:]}" if len(setv) == 4 else setv

            rows.append({
                "Location": header["Location"],
                "Longitude": header["Longitude"],
                "Latitude": header["Latitude"],
                "Body": header["Body"],
                "Year": year,
                "Month": MONTH_NAMES[month_idx],
                "Day": day,
                "Rise (UT)": rise_fmt,
                "Set (UT)": set_fmt,
            })

    return rows


def extract_file(html_path):
    with open(html_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    # Some of these government pages use Windows-1252/Latin-1 punctuation
    # (curly quotes, etc.) that isn't valid UTF-8; re-read leniently if needed.
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError:
        with open(html_path, "r", encoding="latin-1") as f:
            raw = f.read()

    soup = BeautifulSoup(raw, "html.parser")
    pre = soup.find("pre")
    if pre is None:
        return []

    return parse_pre_block(pre.get_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="./raw/sunset", help="Directory containing the yearly HTML files")
    parser.add_argument("--start", type=int, default=2024, help="First year to look for")
    parser.add_argument("--end", type=int, default=2099, help="Last year to look for")
    parser.add_argument("--out", default="./parsed/sunset_times.csv", help="Output CSV path")
    args = parser.parse_args()

    all_rows = []
    found, missing = [], []

    for year in range(args.start, args.end + 1):
        filename = f"{year}.html"
        path = os.path.join(args.dir, filename)
        if not os.path.isfile(path):
            missing.append(filename)
            continue
        rows = extract_file(path)
        all_rows.extend(rows)
        found.append(filename)

    fieldnames = ["Location", "Longitude", "Latitude", "Body", "Year", "Month", "Day", "Rise (UT)", "Set (UT)"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Processed {len(found)} file(s): {', '.join(found) if found else '(none found)'}")
    if missing:
        print(f"Skipped {len(missing)} missing file(s) (e.g. {missing[0]}..{missing[-1]})")
    print(f"Extracted {len(all_rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()
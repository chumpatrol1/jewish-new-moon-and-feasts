#!/usr/bin/env python3
"""
Extract the "Phases of the Moon" table from an AstroPixels-style HTML page
(e.g. https://astropixels.com/ephemeris/phasescat/phases2001.html) and
write it out as a CSV file.

Usage:
    python3 extract_moon_phases.py input.html output.csv
"""

import sys
import csv
import re
import argparse
from bs4 import BeautifulSoup

# Eclipse-type letters that can trail a date/time entry, e.g. "Jun 21 11:58 T"
ECLIPSE_CODES = {"T", "A", "H", "P", "t", "p", "n"}

# Column boundaries (character offsets) within each fixed-width <pre> line.
# Determined from the source formatting:
#   Year          [0:8]
#   New Moon      [8:26]
#   First Quarter [26:44]
#   Full Moon     [44:62]
#   Last Quarter  [62:80]
COLUMNS = {
    "Year": (0, 8),
    "New Moon": (8, 26),
    "First Quarter": (26, 44),
    "Full Moon": (44, 62),
    "Last Quarter": (62, 80),
}

ENTRY_RE = re.compile(
    r"^(?P<date>[A-Za-z]{3}\s*\d{1,2})\s+(?P<time>\d{2}:\d{2})\s*(?P<code>[A-Za-z])?\s*$"
)


def parse_entry(cell_text):
    """Parse a single cell like 'Jan  2  22:31     ' -> (date_str, time_str, eclipse_code)."""
    cell_text = cell_text.strip()
    if not cell_text:
        return None
    m = ENTRY_RE.match(cell_text)
    if not m:
        return None
    date_str = re.sub(r"\s+", " ", m.group("date")).strip()
    time_str = m.group("time")
    code = m.group("code") or ""
    if code and code not in ECLIPSE_CODES:
        code = ""
    return date_str, time_str, code


def extract_rows(html_path):
    with open(html_path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    pre_blocks = soup.find_all("pre")

    rows = []
    current_year = None

    for pre in pre_blocks:
        text = pre.get_text()
        for raw_line in text.split("\n"):
            # Skip header/blank lines
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("Year") and "New Moon" in raw_line:
                continue

            # Pull out the fixed-width columns
            year_cell = raw_line[COLUMNS["Year"][0]:COLUMNS["Year"][1]].strip()
            if year_cell:
                current_year = year_cell

            if current_year is None:
                continue

            row = {"Year": current_year}
            any_data = False
            for phase in ("New Moon", "First Quarter", "Full Moon", "Last Quarter"):
                start, end = COLUMNS[phase]
                cell = raw_line[start:end]
                parsed = parse_entry(cell)
                if parsed:
                    date_str, time_str, code = parsed
                    row[f"{phase} Date"] = f"{date_str} {current_year}"
                    row[f"{phase} Time (UT)"] = time_str
                    row[f"{phase} Eclipse"] = code
                    any_data = True
                else:
                    row[f"{phase} Date"] = ""
                    row[f"{phase} Time (UT)"] = ""
                    row[f"{phase} Eclipse"] = ""

            if any_data:
                rows.append(row)

    return rows


def write_csv(rows, csv_path):
    fieldnames = ["Year"]
    for phase in ("New Moon", "First Quarter", "Full Moon", "Last Quarter"):
        fieldnames += [f"{phase} Date", f"{phase} Time (UT)", f"{phase} Eclipse"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    '''    
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_html", help="Path to the source HTML file")
    parser.add_argument("output_csv", help="Path to write the CSV file")
    args = parser.parse_args()
    '''

    rows = extract_rows("./raw/new_moon/20XX.html")
    write_csv(rows, "./parsed/new_moon.csv")
    print(f"Extracted {len(rows)} rows -> /parsed/new_moon.csv")


if __name__ == "__main__":
    main()

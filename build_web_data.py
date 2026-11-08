"""
build_web_data.py

Converts processed/jewish_new_moon_timings.csv into docs/data/new_moons.json
for the static web app in docs/. Re-run whenever the CSV is regenerated.
"""

import csv
import json
import os

INPUT_FILE = "./processed/jewish_new_moon_timings.csv"
OUTPUT_FILE = "./docs/data/new_moons.json"


def main():
    rows = []
    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append({
                "id": int(row["ID"]),
                "conjunction_utc": f"{row['New Moon Date']}T{row['New Moon Time (UT)']}",
                "sighting": row["JNM Observed Date"],
            })

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, separators=(",", ":"))

    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

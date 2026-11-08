# jewish new moon and feasts
 Calculates the timing of the Jewish New Moon and calculates the potential Feast Dates. Outputs results in an Excel Spreadsheet

## Web app

`docs/` contains a static web page. You pick a calendar year (2024–2099) and one of that
year's new moon sightings between Mar 1 and Apr 30 as the start of the year. The page then
lists every new moon and the Torah feast dates for that year.

- **Rebuild the data** after regenerating `processed/jewish_new_moon_timings.csv`:
  `python build_web_data.py` (writes `docs/data/new_moons.json`)
- **Preview locally**: `python -m http.server -d docs 8000`, then open http://localhost:8000.
  The page loads its data with `fetch`, so opening `index.html` directly from disk won't work.
- **Publish**: in the GitHub repo settings, go to Pages, choose "Deploy from a branch", and select `main` and `/docs`.

Rules used:
- The crescent is sighted on the evening of the CSV's observed date. Day 1 begins at that sunset, so its daylight date is the next day.
- Passover is 1/14 and Unleavened Bread is 1/15–1/21.
- The Wave Sheaf is the Sunday within Unleavened Bread. Pentecost is the 50th day counted from it, so it's always a Sunday.
- Trumpets is 7/1, Atonement is 7/10, Tabernacles is 7/15–7/21, and the Eighth Day is 7/22.
- The app flags a 13th month as **required** if the 13th sighting falls before Mar 1 of the next year. It flags it as **possible** if that sighting falls between Mar 1 and Apr 30.

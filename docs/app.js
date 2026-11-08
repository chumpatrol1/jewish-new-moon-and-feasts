"use strict";

// The CSV's "JNM Observed Date" is the evening the crescent is sighted. Day 1 begins at
// that sunset, so its daylight date is the following day.
const DAY1_OFFSET_DAYS = 1;

const DAY_MS = 86400000;
const START_WINDOW = { from: [3, 1], to: [4, 30] }; // [month, day]: Mar 1 to Apr 30

// ---------- date helpers (all dates are UTC midnight, so time zones never shift a day) ----------
function parseISODate(s) {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}
function addDays(date, n) { return new Date(date.getTime() + n * DAY_MS); }
function ymd(y, m, d) { return new Date(Date.UTC(y, m - 1, d)); }

const FMT_LONG = { timeZone: "UTC", weekday: "short", month: "short", day: "numeric", year: "numeric" };
const FMT_SHORT = { timeZone: "UTC", weekday: "short", month: "short", day: "numeric" };
function fmt(date, opts = FMT_LONG) { return date.toLocaleDateString("en-US", opts); }
function fmtRange(a, b) { return `${fmt(a, FMT_SHORT)} – ${fmt(b)}`; }
function fmtConjunction(s) {
  const [d, t] = s.split("T");
  return `${fmt(parseISODate(d), FMT_SHORT)}, ${t}`;
}

// ---------- calendar logic ----------
function loadMoons(raw) {
  return raw.map(r => ({ ...r, day1: addDays(parseISODate(r.sighting), DAY1_OFFSET_DAYS) }));
}

/** Indexes into moons[] whose day 1 falls in Mar 1 to Apr 30 of `year`. */
function candidates(moons, year) {
  const lo = ymd(year, ...START_WINDOW.from), hi = ymd(year, ...START_WINDOW.to);
  const out = [];
  moons.forEach((m, i) => { if (m.day1 >= lo && m.day1 <= hi) out.push(i); });
  return out;
}

/**
 * Months of the year that starts at moons[startIdx].
 * Returns { months: [...up to 12], month13: {moon, status} | null, dataEnds: bool }.
 * The 13th month is "required" if its sighting falls before Mar 1 of the next year,
 * and "possible" if it falls inside next year's Mar 1 to Apr 30 window.
 */
function buildYear(moons, startIdx) {
  const months = moons.slice(startIdx, startIdx + 12);
  const year = moons[startIdx].day1.getUTCFullYear();
  let month13 = null;
  const next = moons[startIdx + 12];
  if (next) {
    const lo = ymd(year + 1, ...START_WINDOW.from), hi = ymd(year + 1, ...START_WINDOW.to);
    if (next.day1 < lo) month13 = { moon: next, status: "required" };
    else if (next.day1 <= hi) month13 = { moon: next, status: "possible" };
  }
  return { months, month13, dataEnds: !next };
}

/** Gregorian daylight date of biblical month m (1-based), day d, or null if no data. */
function bibDate(months, m, d) {
  const mo = months[m - 1];
  return mo ? addDays(mo.day1, d - 1) : null;
}

/** Biblical "m/d" label for a Gregorian date, using the month starts. */
function bibLabel(months, date) {
  for (let i = months.length - 1; i >= 0; i--) {
    if (date >= months[i].day1) {
      return `${i + 1}/${Math.round((date - months[i].day1) / DAY_MS) + 1}`;
    }
  }
  return "";
}

function feasts(months) {
  const list = [];
  const add = (name, start, end, high, bib) => { if (start) list.push({ name, start, end, high, bib }); };

  const passover = bibDate(months, 1, 14);
  add("Passover", passover, null, false, "1/14");

  const ulb1 = bibDate(months, 1, 15), ulb7 = bibDate(months, 1, 21);
  add("Feast of Unleavened Bread", ulb1, ulb7, false, "1/15 – 1/21");
  add("First Day of Unleavened Bread", ulb1, null, true, "1/15");
  add("Last Day of Unleavened Bread", ulb7, null, true, "1/21");

  if (ulb1) {
    // The single Sunday that falls within 1/15 to 1/21.
    let waveSheaf = null;
    for (let d = 0; d < 7; d++) {
      const day = addDays(ulb1, d);
      if (day.getUTCDay() === 0) { waveSheaf = day; break; }
    }
    add("Wave Sheaf (Firstfruits)", waveSheaf, null, false, bibLabel(months, waveSheaf));
    const pentecost = addDays(waveSheaf, 49);
    add("Pentecost (Shavuot)", pentecost, null, true, bibLabel(months, pentecost));
  }

  add("Trumpets", bibDate(months, 7, 1), null, true, "7/1");
  add("Day of Atonement", bibDate(months, 7, 10), null, true, "7/10");
  add("Feast of Tabernacles", bibDate(months, 7, 15), bibDate(months, 7, 21), false, "7/15 – 7/21");
  add("First Day of Tabernacles", bibDate(months, 7, 15), null, true, "7/15");
  add("Eighth Day (Last Great Day)", bibDate(months, 7, 22), null, true, "7/22");
  return list;
}

// ---------- UI ----------
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v; else node.setAttribute(k, v);
  }
  for (const c of children) if (c != null) node.append(c);
  return node;
}
function tag(text, cls) { return el("span", { class: `tag ${cls}` }, text); }

function storageGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function storageSet(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } }

function initUI(moons) {
  const yearSel = document.getElementById("year");
  const optsBox = document.getElementById("start-options");
  const message = document.getElementById("message");
  const feastsCard = document.getElementById("feasts-card");
  const monthsCard = document.getElementById("months-card");

  const firstYear = moons[0].day1.getUTCFullYear();
  const lastYear = moons[moons.length - 1].day1.getUTCFullYear();
  for (let y = firstYear; y <= lastYear; y++) yearSel.append(el("option", { value: y }, String(y)));

  const thisYear = new Date().getFullYear();
  const saved = Number(storageGet("nmf-year"));
  yearSel.value = String(saved >= firstYear && saved <= lastYear ? saved
    : Math.min(Math.max(thisYear, firstYear), lastYear));

  function showMessage(text) {
    message.textContent = text;
    message.hidden = !text;
  }

  function renderStarts() {
    const year = Number(yearSel.value);
    storageSet("nmf-year", year);
    optsBox.replaceChildren();
    const idxs = candidates(moons, year);
    if (!idxs.length) {
      showMessage(`No new moon sightings fall between Mar 1 and Apr 30, ${year} in the data.`);
      feastsCard.hidden = monthsCard.hidden = true;
      return;
    }
    idxs.forEach((idx, n) => {
      const m = moons[idx];
      const input = el("input", { type: "radio", name: "start", value: idx });
      if (n === 0) input.checked = true;
      input.addEventListener("change", () => renderYear(idx));
      optsBox.append(el("label", { class: "start-option" }, input,
        el("span", {}, `Begins at sunset ${fmt(addDays(m.day1, -1))}`,
          el("small", {}, `Day 1: ${fmt(m.day1)}`))));
    });
    renderYear(idxs[0]);
  }

  function renderYear(startIdx) {
    const { months, month13, dataEnds } = buildYear(moons, startIdx);
    showMessage(dataEnds ? "The data ends before this year does, so some months or feasts are missing." : "");

    const ftbody = document.getElementById("feasts");
    ftbody.replaceChildren(...feasts(months).map(f => el("tr", {},
      el("td", { class: "name" }, f.name, f.high ? tag("High day", "high") : null),
      el("td", {}, f.bib),
      el("td", {}, fmt(addDays(f.start, -1))),
      el("td", {}, f.end ? fmtRange(f.start, f.end) : fmt(f.start)))));
    feastsCard.hidden = false;

    const mtbody = document.getElementById("months");
    const rows = months.map((m, i) => el("tr", {},
      el("td", {}, String(i + 1)),
      el("td", {}, fmt(addDays(m.day1, -1))),
      el("td", {}, fmt(m.day1)),
      el("td", {}, fmtConjunction(m.conjunction_utc))));
    const note = document.getElementById("month13-note");
    if (month13) {
      const m = month13.moon;
      rows.push(el("tr", { class: "month13" },
        el("td", {}, "13", tag(month13.status === "required" ? "Required" : "Possible", "flag")),
        el("td", {}, fmt(addDays(m.day1, -1))),
        el("td", {}, fmt(m.day1)),
        el("td", {}, fmtConjunction(m.conjunction_utc))));
      note.textContent = month13.status === "required"
        ? "A 13th month is required: this sighting falls before Mar 1, so the next year can't start yet."
        : "A 13th month is possible: this sighting falls between Mar 1 and Apr 30, so it could be month 13 or month 1 of next year.";
      note.hidden = false;
    } else {
      note.hidden = true;
    }
    mtbody.replaceChildren(...rows);
    monthsCard.hidden = false;
  }

  yearSel.addEventListener("change", renderStarts);
  renderStarts();
}

if (typeof module !== "undefined" && module.exports) {
  // Lets Node load the calendar logic for testing.
  module.exports = { loadMoons, candidates, buildYear, bibDate, feasts };
} else {
  fetch("data/new_moons.json")
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(raw => initUI(loadMoons(raw)))
    .catch(err => {
      const m = document.getElementById("message");
      m.textContent = `Couldn't load data/new_moons.json (${err.message}). Serve the docs/ folder over HTTP.`;
      m.hidden = false;
    });
}

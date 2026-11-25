"""CAMS-BD workbook parsing.

The four CAMS-BD workbooks do not share a schema. Known problems handled here
(each one is counted in the returned audit so the data-quality report can show it):

* 2012-2021: one sheet of stacked station blocks. Every block has its own header
  row and unit row. The Savar block's header swaps "Solar Rad" and "BP", so the
  columns are mapped per block from that block's own header, not the sheet header.
* 2012-2021: dates were originally dd/mm/yyyy text. Excel converted those with
  day <= 12 into serial dates with day and month swapped and left the rest as
  text. Some ranges are correct serials, some carry the hour as a fraction.
  We decode each row into candidate timestamps and pick the one that continues
  the station's hourly sequence (see ``_decode_sequence``).
* 2012-2021: the Khulna, Rajshahi and Sangsad blocks contain no dates at all,
  only an hour-of-day. Their timestamps cannot be verified, so those blocks are
  excluded rather than reconstructed from row position.
* 2022-2024: a single "Date & Time" column, PM10/PM2.5 column order differs by
  year, and some stations' meteorology columns are shifted (handled later by
  physical-range validation in ``cleaning.py``).

Timestamps: the source uses hour-ending labels 01:00..24:00 in Bangladesh local
time. ``ts`` is the end of the averaging hour as naive Asia/Dhaka time (UTC+6,
no DST); 24:00 becomes 00:00 of the next day.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

CANONICAL = ["so2", "no", "no2", "nox", "co", "o3", "pm25", "pm10",
             "ws", "wd", "temp", "rh", "sr", "bp", "rain", "vws"]

# Source header label (lower-cased, stripped) -> canonical column.
HEADER_MAP = {
    "so2": "so2", "no": "no", "no2": "no2", "nox": "nox", "co": "co", "o3": "o3",
    "pm2.5": "pm25", "pm10": "pm10",
    "wind speed": "ws", "ws": "ws", "wind dir": "wd", "wd": "wd",
    "temperature": "temp", "temp": "temp", "rh": "rh",
    "solar rad": "sr", "sr": "sr", "bp": "bp", "rain": "rain",
    "v wind speed": "vws", "vws": "vws",
}

# Expected unit per canonical column; anything else is reported, not converted.
EXPECTED_UNITS = {
    "so2": {"ppb"}, "no": {"ppb"}, "no2": {"ppb"}, "nox": {"ppb"}, "co": {"ppm"},
    "o3": {"ppb"}, "pm25": {"ug/m3"}, "pm10": {"ug/m3"}, "ws": {"m/s"},
    "wd": {"deg", "degre-----", "degree----"}, "temp": {"c°", "degreec"},
    "rh": {"%"}, "sr": {"w/m2"}, "bp": {"mb", "hpa"}, "rain": {"mm", "m m"},
    "vws": {"m/s"},
}

# Raw station label -> (station_id, display name). CDA is taken to be the
# Agrabad (Chattogram) site; this is an assumption recorded in the data card.
STATION_MAP = {
    "agrabad chittagong": "ctg_agrabad", "cda": "ctg_agrabad",
    "tv st-chittagong": "ctg_tv", "tv center": "ctg_tv", "tv sation": "ctg_tv",
    "barc": "dhk_barc", "darussalam": "dhk_darussalam", "sangsad": "dhk_sangsad",
    "doe": "dhk_doe", "gazipur": "gazipur", "narayonganj": "narayanganj",
    "narayangonj": "narayanganj", "narayanganj": "narayanganj",
    "savar": "savar", "narsingdi": "narsingdi", "mymensingh": "mymensingh",
    "mymensing": "mymensingh", "cumilla": "cumilla", "rajshahi": "rajshahi",
    "khulna": "khulna", "barishal": "barishal", "sylhet": "sylhet",
    "rangpur": "rangpur",
}

EXCEL_EPOCH = pd.Timestamp("1899-12-30")
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})(?::\d{2})?\s*([AP]M)?\s*$", re.I)


@dataclass
class Audit:
    rows_in: int = 0
    rows_out: int = 0
    dropped: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    unit_issues: List[dict] = field(default_factory=list)
    date_fixes: Dict[str, int] = field(default_factory=dict)

    def drop(self, reason: str, n: int) -> None:
        if n:
            self.dropped[reason] = self.dropped.get(reason, 0) + int(n)

    def to_dict(self) -> dict:
        return {"rows_in": self.rows_in, "rows_out": self.rows_out,
                "dropped": self.dropped, "notes": self.notes,
                "unit_issues": self.unit_issues, "date_fixes": self.date_fixes}


def station_id(raw: str) -> Optional[str]:
    return STATION_MAP.get(str(raw).strip().lower())


def parse_hour(x) -> Optional[int]:
    """Hour-ending label -> 1..24. Accepts '01:00', '24:00:00 PM', 8, time objects."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    if isinstance(x, dt.time):
        return x.hour or 24
    if isinstance(x, (int, np.integer)) or (isinstance(x, float) and x == int(x)):
        h = int(x)
        return h if 0 <= h <= 24 else None
    m = _TIME_RE.search(str(x))
    if not m:
        return None
    h = int(m.group(1))
    ampm = (m.group(3) or "").upper()
    if h != 24 and ampm == "PM" and h < 12:
        h += 12
    elif ampm == "AM" and h == 12:
        h = 0
    if h == 0:
        h = 24
    return h if 1 <= h <= 24 else None


def _swap(d: pd.Timestamp) -> Optional[pd.Timestamp]:
    if d.day > 12 or d.day == d.month:
        return None
    try:
        return d.replace(month=d.day, day=d.month)
    except ValueError:
        return None


def date_candidates(x, hour: Optional[int]) -> List[pd.Timestamp]:
    """All plausible end-of-hour timestamps for one 2012-2021 row, as-is reading first."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return []
    if isinstance(x, (int, float, np.integer, np.floating)):
        # Round to the hour first: float error turns 00:00 into 23:59:59.99.
        serial = round(float(x) * 24) / 24
        day = EXCEL_EPOCH + pd.Timedelta(days=int(np.floor(serial)))
        h_frac = int(round((serial - np.floor(serial)) * 24))
        if hour is None:
            if h_frac == 0:
                # A bare midnight serial is 24:00 of the previous day.
                return [day]
            hour = h_frac
        serial_ts = day + pd.Timedelta(hours=h_frac)
        out = []
        if h_frac == 0 and hour == 24:
            # Midnight serial labelled 24:00 is that same instant.
            out.append(serial_ts)
        bases = [day] + ([s] if (s := _swap(day)) is not None else [])
        out += [b + pd.Timedelta(hours=hour) for b in bases]
        if h_frac:
            # Some ranges store the full timestamp, or timestamp - 1h, in the serial.
            out += [serial_ts, serial_ts + pd.Timedelta(hours=1)]
        return list(dict.fromkeys(out))
    if isinstance(x, (dt.datetime, pd.Timestamp)):
        d = pd.Timestamp(x)
        if hour is None:
            return [d]
        return [d.normalize() + pd.Timedelta(hours=hour)]
    s = str(x).strip()
    out = []
    for fmt in ("%d/%m/%Y", "%m/%d/%Y"):
        try:
            d = pd.to_datetime(s, format=fmt)
        except (ValueError, TypeError):
            continue
        if hour is not None:
            d = d + pd.Timedelta(hours=hour)
        if d not in out:
            out.append(d)
    return out


def _decode_sequence(cands: List[List[pd.Timestamp]], audit: Audit, max_gap_days: int = 400):
    """Choose one timestamp per row so the station series runs forward hourly.

    Preference order: the candidate equal to previous+1h; else the earliest
    candidate after the previous timestamp within ``max_gap_days``. Rows with no
    candidate that moves forward are dropped (counted as out-of-sequence).
    """
    one_h = pd.Timedelta(hours=1)
    max_gap = pd.Timedelta(days=max_gap_days)
    chosen: List[Optional[pd.Timestamp]] = []
    prev: Optional[pd.Timestamp] = None
    for c in cands:
        if not c:
            chosen.append(None)
            continue
        if prev is None:
            pick = c[0]
        elif prev + one_h in c:
            pick = prev + one_h
        else:
            fwd = [t for t in c if prev < t <= prev + max_gap]
            if not fwd:
                audit.date_fixes["out_of_sequence_dropped"] = audit.date_fixes.get("out_of_sequence_dropped", 0) + 1
                chosen.append(None)
                continue
            pick = min(fwd)
            audit.date_fixes["sequence_gaps"] = audit.date_fixes.get("sequence_gaps", 0) + 1
        if pick != c[0]:
            audit.date_fixes["day_month_swapped"] = audit.date_fixes.get("day_month_swapped", 0) + 1
        chosen.append(pick)
        prev = pick
    return chosen


def _check_units(station: str, header: List[str], units: List, audit: Audit, source: str) -> None:
    for h, u in zip(header, units):
        col = HEADER_MAP.get(str(h).strip().lower())
        if col is None or u is None or (isinstance(u, float) and np.isnan(u)):
            continue
        u_norm = str(u).strip().lower()
        if u_norm not in EXPECTED_UNITS[col]:
            audit.unit_issues.append({"source": source, "station": station, "column": col, "unit": str(u).strip()})


def parse_2012_2021(path: Path, audit: Optional[Audit] = None) -> pd.DataFrame:
    audit = audit or Audit()
    raw = pd.read_excel(path, header=None, dtype=object) if not isinstance(path, pd.DataFrame) else path
    audit.rows_in += len(raw) - 1
    # A block header is any row whose Time cell reads "Time".
    hdr_rows = raw.index[raw[2].astype(str).str.strip() == "Time"].tolist()
    if not hdr_rows or hdr_rows[0] != 0:
        hdr_rows = [0] + hdr_rows
    bounds = list(zip(hdr_rows, hdr_rows[1:] + [len(raw)]))
    frames = []
    for start, end in bounds:
        header = [str(v).strip() if v is not None else "" for v in raw.iloc[start]]
        block = raw.iloc[start + 1:end]
        units_mask = block[3].astype(str).str.strip().str.lower() == "ppb"
        locs = block[0].dropna().unique()
        # The sheet's first header row also heads the first station's block.
        for loc in locs:
            g = block[block[0] == loc]
            sid = station_id(loc)
            urows = g[units_mask.reindex(g.index, fill_value=False)]
            if len(urows):
                _check_units(sid, header, urows.iloc[0].tolist(), audit, "2012-2021")
            g = g[~units_mask.reindex(g.index, fill_value=False)]
            if sid is None:
                audit.drop("unknown_station", len(g))
                continue
            has_date = g[1].notna() & (g[1].astype(str).str.strip() != "")
            if not has_date.any():
                audit.drop(f"no_date_column_{sid}", len(g))
                audit.notes.append(f"2012-2021 {loc}: block has no dates ({len(g)} rows); excluded, not reconstructed.")
                continue
            hours = [parse_hour(x) for x in g[2]]
            cands = [date_candidates(d, h) for d, h in zip(g[1], hours)]
            ts = _decode_sequence(cands, audit)
            out = pd.DataFrame({"station_id": sid, "ts": ts}, index=g.index)
            for j, h in enumerate(header):
                col = HEADER_MAP.get(h.lower())
                if col:
                    out[col] = pd.to_numeric(g[j], errors="coerce")
            n_bad = out["ts"].isna().sum()
            audit.drop("unparseable_timestamp", n_bad)
            frames.append(out.dropna(subset=["ts"]))
    df = pd.concat(frames, ignore_index=True)
    df["source_file"] = "2012-2021"
    return df


def parse_annual(path, year_label: str, audit: Optional[Audit] = None) -> pd.DataFrame:
    """2022, 2023 and 2024 workbooks: one 'Date & Time' column, header in row 0."""
    audit = audit or Audit()
    raw = pd.read_excel(path, header=None, dtype=object) if not isinstance(path, pd.DataFrame) else path
    header = [str(v).strip() if v is not None else "" for v in raw.iloc[0]]
    body = raw.iloc[1:]
    audit.rows_in += len(body)
    units_mask = body[2].astype(str).str.strip().str.lower() == "ppb"
    for loc, u in body[units_mask].groupby(0):
        _check_units(station_id(loc), header, u.iloc[0].tolist(), audit, year_label)
    body = body[~units_mask]
    audit.drop("unit_rows", int(units_mask.sum()))
    ts = pd.to_datetime(body[1], errors="coerce")
    sids = body[0].map(station_id)
    out = pd.DataFrame({"station_id": sids, "ts": ts})
    for j, h in enumerate(header):
        col = HEADER_MAP.get(h.lower())
        if col:
            out[col] = pd.to_numeric(body[j], errors="coerce")
    audit.drop("unknown_station", int(out["station_id"].isna().sum()))
    out = out.dropna(subset=["station_id"])
    bad = out["ts"].isna()
    audit.drop("unparseable_timestamp", int(bad.sum()))
    out = out[~bad].copy()
    # Snap to the hour; sub-hour stamps are reported rather than silently kept.
    off = out["ts"] != out["ts"].dt.round("h")
    audit.drop("non_hourly_timestamp", int(off.sum()))
    out = out[~off]
    out["source_file"] = year_label
    return out.reset_index(drop=True)


def parse_all(raw_dir: Path) -> tuple[pd.DataFrame, Audit]:
    raw_dir = Path(raw_dir)
    audit = Audit()
    parts = [parse_2012_2021(raw_dir / "Bangladesh_CAMS_AirQuality_Meteorology_2012-2021.xlsx", audit)]
    for y in ("2022", "2023", "2024"):
        parts.append(parse_annual(raw_dir / f"Bangladesh_CAMS_AirQuality_Meteorology_{y}.xlsx", y, audit))
    df = pd.concat(parts, ignore_index=True)
    for c in CANONICAL:
        if c not in df:
            df[c] = np.nan
    return df[["station_id", "ts", *CANONICAL, "source_file"]], audit

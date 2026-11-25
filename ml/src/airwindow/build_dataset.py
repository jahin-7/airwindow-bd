"""Build the processed CAMS-BD dataset and its data-quality report.

    python -m airwindow.build_dataset --raw data/raw/CAMS-BD --out data/processed [--weather]

Outputs:
    cams_bd_hourly.parquet   cleaned station-hour table on a complete hourly grid
    era5_station_weather.parquet  (with --weather) Open-Meteo ERA5 per station-hour
    data_quality.json / DATA_QUALITY.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .cleaning import clean, to_hourly_grid
from .parsing import CANONICAL, parse_all
from .stations import STATIONS


def quality_markdown(q: dict) -> str:
    L = ["# CAMS-BD data-quality report", "",
         f"Source rows read: **{q['parse']['rows_in']:,}** · station-hours kept: **{q['rows_clean']:,}** · "
         f"with PM2.5: **{q['pm25_nonnull']:,}** · with PM10: **{q['pm10_nonnull']:,}**", "",
         "## Rows dropped while parsing", "", "| Reason | Rows |", "|---|---:|"]
    L += [f"| {k} | {v:,} |" for k, v in q["parse"]["dropped"].items()]
    L += ["", "## Timestamp repairs (2012-2021 workbook)", "", "| Repair | Rows |", "|---|---:|"]
    L += [f"| {k} | {v:,} |" for k, v in q["parse"]["date_fixes"].items()]
    L += ["", "## Station coverage", "", "| Station | First | Last | Hours on grid | PM2.5 present | PM10 present |",
          "|---|---|---|---:|---:|---:|"]
    for s in q["coverage"]:
        L.append(f"| {s['station_id']} | {s['first']} | {s['last']} | {s['hours']:,} | "
                 f"{s['pm25_frac']:.0%} | {s['pm10_frac']:.0%} |")
    L += ["", "## Values nulled by physical-range checks", "", "| Column | Values |", "|---|---:|"]
    L += [f"| {k} | {v:,} |" for k, v in q["clean"]["range_nulled"].items()]
    L += ["", f"Stuck-sensor PM values nulled (≥6 identical consecutive hours): "
          f"PM2.5 {q['clean']['stuck_nulled']['pm25']:,}, PM10 {q['clean']['stuck_nulled']['pm10']:,}.", "",
          "## Station-year columns quarantined (>20% of values physically impossible)", "",
          "| Station | Year | Column | Bad fraction | Values nulled |", "|---|---:|---|---:|---:|"]
    L += [f"| {r['station_id']} | {r['year']} | {r['column']} | {r['bad_frac']:.0%} | {r['n_nulled']:,} |"
          for r in q["clean"]["quarantined"]]
    L += ["", f"Duplicates on (station, hour): {json.dumps(q['clean']['duplicates'])}", "",
          f"PM2.5 > PM10 (physically inconsistent, kept but flagged): {q['pm25_gt_pm10']:,} station-hours.", "",
          "## Unit labels that differ from the expected unit", "", "| Source | Station | Column | Unit as written |",
          "|---|---|---|---|"]
    L += [f"| {u['source']} | {u['station']} | {u['column']} | {u['unit']} |" for u in q["unit_issues"]]
    L += ["", "## Notes", ""] + [f"- {n}" for n in q["parse"]["notes"]]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("data/raw/CAMS-BD"))
    ap.add_argument("--out", type=Path, default=Path("data/processed"))
    ap.add_argument("--weather", action="store_true", help="also download ERA5 weather from Open-Meteo")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    raw, audit = parse_all(a.raw)
    df, rep = clean(raw)
    grid = to_hourly_grid(df)
    grid = grid[["station_id", "ts", *CANONICAL, "source_file"]]
    grid.to_parquet(a.out / "cams_bd_hourly.parquet", index=False)

    cov = []
    for sid, g in grid.groupby("station_id"):
        cov.append({"station_id": sid, "first": str(g.ts.min()), "last": str(g.ts.max()), "hours": len(g),
                    "pm25_frac": float(g.pm25.notna().mean()), "pm10_frac": float(g.pm10.notna().mean())})
    uniq_units = {(u["source"], u["station"], u["column"], u["unit"]): u for u in audit.unit_issues}
    q = {"parse": {**audit.to_dict(), "unit_issues": None}, "clean": rep, "coverage": cov,
         "rows_clean": int(len(df)), "grid_rows": int(len(grid)),
         "pm25_nonnull": int(df.pm25.notna().sum()), "pm10_nonnull": int(df.pm10.notna().sum()),
         "pm25_gt_pm10": int((df.pm25 > df.pm10).sum()), "unit_issues": list(uniq_units.values()),
         "timezone": "Asia/Dhaka (UTC+6), naive; ts = end of averaging hour",
         "stations": STATIONS}
    (a.out / "data_quality.json").write_text(json.dumps(q, indent=1, default=str))
    (a.out / "DATA_QUALITY.md").write_text(quality_markdown(q))
    print(f"wrote {len(grid):,} grid rows; PM2.5 present {q['pm25_nonnull']:,}")

    if a.weather:
        fetch_station_weather(grid, a.out)


def fetch_station_weather(grid: pd.DataFrame, out: Path, pause_s: float = 20.0) -> None:
    """ERA5 per station, cached one file per station (Open-Meteo rate-limits long ranges)."""
    import time
    from .weather import fetch_archive
    cache = out / "weather_cache"
    cache.mkdir(exist_ok=True)
    frames = []
    for sid, g in grid.groupby("station_id"):
        f = cache / f"{sid}.parquet"
        if not f.exists():
            st = STATIONS[sid]
            w = fetch_archive(st["lat"], st["lon"], str(g.ts.min().date()), str(g.ts.max().date()))
            w.insert(0, "station_id", sid)
            w.to_parquet(f, index=False)
            print("weather", sid, len(w), flush=True)
            time.sleep(pause_s)
        frames.append(pd.read_parquet(f))
    pd.concat(frames, ignore_index=True).to_parquet(out / "era5_station_weather.parquet", index=False)

if __name__ == "__main__":
    main()

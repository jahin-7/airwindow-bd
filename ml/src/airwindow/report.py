"""Render results tables from saved metrics so no number is typed by hand.

    python -m airwindow.report --art ml/artifacts > docs/RESULTS.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NAMES = {
    "persistence": "Persistence (last value)",
    "seasonal_naive_24h": "Seasonal naive (same hour yesterday)",
    "lightgbm_now_weather": "LightGBM, weather at issue time",
    "lightgbm_tgt_weather": "LightGBM, + target-hour weather (ERA5 proxy)",
    "gru_now_weather": "GRU, weather at issue time",
    "gru_tgt_weather": "GRU, + target-hour weather (ERA5 proxy)",
}
POL = {"pm25": "PM2.5", "pm10": "PM10"}


def _f(x, d=1):
    return "–" if x is None else f"{x:.{d}f}"


def tables(m: dict) -> str:
    rows = m["overall"] + m.get("gru", [])
    serving = m.get("serving", {})
    out = []
    for pol in ("pm25", "pm10"):
        out += [f"### {POL[pol]} — test year 2024 (never used for training or model choice)", "",
                "| Model | +1 h MAE | +3 h MAE | +6 h MAE | +6 h RMSE | +6 h R² | +6 h skill vs persistence | 80% interval coverage (+1/+3/+6 h) |",
                "|---|---:|---:|---:|---:|---:|---:|---|"]
        for key, name in NAMES.items():
            r = {x["horizon"]: x for x in rows if x["pollutant"] == pol and x["model"] == key}
            if not r:
                continue
            cov = " / ".join(_f(r[h].get("interval80_coverage"), 2) for h in (1, 3, 6)) if "interval80_coverage" in r[1] else "–"
            served = " **(served)**" if key == f"lightgbm_{serving.get(pol, '')}" else ""
            out.append(f"| {name}{served} | {_f(r[1]['mae'])} | {_f(r[3]['mae'])} | {_f(r[6]['mae'])} | "
                       f"{_f(r[6]['rmse'])} | {_f(r[6]['r2'], 3)} | {_f(100 * r[6].get('skill_vs_persistence', 0), 0)}% | {cov} |")
        n = next((x["n"] for x in rows if x["pollutant"] == pol and x["model"] == "persistence" and x["horizon"] == 6), None)
        out += ["", f"MAE/RMSE in µg/m³. n = {n:,} station-hours at +6 h." if n else "", ""]
    if m.get("leave_station_out"):
        out += ["### Unseen-station test (station left out of training, scored on its 2024 data)", "",
                "| Held-out station | Pollutant | +1 h MAE | +3 h MAE | +6 h MAE | +6 h skill vs persistence |",
                "|---|---|---:|---:|---:|---:|"]
        lo = m["leave_station_out"]
        for sid in dict.fromkeys(r["held_out_station"] for r in lo):
            for pol in ("pm25", "pm10"):
                r = {x["horizon"]: x for x in lo if x["held_out_station"] == sid and x["pollutant"] == pol}
                if r:
                    out.append(f"| {sid} | {POL[pol]} | {_f(r[1]['mae'])} | {_f(r[3]['mae'])} | {_f(r[6]['mae'])} | "
                               f"{_f(100 * r[6]['skill_vs_persistence'], 0)}% |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", type=Path, default=Path("ml/artifacts"))
    a = ap.parse_args()
    m = json.loads((a.art / "metrics.json").read_text())
    sv = a.art / "serving.json"
    if sv.exists():
        m["serving"] = json.loads(sv.read_text())
    print(tables(m))


if __name__ == "__main__":
    main()

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
    "gru_now_weather": "GRU (Kaggle T4), weather at issue time",
    "gru_tgt_weather": "GRU (Kaggle T4), + target-hour weather (ERA5 proxy)",
}
POL = {"pm25": "PM2.5", "pm10": "PM10"}


def _f(x, d=1):
    return "–" if x is None else f"{x:.{d}f}"


def headline(m: dict) -> str:
    serving = m.get("serving", {})
    out = []
    for pol in ("pm25", "pm10"):
        key = f"lightgbm_{serving.get(pol, 'now_weather')}"
        r = {x["horizon"]: x for x in m["overall"] if x["pollutant"] == pol and x["model"] == key}
        p = {x["horizon"]: x for x in m["overall"] if x["pollutant"] == pol and x["model"] == "persistence"}
        out.append(f"- **{POL[pol]}, served model:** 6-hour-ahead error (MAE) **{r[6]['mae']:.1f} µg/m³** vs "
                   f"{p[6]['mae']:.1f} for \"no change\" ({100 * r[6]['skill_vs_persistence']:.0f}% lower); "
                   f"3 h: {r[3]['mae']:.1f} vs {p[3]['mae']:.1f}; 1 h: {r[1]['mae']:.1f} vs {p[1]['mae']:.1f}. "
                   f"80% ranges contained the true value {100 * r[6]['interval80_coverage']:.0f}% of the time at 6 h.")
    return "\n".join(out)


def validation_table(rows: list) -> str:
    out = ["### Variant choice (validation year 2023 only)", "",
           "| Pollutant | Variant | +1 h MAE | +3 h MAE | +6 h MAE |", "|---|---|---:|---:|---:|"]
    for pol in ("pm25", "pm10"):
        for v in ("now_weather", "tgt_weather"):
            r = {x["horizon"]: x["mae"] for x in rows if x["pollutant"] == pol and x["variant"] == v}
            out.append(f"| {POL[pol]} | {v} | {r[1]:.1f} | {r[3]:.1f} | {r[6]:.1f} |")
    return "\n".join(out) + "\n"


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
    rep = m.get("gru_replication_apple_m4")
    if rep:
        t4 = {(x["pollutant"], x["horizon"], x["model"]): x["mae"] for x in m["gru"]}
        out += ["### GRU replication (same code and test rows, different hardware)", "",
                "| Model | Pollutant | Kaggle T4 MAE +1/+3/+6 h | Apple M4 MAE +1/+3/+6 h |", "|---|---|---|---|"]
        for key in ("gru_now_weather", "gru_tgt_weather"):
            for pol in ("pm25", "pm10"):
                a = " / ".join(_f(t4[(pol, h, key)]) for h in (1, 3, 6))
                b = " / ".join(_f(next(x["mae"] for x in rep if x["pollutant"] == pol and x["horizon"] == h and x["model"] == key)) for h in (1, 3, 6))
                out.append(f"| {key} | {POL[pol]} | {a} | {b} |")
        out.append("")
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
    print(headline(m) + "\n\n" + tables(m))
    vm = a.art / "validation_metrics.json"
    if vm.exists():
        print(validation_table(json.loads(vm.read_text())))


if __name__ == "__main__":
    main()

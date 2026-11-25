"""Pick which model variant the API serves, per pollutant, using the VALIDATION split only.

    python -m airwindow.select_serving --data data/kaggle_upload --art ml/artifacts

Writes ``serving.json`` (read by services/api) and ``validation_metrics.json``.
The 2024 test split is never looked at here, so test results stay an unbiased
estimate of the served model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from . import train as T
from .features import HORIZONS, POLLUTANTS, build_all


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data/kaggle_upload"))
    ap.add_argument("--art", type=Path, default=Path("ml/artifacts"))
    a = ap.parse_args()
    hourly = pd.read_parquet(a.data / "cams_bd_hourly.parquet", columns=["station_id", "ts", "pm25", "pm10"])
    weather = pd.read_parquet(a.data / "era5_station_weather.parquet")
    for d in (hourly, weather):
        d["station_id"] = d["station_id"].astype(str)
    val = T.split(build_all(hourly, weather))["val"]
    rows, serving = [], {}
    for pol in POLLUTANTS:
        va = T.usable(val, pol)
        mae = {}
        for v in ("now_weather", "tgt_weather"):
            m = lgb.Booster(model_file=str(a.art / f"lgb_{pol}_{v}.txt"))
            p = np.clip(np.expm1(m.predict(va[m.feature_name()])), 0, None)
            err = np.abs(p - va[f"y_{pol}"].values)
            mae[v] = float(err.mean())
            for h in HORIZONS:
                k = (va.horizon == h).values
                rows.append({"pollutant": pol, "variant": v, "horizon": h, "split": "val", "mae": float(err[k].mean())})
        serving[pol] = min(mae, key=mae.get)
        print(pol, {k: round(x, 2) for k, x in mae.items()}, "->", serving[pol])
    (a.art / "serving.json").write_text(json.dumps(serving, indent=1))
    (a.art / "validation_metrics.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()

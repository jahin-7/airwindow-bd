"""End-to-end experiment: features -> baselines + LightGBM (+intervals) -> LOSO -> GRU -> report.

    python -m airwindow.run_experiment --data data/processed --out ml/artifacts [--quick] [--no-gru]
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import train as T
from .features import HORIZONS, POLLUTANTS, build_all, feature_columns

LOSO_STATIONS = ["dhk_darussalam", "ctg_agrabad", "sylhet", "rajshahi", "khulna"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data/processed"))
    ap.add_argument("--out", type=Path, default=Path("ml/artifacts"))
    ap.add_argument("--quick", action="store_true", help="2 stations, few rounds: smoke test only")
    ap.add_argument("--no-gru", action="store_true")
    ap.add_argument("--gru-epochs", type=int, default=12)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    logf = open(a.out / "train_log.txt", "a")

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()

    t0 = time.time()
    hourly = pd.read_parquet(a.data / "cams_bd_hourly.parquet", columns=["station_id", "ts", "pm25", "pm10"])
    weather = pd.read_parquet(a.data / "era5_station_weather.parquet")
    for d in (hourly, weather):  # upload copies store these as categoricals
        d["station_id"] = d["station_id"].astype(str)
    cfg = T.TreeConfig()
    loso = LOSO_STATIONS
    if a.quick:
        keep = ["dhk_darussalam", "khulna"]
        hourly, weather = hourly[hourly.station_id.isin(keep)], weather[weather.station_id.isin(keep)]
        cfg = T.TreeConfig(num_boost_round=60, early_stopping=20)
        loso = []
    feats = build_all(hourly, weather)
    log(f"feature table {feats.shape} in {time.time()-t0:.0f}s")

    res = T.run_chronological(feats, a.out, cfg, log=log)
    res["leave_station_out"] = T.run_leave_station_out(feats, loso, cfg, log=log) if loso else []

    if not a.no_gru:
        import torch
        from . import deep
        lgb_test = pd.read_parquet(a.out / "test_predictions_lgb.parquet")
        res["gru"], res["gru_history"] = [], {}
        for variant, use_tw in (("tgt_weather", True), ("now_weather", False)):
            model, d, arr, smp, m_te, st_ids, hist = deep.train_gru(
                hourly, weather, use_tgt_weather=use_tw, epochs=2 if a.quick else a.gru_epochs, log=log)
            pg = deep.predict_test(model, d, arr, smp, m_te)
            scores, merged = deep.score_against(pg, smp, arr, lgb_test, variant)
            for s in scores:
                log(f"GRU {variant} {s['pollutant']} h={s['horizon']} MAE={s['mae']:.2f} skill={s['skill_vs_persistence']:.3f}")
            res["gru"] += scores
            res["gru_history"][variant] = hist
            torch.save({"state_dict": model.state_dict(), "mu": d.mu.tolist(), "sd": d.sd.tolist(),
                        "stations": st_ids, "use_tgt_weather": use_tw}, a.out / f"gru_{variant}.pt")
            merged.to_parquet(a.out / f"test_predictions_gru_{variant}.parquet", index=False)
        res["gru_device"] = "cuda" if torch.cuda.is_available() else "cpu"
        if torch.cuda.is_available():
            res["gpu_name"] = torch.cuda.get_device_name(0)

    sp = T.split(feats)
    res["meta"] = {
        "dataset": "CAMS-BD (doi:10.17632/hwmzyh5w4w.1), CC BY 4.0; weather: Open-Meteo ERA5 archive",
        "splits": {"train": f"targets <= {T.TRAIN_END}", "val": f"{T.TRAIN_END} .. {T.VAL_END}",
                   "test": f"{T.VAL_END} .. {T.TEST_END}"},
        "rows": {k: int(len(v)) for k, v in sp.items()},
        "horizons_h": list(HORIZONS), "pollutants": list(POLLUTANTS),
        "features_now_weather": feature_columns(feats, False), "features_tgt_weather": feature_columns(feats, True),
        "interval": "LightGBM q10/q90 widened by split-conformal offset fitted on validation (CQR), nominal 80%",
        "tgt_weather_caveat": "Uses ERA5 reanalysis at the target hour as a stand-in for the weather forecast "
                              "the app fetches live; real forecasts are less accurate, so treat as optimistic.",
        "quick_mode": bool(a.quick), "python": platform.python_version(), "runtime_s": round(time.time() - t0),
    }
    T.save_json(res, a.out / "metrics.json")
    log(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()

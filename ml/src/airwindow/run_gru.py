"""Train the GRU forecasters on their own (any device) and save raw test predictions.

    python -m airwindow.run_gru --data data/kaggle_upload --out ml/artifacts/gru

Scoring against the tree models' exact test rows happens later with
``deep.score_against`` once ``test_predictions_lgb.parquet`` is available.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
import torch

from . import deep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data/kaggle_upload"))
    ap.add_argument("--out", type=Path, default=Path("ml/artifacts/gru"))
    ap.add_argument("--epochs", type=int, default=12)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    hourly = pd.read_parquet(a.data / "cams_bd_hourly.parquet", columns=["station_id", "ts", "pm25", "pm10"])
    weather = pd.read_parquet(a.data / "era5_station_weather.parquet")
    for d in (hourly, weather):
        d["station_id"] = d["station_id"].astype(str)
    meta = {"device": str(deep.pick_device()), "epochs": a.epochs, "history": {}}
    for variant, use_tw in (("tgt_weather", True), ("now_weather", False)):
        t0 = time.time()
        model, d, arr, smp, m_te, st_ids, hist = deep.train_gru(hourly, weather, use_tw, epochs=a.epochs)
        pg = deep.predict_test(model, d, arr, smp, m_te)
        key = smp[["row", "ts"]].assign(station_id=arr.station_id.values[smp.row.values])
        pg.merge(key, on="row").to_parquet(a.out / f"gru_test_raw_{variant}.parquet", index=False)
        torch.save({"state_dict": model.state_dict(), "mu": d.mu.tolist(), "sd": d.sd.tolist(),
                    "stations": st_ids, "use_tgt_weather": use_tw}, a.out / f"gru_{variant}.pt")
        meta["history"][variant] = hist
        meta[f"{variant}_train_s"] = round(time.time() - t0)
        (a.out / "gru_meta.json").write_text(json.dumps(meta, indent=1))
        print(f"saved {variant} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()

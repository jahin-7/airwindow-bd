"""Forecasts from the trained LightGBM models, using the training feature code.

The served model is the "tgt_weather" variant when weather for the target hours
is available (Open-Meteo forecast live, ERA5 for replay), else "now_weather".
Intervals are the q10/q90 models widened by the conformal offset recorded on the
validation split, i.e. the same nominal-80% interval reported in the model card.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np
import pandas as pd

from .config import settings  # noqa: I001  (puts ml/src on sys.path first)
from airwindow.features import HORIZONS, MAX_OBS_AGE_H, POLLUTANTS, feature_columns, station_features
from airwindow.stations import STATIONS
from airwindow.weather import fetch_forecast

from .providers import History

MODEL_VERSION_FILE = "metrics.json"


class ModelsMissing(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _bundle(art: Path) -> dict:
    metrics_path = art / MODEL_VERSION_FILE
    if not metrics_path.exists():
        raise ModelsMissing(f"no trained models in {art}")
    metrics = json.loads(metrics_path.read_text())
    offsets = {(r["pollutant"], r["horizon"], r["model"].removeprefix("lightgbm_")): r["conformal_offset"]
               for r in metrics["overall"] if r["model"].startswith("lightgbm_")}
    models = {}
    for pol in POLLUTANTS:
        for v in ("tgt_weather", "now_weather"):
            f = art / f"lgb_{pol}_{v}.txt"
            if f.exists():
                models[(pol, v)] = {q: lgb.Booster(model_file=str(art / f"lgb_{pol}_{v}{q}.txt"))
                                    for q in ("", "_q10", "_q90")}
    # Which variant to serve per pollutant, chosen on the validation split (see ml/src/airwindow/select_serving.py).
    sv = art / "serving.json"
    serving = json.loads(sv.read_text()) if sv.exists() else {}
    version = f"lgb-{pd.Timestamp(metrics_path.stat().st_mtime, unit='s'):%Y%m%d}"
    return {"models": models, "offsets": offsets, "metrics": metrics, "version": version, "serving": serving}


@lru_cache(maxsize=1)
def _era5() -> pd.DataFrame:
    w = pd.read_parquet(settings.data_dir / "era5_station_weather.parquet")
    w["station_id"] = w["station_id"].astype(str)
    return w


def weather_for(station_id: str, start: pd.Timestamp, end: pd.Timestamp, live: bool) -> Optional[pd.DataFrame]:
    st = STATIONS[station_id]
    if not live:  # replay: the same ERA5 file the models were trained with
        w = _era5()
        w = w[(w.station_id == station_id) & (w.ts >= start) & (w.ts <= end)].copy()
        return w if len(w) else None
    try:
        w = fetch_forecast(st["lat"], st["lon"], past_days=3, forecast_days=2)
    except Exception:
        return None
    w["station_id"] = station_id
    return w


def forecast(hist: History, weather: Optional[pd.DataFrame]) -> dict:
    b = _bundle(settings.artifacts_dir)
    g = hist.frame.copy()
    issue = g.ts.max()
    # station_features needs rows for t+h to hold target-hour weather; pad the future.
    pad = pd.DataFrame({"ts": pd.date_range(issue + pd.Timedelta(hours=1), periods=max(HORIZONS), freq="h")})
    g = pd.concat([g, pad], ignore_index=True)
    f = station_features(g, weather, with_targets=False)
    f["station_id"] = pd.Categorical([hist.station_id] * len(f),
                                     categories=b["metrics"]["meta"].get("stations", sorted(STATIONS)))
    out = {"issued_at": issue.isoformat(), "model_version": b["version"], "points": [], "reasons": []}
    for pol in POLLUTANTS:
        row_all = f[f.ts == issue]
        if row_all.empty or pd.isna(row_all[f"{pol}_last"].iloc[0]):
            out["reasons"].append(f"{pol}: no reading in the last {MAX_OBS_AGE_H} h, forecast not issued")
            continue
        variant = b["serving"].get(pol, "now_weather")
        if variant == "tgt_weather" and weather is None:
            variant = "now_weather"
        if (pol, variant) not in b["models"]:
            continue
        m = b["models"][(pol, variant)]
        cols = m[""].feature_name()
        for h in HORIZONS:
            x = row_all[row_all.horizon == h]
            if variant == "tgt_weather" and x[[c for c in cols if c.endswith("_tgt")]].isna().any(axis=None):
                continue
            p = float(np.expm1(m[""].predict(x[cols]))[0])
            off = b["offsets"].get((pol, h, variant), 0.0)
            lo = float(np.expm1(m["_q10"].predict(x[cols]))[0]) - off
            hi = float(np.expm1(m["_q90"].predict(x[cols]))[0]) + off
            out["points"].append({"pollutant": pol, "horizon_h": h,
                                  "valid_at": (issue + pd.Timedelta(hours=h)).isoformat(),
                                  "value": round(max(p, 0), 1), "lo80": round(max(lo, 0), 1),
                                  "hi80": round(hi, 1), "variant": variant})
    return out


def rank_windows(points: list, pollutant: str, current: Optional[float], issued_at: str) -> list:
    """Order the forecast hours (plus 'now' if measured) by predicted concentration.

    Relative ranking only, over hours where a forecast exists; not a safety claim.
    """
    cands = [{"valid_at": p["valid_at"], "horizon_h": p["horizon_h"], "value": p["value"],
              "lo80": p["lo80"], "hi80": p["hi80"], "kind": "forecast"}
             for p in points if p["pollutant"] == pollutant]
    if current is not None:
        cands.append({"valid_at": issued_at, "horizon_h": 0, "value": current, "lo80": None, "hi80": None,
                      "kind": "measured"})
    if not cands:
        return []
    best = min(c["value"] for c in cands)
    for c in sorted(cands, key=lambda c: c["value"]):
        c["relative_to_best_pct"] = round(100 * (c["value"] - best) / best, 0) if best else 0
    ranked = sorted(cands, key=lambda c: c["value"])
    for i, c in enumerate(ranked):
        c["rank"] = i + 1
        # overlapping intervals mean the ordering is not clear-cut
        c["clearly_lower_than_next"] = (
            i + 1 < len(ranked) and c["hi80"] is not None and ranked[i + 1]["lo80"] is not None
            and c["hi80"] < ranked[i + 1]["lo80"])
    return ranked

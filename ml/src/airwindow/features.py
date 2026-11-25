"""Forecast features. Every feature uses only what is known at issue time t.

Input is one station on a complete hourly grid (missing hours present as NaN).
Each output row is an issue time t with targets y_{pol}_h{h} = value at t+h.

Weather comes in two forms:
* ``w_*_now``  - weather at t (observed/analysis; always available at issue time)
* ``w_*_tgt``  - weather at t+h. In training this is ERA5 reanalysis, standing in
  for the weather *forecast* the live app fetches; it is therefore an optimistic
  proxy and models using it are reported separately ("with weather forecast").
Rolling statistics use ``min_periods`` and only past rows; nothing is filled
from the future. No global scaling is fitted here (trees need none; the neural
model fits its scaler on the training split only).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

POLLUTANTS = ("pm25", "pm10")
HORIZONS = (1, 3, 6)
LAGS = (1, 2, 3, 6, 12, 23)  # lag 0 is the value at t itself
WINDOWS = (3, 6, 24)
WEATHER = ("w_temp", "w_rh", "w_ws", "w_wd", "w_rain", "w_bp", "w_blh")
MAX_OBS_AGE_H = 3  # issue a forecast only if the latest PM reading is this fresh


def _hours_since_valid(s: pd.Series) -> pd.Series:
    idx = np.arange(len(s), dtype=float)
    last = pd.Series(np.where(s.notna(), idx, np.nan), index=s.index).ffill()
    return pd.Series(idx, index=s.index) - last


def station_features(g: pd.DataFrame, weather: pd.DataFrame | None = None,
                     horizons=HORIZONS, with_targets: bool = True) -> pd.DataFrame:
    """g: one station, columns ts, pm25, pm10, sorted, hourly, no gaps in ts."""
    g = g.sort_values("ts").reset_index(drop=True)
    f = pd.DataFrame({"ts": g["ts"]})
    for p in POLLUTANTS:
        s = g[p]
        f[f"{p}_lag0"] = s
        for L in LAGS:
            f[f"{p}_lag{L}"] = s.shift(L)
        for w in WINDOWS:
            r = s.rolling(w, min_periods=max(1, w // 2))
            f[f"{p}_mean{w}"] = r.mean()
            f[f"{p}_std{w}"] = r.std()
        f[f"{p}_d1"] = s - s.shift(1)
        f[f"{p}_d3"] = s - s.shift(3)
        f[f"{p}_age"] = _hours_since_valid(s)
        f[f"{p}_last"] = s.ffill(limit=MAX_OBS_AGE_H)  # last reading within 3 h
    f["ratio_25_10"] = f["pm25_lag0"] / f["pm10_lag0"]
    hr = g["ts"].dt.hour
    f["hour_sin"], f["hour_cos"] = np.sin(2 * np.pi * hr / 24), np.cos(2 * np.pi * hr / 24)
    doy = g["ts"].dt.dayofyear
    f["doy_sin"], f["doy_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    f["dow"] = g["ts"].dt.dayofweek

    if weather is not None:
        w = weather.set_index("ts").reindex(g["ts"]).reset_index(drop=True)
        for c in WEATHER:
            f[f"{c}_now"] = w[c].values
        f["w_rain_6h"] = w["w_rain"].rolling(6, min_periods=1).sum().values
        wd = np.deg2rad(w["w_wd"])
        f["w_u_now"], f["w_v_now"] = (-w["w_ws"] * np.sin(wd)).values, (-w["w_ws"] * np.cos(wd)).values

    rows = []
    for h in horizons:
        fh = f.copy()
        fh["horizon"] = h
        tgt_hr = (hr + h) % 24
        fh["tgt_hour_sin"], fh["tgt_hour_cos"] = np.sin(2 * np.pi * tgt_hr / 24), np.cos(2 * np.pi * tgt_hr / 24)
        for p in POLLUTANTS:
            # same clock hour as the target, one day earlier: known at t for h <= 24
            fh[f"{p}_sameh_yday"] = g[p].shift(24 - h)
            if with_targets:
                fh[f"y_{p}"] = g[p].shift(-h)
        if weather is not None:
            wt = w.shift(-h)
            for c in WEATHER:
                fh[f"{c}_tgt"] = wt[c].values
            wdt = np.deg2rad(wt["w_wd"])
            fh["w_u_tgt"], fh["w_v_tgt"] = (-wt["w_ws"] * np.sin(wdt)).values, (-wt["w_ws"] * np.cos(wdt)).values
            # rain summed over (t, t+h]
            fh["w_rain_next"] = w["w_rain"].rolling(h, min_periods=1).sum().shift(-h).values
        rows.append(fh)
    return pd.concat(rows, ignore_index=True)


def build_all(hourly: pd.DataFrame, weather: pd.DataFrame | None) -> pd.DataFrame:
    out = []
    for sid, g in hourly.groupby("station_id"):
        w = None if weather is None else weather[weather.station_id == sid]
        fs = station_features(g[["ts", "pm25", "pm10"]], w)
        fs.insert(0, "station_id", sid)
        out.append(fs)
    df = pd.concat(out, ignore_index=True)
    df["station_id"] = df["station_id"].astype("category")
    return df


def feature_columns(df: pd.DataFrame, use_tgt_weather: bool, use_station: bool = True) -> list:
    drop = {"ts", "y_pm25", "y_pm10"}
    cols = [c for c in df.columns if c not in drop and not c.startswith("y_")]
    if not use_tgt_weather:
        cols = [c for c in cols if not (c.endswith("_tgt") or c == "w_rain_next")]
    if not use_station:
        cols = [c for c in cols if c != "station_id"]
    return cols

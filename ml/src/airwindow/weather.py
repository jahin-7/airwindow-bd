"""Open-Meteo weather at each station (no API key needed).

Training uses the ERA5 archive; the live app uses the forecast API with the
same variable names, so the model sees the same kind of input in both places.
Open-Meteo labels hours by their start in local time; precipitation is the sum
over the preceding hour. We key both on the same local clock hour as CAMS ``ts``.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

import pandas as pd

VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m",
        "precipitation", "surface_pressure", "boundary_layer_height"]
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
RENAME = {"temperature_2m": "w_temp", "relative_humidity_2m": "w_rh", "wind_speed_10m": "w_ws",
          "wind_direction_10m": "w_wd", "precipitation": "w_rain", "surface_pressure": "w_bp",
          "boundary_layer_height": "w_blh"}


def _get(url: str, params: dict, retries: int = 6) -> dict:
    q = url + "?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            with urllib.request.urlopen(q, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if i == retries - 1:
                raise
            # 429 = minute/hour quota; back off long enough for the window to reset.
            time.sleep(70 if getattr(e, "code", None) == 429 else 5 * (i + 1))
    raise RuntimeError("unreachable")


def _frame(payload: dict) -> pd.DataFrame:
    h = payload["hourly"]
    df = pd.DataFrame({k: h[k] for k in VARS})
    df.insert(0, "ts", pd.to_datetime(h["time"]))
    return df.rename(columns=RENAME)


def fetch_archive(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    return _frame(_get(ARCHIVE_URL, {"latitude": lat, "longitude": lon, "start_date": start,
                                     "end_date": end, "hourly": ",".join(VARS),
                                     "timezone": "Asia/Dhaka", "wind_speed_unit": "ms"}))


def fetch_forecast(lat: float, lon: float, past_days: int = 2, forecast_days: int = 2) -> pd.DataFrame:
    return _frame(_get(FORECAST_URL, {"latitude": lat, "longitude": lon, "hourly": ",".join(VARS),
                                      "past_days": past_days, "forecast_days": forecast_days,
                                      "timezone": "Asia/Dhaka", "wind_speed_unit": "ms"}))

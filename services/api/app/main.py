"""AirWindow BD API.

    uvicorn app.main:app --port 8010   (from services/api)
"""
from __future__ import annotations

import datetime as dt
import math
import time
from collections import defaultdict, deque
from functools import lru_cache
from typing import Literal, Optional

import pandas as pd

from .config import DHAKA_TZ, settings  # noqa: I001  (puts ml/src on sys.path first)
from airwindow.stations import STATIONS
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import forecast as fc
from .aqi import WHO_2021_24H, aqi_from_hourly
from .providers import ReplayProvider, make_provider

app = FastAPI(title="AirWindow BD API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"],
                   allow_headers=["*"])

provider = make_provider()
MODE = "live" if provider.name == "openaq" else "replay"
_hits: dict = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = request.client.host if request.client else "?"
    q, now = _hits[ip], time.monotonic()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.rate_limit_per_min:
        return JSONResponse({"detail": "Too many requests, try again in a minute."}, status_code=429)
    q.append(now)
    return await call_next(request)


def _station(station_id: str) -> dict:
    if station_id not in STATIONS or station_id == "dhk_sangsad":
        raise HTTPException(404, "Unknown station")
    return {"id": station_id, **STATIONS[station_id]}


def _km(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def _clock_now() -> pd.Timestamp:
    """Current Dhaka time; in replay mode, the same hour of 2024."""
    now = pd.Timestamp(dt.datetime.now(DHAKA_TZ).replace(tzinfo=None))
    return provider.replay_time(now) if isinstance(provider, ReplayProvider) else now


# Short cache so a burst of screens doesn't refetch the provider every call.
@lru_cache(maxsize=64)
def _history_cached(station_id: str, bucket: int):
    return provider.history(station_id, hours=72)


def _history(station_id: str):
    try:
        return _history_cached(station_id, int(time.time() // 300))
    except Exception:
        return None


@app.get("/api/meta")
def meta():
    return {"mode": MODE, "replay_note": None if MODE == "live" else
            "No live provider configured. Showing CAMS-BD 2024 history at today's date and hour. "
            "These are past measurements, not current air.",
            "stale_after_hours": settings.stale_after_h,
            "sources": {"training": "CAMS-BD, doi:10.17632/hwmzyh5w4w.1 (CC BY 4.0)",
                        "live": "OpenAQ v3 (when configured)", "weather": "Open-Meteo (ERA5 archive / forecast)"}}


@app.get("/api/locations")
def locations(query: str = Query("", max_length=60)):
    q = query.strip().lower()
    out = [{"id": k, **v} for k, v in STATIONS.items() if k != "dhk_sangsad"]
    if q:
        out = [s for s in out if q in s["name"].lower() or q in s["city"].lower() or q in s["name_bn"]]
    return out


@app.get("/api/stations/nearby")
def nearby(lat: float = Query(..., ge=20, le=27), lon: float = Query(..., ge=88, le=93)):
    out = [{"id": k, **v, "distance_km": round(_km(lat, lon, v["lat"], v["lon"]), 1)}
           for k, v in STATIONS.items() if k != "dhk_sangsad"]
    return sorted(out, key=lambda s: s["distance_km"])


@app.get("/api/observations/latest")
def latest(station_id: str):
    st = _station(station_id)
    h = _history(station_id)
    base = {"station": st, "mode": MODE}
    if h is None:
        return {**base, "status": "no_data", "message": "No current observation available for this area."}
    now = _clock_now()
    age_h = (now - pd.Timestamp(h.observed_at)).total_seconds() / 3600
    fresh = age_h <= settings.stale_after_h
    last = h.frame.dropna(subset=["pm25"]).iloc[-1]
    win = h.frame[h.frame.ts > now - pd.Timedelta(hours=24)]
    readings = {}
    for pol in ("pm25", "pm10"):
        row = h.frame.dropna(subset=[pol])
        if row.empty:
            continue
        r = row.iloc[-1]
        readings[pol] = {"value": round(float(r[pol]), 1), "unit": "µg/m³", "observed_at": r.ts.isoformat(),
                         "aqi_24h": aqi_from_hourly(pol, [None if pd.isna(v) else float(v) for v in win[pol]]),
                         "who_24h_guideline": WHO_2021_24H[pol]}
    return {**base, "status": "ok" if fresh else "stale", "observed_at": last.ts.isoformat(),
            "age_hours": round(age_h, 1), "source": h.source, "is_live": h.is_live,
            "provider_location": h.provider_location, "provider_distance_m": h.distance_m,
            "readings": readings}


def _forecast_for(station_id: str) -> dict:
    h = _history(station_id)
    if h is None:
        raise HTTPException(409, "No recent observations for this station, so no forecast can be issued.")
    now = _clock_now()
    if (now - pd.Timestamp(h.observed_at)).total_seconds() / 3600 > settings.stale_after_h:
        raise HTTPException(409, "Latest observation is stale; forecasts are only issued from fresh data.")
    issue = h.frame.ts.max()
    w = fc.weather_for(station_id, issue - pd.Timedelta(hours=72), issue + pd.Timedelta(hours=8), h.is_live)
    try:
        out = fc.forecast(h, w)
    except fc.ModelsMissing:
        raise HTTPException(503, "Forecast models are not installed on this server yet.")
    out.update({"station_id": station_id, "mode": MODE, "is_live": h.is_live, "source": h.source,
                "weather_source": None if w is None else ("Open-Meteo forecast" if h.is_live else "ERA5 (replay)")})
    return out


@app.get("/api/forecast")
def forecast(station_id: str, pollutant: Optional[Literal["pm25", "pm10"]] = None,
             horizon: Optional[int] = Query(None, ge=1, le=6)):
    _station(station_id)
    out = _forecast_for(station_id)
    out["points"] = [p for p in out["points"] if (pollutant is None or p["pollutant"] == pollutant)
                     and (horizon is None or p["horizon_h"] == horizon)]
    return out


class WindowRequest(BaseModel):
    station_id: str
    pollutant: Literal["pm25", "pm10"] = "pm25"
    activity: Literal["walk", "exercise", "commute", "school_run", "errands"] = "walk"
    duration_min: int = Field(60, ge=15, le=240)


@app.post("/api/activity-windows")
def activity_windows(req: WindowRequest):
    _station(req.station_id)
    out = _forecast_for(req.station_id)
    lat = latest(req.station_id)
    cur = lat.get("readings", {}).get(req.pollutant, {}).get("value") if lat.get("status") == "ok" else None
    ranked = fc.rank_windows(out["points"], req.pollutant, cur, out["issued_at"])
    if not ranked:
        raise HTTPException(409, "No valid forecast hours for this station right now.")
    return {"station_id": req.station_id, "pollutant": req.pollutant, "activity": req.activity,
            "duration_min": req.duration_min, "issued_at": out["issued_at"], "model_version": out["model_version"],
            "mode": MODE, "is_live": out["is_live"], "windows": ranked,
            "note": "Ranking compares only these hours by predicted concentration. "
                    "A lower value is not a guarantee of safe air. Follow official advisories."}


@app.get("/api/trends")
def trends(station_id: str, days: int = Query(7, ge=1, le=31)):
    _station(station_id)
    rp = provider if isinstance(provider, ReplayProvider) else ReplayProvider(settings.data_dir / "cams_bd_hourly.parquet")
    end = rp.replay_time()
    g = rp.df[(rp.df.station_id == station_id) & (rp.df.ts > end - pd.Timedelta(days=days)) & (rp.df.ts <= end)]
    daily = g.set_index("ts")[["pm25", "pm10"]].resample("D").agg(["mean", "count"])
    rows = [{"date": d.date().isoformat(),
             "pm25_mean": None if r[("pm25", "count")] < 18 else round(float(r[("pm25", "mean")]), 1),
             "pm10_mean": None if r[("pm10", "count")] < 18 else round(float(r[("pm10", "mean")]), 1)}
            for d, r in daily.iterrows()]
    hourly = [{"ts": t.isoformat(), "pm25": None if pd.isna(a) else round(float(a), 1),
               "pm10": None if pd.isna(b) else round(float(b), 1)} for t, a, b in zip(g.ts, g.pm25, g.pm10)]
    return {"station_id": station_id, "source": "CAMS-BD historical (2024)", "is_live": False,
            "daily": rows, "hourly": hourly}


@app.get("/api/model-card")
def model_card():
    try:
        b = fc._bundle(settings.artifacts_dir)
    except fc.ModelsMissing:
        raise HTTPException(503, "Model metrics not available yet.")
    m = b["metrics"]
    return {"model_version": b["version"], "meta": m.get("meta"), "overall": m.get("overall"),
            "gru": m.get("gru"), "leave_station_out": m.get("leave_station_out")}


@app.get("/api/health")
def health():
    return {"ok": True, "mode": MODE}

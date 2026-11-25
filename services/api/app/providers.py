"""Air-quality observation providers behind one interface.

* ``OpenAQProvider``  - live hourly PM from OpenAQ v3 (needs OPENAQ_API_KEY). A CAMS
  station is matched to an OpenAQ location only if one with the pollutant lies
  within ``MATCH_RADIUS_M`` of the station's coordinates.
* ``ReplayProvider``  - replays CAMS-BD 2024 history on today's clock for demos.
  Every observation it returns is marked ``is_live=False`` with its true
  historical timestamp, so the UI can never present it as current.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

import httpx
import pandas as pd

from .config import DHAKA_TZ, settings

OPENAQ = "https://api.openaq.org/v3"
PARAM_IDS = {"pm25": 2, "pm10": 1}  # OpenAQ parameter ids
MATCH_RADIUS_M = 10_000


@dataclass
class History:
    """Hourly series for one station, local Dhaka time (naive), hour-ending ts."""
    station_id: str
    frame: pd.DataFrame          # columns ts, pm25, pm10
    source: str
    is_live: bool
    observed_at: Optional[dt.datetime]   # timestamp of the newest reading
    provider_location: Optional[str] = None
    distance_m: Optional[float] = None


class AirQualityProvider(Protocol):
    name: str

    def history(self, station_id: str, hours: int = 72) -> Optional[History]: ...


class OpenAQProvider:
    name = "openaq"

    def __init__(self, api_key: str, timeout_s: float = 8.0):
        self.client = httpx.Client(base_url=OPENAQ, headers={"X-API-Key": api_key}, timeout=timeout_s)
        self._match: dict = {}

    def _sensors_near(self, lat: float, lon: float) -> dict:
        key = (lat, lon)
        if key not in self._match:
            r = self.client.get("/locations", params={"coordinates": f"{lat},{lon}",
                                                      "radius": MATCH_RADIUS_M, "limit": 20})
            r.raise_for_status()
            found = {}
            for loc in r.json().get("results", []):
                d = loc.get("distance") or 0
                for s in loc.get("sensors", []):
                    pid = s.get("parameter", {}).get("id")
                    for pol, want in PARAM_IDS.items():
                        if pid == want and (pol not in found or d < found[pol][2]):
                            found[pol] = (s["id"], loc.get("name"), d)
            self._match[key] = found
        return self._match[key]

    def history(self, station_id: str, hours: int = 72) -> Optional[History]:
        from airwindow.stations import STATIONS
        st = STATIONS[station_id]
        sensors = self._sensors_near(st["lat"], st["lon"])
        if "pm25" not in sensors:
            return None
        now = dt.datetime.now(dt.timezone.utc)
        series, loc_name, dist = {}, None, None
        for pol, (sid, name, d) in sensors.items():
            r = self.client.get(f"/sensors/{sid}/hours", params={
                "datetime_from": (now - dt.timedelta(hours=hours)).isoformat(), "datetime_to": now.isoformat(),
                "limit": hours + 5})
            r.raise_for_status()
            pts = {}
            for m in r.json().get("results", []):
                end = m["period"]["datetimeTo"]["utc"]
                t = pd.Timestamp(end).tz_convert(DHAKA_TZ).tz_localize(None)
                pts[t] = m["value"]
            series[pol] = pd.Series(pts, dtype=float)
            if pol == "pm25":
                loc_name, dist = name, d
        if series["pm25"].empty:
            return None
        frame = pd.DataFrame(series).sort_index()
        frame = frame.reindex(pd.date_range(frame.index.min(), frame.index.max(), freq="h"))
        frame = frame.rename_axis("ts").reset_index()
        for c in ("pm25", "pm10"):
            if c not in frame:
                frame[c] = float("nan")
        last = frame.dropna(subset=["pm25"]).ts.max()
        return History(station_id, frame[["ts", "pm25", "pm10"]], "OpenAQ v3", True,
                       last.to_pydatetime(), loc_name, dist)


class ReplayProvider:
    """CAMS-BD 2024 shown on today's date/hour. Historical, never live."""
    name = "replay"

    def __init__(self, parquet: Path):
        df = pd.read_parquet(parquet, columns=["station_id", "ts", "pm25", "pm10"])
        df["station_id"] = df["station_id"].astype(str)
        self.df = df[(df.ts > "2024-01-01") & (df.ts <= "2025-01-01")]

    def replay_time(self, now: Optional[dt.datetime] = None) -> pd.Timestamp:
        now = now or dt.datetime.now(DHAKA_TZ).replace(tzinfo=None)
        t = pd.Timestamp(now).floor("h")
        try:
            return t.replace(year=2024)
        except ValueError:  # 29 Feb outside a leap year cannot happen here; guard anyway
            return t.replace(year=2024, day=28)

    def history(self, station_id: str, hours: int = 72, now: Optional[dt.datetime] = None) -> Optional[History]:
        t = self.replay_time(now)
        g = self.df[(self.df.station_id == station_id) & (self.df.ts > t - pd.Timedelta(hours=hours))
                    & (self.df.ts <= t)]
        if g.empty or g.pm25.notna().sum() == 0:
            return None
        last = g.dropna(subset=["pm25"]).ts.max()
        return History(station_id, g[["ts", "pm25", "pm10"]].reset_index(drop=True),
                       "CAMS-BD historical replay (2024)", False, last.to_pydatetime())


def make_provider() -> AirQualityProvider:
    if settings.openaq_api_key:
        return OpenAQProvider(settings.openaq_api_key)
    return ReplayProvider(settings.data_dir / "cams_bd_hourly.parquet")

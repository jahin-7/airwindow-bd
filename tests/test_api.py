"""Product-rule tests for the API (historical replay mode, no network)."""
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
os.environ["OPENAQ_API_KEY"] = ""  # force replay mode for tests
DATA = ROOT / "data" / "kaggle_upload" / "cams_bd_hourly.parquet"
pytestmark = pytest.mark.skipif(not DATA.exists(), reason="processed data not built")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_replay_is_never_labelled_live(client):
    meta = client.get("/api/meta").json()
    assert meta["mode"] == "replay" and "not current" in meta["replay_note"]
    r = client.get("/api/observations/latest", params={"station_id": "dhk_darussalam"}).json()
    if r["status"] != "no_data":
        assert r["is_live"] is False and "historical" in r["source"].lower()
        assert r["observed_at"].startswith("2024") or r["observed_at"].startswith("2025-01-01")


def test_unknown_and_dropped_stations_rejected(client):
    assert client.get("/api/observations/latest", params={"station_id": "nowhere"}).status_code == 404
    # Sangsad's dates could not be verified; it is excluded everywhere
    assert client.get("/api/observations/latest", params={"station_id": "dhk_sangsad"}).status_code == 404
    assert all(s["id"] != "dhk_sangsad" for s in client.get("/api/locations").json())


def test_nearby_requires_bangladesh_coordinates(client):
    assert client.get("/api/stations/nearby", params={"lat": 51.5, "lon": -0.1}).status_code == 422
    near = client.get("/api/stations/nearby", params={"lat": 22.35, "lon": 91.81}).json()
    assert near[0]["city"] == "Chattogram"


def test_stale_observation_blocks_forecast(client, monkeypatch):
    from app import main
    from app.providers import History
    old = pd.DataFrame({"ts": pd.date_range("2024-03-01 01:00", periods=30, freq="h"), "pm25": 80.0, "pm10": 120.0})
    stale = History("dhk_barc", old, "test", False, old.ts.max().to_pydatetime())
    monkeypatch.setattr(main, "_history", lambda sid: stale)
    monkeypatch.setattr(main, "_clock_now", lambda: pd.Timestamp("2024-03-05 12:00"))
    assert client.get("/api/observations/latest", params={"station_id": "dhk_barc"}).json()["status"] == "stale"
    assert client.get("/api/forecast", params={"station_id": "dhk_barc"}).status_code == 409


def test_no_data_message(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_history", lambda sid: None)
    r = client.get("/api/observations/latest", params={"station_id": "sylhet"}).json()
    assert r["status"] == "no_data" and r["message"] == "No current observation available for this area."
    assert client.get("/api/forecast", params={"station_id": "sylhet"}).status_code == 409


def test_aqi_requires_enough_hours_and_matches_epa():
    from app.aqi import aqi, aqi_from_hourly
    assert aqi("pm25", 9.0) == 50 and aqi("pm25", 35.5) == 101 and aqi("pm25", 225.4) == 300
    assert aqi("pm10", 154) == 100 and aqi("pm10", 155) == 101
    assert aqi_from_hourly("pm25", [50.0] * 17 + [None] * 7) is None
    r = aqi_from_hourly("pm25", [50.0] * 18)
    assert r["band"] == "usg" and r["who_multiple"] == pytest.approx(3.3, abs=0.05)


def test_ranking_is_relative_and_flags_overlap():
    from app.forecast import rank_windows
    pts = [{"pollutant": "pm25", "horizon_h": 1, "valid_at": "2024-01-01T11:00:00", "value": 80, "lo80": 60, "hi80": 100},
           {"pollutant": "pm25", "horizon_h": 3, "valid_at": "2024-01-01T13:00:00", "value": 40, "lo80": 30, "hi80": 50}]
    r = rank_windows(pts, "pm25", 90.0, "2024-01-01T10:00:00")
    assert [w["horizon_h"] for w in r] == [3, 1, 0]
    assert r[0]["clearly_lower_than_next"] is True    # 50 < 60
    assert r[1]["clearly_lower_than_next"] is False   # measured 'now' has no interval
    assert rank_windows([], "pm25", None, "x") == []

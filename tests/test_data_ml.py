import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ml" / "src"))

from airwindow.cleaning import clean, to_hourly_grid  # noqa: E402
from airwindow.features import station_features  # noqa: E402
from airwindow.parsing import (Audit, _decode_sequence, date_candidates, parse_2012_2021,  # noqa: E402
                               parse_annual, parse_hour)
from airwindow.train import TRAIN_END, VAL_END, split  # noqa: E402

HDR = ["Location", "Date", "Time", "SO2", "NO", "NO2", "NOX", "CO", "O3", "PM2.5", "PM10", "Wind Speed",
       "Wind Dir", "Temperature", "RH", "Solar Rad", "BP", "Rain", "V Wind Speed", "Ratio"]
UNITS = ["ppb"] * 4 + ["ppm", "ppb", "ug/m3", "ug/m3", "m/s", "Deg", "C°", "%", "w/m2", "mb", "mm", "m/s", "x"]


def _row(loc, date, time, pm25=50.0, sr=10.0, bp=1010.0, hdr=HDR):
    vals = {h: np.nan for h in hdr}
    vals.update({"Location": loc, "Date": date, "Time": time, "PM2.5": pm25, "PM10": pm25 * 1.5,
                 "Solar Rad": sr, "BP": bp})
    return [vals[h] for h in hdr]


def test_parse_hour_variants():
    assert parse_hour("01:00") == 1
    assert parse_hour("24:00") == 24
    assert parse_hour("24:00:00 PM") == 24
    assert parse_hour("12/31/1899 10:00:00 PM") == 22
    assert parse_hour(8) == 8
    assert parse_hour(float("nan")) is None


def test_day_month_swap_is_recovered_by_sequence():
    # 31 Jan 2017 24:00, then "01/02/2017" which Excel stored as serial for 2 Jan 2017.
    jan31 = date_candidates("31/01/2017", 24)
    feb1_wrong_serial = (pd.Timestamp("2017-01-02") - pd.Timestamp("1899-12-30")).days
    feb1 = date_candidates(feb1_wrong_serial, 1)
    a = Audit()
    out = _decode_sequence([jan31, feb1], a)
    assert out == [pd.Timestamp("2017-02-01 00:00"), pd.Timestamp("2017-02-01 01:00")]
    assert a.date_fixes["day_month_swapped"] == 1


def test_fractional_serial_float_error_rounds_to_hour():
    # 44195.99999 is 31 Dec 2020 00:00 with float error, labelled 01:00 -> 01:00 that day.
    c = date_candidates(44195.99999438658, 1)
    assert pd.Timestamp("2020-12-31 01:00") in c


def test_midnight_serial_labelled_24():
    assert date_candidates(43833.0, 24)[0] == pd.Timestamp("2020-01-03 00:00")


def _sheet(blocks):
    rows = [HDR]
    for hdr, data in blocks:
        rows.extend(data)
    return pd.DataFrame(rows, dtype=object)


def test_savar_block_header_swap_and_dateless_block_excluded():
    savar_hdr = HDR.copy()
    i, j = savar_hdr.index("Solar Rad"), savar_hdr.index("BP")
    savar_hdr[i], savar_hdr[j] = savar_hdr[j], savar_hdr[i]
    d0 = 43831  # 2020-01-01
    rows = [HDR, ["Gazipur", None, None, *UNITS]]
    rows += [_row("Gazipur", d0, f"{h:02d}:00") for h in range(1, 4)]
    # Savar's own header row lists BP before Solar Rad; its values follow that order.
    rows += [savar_hdr, ["Savar", None, None, *UNITS]]
    rows += [_row("Savar", d0, f"{h:02d}:00", sr=1009.0, bp=12.0) for h in range(1, 4)]
    kh_hdr = HDR.copy()
    kh_hdr[1] = None
    rows += [["Khulna", None, "Time", *HDR[3:]]]
    rows += [_row("Khulna", None, f"{h:02d}:00") for h in range(1, 4)]
    raw = pd.DataFrame(rows, dtype=object)
    a = Audit()
    df = parse_2012_2021(raw, a)
    sav = df[df.station_id == "savar"]
    assert (sav.bp == 1009.0).all() and (sav.sr == 12.0).all()
    assert "khulna" not in set(df.station_id)
    assert a.dropped["no_date_column_khulna"] == 3
    assert sav.ts.tolist() == [pd.Timestamp("2020-01-01 01:00") + pd.Timedelta(hours=k) for k in range(3)]


def test_annual_parser_column_order_and_unit_rows():
    hdr = ["Location", "Date & Time", "SO2", "NO", "NO2", "NOX", "CO", "O3", "PM10", "PM2.5"]
    raw = pd.DataFrame([hdr, ["BARC", None, " ppb ", "ppb", "ppb", "ppb", "ppm", "ppb", "ug/m3", "ug/m3"],
                        ["BARC", pd.Timestamp("2022-01-01 01:00"), 1, 1, 1, 1, 1, 1, 200.0, 100.0]], dtype=object)
    df = parse_annual(raw, "2022")
    assert df.pm25.iloc[0] == 100.0 and df.pm10.iloc[0] == 200.0


def test_clean_nulls_range_and_stuck_and_never_fills():
    ts = pd.date_range("2020-01-01 01:00", periods=12, freq="h")
    pm = [10, 20, 30, 5000, 40, 7, 7, 7, 7, 7, 7, 8]
    df = pd.DataFrame({"station_id": "x", "ts": ts, "pm25": pm, "pm10": np.arange(12) + 50.0,
                       "source_file": "2022"})
    for c in ["so2", "no", "no2", "nox", "co", "o3", "ws", "wd", "temp", "rh", "sr", "bp", "rain", "vws"]:
        df[c] = np.nan
    out, rep = clean(df)
    assert np.isnan(out.pm25.iloc[3])            # out of range
    assert out.pm25.iloc[5:11].isna().all()      # stuck run of 6
    assert out.pm25.iloc[11] == 8
    grid = to_hourly_grid(out.drop(index=[2]))
    assert len(grid) == 12 and np.isnan(grid.pm25.iloc[2])  # gap stays missing


def _series(n=200):
    ts = pd.date_range("2022-12-20 01:00", periods=n, freq="h")
    rng = np.random.default_rng(0)
    return pd.DataFrame({"ts": ts, "pm25": rng.uniform(10, 100, n), "pm10": rng.uniform(20, 200, n)})


def test_features_do_not_use_future_values():
    g = _series()
    f1 = station_features(g, None)
    g2 = g.copy()
    k = 120
    g2.loc[k:, ["pm25", "pm10"]] = 9999.0  # change everything from row k on
    f2 = station_features(g2, None)
    feat = [c for c in f1.columns if not c.startswith("y_")]
    for h in (1, 3, 6):
        a = f1[(f1.horizon == h)].iloc[:k][feat]
        b = f2[(f2.horizon == h)].iloc[:k][feat]
        pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True))


def test_target_is_value_h_hours_ahead():
    g = _series()
    f = station_features(g, None)
    for h in (1, 3, 6):
        fh = f[f.horizon == h].reset_index(drop=True)
        assert fh.y_pm25.iloc[10] == pytest.approx(g.pm25.iloc[10 + h])


def test_chronological_split_has_no_target_overlap():
    g = pd.DataFrame({"ts": pd.date_range("2022-12-31 12:00", periods=24 * 400, freq="h")})
    rows = []
    for h in (1, 3, 6):
        rows.append(g.assign(horizon=h))
    df = pd.concat(rows, ignore_index=True)
    sp = split(df)
    tr_tgt = sp["train"].ts + pd.to_timedelta(sp["train"].horizon, unit="h")
    va_tgt = sp["val"].ts + pd.to_timedelta(sp["val"].horizon, unit="h")
    assert tr_tgt.max() <= TRAIN_END
    assert sp["val"].ts.min() >= TRAIN_END and va_tgt.max() <= VAL_END
    assert sp["test"].ts.min() >= VAL_END

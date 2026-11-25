"""Validation and cleaning after parsing. Never fills values; only nulls bad ones.

Rules (all counted into the quality report):
1. Physical range per column. Out-of-range values become NaN.
2. Station-year quarantine: if more than QUARANTINE_FRAC of a column's
   non-null values in one station-year fail the range check, the column is
   treated as shifted/mislabelled for that station-year and nulled entirely.
3. Stuck sensor: PM values repeated unchanged for >= STUCK_HOURS consecutive
   hours are nulled (a flat line is an instrument fault, not air).
4. Duplicates on (station_id, ts): identical rows collapse; conflicting rows
   keep the later source file and the conflict count is reported.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .parsing import CANONICAL

RANGES = {
    "pm25": (0.5, 1000.0), "pm10": (0.5, 2000.0),
    "so2": (0, 500), "no": (0, 1000), "no2": (0, 500), "nox": (0, 1500),
    "co": (0, 50), "o3": (0, 300),
    "ws": (0, 40), "wd": (0, 360), "temp": (0, 48), "rh": (1, 100),
    "sr": (0, 1400), "bp": (950, 1050), "rain": (0, 200), "vws": (-10, 10),
}
QUARANTINE_FRAC = 0.2
STUCK_HOURS = 6


def _stuck_mask(s: pd.Series, n: int) -> pd.Series:
    run_id = (s != s.shift()).cumsum()
    run_len = s.groupby(run_id).transform("size")
    return s.notna() & (run_len >= n)


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    report: dict = {"range_nulled": {}, "quarantined": [], "stuck_nulled": {}, "duplicates": {}}
    df = df.copy()
    # Hour-ending stamps: 00:00 on 1 Jan closes the previous year.
    df["year"] = (df["ts"] - pd.Timedelta(hours=1)).dt.year

    # 2. quarantine first, so whole shifted columns are reported as such.
    for col, (lo, hi) in RANGES.items():
        bad = df[col].notna() & ~df[col].between(lo, hi)
        frac = bad.groupby([df["station_id"], df["year"]]).sum() / \
            df[col].notna().groupby([df["station_id"], df["year"]]).sum().replace(0, np.nan)
        for (sid, yr), f in frac[frac > QUARANTINE_FRAC].items():
            m = (df["station_id"] == sid) & (df["year"] == yr)
            report["quarantined"].append({"station_id": sid, "year": int(yr), "column": col,
                                          "bad_frac": round(float(f), 3),
                                          "n_nulled": int(df.loc[m, col].notna().sum())})
            df.loc[m, col] = np.nan
        # 1. remaining isolated out-of-range values.
        bad = df[col].notna() & ~df[col].between(lo, hi)
        report["range_nulled"][col] = int(bad.sum())
        df.loc[bad, col] = np.nan

    # 4. duplicates
    key = ["station_id", "ts"]
    dup_any = df.duplicated(key, keep=False)
    exact = df.duplicated(key + CANONICAL, keep="first")
    df = df[~exact]
    conflicts = df.duplicated(key, keep=False)
    report["duplicates"] = {"rows_in_duplicate_keys": int(dup_any.sum()),
                            "exact_dropped": int(exact.sum()),
                            "conflicting_keys": int(df[conflicts].drop_duplicates(key).shape[0])}
    order = {"2012-2021": 0, "2022": 1, "2023": 2, "2024": 3}
    df = (df.assign(_o=df["source_file"].map(order)).sort_values(key + ["_o"])
            .drop_duplicates(key, keep="last").drop(columns="_o"))

    # 3. stuck sensors, per station in time order
    df = df.sort_values(key).reset_index(drop=True)
    for col in ("pm25", "pm10"):
        m = df.groupby("station_id", group_keys=False)[col].apply(lambda s: _stuck_mask(s, STUCK_HOURS))
        report["stuck_nulled"][col] = int(m.sum())
        df.loc[m, col] = np.nan

    return df.drop(columns="year"), report


def to_hourly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex each station onto a complete hourly index (missing hours = NaN rows)."""
    out = []
    for sid, g in df.groupby("station_id"):
        idx = pd.date_range(g["ts"].min(), g["ts"].max(), freq="h", name="ts")
        g = g.set_index("ts").reindex(idx)
        g["station_id"] = sid
        out.append(g.reset_index())
    return pd.concat(out, ignore_index=True)

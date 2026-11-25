"""Baselines, gradient-boosted trees, intervals and evaluation.

Splits are chronological on issue time t; the target time t+h of the last
training row may fall a few hours into validation, so we also drop rows whose
*target* crosses a split boundary (purge), which removes any overlap.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from .features import HORIZONS, POLLUTANTS, feature_columns

TRAIN_END = pd.Timestamp("2023-01-01 00:00")
VAL_END = pd.Timestamp("2024-01-01 00:00")
TEST_END = pd.Timestamp("2025-01-01 00:00")
QUANTILES = (0.1, 0.9)  # 80% interval


def split(df: pd.DataFrame) -> dict:
    tgt = df["ts"] + pd.to_timedelta(df["horizon"], unit="h")
    return {
        "train": df[(tgt <= TRAIN_END)],
        "val": df[(df["ts"] >= TRAIN_END) & (tgt <= VAL_END)],
        "test": df[(df["ts"] >= VAL_END) & (tgt <= TEST_END)],
    }


def usable(df: pd.DataFrame, pol: str) -> pd.DataFrame:
    """Rows where a forecast would be issued (fresh reading) and the target exists."""
    return df[df[f"{pol}_last"].notna() & df[f"y_{pol}"].notna()]


def metrics(y: np.ndarray, p: np.ndarray, p_persist: np.ndarray | None = None,
            naive_scale: float | None = None) -> dict:
    e = p - y
    out = {"n": int(len(y)), "mae": float(np.mean(np.abs(e))), "rmse": float(np.sqrt(np.mean(e ** 2))),
           "r2": float(1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2)), "bias": float(np.mean(e))}
    if p_persist is not None:
        out["skill_vs_persistence"] = float(1 - out["mae"] / np.mean(np.abs(p_persist - y)))
    if naive_scale:
        out["mase"] = float(out["mae"] / naive_scale)
    return out


@dataclass
class TreeConfig:
    learning_rate: float = 0.05
    num_leaves: int = 127
    min_data_in_leaf: int = 200
    feature_fraction: float = 0.8
    bagging_fraction: float = 0.8
    bagging_freq: int = 1
    lambda_l2: float = 1.0
    num_boost_round: int = 4000
    early_stopping: int = 150


def fit_lgb(tr: pd.DataFrame, va: pd.DataFrame, cols: list, pol: str, cfg: TreeConfig,
            objective: str = "l2", alpha: float | None = None, log_target: bool = True):
    ytr, yva = tr[f"y_{pol}"].values, va[f"y_{pol}"].values
    if log_target:
        ytr, yva = np.log1p(ytr), np.log1p(yva)
    params = {"objective": objective, "learning_rate": cfg.learning_rate, "num_leaves": cfg.num_leaves,
              "min_data_in_leaf": cfg.min_data_in_leaf, "feature_fraction": cfg.feature_fraction,
              "bagging_fraction": cfg.bagging_fraction, "bagging_freq": cfg.bagging_freq,
              "lambda_l2": cfg.lambda_l2, "verbosity": -1, "seed": 7, "num_threads": 0}
    if alpha is not None:
        params["alpha"] = alpha
    dtr = lgb.Dataset(tr[cols], ytr, categorical_feature=[c for c in cols if c == "station_id"])
    dva = lgb.Dataset(va[cols], yva, reference=dtr)
    m = lgb.train(params, dtr, cfg.num_boost_round, valid_sets=[dva],
                  callbacks=[lgb.early_stopping(cfg.early_stopping, verbose=False), lgb.log_evaluation(0)])
    return m


def predict(m, df, cols, log_target=True):
    p = m.predict(df[cols], num_iteration=m.best_iteration)
    return np.clip(np.expm1(p) if log_target else p, 0, None)


def conformal_offset(lo, hi, y, coverage=0.8) -> float:
    """CQR: widen [lo, hi] by the quantile of non-conformity scores on validation."""
    s = np.maximum(lo - y, y - hi)
    n = len(s)
    return float(np.quantile(s, min(1.0, np.ceil((n + 1) * coverage) / n)))


def naive_scales(train: pd.DataFrame) -> dict:
    """In-sample MAE of persistence on the training split, per pollutant/horizon (MASE denominator)."""
    out = {}
    for pol in POLLUTANTS:
        u = usable(train, pol)
        for h in HORIZONS:
            uh = u[u.horizon == h]
            out[(pol, h)] = float(np.mean(np.abs(uh[f"{pol}_last"] - uh[f"y_{pol}"])))
    return out


def run_chronological(df: pd.DataFrame, out_dir: Path, cfg: TreeConfig = TreeConfig(),
                      variants=("now_weather", "tgt_weather"), log=print) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sp = split(df)
    scales = naive_scales(sp["train"])
    results, preds = [], []
    for pol in POLLUTANTS:
        tr, va, te = (usable(sp[k], pol) for k in ("train", "val", "test"))
        for variant in variants:
            cols = feature_columns(df, use_tgt_weather=(variant == "tgt_weather"))
            log(f"[{pol}/{variant}] train={len(tr):,} val={len(va):,} test={len(te):,} features={len(cols)}")
            m = fit_lgb(tr, va, cols, pol, cfg)
            m.save_model(str(out_dir / f"lgb_{pol}_{variant}.txt"), num_iteration=m.best_iteration)
            q = {a: fit_lgb(tr, va, cols, pol, cfg, objective="quantile", alpha=a) for a in QUANTILES}
            for a, qm in q.items():
                qm.save_model(str(out_dir / f"lgb_{pol}_{variant}_q{int(a*100)}.txt"), num_iteration=qm.best_iteration)
            for h in HORIZONS:
                vh, th = va[va.horizon == h], te[te.horizon == h]
                lo_v, hi_v = predict(q[0.1], vh, cols), predict(q[0.9], vh, cols)
                off = conformal_offset(lo_v, hi_v, vh[f"y_{pol}"].values)
                y = th[f"y_{pol}"].values
                p = predict(m, th, cols)
                persist = th[f"{pol}_last"].values
                seas = th[f"{pol}_sameh_yday"].values
                lo = np.clip(predict(q[0.1], th, cols) - off, 0, None)
                hi = predict(q[0.9], th, cols) + off
                base = {"pollutant": pol, "horizon": h, "split": "test"}
                results.append({**base, "model": "persistence", **metrics(y, persist, persist, scales[(pol, h)])})
                ok = ~np.isnan(seas)
                results.append({**base, "model": "seasonal_naive_24h",
                                **metrics(y[ok], seas[ok], persist[ok], scales[(pol, h)]),
                                "note": "rows with a same-hour-yesterday value"})
                r = {**base, "model": f"lightgbm_{variant}", **metrics(y, p, persist, scales[(pol, h)]),
                     "interval80_coverage": float(np.mean((y >= lo) & (y <= hi))),
                     "interval80_median_width": float(np.median(hi - lo)),
                     "conformal_offset": off, "best_iteration": int(m.best_iteration)}
                results.append(r)
                log(f"  h={h} MAE persist={results[-3]['mae']:.2f} lgb={r['mae']:.2f} "
                    f"skill={r['skill_vs_persistence']:.3f} cov80={r['interval80_coverage']:.3f}")
                preds.append(pd.DataFrame({"station_id": th.station_id.values, "ts": th.ts.values,
                                           "pollutant": pol, "horizon": h, "variant": variant, "y": y,
                                           "pred": p, "lo80": lo, "hi80": hi, "persistence": persist}))
            imp = pd.Series(m.feature_importance("gain"), index=cols).sort_values(ascending=False)
            imp.head(30).to_csv(out_dir / f"importance_{pol}_{variant}.csv")
    pr = pd.concat(preds, ignore_index=True)
    pr.to_parquet(out_dir / "test_predictions_lgb.parquet", index=False)
    return {"overall": results, "per_station": per_station(pr)}


def per_station(pr: pd.DataFrame) -> list:
    rows = []
    for (sid, pol, h, var), g in pr.groupby(["station_id", "pollutant", "horizon", "variant"], observed=True):
        rows.append({"station_id": sid, "pollutant": pol, "horizon": int(h), "variant": var, "n": len(g),
                     "mae": float(np.mean(np.abs(g.pred - g.y))),
                     "mae_persistence": float(np.mean(np.abs(g.persistence - g.y))),
                     "rmse": float(np.sqrt(np.mean((g.pred - g.y) ** 2)))})
    return rows


def run_leave_station_out(df: pd.DataFrame, holdout: list, cfg: TreeConfig = TreeConfig(),
                          variant: str = "tgt_weather", log=print) -> list:
    """Train without the held-out station (and without station_id), test on it in 2024."""
    sp = split(df)
    cols = feature_columns(df, use_tgt_weather=(variant == "tgt_weather"), use_station=False)
    rows = []
    for sid in holdout:
        for pol in POLLUTANTS:
            tr = usable(sp["train"][sp["train"].station_id != sid], pol)
            va = usable(sp["val"][sp["val"].station_id != sid], pol)
            te = usable(sp["test"][sp["test"].station_id == sid], pol)
            if len(te) < 500:
                log(f"skip {sid}/{pol}: only {len(te)} test rows")
                continue
            m = fit_lgb(tr, va, cols, pol, cfg)
            for h in HORIZONS:
                th = te[te.horizon == h]
                y, p, persist = th[f"y_{pol}"].values, predict(m, th, cols), th[f"{pol}_last"].values
                rows.append({"held_out_station": sid, "pollutant": pol, "horizon": h, "variant": variant,
                             **metrics(y, p, persist)})
                log(f"LOSO {sid} {pol} h={h} MAE={rows[-1]['mae']:.2f} skill={rows[-1]['skill_vs_persistence']:.3f}")
    return rows


def save_json(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, indent=1, default=str))

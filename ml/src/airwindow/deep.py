"""GRU forecaster: past 48 h sequence -> PM2.5/PM10 at +1/+3/+6 h in one pass.

Inputs per hour: log1p PM2.5/PM10 (scaled), their missing masks, weather at that
hour, hour-of-day. Optional decoder vector: weather at each target hour (the
"forecast weather" variant). The scaler is fitted on the training split only.
Windows are gathered on the device from one contiguous array, so nothing is
materialised per sample. Missing targets are masked out of the loss.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from .features import HORIZONS, MAX_OBS_AGE_H, POLLUTANTS, WEATHER
from .train import TEST_END, TRAIN_END, VAL_END, metrics

SEQ = 48
SEQ_FEATS = ["pm25_l", "pm10_l", "pm25_m", "pm10_m", *WEATHER, "hour_sin", "hour_cos"]
TGT_W = ["w_temp", "w_rh", "w_ws", "w_rain", "w_blh"]


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():  # Apple-silicon GPU
        return torch.device("mps")
    return torch.device("cpu")


class GRUForecaster(nn.Module):
    def __init__(self, n_in, n_stations, n_tgt_w, hidden=128, layers=2, emb=8, dropout=0.1):
        super().__init__()
        self.emb = nn.Embedding(n_stations, emb)
        self.gru = nn.GRU(n_in, hidden, layers, batch_first=True, dropout=dropout)
        self.head = nn.Sequential(nn.Linear(hidden + emb + n_tgt_w, 128), nn.GELU(), nn.Dropout(dropout),
                                  nn.Linear(128, len(POLLUTANTS) * len(HORIZONS)))

    def forward(self, x, sid, tw):
        _, h = self.gru(x)
        z = torch.cat([h[-1], self.emb(sid), tw], dim=1)
        return self.head(z)


def prepare(hourly: pd.DataFrame, weather: pd.DataFrame, use_tgt_weather: bool):
    """Concatenate all stations into one array; return arrays + sample index table."""
    st_ids = sorted(hourly.station_id.unique())
    sid_map = {s: i for i, s in enumerate(st_ids)}
    parts, samples, off = [], [], 0
    for sid in st_ids:
        g = hourly[hourly.station_id == sid].sort_values("ts").reset_index(drop=True)
        w = weather[weather.station_id == sid].set_index("ts").reindex(g.ts).reset_index(drop=True)
        a = pd.DataFrame({"ts": g.ts})
        for p in POLLUTANTS:
            a[f"{p}_l"] = np.log1p(g[p])
            a[f"{p}_m"] = g[p].isna().astype(float)
            a[f"y_{p}"] = g[p]
        for c in WEATHER:
            a[c] = w[c].values
        a["hour_sin"], a["hour_cos"] = np.sin(2 * np.pi * g.ts.dt.hour / 24), np.cos(2 * np.pi * g.ts.dt.hour / 24)
        n = len(a)
        # sample = issue index i with i >= SEQ-1 and i + max(h) < n
        i = np.arange(SEQ - 1, n - max(HORIZONS))
        fresh = {}
        for p in POLLUTANTS:
            last_valid = pd.Series(np.where(g[p].notna(), np.arange(n), np.nan)).ffill().values
            fresh[p] = (np.arange(n) - last_valid) <= MAX_OBS_AGE_H
        s = pd.DataFrame({"row": i + off, "local": i, "ts": a.ts.values[i], "sid": sid_map[sid],
                          "fresh_pm25": fresh["pm25"][i], "fresh_pm10": fresh["pm10"][i]})
        samples.append(s)
        a["station_id"] = sid
        parts.append(a)
        off += n
    arr = pd.concat(parts, ignore_index=True)
    smp = pd.concat(samples, ignore_index=True)
    return arr, smp, st_ids


class Data:
    def __init__(self, arr: pd.DataFrame, device, use_tgt_weather):
        tr_hours = arr[arr.ts < TRAIN_END]  # scaler sees training-period hours only
        self.mu = tr_hours[SEQ_FEATS].mean().values
        self.sd = tr_hours[SEQ_FEATS].std().replace(0, 1).values
        x = (arr[SEQ_FEATS].values - self.mu) / self.sd
        self.x = torch.tensor(np.nan_to_num(x, nan=0.0), dtype=torch.float32, device=device)
        y = np.stack([np.log1p(arr[f"y_{p}"].values) for p in POLLUTANTS], 1)
        self.y = torch.tensor(y, dtype=torch.float32, device=device)  # NaN where missing
        self.use_tw = use_tgt_weather
        tw_idx = [SEQ_FEATS.index(c) for c in TGT_W]
        self.tw_cols = torch.tensor(tw_idx, device=device)
        self.device = device
        self.hz = torch.tensor(HORIZONS, device=device)
        self.back = torch.arange(SEQ - 1, -1, -1, device=device)

    def batch(self, rows: np.ndarray, sids: np.ndarray):
        r = torch.as_tensor(rows, device=self.device)
        xb = self.x[r[:, None] - self.back[None, :]]            # B x SEQ x F
        tgt = r[:, None] + self.hz[None, :]                       # B x H
        yb = self.y[tgt]                                          # B x H x P
        yb = yb.permute(0, 2, 1).reshape(len(rows), -1)           # B x (P*H), pol-major
        if self.use_tw:
            tw = self.x[tgt][:, :, self.tw_cols].reshape(len(rows), -1)
        else:
            tw = torch.zeros(len(rows), 0, device=self.device)
        return xb, torch.as_tensor(sids, device=self.device), tw, yb


def train_gru(hourly, weather, use_tgt_weather=True, epochs=12, batch=2048, lr=2e-3, log=print, seed=7):
    torch.manual_seed(seed)
    np.random.seed(seed)
    dev = pick_device()
    arr, smp, st_ids = prepare(hourly, weather, use_tgt_weather)
    tgt_end = smp.ts + pd.Timedelta(hours=max(HORIZONS))
    fresh_any = smp.fresh_pm25 | smp.fresh_pm10
    m_tr = (tgt_end <= TRAIN_END) & fresh_any
    m_va = (smp.ts >= TRAIN_END) & (tgt_end <= VAL_END) & fresh_any
    m_te = (smp.ts >= VAL_END) & (tgt_end <= TEST_END)
    d = Data(arr, dev, use_tgt_weather)
    n_tw = len(TGT_W) * len(HORIZONS) if use_tgt_weather else 0
    model = GRUForecaster(len(SEQ_FEATS), len(st_ids), n_tw).to(dev)
    with torch.no_grad():  # start at the training mean (log space) instead of 0
        y_tr = d.y[torch.as_tensor(smp.row.values[m_tr.values], device=dev)]
        model.head[-1].bias.copy_(torch.nanmean(y_tr, 0).repeat_interleave(len(HORIZONS)))
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    tr_rows, tr_sid = smp.row.values[m_tr], smp.sid.values[m_tr]
    va_rows, va_sid = smp.row.values[m_va], smp.sid.values[m_va]
    steps = epochs * int(np.ceil(len(tr_rows) / batch))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps)
    lossf = nn.HuberLoss(reduction="none", delta=0.5)

    def masked(pred, yb):
        m = ~torch.isnan(yb)
        return (lossf(pred, torch.nan_to_num(yb)) * m).sum() / m.sum().clamp(min=1)

    best, best_state, hist = 1e9, None, []
    for ep in range(epochs):
        model.train()
        t0 = time.time()
        perm = np.random.permutation(len(tr_rows))
        tot = 0.0
        for k in range(0, len(perm), batch):
            j = perm[k:k + batch]
            xb, sb, tw, yb = d.batch(tr_rows[j], tr_sid[j])
            loss = masked(model(xb, sb, tw), yb)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item() * len(j)
        vl = evaluate_loss(model, d, va_rows, va_sid, masked)
        hist.append({"epoch": ep + 1, "train_loss": tot / len(perm), "val_loss": vl, "sec": time.time() - t0})
        log(f"epoch {ep+1} train={tot/len(perm):.4f} val={vl:.4f} ({time.time()-t0:.0f}s)")
        if vl < best:
            best, best_state = vl, {k: v.detach().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return model, d, arr, smp, m_te.values, st_ids, hist


@torch.no_grad()
def evaluate_loss(model, d, rows, sids, masked, batch=8192):
    model.eval()
    tot, n = 0.0, 0
    for k in range(0, len(rows), batch):
        xb, sb, tw, yb = d.batch(rows[k:k + batch], sids[k:k + batch])
        tot += masked(model(xb, sb, tw), yb).item() * len(xb)
        n += len(xb)
    return tot / max(n, 1)


@torch.no_grad()
def predict_test(model, d, arr, smp, m_te, batch=8192):
    model.eval()
    rows, sids = smp.row.values[m_te], smp.sid.values[m_te]
    out = []
    for k in range(0, len(rows), batch):
        xb, sb, tw, _ = d.batch(rows[k:k + batch], sids[k:k + batch])
        out.append(torch.expm1(model(xb, sb, tw)).clamp(min=0).cpu().numpy())
    P = np.concatenate(out)
    recs = []
    for pi, pol in enumerate(POLLUTANTS):
        for hi, h in enumerate(HORIZONS):
            recs.append(pd.DataFrame({"row": rows, "pollutant": pol, "horizon": h,
                                      "pred": P[:, pi * len(HORIZONS) + hi]}))
    return pd.concat(recs, ignore_index=True)


def score_against(pred_gru: pd.DataFrame, smp: pd.DataFrame, arr: pd.DataFrame, lgb_test: pd.DataFrame,
                  variant: str) -> list:
    """Score GRU on exactly the rows the tree models were scored on (same station, ts, horizon)."""
    key = smp[["row", "ts"]].assign(station_id=arr.station_id.values[smp.row.values])
    g = pred_gru.merge(key, on="row")
    ref = lgb_test[lgb_test.variant == variant][["station_id", "ts", "pollutant", "horizon", "y", "persistence"]]
    m = ref.merge(g[["station_id", "ts", "pollutant", "horizon", "pred"]],
                  on=["station_id", "ts", "pollutant", "horizon"], how="inner")
    res = []
    for (pol, h), x in m.groupby(["pollutant", "horizon"]):
        res.append({"pollutant": pol, "horizon": int(h), "split": "test", "model": f"gru_{variant}",
                    **metrics(x.y.values, x.pred.values, x.persistence.values)})
    return res, m

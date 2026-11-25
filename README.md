# AirWindow BD

**Choose a better time to be outdoors in Bangladesh, using measured air quality and short-term PM2.5 / PM10 forecasts.**

AirWindow shows the latest measured PM2.5/PM10 near you, forecasts the next 1, 3 and 6 hours, and ranks those hours so you can pick a relatively lower-pollution time for a walk, exercise, a commute or the school run. It is bilingual (বাংলা / English), works without an account, and is honest about what it doesn't know: old data is labelled, missing data is shown as missing, and forecasts come with ranges.

Three clients share one Python API and one set of trained models:

| Client | Stack | Where |
|---|---|---|
| Mobile web app (PWA) + desktop web | Next.js 15, TypeScript, Tailwind | `apps/web` |
| Android app | Kotlin, Jetpack Compose (Material 3, One UI-style) | `apps/android` |
| API | Python, FastAPI | `services/api` |
| Data + models | pandas, LightGBM, PyTorch | `ml/` |

> ⚠️ AirWindow does not give medical advice and a lower forecast is not a guarantee of safe air. During severe pollution, follow official public-health advisories.

## Results

<!-- RESULTS:START -->
- **PM2.5, served model:** 6-hour-ahead error (MAE) **35.8 µg/m³** vs 53.7 for "no change" (33% lower); 3 h: 32.0 vs 42.4; 1 h: 25.0 vs 25.5. 80% ranges contained the true value 78% of the time at 6 h.
- **PM10, served model:** 6-hour-ahead error (MAE) **44.9 µg/m³** vs 68.6 for "no change" (34% lower); 3 h: 39.4 vs 50.5; 1 h: 26.9 vs 26.7. 80% ranges contained the true value 80% of the time at 6 h.

### PM2.5 — test year 2024 (never used for training or model choice)

| Model | +1 h MAE | +3 h MAE | +6 h MAE | +6 h RMSE | +6 h R² | +6 h skill vs persistence | 80% interval coverage (+1/+3/+6 h) |
|---|---:|---:|---:|---:|---:|---:|---|
| Persistence (last value) | 25.5 | 42.4 | 53.7 | 139.7 | -0.351 | 0% | – |
| Seasonal naive (same hour yesterday) | 48.3 | 48.2 | 48.2 | 130.6 | -0.258 | 7% | – |
| LightGBM, weather at issue time | 24.3 | 31.2 | 34.8 | 104.8 | 0.241 | 35% | 0.78 / 0.79 / 0.79 |
| LightGBM, + target-hour weather (ERA5 proxy) **(served)** | 25.0 | 32.0 | 35.8 | 104.8 | 0.241 | 33% | 0.78 / 0.78 / 0.78 |
| GRU, weather at issue time | 24.2 | 31.7 | 35.2 | 106.6 | 0.214 | 34% | – |
| GRU, + target-hour weather (ERA5 proxy) | 24.3 | 32.0 | 36.1 | 107.7 | 0.197 | 33% | – |

MAE/RMSE in µg/m³. n = 106,184 station-hours at +6 h.

### PM10 — test year 2024 (never used for training or model choice)

| Model | +1 h MAE | +3 h MAE | +6 h MAE | +6 h RMSE | +6 h R² | +6 h skill vs persistence | 80% interval coverage (+1/+3/+6 h) |
|---|---:|---:|---:|---:|---:|---:|---|
| Persistence (last value) | 26.7 | 50.5 | 68.6 | 131.6 | 0.026 | 0% | – |
| Seasonal naive (same hour yesterday) | 57.8 | 57.8 | 57.9 | 115.0 | 0.251 | 16% | – |
| LightGBM, weather at issue time | 26.1 | 38.2 | 43.4 | 86.5 | 0.580 | 37% | 0.80 / 0.80 / 0.81 |
| LightGBM, + target-hour weather (ERA5 proxy) **(served)** | 26.9 | 39.4 | 44.9 | 87.0 | 0.574 | 34% | 0.81 / 0.81 / 0.80 |
| GRU, weather at issue time | 25.3 | 38.1 | 43.2 | 89.5 | 0.549 | 37% | – |
| GRU, + target-hour weather (ERA5 proxy) | 25.6 | 39.2 | 44.8 | 93.4 | 0.510 | 35% | – |

MAE/RMSE in µg/m³. n = 87,758 station-hours at +6 h.

### Unseen-station test (station left out of training, scored on its 2024 data)

| Held-out station | Pollutant | +1 h MAE | +3 h MAE | +6 h MAE | +6 h skill vs persistence |
|---|---|---:|---:|---:|---:|
| dhk_darussalam | PM2.5 | 22.2 | 29.0 | 31.9 | 30% |
| dhk_darussalam | PM10 | 31.4 | 42.9 | 47.7 | 29% |
| ctg_agrabad | PM2.5 | 16.4 | 22.1 | 24.2 | 28% |
| ctg_agrabad | PM10 | 26.6 | 36.4 | 40.2 | 22% |
| sylhet | PM2.5 | 36.5 | 43.9 | 48.1 | 34% |
| sylhet | PM10 | 47.2 | 60.2 | 65.0 | 37% |
| rajshahi | PM2.5 | 17.4 | 26.1 | 30.7 | 35% |
| rajshahi | PM10 | 26.3 | 42.4 | 51.2 | 43% |
| khulna | PM2.5 | 13.1 | 19.7 | 23.3 | 29% |
| khulna | PM10 | 18.2 | 30.3 | 36.5 | 41% |

### Variant choice (validation year 2023 only)

| Pollutant | Variant | +1 h MAE | +3 h MAE | +6 h MAE |
|---|---|---:|---:|---:|
| PM2.5 | now_weather | 14.2 | 21.2 | 25.1 |
| PM2.5 | tgt_weather | 14.2 | 21.1 | 24.7 |
| PM10 | now_weather | 24.0 | 35.8 | 41.8 |
| PM10 | tgt_weather | 24.2 | 35.6 | 40.9 |


**Reading these results honestly**

- **Where it helps:** forecasting is most useful at **3–6 hours**, cutting error by about a third compared with "no change". At **1 hour the models are no better than the latest measurement** (served PM10 is marginally worse), so the app's value is in the next few hours, not the next one.
- **Variant choice:** the served variant (weather at the target hour) was picked on the 2023 validation year, where it was slightly better. On the 2024 test year it is slightly *worse* than the simpler variant (PM2.5 6 h: 35.8 vs 34.8). We report this rather than switch after seeing test results. Both variants are within a few percent, and live weather *forecasts* are noisier than the ERA5 reanalysis used in training, so treat the target-weather rows as optimistic.
- **Metric choice:** R² for PM2.5 is low (≈0.24) because a few extreme pollution spikes dominate squared error; MAE is the primary metric.
- **GRU vs LightGBM:** the GRU (Apple M4 GPU) is on par with LightGBM: slightly better at 1 h, slightly worse at 6 h for PM2.5. It is scored on the same test rows, minus 182 of 587k that lack the 48 h of history it needs. LightGBM is served because it is smaller, faster and comes with calibrated intervals.
- **Unseen stations:** models trained without a station still beat persistence there by 22–43% at 6 h, so the approach transfers to stations not seen in training.
- **Reproducibility:** every number above is generated from `ml/artifacts/metrics.json` by `python -m airwindow.report`, and was independently re-computed from the saved raw test predictions (`test_predictions_lgb.parquet`) before publishing.
- **Training runs:**
  - Trees: [Kaggle notebook (CPU)](https://www.kaggle.com/code/rashidazraf/airwindow-bd-trees-cpu), with the same code as `ml/notebooks/airwindow_bd_trees_cpu.ipynb`.
  - GRU: `python -m airwindow.run_gru` on Apple MPS.

<!-- RESULTS:END -->

## Data

- **Training:** [CAMS-BD](https://data.mendeley.com/datasets/hwmzyh5w4w/1) (doi:10.17632/hwmzyh5w4w.1, CC BY 4.0): hourly pollutant and weather records from Bangladesh Department of Environment Continuous Air Monitoring Stations, Nov 2012 – Jan 2025. It is **historical**; the app never shows it as current.
- **Weather:** [Open-Meteo](https://open-meteo.com/) ERA5 archive (training) and forecast API (live).
- **Live readings (optional):** [OpenAQ v3](https://docs.openaq.org/). Without a key, the app runs in a clearly labelled historical-replay demo mode.
- **AQI:** bands, names and colours from the DoE "AQI Scheme for Bangladesh" ([source PDF](docs/sources/DoE_daily_AQI_report_2026-06-05.pdf), p.2). DoE does not publish its µg/m³ breakpoints there, so concentrations are converted with the US EPA 2024 breakpoints (the bands are identical) on 24-hour means, and only when at least 18 of the last 24 hours were measured. WHO 2021 24-hour guideline: PM2.5 15 µg/m³, PM10 45 µg/m³.

The source workbooks needed real repair work. The full report is in [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md):

- **Date repair:** in the 2012–2021 workbook, Excel had swapped day and month on every date with day ≤ 12. About 26.7k timestamps were recovered by decoding each station's hourly sequence. Seasonality checks confirm the fix: every year shows the expected winter peak and monsoon low.
- **Savar columns:** the Savar block's header swaps solar radiation and pressure, so columns are mapped per block.
- **Excluded blocks:** five 2012–2021 station blocks (Khulna, Rajshahi, Sangsad, Narsingdi, Rangpur) have **no dates at all**. They are excluded rather than guessed from row position.
- **Impossible values:** out-of-range values are removed, and station-year columns that are mostly impossible (shifted or mislabelled meteorology) are quarantined. Stuck sensors (six or more identical PM hours in a row) are removed. Nothing is ever filled in.

## Method

- **Task:** at issue hour *t*, forecast PM2.5 and PM10 at *t*+1, *t*+3 and *t*+6 h, using only information available at *t*: recent lags, past-only rolling statistics, calendar, station, and weather.
- **Split:** chronological on issue time, with no row shuffling. Train on targets ≤ 2023-01-01, validate on 2023, **test on all of 2024**. Rows whose target crosses a boundary are purged. The 2024 test set is used once, for reporting; model and variant choices use 2023 only.
- **Models:**
  - Baselines: persistence and seasonal-naive (same hour yesterday).
  - LightGBM on log-PM, plus q10/q90 quantile models widened by a split-conformal offset from validation, giving a nominal 80% interval.
  - A GRU over the past 48 h. It was trained on an Apple M4 GPU (MPS) because the Kaggle T4 queue stalled.
- **Weather variants:** each model is trained with weather at issue time only, and with weather at the target hour. Target-hour weather uses ERA5 reanalysis as a stand-in for a weather forecast, so it is an **optimistic** upper bound.
- **Station generalisation:** leave-one-station-out runs for five stations. Each is trained without that station and scored on its 2024 data.
- **Reproducibility:** the Kaggle notebook (`ml/notebooks/airwindow_bd_training.ipynb`) is generated from the package source by `ml/notebooks/make_notebook.py`, so the notebook and the code can't drift apart.

## Run it

```bash
# 1. data (downloads CAMS-BD, ~110 MB, and ERA5 weather per station)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ml/src && ../../.venv/bin/python -m airwindow.build_dataset --raw ../../data/raw/CAMS-BD --out ../../data/processed --weather

# 2. API (port 8010) — replay mode unless services/api/.env has OPENAQ_API_KEY
cd services/api && ../../.venv/bin/uvicorn app.main:app --port 8010

# 3. web (port 3010)
cd apps/web && npm install && npm run dev -- -p 3010

# 4. Android (emulator reaches the API at 10.0.2.2:8010)
cd apps/android && ./gradlew assembleDebug   # APK in app/build/outputs/apk/debug/

# tests
.venv/bin/python -m pytest tests -q
```

## License and attribution

Code: MIT. CAMS-BD data © its authors, CC BY 4.0. Weather data by Open-Meteo (CC BY 4.0). Map tiles © OpenStreetMap contributors.

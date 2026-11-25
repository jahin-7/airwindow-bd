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
_Generated from `ml/artifacts/metrics.json` by `python -m airwindow.report`; filled in after the training run is verified._
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

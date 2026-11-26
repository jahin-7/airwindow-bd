# AirWindow BD

An app that helps people in Bangladesh pick a better time to go outside, based on measured air quality and short-term PM2.5 / PM10 forecasts.

It shows the latest PM2.5/PM10 reading near you, forecasts the next 1, 3 and 6 hours, and ranks those hours so you can choose a lower-pollution time for a walk, exercise, a commute or the school run. It works in Bangla and English and doesn't need an account. I tried to keep it upfront about what it doesn't know: old data is labelled as old, missing data is shown as missing, and every forecast comes with a range.

There are three front ends, and they all use the same Python API and the same trained models:

| Part | Stack | Folder |
|---|---|---|
| Web app (mobile + desktop) | Next.js 15, TypeScript, Tailwind | `apps/web` |
| Android app | Kotlin, Jetpack Compose | `apps/android` |
| API | Python, FastAPI | `services/api` |
| Data and models | pandas, LightGBM, PyTorch | `ml/` |

Note: this isn't medical advice, and a lower forecast doesn't mean the air is safe. When pollution is severe, follow the official health advisories.

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
| GRU (Kaggle T4), weather at issue time | 24.1 | 31.6 | 35.3 | 106.8 | 0.210 | 34% | – |
| GRU (Kaggle T4), + target-hour weather (ERA5 proxy) | 24.2 | 31.7 | 36.0 | 107.5 | 0.200 | 33% | – |

MAE/RMSE in µg/m³. n = 106,184 station-hours at +6 h.

### PM10 — test year 2024 (never used for training or model choice)

| Model | +1 h MAE | +3 h MAE | +6 h MAE | +6 h RMSE | +6 h R² | +6 h skill vs persistence | 80% interval coverage (+1/+3/+6 h) |
|---|---:|---:|---:|---:|---:|---:|---|
| Persistence (last value) | 26.7 | 50.5 | 68.6 | 131.6 | 0.026 | 0% | – |
| Seasonal naive (same hour yesterday) | 57.8 | 57.8 | 57.9 | 115.0 | 0.251 | 16% | – |
| LightGBM, weather at issue time | 26.1 | 38.2 | 43.4 | 86.5 | 0.580 | 37% | 0.80 / 0.80 / 0.81 |
| LightGBM, + target-hour weather (ERA5 proxy) **(served)** | 26.9 | 39.4 | 44.9 | 87.0 | 0.574 | 34% | 0.81 / 0.81 / 0.80 |
| GRU (Kaggle T4), weather at issue time | 25.2 | 38.2 | 43.5 | 90.6 | 0.538 | 37% | – |
| GRU (Kaggle T4), + target-hour weather (ERA5 proxy) | 25.4 | 38.4 | 44.3 | 92.6 | 0.519 | 35% | – |

MAE/RMSE in µg/m³. n = 87,758 station-hours at +6 h.

### GRU replication (same code and test rows, different hardware)

| Model | Pollutant | Kaggle T4 MAE +1/+3/+6 h | Apple M4 MAE +1/+3/+6 h |
|---|---|---|---|
| gru_now_weather | PM2.5 | 24.1 / 31.6 / 35.3 | 24.2 / 31.7 / 35.2 |
| gru_now_weather | PM10 | 25.2 / 38.2 / 43.5 | 25.3 / 38.1 / 43.2 |
| gru_tgt_weather | PM2.5 | 24.2 / 31.7 / 36.0 | 24.3 / 32.0 / 36.1 |
| gru_tgt_weather | PM10 | 25.4 / 38.4 / 44.3 | 25.6 / 39.2 / 44.8 |

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


**Notes on the results**

- The forecasts are most useful 3 to 6 hours ahead, where the error is about a third lower than just assuming nothing changes. One hour ahead, the models are basically no better than the latest reading (for PM10 the served model is even a little worse), so the app is really about the next few hours.
- I picked the served variant (the one that also uses weather at the target hour) on the 2023 validation data, where it did slightly better. On the 2024 test data it came out slightly worse than the simpler variant (PM2.5 at 6 h: 35.8 vs 34.8). I left the choice as it was instead of switching after looking at the test results. The two are within a few percent of each other anyway. Training used ERA5 reanalysis for the "future" weather, which is more accurate than a real forecast, so treat those rows as a bit optimistic.
- R² for PM2.5 looks low (about 0.24) because a few extreme pollution spikes dominate the squared error. MAE is the main metric.
- The GRU (trained on a Kaggle T4 GPU) ends up about level with LightGBM: slightly better at 1 h, slightly worse at 6 h. I reran it on my Mac's M4 GPU and got the same numbers within 1–2%, and the two LightGBM runs agreed within 0.02 µg/m³. The app uses LightGBM because it is smaller and faster and gives calibrated ranges.
- When a station is left out of training completely, the model still beats "no change" at that station by 22–43% at 6 h.
- All the numbers above are generated from `ml/artifacts/metrics.json` with `python -m airwindow.report`. I also recomputed them from the saved test predictions to make sure they matched.
- Kaggle notebooks: `ml/notebooks/airwindow_bd_trees_cpu.ipynb` (trees, CPU) and `ml/notebooks/airwindow_bd_training.ipynb` (trees + GRU, T4 GPU). Both are generated from the code in `ml/src`.

<!-- RESULTS:END -->

## Data

- **Training:** [CAMS-BD](https://data.mendeley.com/datasets/hwmzyh5w4w/1) (doi:10.17632/hwmzyh5w4w.1, CC BY 4.0): hourly pollutant and weather records from Bangladesh Department of Environment Continuous Air Monitoring Stations, Nov 2012 – Jan 2025. It is **historical**; the app never shows it as current.
- **Weather:** [Open-Meteo](https://open-meteo.com/) ERA5 archive (training) and forecast API (live).
- **Live readings (optional):** [OpenAQ v3](https://docs.openaq.org/). Without a key, the app runs in a clearly labelled historical-replay demo mode.
  - **Coverage (checked 25 Nov 2026):** 6 of 16 stations have an *active* OpenAQ PM2.5 sensor within 10 km: Dhaka BARC, Darussalam and DoE; Savar; Narayanganj (8 km away); and Khulna. The other 10 show "No current observation available for this area" rather than an estimate.
  - **Sensor choice:** the nearest sensor with a reading in the last 6 hours is used, and reference monitors would be preferred. Every active sensor today is a **low-cost** AirGradient unit; the reference monitors (US Embassy, AirNow) stopped reporting in 2016 and 2025. The apps label these readings as low-cost, because the forecast models were trained on DoE reference monitors and low-cost sensors can read differently.
- **AQI:** bands, names and colours from the DoE "AQI Scheme for Bangladesh" ([source PDF](docs/sources/DoE_daily_AQI_report_2026-06-05.pdf), p.2). DoE does not publish its µg/m³ breakpoints there, so concentrations are converted with the US EPA 2024 breakpoints (the bands are identical) on 24-hour means, and only when at least 18 of the last 24 hours were measured. WHO 2021 24-hour guideline: PM2.5 15 µg/m³, PM10 45 µg/m³.

The raw workbooks needed a fair amount of fixing before they were usable. The full report is in [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md):

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
  - A GRU over the past 48 h, trained on a Kaggle T4 GPU and replicated on an Apple M4 GPU (MPS).
- **Weather variants:** each model is trained with weather at issue time only, and with weather at the target hour. Target-hour weather uses ERA5 reanalysis as a stand-in for a weather forecast, so it is an **optimistic** upper bound.
- **Station generalisation:** leave-one-station-out runs for five stations. Each is trained without that station and scored on its 2024 data.
- The Kaggle notebooks are generated from the package code by `ml/notebooks/make_notebook.py`, so they always match what's in the repo.

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
cd apps/web && npm test
```

### Putting it online

- **API behind a proxy or load balancer:** start it with `uvicorn app.main:app --host 0.0.0.0 --port 8010 --proxy-headers --forwarded-allow-ips=<proxy address>` so it sees each visitor's real address. Without that, the rate limit counts everyone as the one proxy. Set `CORS_ORIGINS` to the website's address.
- **Android release builds** are shrunk with R8 and signed with your upload key from `apps/android/keystore.properties` (copy `keystore.properties.example`; the file and the key are gitignored). Without it they fall back to the debug key, which is fine for testing but can't be uploaded to Play. Build the Play bundle with `cd apps/android && ./gradlew bundleRelease` (output in `app/build/outputs/bundle/release/`).

## License and attribution

Code: MIT. CAMS-BD data © its authors, CC BY 4.0. Weather data by Open-Meteo (CC BY 4.0). Map tiles © OpenStreetMap contributors.

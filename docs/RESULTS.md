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


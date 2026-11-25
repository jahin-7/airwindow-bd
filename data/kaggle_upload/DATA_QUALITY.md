# CAMS-BD data-quality report

Source rows read: **1,373,990** · station-hours kept: **1,102,447** · with PM2.5: **748,036** · with PM10: **721,992**

## Rows dropped while parsing

| Reason | Rows |
|---|---:|
| unparseable_timestamp | 8,794 |
| no_date_column_khulna | 80,352 |
| no_date_column_narsingdi | 17,543 |
| no_date_column_rajshahi | 88,843 |
| no_date_column_rangpur | 17,544 |
| no_date_column_dhk_sangsad | 58,392 |
| unit_rows | 44 |

## Timestamp repairs (2012-2021 workbook)

| Repair | Rows |
|---|---:|
| day_month_swapped | 26,705 |
| out_of_sequence_dropped | 11 |
| sequence_gaps | 17 |

## Station coverage

| Station | First | Last | Hours on grid | PM2.5 present | PM10 present |
|---|---|---|---:|---:|---:|
| barishal | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 63% | 53% |
| ctg_agrabad | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 56% | 67% |
| ctg_tv | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 43% | 47% |
| cumilla | 2020-01-01 01:00:00 | 2025-01-01 00:00:00 | 43,848 | 72% | 58% |
| dhk_barc | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 74% | 63% |
| dhk_darussalam | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 81% | 78% |
| dhk_doe | 2023-01-01 01:00:00 | 2025-01-01 00:00:00 | 17,544 | 83% | 84% |
| gazipur | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 70% | 69% |
| khulna | 2022-01-01 01:00:00 | 2025-01-01 00:00:00 | 26,304 | 80% | 75% |
| mymensingh | 2020-01-01 01:00:00 | 2025-01-01 00:00:00 | 43,848 | 65% | 56% |
| narayanganj | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 70% | 75% |
| narsingdi | 2022-01-01 01:00:00 | 2025-01-01 00:00:00 | 26,304 | 85% | 69% |
| rajshahi | 2022-01-01 01:00:00 | 2025-01-01 00:00:00 | 26,304 | 89% | 68% |
| rangpur | 2022-01-01 01:00:00 | 2025-01-01 00:00:00 | 26,304 | 81% | 69% |
| savar | 2020-01-01 01:00:00 | 2025-01-01 00:00:00 | 43,848 | 74% | 75% |
| sylhet | 2012-11-01 01:00:00 | 2025-01-01 00:00:00 | 106,656 | 61% | 64% |

## Values nulled by physical-range checks

| Column | Values |
|---|---:|
| pm25 | 257 |
| pm10 | 510 |
| so2 | 189 |
| no | 653 |
| no2 | 145 |
| nox | 518 |
| co | 280 |
| o3 | 516 |
| ws | 411 |
| wd | 0 |
| temp | 1,370 |
| rh | 1,717 |
| sr | 92 |
| bp | 2,528 |
| rain | 224 |
| vws | 171 |

Stuck-sensor PM values nulled (≥6 identical consecutive hours): PM2.5 5,922, PM10 3,983.

## Station-year columns quarantined (>20% of values physically impossible)

| Station | Year | Column | Bad fraction | Values nulled |
|---|---:|---|---:|---:|
| narayanganj | 2024 | no2 | 50% | 7,347 |
| dhk_barc | 2020 | wd | 100% | 710 |
| ctg_agrabad | 2020 | temp | 48% | 732 |
| dhk_doe | 2023 | temp | 91% | 3,054 |
| gazipur | 2024 | temp | 36% | 4,118 |
| sylhet | 2024 | temp | 100% | 6,423 |
| ctg_agrabad | 2021 | rh | 39% | 5,928 |
| ctg_tv | 2020 | rh | 100% | 451 |
| cumilla | 2024 | rh | 86% | 8,559 |
| gazipur | 2023 | rh | 94% | 82 |
| gazipur | 2024 | rh | 45% | 3,708 |
| gazipur | 2024 | sr | 31% | 7,633 |
| barishal | 2020 | bp | 100% | 607 |
| barishal | 2021 | bp | 34% | 848 |
| barishal | 2024 | bp | 61% | 7,996 |
| ctg_agrabad | 2020 | bp | 100% | 732 |
| ctg_agrabad | 2024 | bp | 25% | 6,991 |
| ctg_tv | 2012 | bp | 50% | 387 |
| ctg_tv | 2013 | bp | 66% | 4,417 |
| ctg_tv | 2021 | bp | 34% | 4,492 |
| cumilla | 2020 | bp | 100% | 591 |
| dhk_barc | 2012 | bp | 37% | 1,250 |
| dhk_barc | 2013 | bp | 88% | 5,570 |
| dhk_barc | 2021 | bp | 63% | 8,636 |
| dhk_barc | 2023 | bp | 57% | 5,442 |
| dhk_darussalam | 2020 | bp | 100% | 744 |
| dhk_darussalam | 2021 | bp | 100% | 2,961 |
| dhk_doe | 2023 | bp | 100% | 3,054 |
| gazipur | 2023 | bp | 98% | 869 |
| gazipur | 2024 | bp | 100% | 7,639 |
| mymensingh | 2020 | bp | 100% | 744 |
| sylhet | 2012 | bp | 100% | 1,331 |
| sylhet | 2013 | bp | 100% | 6,388 |
| sylhet | 2024 | bp | 100% | 6,423 |
| dhk_doe | 2023 | rain | 100% | 2,923 |
| sylhet | 2024 | rain | 100% | 6,423 |
| cumilla | 2023 | vws | 48% | 1,092 |
| dhk_barc | 2023 | vws | 41% | 1,535 |
| dhk_doe | 2023 | vws | 100% | 3,055 |
| khulna | 2023 | vws | 100% | 3,118 |
| rangpur | 2023 | vws | 36% | 382 |
| sylhet | 2024 | vws | 100% | 6,422 |

Duplicates on (station, hour): {"rows_in_duplicate_keys": 0, "exact_dropped": 0, "conflicting_keys": 0}

PM2.5 > PM10 (physically inconsistent, kept but flagged): 35,082 station-hours.

## Unit labels that differ from the expected unit

| Source | Station | Column | Unit as written |
|---|---|---|---|
| 2022 | dhk_barc | temp | degreC |
| 2022 | barishal | temp | degreC |
| 2022 | ctg_agrabad | no | _ |
| 2022 | ctg_agrabad | temp | degreC |
| 2022 | cumilla | temp | degreC |
| 2022 | dhk_darussalam | no | ug/m3 |
| 2022 | dhk_darussalam | no2 | ug/m3 |
| 2022 | dhk_darussalam | nox | ug/m3 |
| 2022 | dhk_darussalam | temp | degreC |
| 2022 | gazipur | temp | degreC |
| 2022 | khulna | no | ug/m3 |
| 2022 | khulna | no2 | ug/m3 |
| 2022 | khulna | nox | ug/m3 |
| 2022 | khulna | temp | degreC |
| 2022 | mymensingh | temp | degreC |
| 2022 | narayanganj | temp | degreC |
| 2022 | narsingdi | temp | degreC |
| 2022 | rangpur | temp | degreC |
| 2022 | savar | temp | degreC |
| 2022 | sylhet | temp | degreC |
| 2022 | ctg_tv | wd | m/s------- |
| 2022 | ctg_tv | temp | degreC |
| 2023 | dhk_barc | temp | degreC |
| 2023 | barishal | temp | degreC |
| 2023 | ctg_agrabad | no | _ |
| 2023 | ctg_agrabad | temp | degreC |
| 2023 | cumilla | temp | degreC |
| 2023 | dhk_darussalam | no | ug/m3 |
| 2023 | dhk_darussalam | no2 | ug/m3 |
| 2023 | dhk_darussalam | nox | ug/m3 |
| 2023 | dhk_darussalam | temp | degreC |
| 2023 | dhk_doe | temp | degreC |
| 2023 | gazipur | temp | degreC |
| 2023 | khulna | no | ug/m3 |
| 2023 | khulna | no2 | ug/m3 |
| 2023 | khulna | nox | ug/m3 |
| 2023 | khulna | temp | degreC |
| 2023 | mymensingh | temp | degreC |
| 2023 | narayanganj | temp | degreC |
| 2023 | narsingdi | temp | degreC |
| 2023 | rangpur | temp | degreC |
| 2023 | savar | temp | degreC |
| 2023 | sylhet | temp | degreC |
| 2023 | ctg_tv | wd | m/s------- |
| 2023 | ctg_tv | temp | degreC |
| 2024 | dhk_barc | temp | degreC |
| 2024 | barishal | temp | degreC |
| 2024 | ctg_agrabad | no | _ |
| 2024 | ctg_agrabad | temp | degreC |
| 2024 | cumilla | temp | degreC |
| 2024 | dhk_darussalam | no | ug/m3 |
| 2024 | dhk_darussalam | no2 | ug/m3 |
| 2024 | dhk_darussalam | nox | ug/m3 |
| 2024 | dhk_darussalam | temp | degreC |
| 2024 | dhk_doe | temp | degreC |
| 2024 | gazipur | temp | degreC |
| 2024 | khulna | no | ug/m3 |
| 2024 | khulna | no2 | ug/m3 |
| 2024 | khulna | nox | ug/m3 |
| 2024 | khulna | temp | degreC |
| 2024 | mymensingh | temp | degreC |
| 2024 | narsingdi | temp | degreC |
| 2024 | rangpur | temp | degreC |
| 2024 | savar | temp | degreC |
| 2024 | sylhet | temp | degreC |
| 2024 | ctg_tv | wd | m/s------- |
| 2024 | ctg_tv | temp | degreC |

## Notes

- 2012-2021 Khulna: block has no dates (80352 rows); excluded, not reconstructed.
- 2012-2021 Narsingdi: block has no dates (17543 rows); excluded, not reconstructed.
- 2012-2021 Rajshahi: block has no dates (88843 rows); excluded, not reconstructed.
- 2012-2021 Rangpur: block has no dates (17544 rows); excluded, not reconstructed.
- 2012-2021 Sangsad: block has no dates (58392 rows); excluded, not reconstructed.

"""Pollutant concentration -> AQI band, with every number tied to a cited source.

Bands, names and colours: "AQI Scheme for Bangladesh", Department of Environment
daily AQI report (docs/sources/DoE_daily_AQI_report_2026-06-05.pdf, p.2).
DoE does not publish its concentration breakpoints in that report; its bands
match the US EPA index, so concentrations are converted with the US EPA
breakpoints as revised 7 Feb 2024 (PM2.5 annual NAAQS rule). Both are 24-hour
averages: an AQI is only computed when at least MIN_HOURS_24H of the last 24
hourly readings exist; otherwise callers should show the raw concentration.
WHO 2021 Air Quality Guidelines, 24-hour: PM2.5 15 µg/m³, PM10 45 µg/m³.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

MIN_HOURS_24H = 18

# (conc_lo, conc_hi, aqi_lo, aqi_hi); PM2.5 truncated to 0.1, PM10 to integer.
EPA_2024 = {
    "pm25": [(0.0, 9.0, 0, 50), (9.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
             (55.5, 125.4, 151, 200), (125.5, 225.4, 201, 300), (225.5, 325.4, 301, 500)],
    "pm10": [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
             (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)],
}
WHO_2021_24H = {"pm25": 15.0, "pm10": 45.0}


@dataclass(frozen=True)
class Band:
    key: str
    lo: int
    hi: int
    en: str
    bn: str
    color: str


# Bangla names are our translation of the DoE English labels.
BANDS = [
    Band("good", 0, 50, "Good", "ভালো", "#00B050"),
    Band("moderate", 51, 100, "Moderate", "মাঝারি", "#FFFF00"),
    Band("usg", 101, 150, "Unhealthy for Sensitive Group", "সংবেদনশীলদের জন্য অস্বাস্থ্যকর", "#FFC000"),
    Band("unhealthy", 151, 200, "Unhealthy", "অস্বাস্থ্যকর", "#FF0000"),
    Band("very_unhealthy", 201, 300, "Very Unhealthy", "খুবই অস্বাস্থ্যকর", "#7F007F"),
    Band("hazardous", 301, 500, "Hazardous", "বিপজ্জনক", "#7F0000"),
]


def _truncate(pol: str, c: float) -> float:
    return int(c * 10) / 10 if pol == "pm25" else float(int(c))


def aqi(pol: str, conc_24h: float) -> int:
    """US EPA piecewise-linear AQI; values above the top breakpoint cap at 500."""
    c = _truncate(pol, max(conc_24h, 0.0))
    for lo, hi, ilo, ihi in EPA_2024[pol]:
        if c <= hi:
            c = max(c, lo)
            return round((ihi - ilo) / (hi - lo) * (c - lo) + ilo)
    return 500


def band_for(index: int) -> Band:
    for b in BANDS:
        if index <= b.hi:
            return b
    return BANDS[-1]


def aqi_from_hourly(pol: str, last_24h: Sequence[Optional[float]]) -> Optional[dict]:
    vals = [v for v in last_24h if v is not None]
    if len(vals) < MIN_HOURS_24H:
        return None
    mean = sum(vals) / len(vals)
    i = aqi(pol, mean)
    b = band_for(i)
    return {"pollutant": pol, "aqi": i, "band": b.key, "label_en": b.en, "label_bn": b.bn, "color": b.color,
            "mean_24h": round(mean, 1), "hours_used": len(vals),
            "who_multiple": round(mean / WHO_2021_24H[pol], 1),
            "method": "24-h mean, US EPA 2024 breakpoints, DoE Bangladesh bands"}

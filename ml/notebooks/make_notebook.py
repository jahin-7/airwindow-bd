"""Generate the Kaggle notebook from the package source so they never drift.

    python ml/notebooks/make_notebook.py  ->  ml/notebooks/airwindow_bd_training.ipynb
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "src" / "airwindow"
MODULES = ["__init__.py", "parsing.py", "cleaning.py", "stations.py", "weather.py", "features.py",
           "train.py", "deep.py", "run_experiment.py", "build_dataset.py"]


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s}


cells = [md("""# AirWindow BD — PM2.5 / PM10 forecasting (1, 3, 6 h)

Training data: **CAMS-BD** hourly observations from Bangladesh DoE Continuous Air Monitoring Stations
(doi:10.17632/hwmzyh5w4w.1, CC BY 4.0), cleaned by `airwindow.build_dataset` (see `DATA_QUALITY.md`
in the attached dataset), plus **Open-Meteo ERA5** hourly weather at each station.

* Chronological split on issue time: train → targets ≤ 2023-01-01, validation = 2023, **test = 2024 (untouched)**.
* Models: persistence, seasonal-naive (same hour yesterday), LightGBM (point + q10/q90 with conformal
  calibration), GRU (GPU). Each with weather known at issue time, and with weather at the target hour
  (ERA5 as a stand-in for the forecast the app fetches — optimistic, reported separately).
* Leave-one-station-out evaluation for station generalisation.

Attach the dataset containing `cams_bd_hourly.parquet` and `era5_station_weather.parquet`, enable a GPU, then Run All.
""")]
cells.append(code("!mkdir -p /kaggle/working/src/airwindow"))
for m in MODULES:
    p = SRC / m
    body = p.read_text() if p.exists() else ""
    cells.append(code(f"%%writefile /kaggle/working/src/airwindow/{m}\n{body}"))
cells.append(code("""import glob, os, subprocess, sys, json
hits = glob.glob('/kaggle/input/**/cams_bd_hourly.parquet', recursive=True)
assert hits, 'Attach the AirWindow processed dataset (cams_bd_hourly.parquet)'
DATA = os.path.dirname(hits[0]); print('data dir:', DATA, os.listdir(DATA))
import torch, lightgbm; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else '', '| lightgbm', lightgbm.__version__)
!nvidia-smi -L || true"""))
cells.append(code("""%cd /kaggle/working/src
!python -m pytest --version >/dev/null 2>&1 || pip -q install pytest
!python -m airwindow.run_experiment --data {DATA} --out /kaggle/working/artifacts --gru-epochs 12"""))
cells.append(code("""import pandas as pd, json
M = json.load(open('/kaggle/working/artifacts/metrics.json'))
ov = pd.DataFrame(M['overall'] + M.get('gru', []))
cols = ['pollutant','horizon','model','n','mae','rmse','r2','skill_vs_persistence','interval80_coverage','interval80_median_width']
pd.set_option('display.width', 200)
display(ov[[c for c in cols if c in ov]].sort_values(['pollutant','horizon','mae']).round(3))
display(pd.DataFrame(M['leave_station_out']).round(3))"""))
cells.append(code("""import matplotlib.pyplot as plt
pr = pd.read_parquet('/kaggle/working/artifacts/test_predictions_lgb.parquet')
s = pr[(pr.station_id=='dhk_darussalam')&(pr.pollutant=='pm25')&(pr.horizon==3)&(pr.variant=='tgt_weather')]
s = s[(s.ts>='2024-01-10')&(s.ts<'2024-01-24')].sort_values('ts')
fig, ax = plt.subplots(figsize=(13,4))
ax.fill_between(s.ts, s.lo80, s.hi80, alpha=.25, label='80% interval')
ax.plot(s.ts, s.y, 'k.', ms=3, label='observed (t+3h)'); ax.plot(s.ts, s.pred, label='LightGBM forecast')
ax.set_ylabel('PM2.5 µg/m³'); ax.legend(); ax.set_title('Dhaka Darussalam, 3 h ahead, test period (Jan 2024)')
plt.savefig('/kaggle/working/artifacts/example_forecast.png', dpi=120, bbox_inches='tight'); plt.show()"""))
cells.append(code("""!cd /kaggle/working && zip -qr airwindow_artifacts.zip artifacts && ls -la /kaggle/working /kaggle/working/artifacts"""))

def write(cells, name):
    nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    out = ROOT / "ml" / "notebooks" / name
    out.write_text(json.dumps(nb, indent=1))
    print("wrote", out)


write(cells, "airwindow_bd_training.ipynb")
# CPU-only variant (trees, baselines, leave-station-out); starts without waiting for a GPU.
cpu = [dict(c, source=c["source"].replace("--gru-epochs 12", "--no-gru")) for c in cells]
write(cpu, "airwindow_bd_trees_cpu.ipynb")

# nordic-imbalance-basics

Fetch, tidy, and visualize Nordic (SE3/SE4/FI) **imbalance prices & volumes** with hour×weekday patterns and simple deviation-risk views.

> **Why this exists:** Imbalance exposure drives intraday/VPP decisions. This repo cleans Nordic imbalance data (demo for now) and gives fast visuals to decide when to rebid vs accept deviation.

## What’s inside
- `data/` – tidy Parquet extracts (prices/volumes)
- `src/` – small Python CLIs to **fetch** and **plot**
- `reports/` – PNGs + a tiny Markdown stats file
- `notebooks/` – optional EDA later

## Quickstart (Windows, Python 3.10+)
```bat
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt

:: DEMO data (synthetic) for SE3, May 2025
python src\fetch_imbalance.py --area SE3 --start 2025-05-01 --end 2025-05-31 --out data\SE3.parquet --demo

:: Heatmaps + quick stats
python src\make_heatmaps.py --input data\SE3.parquet --out reports

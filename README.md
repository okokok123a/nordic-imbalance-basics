
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

REM DEMO data (synthetic) for SE3, May 2025
python src\fetch_imbalance.py --area SE3 --start 2025-05-01 --end 2025-05-31 --out data\SE3.parquet --demo

REM Heatmaps + quick stats
python src\make_heatmaps.py --input data\SE3.parquet --out reports
```

## Outputs 

**Methods & reproducibility:** see [METHOD.md](METHOD.md) for data sources, steps, assumptions, and checks.

**Quick links:**  
[SE3 weekly report](reports/SE3/weekly_report.md) ·
[SE4 weekly report](reports/SE4/weekly_report.md) ·
[SE3 DA ↔ Imbalance (stats)](reports/SE3/da_vs_imbalance_stats.md) ·
[SE4 − SE3 spread (stats)](reports/SE3_SE4/da_spread_stats.md)

### Heatmaps — SE3 (real data)
<img alt="SE3 real — price" src="reports/SE3/heatmap_price.png" width="480">
<img alt="SE3 real — volume" src="reports/SE3/heatmap_volume.png" width="480">

See quick stats: [reports/SE3/stats.md](reports/SE3/stats.md)

Weekly report (one-pager): [reports/SE3/weekly_report.md](reports/SE3/weekly_report.md)

### Day-ahead price — SE3 · May 2025
<img alt="SE3 DA price — May 2025" src="reports/SE3/da_price.png" width="640">

See quick stats: [reports/SE3/da_price_stats.md](reports/SE3/da_price_stats.md)

<details>
<summary>Demo heatmaps (synthetic, May 2025) — optional</summary>

<img alt="Imbalance price (demo)" src="reports/heatmap_price.png" width="320">
<img alt="Imbalance volume (demo)" src="reports/heatmap_volume.png" width="320">

See quick stats: [reports/stats.md](reports/stats.md)
</details>

### DA price ↔ Imbalance price — SE3 (May 2025)

<img alt="SE3: DA vs Imbalance price — May 2025" src="reports/SE3/da_vs_imbalance.png" width="640">

See quick stats: [reports/SE3/da_vs_imbalance_stats.md](reports/SE3/da_vs_imbalance_stats.md)

### Day-ahead price — SE4 · May 2025
<img alt="SE4 DA price — May 2025" src="reports/SE4/da_price.png" width="640">

See quick stats: [reports/SE4/da_price_stats.md](reports/SE4/da_price_stats.md)

### SE4 − SE3 day-ahead spread — May 2025
<img alt="SE4 − SE3 DA spread — May 2025" src="reports/SE3_SE4/da_spread.png" width="640">

See quick stats: [reports/SE3_SE4/da_spread_stats.md](reports/SE3_SE4/da_spread_stats.md)

Weekly report (one-pager): [reports/SE4/weekly_report.md](reports/SE4/weekly_report.md)

### Rebid vs Accept — SE3 (May 2025)
<img alt="SE3 rebid vs accept — by hour" src="reports/SE3/rebid_accept_by_hour.png" width="640">

See summary: [reports/SE3/rebid_accept_summary.md](reports/SE3/rebid_accept_summary.md)

### IDA Prep Sheet — SE3 (daily)
- CSV: [reports/SE3/ida_prepsheet.csv](reports/SE3/ida_prepsheet.csv)
- One-pager: [reports/SE3/ida_prepsheet.md](reports/SE3/ida_prepsheet.md)

What’s inside: per-day DA/Imbalance means & std, correlation, # of big deviation hours (|Imb−DA| > 50 €/MWh), p95 abs spread, max/min spread.

### Battery-lite DA arbitrage

#### SE3
<img alt="SE3 battery PnL" src="reports/SE3/battery_pnl.png" width="640">

See stats: [reports/SE3/battery_stats.md](reports/SE3/battery_stats.md)

#### SE4
<img alt="SE4 battery PnL" src="reports/SE4/battery_pnl.png" width="640">

Assumptions: 10 MWh cap, 5 MW power, 90% round-trip efficiency; simple DA-only rule; no fees.

See stats: [reports/SE4/battery_stats.md](reports/SE4/battery_stats.md)

**Schedule CSV:** `reports/<ZONE>/battery_schedule.csv` *(coming soon)*


## Using your own CSV (real data)
Convert any CSV to this repo’s schema, then build charts.

**Note:** Change `--area` to your zone (`SE3`/`SE4`/`FI`) to match your data.

```bat
REM 1) Convert CSV -> Parquet
python src\csv_to_parquet.py --csv data\YOUR_FILE.csv --ts-col ts --price-col price_eur_mwh --volume-col imbalance_volume_mwh --area SE3 --out data\SE3_real.parquet

REM 2) Make heatmaps + stats
python src\make_heatmaps.py --input data\SE3_real.parquet --out reports\SE3
```
**Expected columns in CSV:**
- `ts` — timestamp (with or without timezone)
- `price_eur_mwh` — numeric
- `imbalance_volume_mwh` — numeric (± for direction)

---

**Releases:**  
[v0.4.0-demo](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.4.0-demo) ·
[v0.3.0-demo](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.3.0-demo) ·
[v0.2.0-demo](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.2.0-demo) ·
[v0.1.0](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.1.0)


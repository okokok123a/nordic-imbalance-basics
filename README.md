
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
**One-click rebuilds (Windows):**  run [run_all_SE3.bat](run_all_SE3.bat) or [run_all_SE4.bat](run_all_SE4.bat) to regenerate all charts and stats.

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

**Top moves (per day):** [reports/SE3_SE4/spread_monitor.csv](reports/SE3_SE4/spread_monitor.csv) · [summary](reports/SE3_SE4/spread_monitor.md)  
Hourly join parquet: `reports/SE3_SE4/da_spread_hourly.parquet`.

Weekly report (one-pager): [reports/SE4/weekly_report.md](reports/SE4/weekly_report.md)

### Rebid vs Accept — SE3 (May 2025)
<img alt="SE3 rebid vs accept — by hour" src="reports/SE3/rebid_accept_by_hour.png" width="640">

See summary: [reports/SE3/rebid_accept_summary.md](reports/SE3/rebid_accept_summary.md)

### IDA Prep Sheet — SE3 (daily)
- CSV: [reports/SE3/ida_prepsheet.csv](reports/SE3/ida_prepsheet.csv)
- One-pager: [reports/SE3/ida_prepsheet.md](reports/SE3/ida_prepsheet.md)

### IDA Prep Sheet — SE4 (daily)
- CSV: [reports/SE4/ida_prepsheet.csv](reports/SE4/ida_prepsheet.csv)
- One-pager: [reports/SE4/ida_prepsheet.md](reports/SE4/ida_prepsheet.md)

What’s inside: per-day DA/Imbalance means & std, correlation, # of big deviation hours (|Imb−DA| > 50 €/MWh), p95 abs spread, max/min spread.

### Battery-lite DA arbitrage

#### SE3
<img alt="SE3 battery PnL" src="reports/SE3/battery_pnl.png" width="640">

See stats: [reports/SE3/battery_stats.md](reports/SE3/battery_stats.md)

#### SE4
<img alt="SE4 battery PnL" src="reports/SE4/battery_pnl.png" width="640">

Assumptions: 10 MWh cap, 5 MW power, 90% round-trip efficiency; simple DA-only rule; no fees.

See stats: [reports/SE4/battery_stats.md](reports/SE4/battery_stats.md)

**Schedule CSVs:**
- SE3 → [reports/SE3/battery_schedule.csv](reports/SE3/battery_schedule.csv)
- SE4 → [reports/SE4/battery_schedule.csv](reports/SE4/battery_schedule.csv)

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

## ENTSO-E REST API — token & dry-run

**What this does:** fetches day-ahead prices for SE3/SE4 straight from ENTSO-E, saves to Parquet, and (optionally) plots a PNG.

**1) Token (once)**
- In your Transparency Platform account: *My Account Settings → Web API Security Token → Generate new token*.
- Save locally in `.env` (never commit):ENTSOE_TOKEN=YOUR-REAL-TOKEN



**2) Fetch & plot (example window)**
```bat
call .venv\Scripts\activate
python src\fetch_da_entsoe.py --area SE3 --start 2025-05-10 --end 2025-05-13 --out data\DA_SE3_API.parquet
python src\plot_da_api.py --input data\DA_SE3_API.parquet --out reports\SE3\da_price_api.png
```


**3) One-click (Windows)**
```bat
run_all_SE3.bat
run_all_SE4.bat
```

**Dry-run (no token needed)**
Prints the exact endpoint with your token redacted.
```bat
python src\fetch_da_entsoe.py --area SE3 --start 2025-05-10 --end 2025-05-13 --out data\DA_SE3_API.parquet --dry-run
```

**Notes**
- "--end" is exclusive (e.g., 10..13 = 72 hours).
- Times are UTC internally; results are clamped to the area’s local day (Europe/Stockholm). 
- Areas supported now: SE3, SE4 (EICs wired in src/eic_codes.py). FI support can be added later.

---

**Releases:**  

[v0.5.0-demo](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.5.0-demo) ·
[v0.4.0-demo](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.4.0-demo) ·
[v0.3.0-demo](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.3.0-demo) ·
[v0.2.0-demo](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.2.0-demo) ·
[v0.1.0](https://github.com/EmotionalTrader/nordic-imbalance-basics/releases/tag/v0.1.0)



## Secrets / ENTSO-E token

- Copy `.env.example` to `.env` and set your token: `ENTSOE_TOKEN=...`
- `.env` is ignored by git; never commit real tokens.

## Releases

- Latest: https://github.com/EmotionalTrader/nordic-imbalance-basics/releases

## Quickstart: Day-Ahead via ENTSO-E
1. Copy .env.example to .env and set ENTSOE_TOKEN.
2. Fetch demo (SE3, 2 days):
    python src\fetch_da_prices.py --zone SE3 --start 2025-08-15 --end 2025-08-17 --out data\SE3_da_api_demo.parquet
3. Plot:
    python src\plot_da_api.py --input data\SE3_da_api_demo.parquet --out reports\SE3\da_api_demo.png

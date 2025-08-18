@echo off
REM === Optional: ENTSO-E API fetch if token present =========================
REM Load .env into environment (safe when it only has simple KEY=VALUE lines)
if exist ".env" (
  for /f "usebackq delims=" %%x in (".env") do set %%x
)

if defined ENTSOE_TOKEN (
  echo [INFO] ENTSOE_TOKEN found — fetching SE3 DA via ENTSO-E API...
  ".venv\Scripts\python.exe" src\fetch_da_entsoe.py ^
    --area SE3 ^
    --start 2025-05-01 ^
    --end   2025-06-01 ^
    --out   data\DA_SE3_API.parquet
) else (
  echo [INFO] No ENTSOE_TOKEN — skipping ENTSO-E fetch (using existing CSV path).
)
REM ==========================================================================


@echo off
setlocal
call .venv\Scripts\activate

REM --- sanity checks (explain: stop early if files missing)
if not exist data\DA_SE3.parquet echo MISSING data\DA_SE3.parquet & exit /b 1
if not exist data\SE3_real.parquet echo MISSING data\SE3_real.parquet & exit /b 1

REM --- SE3 visuals (explain: rebuild all charts + tables for SE3)
python src\make_heatmaps.py         --input data\SE3_real.parquet --out reports\SE3
python src\plot_da_prices.py        --input data\DA_SE3.parquet   --out reports\SE3 --title "SE3 Day-ahead price - May 2025"
python src\join_da_imbalance.py     --da data\DA_SE3.parquet --imb data\SE3_real.parquet --out reports\SE3 --title "SE3: DA vs Imbalance price - May 2025"
python src\rebid_accept_summary.py  --da data\DA_SE3.parquet --imb data\SE3_real.parquet --out reports\SE3 --title "SE3 Rebid vs Accept - May 2025"
python src\make_ida_prepsheet.py    --da data\DA_SE3.parquet --imb data\SE3_real.parquet --out reports\SE3 --zone SE3 --thr 50 --title "SE3 - IDA Prep Sheet (May 2025)"
python src\battery_da_arbitrage.py  --da data\DA_SE3.parquet --zone SE3 --out reports\SE3 --cap 10 --power 5 --rt 0.90 --title "SE3 Battery-lite DA arbitrage (10MWh/5MW, η=90%)"

echo Done: SE3 reports written to reports\SE3

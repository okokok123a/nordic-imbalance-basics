@echo off
REM === Optional: ENTSO-E API fetch if token present =========================
if exist ".env" (
  for /f "usebackq delims=" %%x in (".env") do set %%x
)

if defined ENTSOE_TOKEN (
  echo [INFO] ENTSOE_TOKEN found — fetching SE4 DA via ENTSO-E API...
  ".venv\Scripts\python.exe" src\fetch_da_entsoe.py ^
    --area SE4 ^
    --start 2025-05-01 ^
    --end   2025-06-01 ^
    --out   data\DA_SE4_API.parquet
) else (
  echo [INFO] No ENTSOE_TOKEN — skipping ENTSO-E fetch (using existing CSV path).
)
REM ==========================================================================


@echo off
setlocal
call .venv\Scripts\activate

REM --- sanity checks
if not exist data\DA_SE4.parquet echo MISSING data\DA_SE4.parquet & exit /b 1
if not exist data\DA_SE3.parquet echo MISSING data\DA_SE3.parquet (needed for spread) & exit /b 1

REM --- SE4 visuals (explain: DA chart, spread, battery)
python src\plot_da_prices.py       --input data\DA_SE4.parquet --out reports\SE4 --title "SE4 Day-ahead price - May 2025"
python src\plot_spread.py          --a data\DA_SE4.parquet --b data\DA_SE3.parquet --out reports\SE3_SE4 --title "SE4 - SE3 DA Spread (May 2025)"
python src\battery_da_arbitrage.py --da data\DA_SE4.parquet --zone SE4 --out reports\SE4 --cap 10 --power 5 --rt 0.90 --title "SE4 Battery-lite DA arbitrage (10MWh/5MW, η=90%)"
python src\spread_monitor.py --a data\DA_SE4.parquet --b data\DA_SE3.parquet --out reports\SE3_SE4 --n 6 --title "SE4−SE3 daily top moves (May 2025)"

echo Done: SE4 reports written to reports\SE4 and reports\SE3_SE4

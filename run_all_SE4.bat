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

echo Done: SE4 reports written to reports\SE4 and reports\SE3_SE4

@echo off
setlocal

REM === Config (demo window) ===
set START=2025-05-10
set END=2025-05-13
set AREA=SE4

set DATA=data\DA_%AREA%_API.parquet
set PLOT=reports\%AREA%\da_price_api.png

mkdir reports\%AREA% 2> NUL

echo Fetching DA via ENTSO-E for %AREA% %START%..%END% ...
python src\fetch_da_entsoe.py --area %AREA% --start %START% --end %END% --out %DATA%
if errorlevel 1 (
  echo Fetch failed. Aborting.
  exit /b 1
)

echo Plotting %AREA% -> %PLOT% ...
python src\plot_da_api.py --input %DATA% --out %PLOT%
if errorlevel 1 (
  echo Plot failed. Aborting.
  exit /b 1
)

echo Done. Wrote:
echo   %DATA%
echo   %PLOT%

endlocal

@echo off
REM ============================================================
REM run_all_SE3.bat — DA + Imbalance (ENTSO-E, token-gated)
REM ============================================================

REM ---------- Day-Ahead via ENTSO-E (API) ----------
setlocal EnableExtensions EnableDelayedExpansion
findstr /c:"ENTSOE_TOKEN=" ".env" >nul 2>&1
if %ERRORLEVEL%==0 (
  set "ZONE=SE3"
  for /f %%A in ('powershell -NoProfile -Command "(Get-Date).ToUniversalTime().AddDays(-2).ToString('yyyy-MM-dd')"') do set "START=%%A"
  for /f %%A in ('powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')"') do set "END=%%A"

  echo [DA] Using ENTSO-E API for !ZONE! from !START! to !END! ...
  python src\fetch_da_entsoe.py --area !ZONE! --start !START! --end !END! --out data\DA_!ZONE!_API_latest.parquet
  if errorlevel 1 goto :eof

  if not exist reports\!ZONE! mkdir reports\!ZONE!
  python src\plot_da_api.py --input data\DA_!ZONE!_API_latest.parquet --out reports\!ZONE!\da_price_api.png
) else (
  echo [DA] ENTSOE_TOKEN not found in .env — skipping ENTSO-E DA fetch for SE3.
)
endlocal

REM ---------- Imbalance via ENTSO-E (A85) ----------
setlocal EnableExtensions EnableDelayedExpansion
findstr /c:"ENTSOE_TOKEN=" ".env" >nul 2>&1
if %ERRORLEVEL%==0 (
  REM Compute UTC window: last 2 days
  FOR /F %%i IN ('powershell -NoProfile -Command "(Get-Date).ToUniversalTime().AddDays(-2).ToString(\"yyyy-MM-dd\")"') DO SET START=%%i
  FOR /F %%i IN ('powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString(\"yyyy-MM-dd\")"') DO SET END=%%i

  echo [A85] SE3 Imbalance: !START!..!END!
  python src\fetch_imbalance_entsoe.py --area SE3 --start !START! --end !END! --out data\SE3_imbalance.parquet
  if errorlevel 1 goto :eof

  REM ---- Skip join if imbalance parquet is empty ----
  python -c "import pandas as pd, sys; import warnings; warnings.filterwarnings('ignore'); sys.exit(0 if len(pd.read_parquet('data\\SE3_imbalance.parquet'))>0 else 1)"
  if errorlevel 1 (
    echo [A85] No imbalance rows in window — skipping DA vs Imbalance plot.
  ) else (
    if not exist reports\SE3 mkdir reports\SE3
    python src\join_da_imbalance.py --da data\DA_SE3_API_latest.parquet --imb data\SE3_imbalance.parquet --out reports\SE3 --title "SE3 - DA vs Imbalance (API)"
  )
) else (
  echo [A85] ENTSOE_TOKEN not found — skipping imbalance fetch/join.
)
endlocal

exit /b 0

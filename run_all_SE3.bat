@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Prefer ENTSO-E API when token present. Safe no-op if token missing.
findstr /c:"ENTSOE_TOKEN=" ".env" >nul 2>&1
if %ERRORLEVEL%==0 (
  set "ZONE=SE3"
  for /f %%A in ('powershell -NoProfile -Command "(Get-Date).AddDays(-2).ToString('yyyy-MM-dd')"') do set "START=%%A"
  for /f %%A in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyy-MM-dd')"') do set "END=%%A"

  echo Using ENTSO-E API for !ZONE! from !START! to !END! ...
  python src\fetch_da_prices.py --zone !ZONE! --start !START! --end !END! --out data\DA_!ZONE!_API_latest.parquet
  if errorlevel 1 goto :eof

  if not exist reports\!ZONE! mkdir reports\!ZONE!
  python src\plot_da_api.py --input data\DA_!ZONE!_API_latest.parquet --out reports\!ZONE!\da_price_api.png
) else (
  echo ENTSOE_TOKEN not found in .env — skipping ENTSO-E fetch for SE3.
)

endlocal

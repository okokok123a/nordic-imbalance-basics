@echo off
setlocal

set "AREA=SE4"
set "START=2025-05-10"
set "END=2025-05-13"
set "OUT=data\DA_%AREA%_API.parquet"

if not exist data mkdir data

echo Fetching DA via ENTSO-E for %AREA% %START%..%END% ...
python src\fetch_da_entsoe.py --area %AREA% --start %START% --end %END% --out "%OUT%"
echo Done. Wrote: %OUT%

endlocal & exit /b 0

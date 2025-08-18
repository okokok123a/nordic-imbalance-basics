call .venv\Scripts\activate
python src\fetch_da_entsoe.py --area SE3 --start 2025-05-10 --end 2025-05-13 --out data\DA_SE3_API.parquet
dir /b data

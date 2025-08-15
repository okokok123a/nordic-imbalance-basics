#!/usr/bin/env python
import argparse, os
from pathlib import Path
import pandas as pd
from entsoe import EntsoePandasClient
from dotenv import load_dotenv

# Map friendly names to entsoe-py bidding zone codes
ZMAP = {"SE3": "SE_3", "SE4": "SE_4", "FI": "FI"}

def main():
    ap = argparse.ArgumentParser(description="Fetch ENTSO-E day-ahead prices and save to Parquet.")
    ap.add_argument("--zone", required=True, help="SE3 | SE4 | FI")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD (exclusive)")
    ap.add_argument("--out", required=True, help="Output Parquet path")
    args = ap.parse_args()

    load_dotenv()
    token = os.getenv("ENTSOE_TOKEN")
    if not token:
        raise SystemExit("Missing ENTSOE_TOKEN in .env")

    zone = ZMAP.get(args.zone.upper(), args.zone)
    client = EntsoePandasClient(api_key=token)

    # ENTSO-E expects Europe/Brussels timestamps
    start = pd.Timestamp(args.start, tz="Europe/Brussels")
    end = pd.Timestamp(args.end, tz="Europe/Brussels")

    s = client.query_day_ahead_prices(zone, start=start, end=end)  # hourly Series
    df = s.to_frame("da_price_eur_mwh").sort_index()
    df.index.name = "ts"

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out)
    print(f"Wrote {len(df):,} rows -> {args.out}")

if __name__ == "__main__":
    main()

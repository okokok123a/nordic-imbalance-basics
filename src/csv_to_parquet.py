#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap = argparse.ArgumentParser(description="Convert a CSV to the standard Parquet schema.")
    ap.add_argument("--csv", required=True, help="Path to input CSV")
    ap.add_argument("--ts-col", required=True, help="Timestamp column name in CSV")
    ap.add_argument("--price-col", required=True, help="Price column (€/MWh)")
    ap.add_argument("--volume-col", required=True, help="Imbalance volume column (MWh; +/-)")
    ap.add_argument("--area", required=True, help="SE3 | SE4 | FI")
    ap.add_argument("--out", required=True, help="Output Parquet path")
    ap.add_argument("--tz", default="Europe/Stockholm", help="Timezone to localize/convert to")
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1) Read CSV
    df = pd.read_csv(args.csv)

    # 2) Parse timestamps and set index AFTER building columns to avoid alignment NaNs
    ts = pd.to_datetime(df[args.ts_col], errors="raise")
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(args.tz)
    else:
        ts = ts.dt.tz_convert(args.tz)

    # 3) Build standard columns (values, not aligned Series)
    out = pd.DataFrame({
        "area": args.area,  # constant area (string) for all rows
        "price_eur_mwh": pd.to_numeric(df[args.price_col].values, errors="coerce"),
        "imbalance_volume_mwh": pd.to_numeric(df[args.volume_col].values, errors="coerce"),
    })

    # 4) Attach index & clean
    out.index = ts.values
    out.index.name = "ts"
    out = out.dropna(subset=["price_eur_mwh", "imbalance_volume_mwh"]).sort_index()

    # 5) Write parquet
    out.to_parquet(out_path)
    print(f"Wrote {len(out):,} rows -> {out_path}")

if __name__ == "__main__":
    main()

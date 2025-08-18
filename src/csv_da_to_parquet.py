#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd
import re


def find_col(cols, *patterns):
    pats = [re.compile(p, re.I) for p in patterns]
    for c in cols:
        for p in pats:
            if p.search(str(c)):
                return c
    return None


def main():
    ap = argparse.ArgumentParser(
        description="Convert ENTSO-E Energy Prices CSV -> Parquet"
    )
    ap.add_argument("--csv", required=True)
    ap.add_argument("--zone", required=True, help="SE3 | SE4 | FI")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # Let pandas infer delimiter; we’ll normalize decimals below
    df = pd.read_csv(args.csv, sep=None, engine="python")

    # Detect likely columns from the new portal
    time_col = find_col(df.columns, r"MTU", r"Time", r"Date")
    price_col = find_col(df.columns, r"price", r"eur.?/mwh", r"EUR/MWh")

    if time_col is None or price_col is None:
        raise SystemExit(f"Could not detect columns. Got columns: {list(df.columns)}")

    # Parse timestamp start from "YYYY-MM-DD HH:MM - YYYY-MM-DD HH:MM"
    ts_raw = df[time_col].astype(str).str.split(" - ").str[0]
    ts = pd.to_datetime(ts_raw, errors="raise")
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("Europe/Brussels")

    # Convert price (handle decimal commas)
    p = df[price_col].astype(str).str.replace(",", ".", regex=False)
    p = pd.to_numeric(p, errors="coerce")

    out = pd.DataFrame({"da_price_eur_mwh": p.values, "area": args.zone})
    out.index = ts.values
    out.index.name = "ts"
    out = out.dropna(subset=["da_price_eur_mwh"]).sort_index()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(args.out)
    print(f"Wrote {len(out):,} rows -> {args.out}")


if __name__ == "__main__":
    main()

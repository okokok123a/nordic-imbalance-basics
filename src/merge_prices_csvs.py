#!/usr/bin/env python
import argparse
import glob
import re
from pathlib import Path
import pandas as pd


def find_col(cols, *patterns):
    pats = [re.compile(p, re.I) for p in patterns]
    for c in cols:
        s = str(c)
        if any(p.search(s) for p in pats):
            return c
    return None


def parse_energy_prices_csv(path, zone):
    df = pd.read_csv(path, sep=None, engine="python")  # let pandas infer delimiter
    time_col = find_col(df.columns, r"MTU", r"Time", r"Date")
    price_col = find_col(df.columns, r"price", r"EUR.?/MWH", r"€/MWH")
    if time_col is None or price_col is None:
        raise SystemExit(
            f"[{path}] Could not detect time/price columns. Columns: {list(df.columns)}"
        )

    # MTU like "01/05/2025 00:00 - 01/05/2025 01:00" -> take start time
    ts_raw = df[time_col].astype(str).str.split(" - ").str[0]
    ts = pd.to_datetime(ts_raw, errors="raise", dayfirst=True)
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("Europe/Brussels")

    p = df[price_col].astype(str).str.replace(",", ".", regex=False)
    p = pd.to_numeric(p, errors="coerce")

    out = pd.DataFrame({"da_price_eur_mwh": p.values, "area": zone})
    out.index = ts.values
    out.index.name = "ts"
    return out.dropna(subset=["da_price_eur_mwh"]).sort_index()


def main():
    ap = argparse.ArgumentParser(
        description="Merge daily ENTSO-E Energy Prices CSVs -> one Parquet"
    )
    ap.add_argument(
        "--pattern", required=True, help=r"Glob like data\GUI_ENERGY_PRICES_202505*.csv"
    )
    ap.add_argument("--zone", required=True, help="SE3 | SE4 | FI")
    ap.add_argument("--out", required=True, help="Output Parquet path")
    args = ap.parse_args()

    files = sorted(glob.glob(args.pattern))
    if not files:
        raise SystemExit(f"No files match: {args.pattern}")

    frames = [parse_energy_prices_csv(f, args.zone) for f in files]
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="first")]  # drop any duplicate hours

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out)
    print(f"Merged {len(files)} files, {len(df)} rows -> {args.out}")


if __name__ == "__main__":
    main()

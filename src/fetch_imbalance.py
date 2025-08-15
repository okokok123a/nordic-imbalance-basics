#!/usr/bin/env python
import argparse
import numpy as np
import pandas as pd

def build_demo(area: str, start: str, end: str) -> pd.DataFrame:
    print(f"[build_demo] area={area} start={start} end={end}")
    idx = pd.date_range(start=start, end=end, freq="H", tz="Europe/Stockholm", inclusive="left")
    rng = np.random.default_rng(42)
    hour = idx.hour
    weekday = idx.dayofweek

    base_price = 35 + 10 * np.sin((hour / 24) * 2 * np.pi)   # diurnal
    wknd = np.where(weekday >= 5, -5, 0)                     # weekend effect
    noise = rng.normal(0, 6, size=len(idx))
    price = np.clip(base_price + wknd + noise, -100, 500)

    base_vol = 50 + 15 * np.cos((hour / 24) * 2 * np.pi) + rng.normal(0, 8, len(idx))
    sign = rng.choice([-1, 1], size=len(idx), p=[0.48, 0.52])
    volume_mwh = np.maximum(base_vol, 0) * sign

    df = pd.DataFrame(
        {"area": area, "price_eur_mwh": price.astype(float), "imbalance_volume_mwh": volume_mwh.astype(float)},
        index=idx,
    )
    df.index.name = "ts"
    print(f"[build_demo] rows={len(df)} first_ts={df.index[0]} last_ts={df.index[-1]}")
    return df

def main():
    ap = argparse.ArgumentParser(description="Fetch Nordic imbalance prices/volumes (demo-supported).")
    ap.add_argument("--area", required=True, help="SE3 | SE4 | FI")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD (exclusive)")
    ap.add_argument("--out", required=True, help="Output Parquet path")
    ap.add_argument("--demo", action="store_true", help="Generate synthetic data instead of fetching")
    args = ap.parse_args()

    print("[main] starting")
    if args.demo:
        df = build_demo(args.area, args.start, args.end)
    else:
        raise NotImplementedError("Real eSett/ENTSO-E fetch coming next. Use --demo for now.")

    df = df.sort_index()
    # Always write a CSV too (debug-friendly)
    csv_path = args.out.replace(".parquet", ".csv")
    df.to_csv(csv_path)
    print(f"[main] wrote CSV -> {csv_path}")

    # Try Parquet with pyarrow; print any error instead of silently failing
    try:
        df.to_parquet(args.out, engine="pyarrow")
        print(f"[main] wrote PARQUET -> {args.out}")
    except Exception as e:
        print(f"[main] PARQUET_ERROR: {e}")

    print(f"[main] done: rows={len(df)}")

if __name__ == "__main__":
    main()

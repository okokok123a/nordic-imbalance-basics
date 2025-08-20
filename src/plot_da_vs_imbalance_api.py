# pyright: reportOperatorIssue=false

import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def load_parquet(fp: str) -> pd.DataFrame:
    df = pd.read_parquet(fp)
    # Normalize to a UTC DateTimeIndex
    if "ts_utc" in df.columns:
        df = df.set_index(pd.to_datetime(df["ts_utc"], utc=True)).drop(columns=["ts_utc"])
    elif df.index.name:
        df.index = pd.to_datetime(df.index, utc=True)
    else:
        for name in ("ts", "timestamp", "timestamp_utc"):
            if name in df.columns:
                df = df.set_index(pd.to_datetime(df[name], utc=True)).drop(columns=[name])
                break
        else:
            raise SystemExit(f"Could not find a timestamp column/index in {fp}")
    return df.sort_index()

def pick_price_col(df: pd.DataFrame) -> str:
    for cand in ("price_eur_mwh", "da_price_eur_mwh", "imbalance_price_eur_mwh", "price"):
        if cand in df.columns:
            return cand
    # fallback: first numeric column
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    raise SystemExit("No numeric price column found.")

def main():
    ap = argparse.ArgumentParser(description="Plot DA vs Imbalance scatter with unit auto-fix (€/MWh).")
    ap.add_argument("--da", required=True, help="Parquet with day-ahead prices (€/MWh).")
    ap.add_argument("--imb", required=True, help="Parquet with imbalance prices (€/MWh or €/kWh).")
    ap.add_argument("--out", required=True, help="Output PNG path.")
    ap.add_argument("--title", default="DA vs Imbalance (API)")
    args = ap.parse_args()

    da  = load_parquet(args.da)
    imb = load_parquet(args.imb)

    da_col  = pick_price_col(da)
    imb_col = pick_price_col(imb)

    # Align on timestamp
    df = pd.DataFrame({"da": da[da_col]}).join(
        imb[[imb_col]].rename(columns={imb_col: "imb"}), how="inner"
    ).dropna()

    # Auto-rescale if imbalance looks like €/kWh (values << 1 while DA >> 1)
    if len(df) and df["imb"].max() < 1 and df["da"].max() > 1:
        df["imb"] = df["imb"] * 1000.0

    plt.figure(figsize=(8, 5))
    plt.scatter(df["da"], df["imb"], s=12, alpha=0.7)

    # Simple trend line (guard against zero variance)
    if len(df) >= 2 and df["da"].var() > 0:
        cov = pd.Series(df["da"]).cov(df["imb"])
        m = cov / df["da"].var()
        b = df["imb"].mean() - m * df["da"].mean()
        xs = pd.Series([df["da"].min(), df["da"].max()])
        plt.plot(xs, m * xs + b)

    plt.title(args.title)
    plt.xlabel("Day-ahead price (EUR/MWh)")
    plt.ylabel("Imbalance price (EUR/MWh)")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(args.out, dpi=120)
    plt.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python
import argparse
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_da(path: str) -> pd.Series:
    df = pd.read_parquet(path)
    if "da_price_eur_mwh" not in df.columns:
        raise ValueError(f"{path} missing 'da_price_eur_mwh'")
    s = df["da_price_eur_mwh"].copy()
    s.index.name = "ts"
    return s.sort_index()


def main():
    ap = argparse.ArgumentParser(
        description="Plot DA spread between two zones and write quick stats."
    )
    ap.add_argument("--a", required=True, help="Parquet A (e.g., SE4)")
    ap.add_argument("--b", required=True, help="Parquet B (e.g., SE3)")
    ap.add_argument("--out", required=True, help="Output folder (will be created)")
    ap.add_argument("--title", default="DA Spread (A - B)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    a = read_da(args.a)
    b = read_da(args.b)

    # align on common timestamps
    df = pd.DataFrame({"A": a, "B": b}).dropna().sort_index()
    df["spread"] = df["A"] - df["B"]  # A minus B

    # plot
    fig = plt.figure(figsize=(10, 4.2))
    ax = fig.gca()
    df["spread"].plot(ax=ax)
    ax.axhline(0, lw=1, ls="--")
    ax.set_title(args.title)
    ax.set_xlabel("Time")
    ax.set_ylabel("€/MWh")
    fig.tight_layout()
    out_png = os.path.join(args.out, "da_spread.png")
    fig.savefig(out_png, dpi=130)
    plt.close(fig)

    # stats
    s = df["spread"]
    stats = {
        "count": int(s.count()),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "min": float(s.min()),
        "p10": float(np.percentile(s, 10)),
        "median": float(np.percentile(s, 50)),
        "p90": float(np.percentile(s, 90)),
        "max": float(s.max()),
    }
    out_md = os.path.join(args.out, "da_spread_stats.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# DA spread stats (A - B)\n\n")
        for k, v in stats.items():
            f.write(f"- **{k}**: {v:.2f}\n")

    print(f"Saved {out_png} and {out_md}")


if __name__ == "__main__":
    main()

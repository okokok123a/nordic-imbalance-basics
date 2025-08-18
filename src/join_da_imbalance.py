#!/usr/bin/env python
# src/join_da_imbalance.py
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

TZ = "Europe/Stockholm"  # unify to one timezone for joining


def read_parquet_tz(path: str | Path, tz: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if df.index.name != "ts":
        df.index.name = "ts"
    # Make index tz-aware and convert to target tz
    if df.index.tz is None:
        df.index = df.index.tz_localize(tz)
    else:
        df.index = df.index.tz_convert(tz)
    return df


def main():
    ap = argparse.ArgumentParser(
        description="Join DA price with imbalance (price & volume) and plot scatter."
    )
    ap.add_argument("--da", required=True, help="Parquet with column da_price_eur_mwh")
    ap.add_argument(
        "--imb", required=True, help="Parquet with price_eur_mwh, imbalance_volume_mwh"
    )
    ap.add_argument("--out", required=True, help="Output folder (e.g., reports\\SE3)")
    ap.add_argument("--title", default="DA vs Imbalance price", help="Plot title")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    da = read_parquet_tz(args.da, TZ)
    imb = read_parquet_tz(args.imb, TZ)

    # Keep the columns we need
    if "da_price_eur_mwh" not in da.columns:
        raise KeyError("DA parquet must contain 'da_price_eur_mwh'")
    need_cols = ["price_eur_mwh", "imbalance_volume_mwh"]
    for c in need_cols:
        if c not in imb.columns:
            raise KeyError(f"Imbalance parquet must contain '{c}'")

    # Inner join on timestamp
    joined = imb[need_cols].join(da[["da_price_eur_mwh"]], how="inner").dropna()
    if joined.empty:
        raise ValueError(
            "No overlapping timestamps after join. Check timezones / ranges."
        )

    # Basic stats
    x = joined["da_price_eur_mwh"].to_numpy()
    y = joined["price_eur_mwh"].to_numpy()
    n = len(joined)

    # Pearson r
    r = float(np.corrcoef(x, y)[0, 1]) if n > 1 else np.nan

    # OLS (y = a + b x)
    if n >= 2:
        b, a = np.polyfit(x, y, 1)  # slope, intercept
    else:
        b, a = np.nan, np.nan

    # Plot
    fig, ax = plt.subplots(figsize=(7, 5), dpi=140)
    ax.scatter(x, y, s=12, alpha=0.35)
    # Regression line
    if n >= 2 and np.isfinite(b):
        xx = np.linspace(x.min(), x.max(), 100)
        ax.plot(xx, a + b * xx, linewidth=2)
    ax.set_xlabel("Day-ahead price (EUR/MWh)")
    ax.set_ylabel("Imbalance price (EUR/MWh)")
    ax.set_title(args.title)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    png_path = out_dir / "da_vs_imbalance.png"
    fig.savefig(png_path)
    plt.close(fig)

    # Stats MD
    md_path = out_dir / "da_vs_imbalance_stats.md"
    t0 = joined.index.min().strftime("%Y-%m-%d %H:%M")
    t1 = joined.index.max().strftime("%Y-%m-%d %H:%M")

    md = [
        "# SE3 — DA vs Imbalance price",
        "",
        f"- Points (hours): **{n}**",
        f"- Period: **{t0} → {t1}** ({TZ})",
        f"- Pearson r: **{r:.3f}**",
        f"- OLS slope (imbalance ≈ a + b·DA): **b = {b:.3f}**, intercept **a = {a:.2f}**",
        f"- Mean DA: **{x.mean():.2f}** EUR/MWh; Mean imbalance: **{y.mean():.2f}** EUR/MWh",
        "",
        "_Note: both series are joined on hourly timestamps after converting to Europe/Stockholm._",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"Saved {png_path} and {md_path}")


if __name__ == "__main__":
    main()

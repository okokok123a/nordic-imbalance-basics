#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def heatmap(df: pd.DataFrame, value_col: str, title: str, outpath: Path):
    pv = df.pivot_table(index="hour", columns="weekday", values=value_col, aggfunc="mean")
    fig, ax = plt.subplots(figsize=(6,5))
    im = ax.imshow(pv.values, aspect="auto")
    ax.set_title(title)
    ax.set_xlabel("Weekday (0=Mon)")
    ax.set_ylabel("Hour")
    ax.set_xticks(range(7)); ax.set_yticks(range(24))
    cb = plt.colorbar(im, ax=ax); cb.ax.set_ylabel(value_col, rotation=270, labelpad=12)
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)

def main():
    ap = argparse.ArgumentParser(description="Hour×weekday heatmaps & quick stats.")
    ap.add_argument("--input", required=True, help="Input Parquet file")
    ap.add_argument("--out", required=True, help="Output folder")
    args = ap.parse_args()

    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(args.input).copy()
    df["hour"] = df.index.hour
    df["weekday"] = df.index.dayofweek

    heatmap(df, "price_eur_mwh", "Imbalance Price (€/MWh): Hour × Weekday", outdir / "heatmap_price.png")
    heatmap(df, "imbalance_volume_mwh", "Imbalance Volume (MWh): Hour × Weekday", outdir / "heatmap_volume.png")

    stats = {
        "rows": len(df),
        "price_mean": float(df["price_eur_mwh"].mean()),
        "price_p95": float(df["price_eur_mwh"].quantile(0.95)),
        "price_p99": float(df["price_eur_mwh"].quantile(0.99)),
        "abs_vol_mean": float(df["imbalance_volume_mwh"].abs().mean()),
        "abs_vol_p95": float(df["imbalance_volume_mwh"].abs().quantile(0.95)),
    }
    lines = ["# Quick stats", ""] + [f"- **{k.replace('_',' ')}:** {v:,.2f}" for k, v in stats.items()]
    (outdir / "stats.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved heatmaps + stats to {outdir}")

if __name__ == "__main__":
    main()

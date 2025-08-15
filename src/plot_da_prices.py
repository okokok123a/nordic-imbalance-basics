#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser(description="Plot day-ahead price time series")
    ap.add_argument("--input", required=True, help="Parquet with column da_price_eur_mwh, index tz-aware")
    ap.add_argument("--out", required=True, help="Output folder (e.g., reports\\SE3)")
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    Path(args.out).mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.input).sort_index()
    # Show in Stockholm time for readability
    if df.index.tz is not None:
        df = df.tz_convert("Europe/Stockholm")
    else:
        df.index = df.index.tz_localize("Europe/Stockholm")

    s = df["da_price_eur_mwh"]

    # Plot
    fig, ax = plt.subplots(figsize=(11, 4))
    s.plot(ax=ax)
    ax.set_title(args.title or "Day-ahead price (EUR/MWh)")
    ax.set_ylabel("EUR/MWh")
    ax.set_xlabel("Time")
    fig.tight_layout()
    out_png = Path(args.out) / "da_price.png"
    fig.savefig(out_png, dpi=150)
    plt.close(fig)

    # Tiny stats
    stats = {
        "rows": len(s),
        "start": s.index.min().strftime("%Y-%m-%d %H:%M"),
        "end": s.index.max().strftime("%Y-%m-%d %H:%M"),
        "mean": float(s.mean()),
        "min": float(s.min()),
        "p10": float(s.quantile(0.10)),
        "p90": float(s.quantile(0.90)),
        "max": float(s.max()),
    }
    out_md = Path(args.out) / "da_price_stats.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# SE3 Day-ahead price — summary\n\n")
        for k, v in stats.items():
            if isinstance(v, float):
                v = f"{v:.2f}"
            f.write(f"- {k}: {v}\n")

    print(f"Saved {out_png} and {out_md}")

if __name__ == "__main__":
    main()

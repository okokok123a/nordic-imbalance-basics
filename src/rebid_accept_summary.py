#!/usr/bin/env python3
import argparse, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_parquet_ts(path):
    df = pd.read_parquet(path)
    # Ensure index named ts and is datetime
    if df.index.name != "ts":
        if "ts" in df.columns:
            df = df.set_index("ts")
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="raise")
    # Align to Europe/Stockholm and drop tz for clean join
    if df.index.tz is not None:
        df.index = df.index.tz_convert("Europe/Stockholm").tz_localize(None)
    return df.sort_index()

def safe_join(da_path, imb_path):
    da = load_parquet_ts(da_path).copy()
    imb = load_parquet_ts(imb_path).copy()

    # Expect these columns
    # DA: da_price_eur_mwh, area
    # IMB: price_eur_mwh, imbalance_volume_mwh, area
    if "da_price_eur_mwh" not in da.columns:
        raise ValueError("DA parquet must have column 'da_price_eur_mwh'")
    if "price_eur_mwh" not in imb.columns:
        raise ValueError("Imbalance parquet must have column 'price_eur_mwh'")

    # Also force Stockholm/no-tz for DA if tz-naive but actually Brussels hours
    # (Our merge script already normalized to local time, so this is just a guard.)
    if da.index.tz is not None:
        da.index = da.index.tz_convert("Europe/Stockholm").tz_localize(None)
    if imb.index.tz is not None:
        imb.index = imb.index.tz_convert("Europe/Stockholm").tz_localize(None)

    j = da[["da_price_eur_mwh"]].join(
        imb[["price_eur_mwh", "imbalance_volume_mwh"]],
        how="inner"
    )
    j = j.rename(columns={"price_eur_mwh": "imb_price_eur_mwh"})
    j["spread_eur_mwh"] = j["imb_price_eur_mwh"] - j["da_price_eur_mwh"]
    return j

def make_summary_md(df, title, outdir):
    corr = df["imb_price_eur_mwh"].corr(df["da_price_eur_mwh"])
    mae = (df["spread_eur_mwh"]).abs().mean()
    mean_spread = df["spread_eur_mwh"].mean()
    n = len(df)

    # Hour-of-day median |spread|
    hour_med = (df["spread_eur_mwh"].abs()
                .groupby(df.index.hour).median()
                .sort_values(ascending=False))

    # Weekday median |spread| (0=Mon)
    dow_med = (df["spread_eur_mwh"].abs()
               .groupby(df.index.dayofweek).median()
               .sort_values(ascending=False))

    md = []
    md.append(f"# {title}")
    md.append("")
    md.append(f"- Samples (hours): **{n}**")
    md.append(f"- Corr(DA, Imbalance): **{corr:.3f}**")
    md.append(f"- Mean abs spread: **{mae:.2f} €/MWh**")
    md.append(f"- Mean spread (imb − DA): **{mean_spread:.2f} €/MWh**")
    md.append("")
    md.append("## Highest median |spread| by hour (top 6)")
    for h, v in hour_med.head(6).items():
        md.append(f"- **{h:02d}:00** → {v:.2f} €/MWh")
    md.append("")
    md.append("## Highest median |spread| by weekday (top 6, 0=Mon)")
    for d, v in dow_med.head(6).items():
        md.append(f"- **{d}** → {v:.2f} €/MWh")
    md.append("")
    md.append("_Interpretation: bigger median |spread| means more deviation risk at that hour/weekday → you’re more likely to **rebid** vs accept._")
    out_md = os.path.join(outdir, "rebid_accept_summary.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return out_md, hour_med

def plot_hour_bars(hour_med, title, outdir):
    fig, ax = plt.subplots(figsize=(8,4.5))
    hour_med.sort_index().plot(kind="bar", ax=ax)
    ax.set_title(f"{title} — median |imb − DA| by hour")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Median |spread| (€/MWh)")
    plt.tight_layout()
    out_png = os.path.join(outdir, "rebid_accept_by_hour.png")
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png

def main():
    p = argparse.ArgumentParser(description="Rebid vs Accept cheat-sheet: join DA & imbalance, summarize spread risk.")
    p.add_argument("--da", required=True, help="Parquet with DA prices (index ts, column da_price_eur_mwh)")
    p.add_argument("--imb", required=True, help="Parquet with imbalance data (index ts, column price_eur_mwh)")
    p.add_argument("--out", required=True, help="Output folder (will be created)")
    p.add_argument("--title", default="Rebid vs Accept — SE3 (May 2025)")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    df = safe_join(args.da, args.imb)
    md_path, hour_med = make_summary_md(df, args.title, args.out)
    png_path = plot_hour_bars(hour_med, args.title, args.out)
    print(f"Saved {md_path} and {png_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd


def load_parquet(path):
    df = pd.read_parquet(path)
    # Ensure DatetimeIndex and strip/align tz if present
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"{path} has no DatetimeIndex")
    idx = df.index
    if idx.tz is not None:
        idx = idx.tz_convert("Europe/Stockholm").tz_localize(None)
    return df.set_index(idx)


def main():
    p = argparse.ArgumentParser(
        description="Build daily IDA prep sheet from DA & imbalance."
    )
    p.add_argument(
        "--da",
        required=True,
        help="Parquet with day-ahead price (index=ts, col=da_price_eur_mwh)",
    )
    p.add_argument(
        "--imb",
        required=True,
        help="Parquet with imbalance data (index=ts, col=price_eur_mwh)",
    )
    p.add_argument("--out", required=True, help="Output folder, e.g. reports\\SE3")
    p.add_argument("--zone", default="SE3")
    p.add_argument(
        "--thr",
        type=float,
        default=50.0,
        help="Big deviation threshold in €/MWh (abs(Imb-DA) > thr)",
    )
    p.add_argument("--title", default=None)
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    da = load_parquet(args.da).rename(columns={"da_price_eur_mwh": "DA"})
    imb = load_parquet(args.imb).rename(columns={"price_eur_mwh": "Imb"})

    # Keep only needed columns
    da = da[["DA"]]
    # Some imbalance parquet also has 'area' col; keep price only
    if "Imb" not in imb.columns:
        raise ValueError("imbalance parquet must have column 'price_eur_mwh'")
    imb = imb[["Imb"]]

    # Align hourly indexes
    df = da.join(imb, how="inner")
    if df.empty:
        raise ValueError("No overlapping timestamps between DA and imbalance data.")

    # Derived columns
    df["Spread"] = df["Imb"] - df["DA"]
    df["AbsSpread"] = df["Spread"].abs()

    # Group by calendar day
    day = df.index.date
    g = df.groupby(day, sort=True)

    rows = []
    for d, x in g:
        hrs = len(x)
        da_mean = x["DA"].mean()
        da_std = x["DA"].std()
        imb_mean = x["Imb"].mean()
        imb_std = x["Imb"].std()
        corr = x["DA"].corr(x["Imb"]) if hrs >= 3 else float("nan")
        bigdev = int((x["AbsSpread"] > args.thr).sum())
        tail95 = x["AbsSpread"].quantile(0.95)
        max_pos = x["Spread"].max()
        min_neg = x["Spread"].min()
        rows.append(
            {
                "date": pd.to_datetime(d).date(),
                "hours": hrs,
                "da_mean": round(da_mean, 2),
                "da_std": round(da_std, 2) if pd.notna(da_std) else None,
                "imb_mean": round(imb_mean, 2),
                "imb_std": round(imb_std, 2) if pd.notna(imb_std) else None,
                "corr": round(corr, 3) if pd.notna(corr) else None,
                "big_deviation_hours": bigdev,
                "p95_abs_spread": round(tail95, 2) if pd.notna(tail95) else None,
                "max_pos_spread": round(max_pos, 2) if pd.notna(max_pos) else None,
                "min_neg_spread": round(min_neg, 2) if pd.notna(min_neg) else None,
            }
        )

    daily = pd.DataFrame(rows).sort_values("date")
    csv_path = out_dir / "ida_prepsheet.csv"
    daily.to_csv(csv_path, index=False)

    # Build quick summary markdown
    title = args.title or f"{args.zone} — IDA Prep Sheet"
    start, end = daily["date"].min(), daily["date"].max()
    total_days = len(daily)
    total_hours = len(df)

    # Top 5 risky days by big deviation count
    top_risk = daily.sort_values("big_deviation_hours", ascending=False).head(5)

    md_lines = []
    md_lines.append(f"# {title}")
    md_lines.append("")
    md_lines.append(
        f"- Period: **{start} → {end}**  ·  Days: **{total_days}**  ·  Hours (overlap): **{total_hours}**"
    )
    md_lines.append(
        f"- Threshold for 'big deviation': **|Imb − DA| > {args.thr:.0f} €/MWh**"
    )
    md_lines.append("")
    md_lines.append("## Top 5 risky days (by big deviation hours)")
    if not top_risk.empty:
        for _, r in top_risk.iterrows():
            md_lines.append(
                f"- {r['date']}: **{int(r['big_deviation_hours'])}h**  "
                f"(p95 abs spread: {r['p95_abs_spread']} €/MWh, "
                f"corr: {r['corr']})"
            )
    else:
        md_lines.append("- (no days exceed the threshold)")

    md_lines.append("")
    md_lines.append("## Notes")
    md_lines.append("- DA and imbalance are aligned on overlapping hourly timestamps.")
    md_lines.append("- Use the CSV to spot days that deserve more attention in IDA.")
    md_lines.append("")
    md_path = out_dir / "ida_prepsheet.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote {csv_path} and {md_path}")


if __name__ == "__main__":
    main()

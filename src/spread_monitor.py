# src/spread_monitor.py
import argparse, os
import pandas as pd

def load_price_series(path, price_col="da_price_eur_mwh"):
    df = pd.read_parquet(path)
    # Ensure index is named ts and sorted
    if df.index.name != "ts":
        df.index.name = "ts"
    df = df.sort_index()
    # Keep ONLY the price column to avoid overlaps
    if price_col not in df.columns:
        raise ValueError(f"{path} missing column {price_col}")
    return df[[price_col]].rename(columns={price_col: "price"})

def daily_top_moves(df_spread, n):
    d = df_spread.copy()
    d["date"] = d.index.date
    d["abs_spread"] = d["spread_eur_mwh"].abs()
    out = []
    for day, g in d.groupby("date", sort=True):
        top = g.nlargest(n, "abs_spread")
        top = top.assign(rank_abs=top["abs_spread"].rank(ascending=False, method="first").astype(int))
        out.append(top)
    if not out:
        return pd.DataFrame(columns=["se4_eur_mwh","se3_eur_mwh","spread_eur_mwh","abs_spread","rank_abs"])
    res = pd.concat(out).sort_index()
    return res[["se4_eur_mwh", "se3_eur_mwh", "spread_eur_mwh", "abs_spread", "rank_abs"]]

def make_summary(df_spread):
    s = df_spread["spread_eur_mwh"]
    return {
        "rows": int(len(df_spread)),
        "start": str(df_spread.index.min()),
        "end": str(df_spread.index.max()),
        "mean_spread": round(float(s.mean()), 2),
        "p95_abs": round(float(s.abs().quantile(0.95)), 2),
        "max_spread": round(float(s.max()), 2),
        "min_spread": round(float(s.min()), 2),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="SE4 parquet")
    ap.add_argument("--b", required=True, help="SE3 parquet")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=6, help="top N hours per day by |spread|")
    ap.add_argument("--title", default="Spread monitor")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    se4 = load_price_series(args.a).rename(columns={"price": "se4_eur_mwh"})
    se3 = load_price_series(args.b).rename(columns={"price": "se3_eur_mwh"})
    # Inner join on hourly timestamps
    df = se4.join(se3, how="inner")
    df["spread_eur_mwh"] = df["se4_eur_mwh"] - df["se3_eur_mwh"]

    # Save hourly joined spread (handy for other charts later)
    hourly_path = os.path.join(args.out, "da_spread_hourly.parquet")
    df.to_parquet(hourly_path)

    # Top moves per day
    topN = daily_top_moves(df, args.n)
    csv_path = os.path.join(args.out, "spread_monitor.csv")
    topN.to_csv(csv_path, float_format="%.2f")

    # Small Markdown summary
    st = make_summary(df)
    md = [
        f"# {args.title}",
        "",
        f"- Rows: **{st['rows']}**",
        f"- Range: **{st['start']} → {st['end']}**",
        f"- Mean spread (SE4−SE3): **{st['mean_spread']} €/MWh**",
        f"- p95 |spread|: **{st['p95_abs']} €/MWh**",
        f"- Max spread: **{st['max_spread']} €/MWh** · Min spread: **{st['min_spread']} €/MWh**",
        "",
        f"CSV: `spread_monitor.csv` (top {args.n} hours per day by |SE4−SE3|).",
    ]
    with open(os.path.join(args.out, "spread_monitor.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Wrote {csv_path} and spread_monitor.md\nHourly join saved to {hourly_path}")

if __name__ == "__main__":
    main()

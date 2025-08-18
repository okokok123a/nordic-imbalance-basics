import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt


def main():
    p = argparse.ArgumentParser(description="Plot DA price from API parquet to PNG.")
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    df = pd.read_parquet(args.input)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    area = str(df.get("area", pd.Series(["?"])).iloc[0])
    start = df.index.min().strftime("%Y-%m-%d %H:%M UTC")
    end = df.index.max().strftime("%Y-%m-%d %H:%M UTC")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["da_price_eur_mwh"])
    plt.title(f"Day-ahead price — {area} — {start} → {end}")
    plt.xlabel("Time (UTC)")
    plt.ylabel("€/MWh")
    plt.tight_layout()
    plt.savefig(args.out, dpi=120)
    plt.close()
    print(f"OK: wrote plot {args.out}")


if __name__ == "__main__":
    main()

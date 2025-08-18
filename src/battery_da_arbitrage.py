# src/battery_da_arbitrage.py
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def simulate_battery(df_prices: pd.DataFrame, cap_mwh=10.0, power_mw=5.0, eta_rt=0.90):
    """
    Very simple DA-threshold strategy:
    - For each day, compute 25th/75th percentile of price.
    - If price <= p25 and SOC < cap: charge up to power (1h) and remaining capacity.
    - If price >= p75 and SOC > 0:  discharge up to power (1h) and available SOC.
    - Otherwise hold.
    Efficiency applied on discharge revenue (approx for simplicity).
    """

    df = df_prices.copy()

    # Per-day thresholds
    daily = df["da_price_eur_mwh"].groupby(df.index.date)
    p25 = daily.transform(lambda s: np.nanpercentile(s, 25))
    p75 = daily.transform(lambda s: np.nanpercentile(s, 75))
    df["p25"] = p25.values
    df["p75"] = p75.values

    # State & logs
    soc = 0.0  # MWh
    charge_mwh = []
    discharge_mwh = []
    pnl_eur = []
    action = []  # -1 = charge, +1 = discharge, 0 = hold

    for ts, row in df.iterrows():
        price = float(row["da_price_eur_mwh"])
        want_charge = price <= row["p25"]
        want_discharge = price >= row["p75"]

        c = 0.0
        d = 0.0
        pnl = 0.0

        # Priority: discharge on high price, else charge on low price
        if want_discharge and soc > 0.0:
            d = min(power_mw, soc)  # 1 hour step => MWh == MW
            soc -= d
            pnl += price * d * eta_rt  # apply round-trip eff on the way out
            act = +1
        elif want_charge and soc < cap_mwh:
            c = min(power_mw, cap_mwh - soc)
            soc += c
            pnl -= price * c  # pay to charge
            act = -1
        else:
            act = 0

        charge_mwh.append(c)
        discharge_mwh.append(d)
        pnl_eur.append(pnl)
        action.append(act)

    df["charge_mwh"] = charge_mwh
    df["discharge_mwh"] = discharge_mwh
    df["pnl_eur"] = pnl_eur
    df["action"] = action
    df["soc_mwh"] = df["charge_mwh"].cumsum() - df["discharge_mwh"].cumsum()

    stats = {
        "hours": len(df),
        "days": df.index.normalize().nunique(),
        "cap_mwh": cap_mwh,
        "power_mw": power_mw,
        "eta_rt": eta_rt,
        "total_charge_mwh": float(df["charge_mwh"].sum()),
        "total_discharge_mwh": float(df["discharge_mwh"].sum()),
        "utilisation": float((df["charge_mwh"].abs() + df["discharge_mwh"].abs()).sum())
        / (len(df) * power_mw),
        "cycles_approx": float(df["discharge_mwh"].sum() / cap_mwh),
        "total_pnl_eur": float(df["pnl_eur"].sum()),
        "pnl_per_day_eur": float(df["pnl_eur"].sum())
        / max(1, df.index.normalize().nunique()),
        "pnl_per_mwh_throughput": float(df["pnl_eur"].sum())
        / max(1e-9, (df["charge_mwh"].sum() + df["discharge_mwh"].sum())),
    }
    return df, stats


def plot_pnl(df, out_png: Path, title: str):
    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["da_price_eur_mwh"], linewidth=1)
    # markers
    ch = df["action"] == -1
    ds = df["action"] == +1
    plt.scatter(df.index[ch], df.loc[ch, "da_price_eur_mwh"], s=10, marker="v")
    plt.scatter(df.index[ds], df.loc[ds, "da_price_eur_mwh"], s=10, marker="^")

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("EUR/MWh")
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=140)
    plt.close()


def write_stats_md(stats: dict, out_md: Path):
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Battery-lite DA arbitrage — stats\n",
        f"- Hours: **{stats['hours']}**, Days: **{stats['days']}**",
        f"- Cap: **{stats['cap_mwh']} MWh**, Power: **{stats['power_mw']} MW**, Round-trip eff: **{int(stats['eta_rt']*100)}%**",
        f"- Total charge: **{stats['total_charge_mwh']:.1f} MWh**, Total discharge: **{stats['total_discharge_mwh']:.1f} MWh**",
        f"- Utilisation (|P|/(Pmax)): **{stats['utilisation']:.2f}**",
        f"- Approx cycles (discharge/cap): **{stats['cycles_approx']:.2f}**",
        f"- Total PnL: **€{stats['total_pnl_eur']:.0f}**, PnL/day: **€{stats['pnl_per_day_eur']:.0f}**",
        f"- PnL per MWh throughput: **€{stats['pnl_per_mwh_throughput']:.1f} /MWh**",
        "",
        "_Strategy: charge when price ≤ daily P25; discharge when price ≥ daily P75; power/cap limits respected; losses applied on discharge revenue._",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--da", required=True, help="Path to DA parquet (e.g., data/DA_SE3.parquet)"
    )
    ap.add_argument("--zone", required=True, help="SE3 / SE4 / FI")
    ap.add_argument("--out", required=True, help="output folder (e.g., reports/SE3)")
    ap.add_argument("--cap", type=float, default=10.0, help="Battery capacity MWh")
    ap.add_argument("--power", type=float, default=5.0, help="Battery power MW")
    ap.add_argument(
        "--rt", type=float, default=0.90, help="Round-trip efficiency (0-1)"
    )
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.da)
    if "da_price_eur_mwh" not in df.columns:
        raise SystemExit("Input parquet missing column 'da_price_eur_mwh'.")

    # If file contains multiple areas, filter by --zone
    if "area" in df.columns:
        df = df[df["area"] == args.zone]

    # Ensure hourly and sorted
    df = df.sort_index()
    if df.index.tz is None:
        # assume Europe/Brussels from the previous pipeline
        df.index = df.index.tz_localize("Europe/Brussels")

    sim, stats = simulate_battery(
        df, cap_mwh=args.cap, power_mw=args.power, eta_rt=args.rt
    )

    title = (
        args.title
        or f"{args.zone} Battery-lite DA arbitrage ({int(args.cap)}MWh/{int(args.power)}MW, η={int(args.rt*100)}%)"
    )
    out_png = outdir / "battery_pnl.png"
    plot_pnl(sim, out_png, title)

    out_md = outdir / "battery_stats.md"
    write_stats_md(stats, out_md)

    print(f"Saved {out_png} and {out_md}")


if __name__ == "__main__":
    main()

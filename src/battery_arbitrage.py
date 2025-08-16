#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
battery_arbitrage.py
Greedy day-ahead battery arbitrage on hourly prices.

Inputs:
  --price  Parquet with hourly DA prices (index=ts, col=da_price_eur_mwh, 'area')
  --out    Output folder for charts/stats/CSV
  --zone   (optional) label to print on plots
  --e-mwh  Energy capacity, e.g. 10
  --p-mw   Power limit (1h step), e.g. 5
  --eta    Round-trip efficiency (0..1), e.g. 0.9
  --soc0   Initial state of charge (MWh), default 0
  --title  Plot title

Outputs in --out:
  battery_schedule.csv
  battery_stats.md
  battery_pnl.png
"""
import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plan_day_greedy(day_df: pd.DataFrame, p_mw: float, e_mwh: float) -> pd.Series:
    """
    Pick the H cheapest hours to CHARGE and H most expensive to DISCHARGE (no overlap),
    where H = ceil(e_mwh / p_mw). Returns a 'plan' Series with 'charge'/'discharge'/'idle'.
    """
    n_slots = int(math.ceil(e_mwh / p_mw))
    plan = pd.Series('idle', index=day_df.index)

    # Sort hours by price
    cheapest = day_df['da_price_eur_mwh'].sort_values().index.tolist()
    priciest = day_df['da_price_eur_mwh'].sort_values(ascending=False).index.tolist()

    # Choose charge slots
    charge_hours = []
    for ts in cheapest:
        if len(charge_hours) >= n_slots:
            break
        charge_hours.append(ts)

    # Choose discharge slots, avoiding charge overlap
    discharge_hours = []
    for ts in priciest:
        if len(discharge_hours) >= n_slots:
            break
        if ts in charge_hours:
            continue
        discharge_hours.append(ts)

    plan.loc[charge_hours] = 'charge'
    plan.loc[discharge_hours] = 'discharge'
    return plan


def simulate(prices: pd.DataFrame, e_mwh: float, p_mw: float, eta_rt: float, soc0: float) -> pd.DataFrame:
    """
    Step forward hour-by-hour applying the plan of charge/discharge.
    Efficiency split: eta_c = eta_d = sqrt(eta_rt).
    """
    eta_c = math.sqrt(eta_rt)
    eta_d = math.sqrt(eta_rt)

    # Build daily plan first (cheap vs expensive hours)
    plans = []
    for d, day_df in prices.groupby(prices.index.date):
        day_plan = plan_day_greedy(day_df, p_mw=p_mw, e_mwh=e_mwh)
        plans.append(day_plan)
    plan = pd.concat(plans).sort_index()
    plan.name = 'action'

    df = prices[['da_price_eur_mwh']].copy()
    df['action'] = plan.reindex(df.index).fillna('idle')

    # Simulate battery state & cashflow
    soc = soc0  # MWh in battery
    rows = []
    for ts, row in df.iterrows():
        price = float(row['da_price_eur_mwh'])
        action = row['action']

        charge_mwh_from_grid = 0.0
        discharge_mwh_to_grid = 0.0
        cash = 0.0

        if action == 'charge' and soc < e_mwh - 1e-9:
            # Max energy we can draw from grid this hour
            max_grid_energy = min(p_mw, max(0.0, (e_mwh - soc) / eta_c))
            charge_mwh_from_grid = max_grid_energy
            soc += max_grid_energy * eta_c
            cash -= price * charge_mwh_from_grid

        elif action == 'discharge' and soc > 1e-9:
            # Max we can send to grid given SOC and power
            max_to_grid = min(p_mw, soc * eta_d)
            discharge_mwh_to_grid = max_to_grid
            soc -= max_to_grid / eta_d
            cash += price * discharge_mwh_to_grid

        rows.append({
            'ts': ts,
            'price': price,
            'action': action,
            'charge_mwh_from_grid': charge_mwh_from_grid,
            'discharge_mwh_to_grid': discharge_mwh_to_grid,
            'soc_mwh': soc,
            'cashflow_eur': cash
        })

    out = pd.DataFrame(rows).set_index('ts').sort_index()
    out['cum_pnl_eur'] = out['cashflow_eur'].cumsum()
    return out


def make_plot(schedule: pd.DataFrame, title: str, out_png: Path):
    plt.figure(figsize=(11, 5))
    ax = plt.gca()
    schedule['price'].plot(ax=ax, lw=1)
    # Mark charge/discharge hours
    ch = schedule[schedule['action'] == 'charge']
    dh = schedule[schedule['action'] == 'discharge']
    ax.scatter(ch.index, ch['price'], marker='^', s=30)      # charge markers
    ax.scatter(dh.index, dh['price'], marker='v', s=30)      # discharge markers
    ax.set_title(title)
    ax.set_xlabel('Time')
    ax.set_ylabel('€/MWh')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def write_stats_md(schedule: pd.DataFrame, zone: str, e_mwh: float, p_mw: float, eta_rt: float, soc0: float, out_md: Path):
    period = f"{schedule.index.min()} → {schedule.index.max()}"
    pnl = schedule['cashflow_eur'].sum()
    days = schedule.index.normalize().nunique()
    avg_day = pnl / days if days else pnl

    n_charge = int((schedule['charge_mwh_from_grid'] > 0).sum())
    n_discharge = int((schedule['discharge_mwh_to_grid'] > 0).sum())
    e_in = schedule['charge_mwh_from_grid'].sum()
    e_out = schedule['discharge_mwh_to_grid'].sum()
    approx_cycles = e_out / e_mwh if e_mwh > 0 else 0.0

    md = []
    md.append(f"# Battery-lite DA arbitrage — {zone}")
    md.append("")
    md.append(f"**Period:** {period}")
    md.append(f"**Params:** E={e_mwh} MWh  |  P={p_mw} MW  |  η={eta_rt:.2f}  |  SOC₀={soc0} MWh")
    md.append("")
    md.append(f"**PnL:** {pnl:,.0f} €  (avg/day: {avg_day:,.0f} €)")
    md.append("")
    md.append("**Utilization:**")
    md.append(f"- Charge hours: {n_charge}  |  Discharge hours: {n_discharge}")
    md.append(f"- Energy in (grid→bat): {e_in:.1f} MWh  |  Energy out (bat→grid): {e_out:.1f} MWh")
    md.append(f"- Approx cycles over period: {approx_cycles:.2f}  ( = total discharge MWh / E )")
    md.append("")
    md.append("_Greedy rule: charge the cheapest H hours, discharge the priciest H hours per day, where H≈ceil(E/P). Efficiency applied on both legs._")

    out_md.write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Greedy battery arbitrage on day-ahead prices.")
    ap.add_argument("--price", required=True, help="Parquet with hourly DA prices")
    ap.add_argument("--out", required=True, help="Output folder")
    ap.add_argument("--zone", default="", help="Label/zone for titles")
    ap.add_argument("--e-mwh", type=float, default=10.0, help="Energy capacity (MWh)")
    ap.add_argument("--p-mw", type=float, default=5.0, help="Power limit (MW)")
    ap.add_argument("--eta", type=float, default=0.90, help="Round-trip efficiency (0..1)")
    ap.add_argument("--soc0", type=float, default=0.0, help="Initial SOC (MWh)")
    ap.add_argument("--title", default="", help="Plot title")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.price)
    if 'da_price_eur_mwh' not in df.columns:
        raise SystemExit("Expected column 'da_price_eur_mwh' in price parquet.")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise SystemExit("Price parquet index must be datetime.")

    # Keep just hourly prices, sorted
    prices = df[['da_price_eur_mwh']].copy().sort_index()

    schedule = simulate(prices, e_mwh=args.e_mwh, p_mw=args.p_mw, eta_rt=args.eta, soc0=args.soc0)

    # Outputs
    zone = args.zone or (df['area'].iloc[0] if 'area' in df.columns and len(df) else "ZONE")
    title = args.title or f"{zone} battery-lite DA arbitrage (E={args.e_mwh}MWh, P={args.p_mw}MW, η={args.eta:.0%})"

    csv_path = out_dir / "battery_schedule.csv"
    md_path = out_dir / "battery_stats.md"
    png_path = out_dir / "battery_pnl.png"

    schedule.to_csv(csv_path, index=True)
    write_stats_md(schedule, zone=zone, e_mwh=args.e_mwh, p_mw=args.p_mw, eta_rt=args.eta, soc0=args.soc0, out_md=md_path)
    make_plot(schedule, title=title, out_png=png_path)

    print(f"Saved {csv_path.name}, {md_path.name}, {png_path.name} → {out_dir}")


if __name__ == "__main__":
    main()

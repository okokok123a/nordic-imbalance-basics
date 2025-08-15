METHOD — nordic-imbalance-basics

This file explains what data is used, how it’s processed, key assumptions, and basic checks so someone else can reproduce the outputs.

---

## Data sources

**Imbalance (Nordics)**
Columns used:

- ts (timestamp), area (e.g., SE3), price_eur_mwh, imbalance_volume_mwh (+/− for direction).

Scripts:

- src/fetch_imbalance.py — --demo makes synthetic hourly data for quick visuals.
- src/csv_to_parquet.py — converts a real CSV to Parquet with a tz-aware index.
- src/join_da_imbalance.py — joins DA price with imbalance and creates scatter + stats.


**Day-ahead prices (ENTSO-E, new portal)**

- Dataset: Energy Prices (bidding zone).
- Zone in this drop: SE3, May 2025.
- Current acquisition: daily **CSV exports** from the portal UI, merged locally.
- Planned: REST API via entsoe-py once a securityToken is active (stored in .env, never committed).

---

## Repo layout (relevant bits)

```text
data/
  DA_SE3.parquet                  # merged DA prices (tz=Europe/Brussels)
  SE3.parquet, SE3.csv            # imbalance (demo)

reports/
  SE3/
    da_price.png                  # SE3 DA price plot (May 2025)
    da_price_stats.md             # stats for the plot
    heatmap_price.png             # imbalance heatmap (price)
    heatmap_volume.png            # imbalance heatmap (volume)
    stats.md                      # imbalance quick stats

src/
  fetch_imbalance.py
  csv_to_parquet.py
  merge_prices_csvs.py            # merges daily Energy Prices CSVs → Parquet
  plot_da_prices.py               # DA price plot + stats
  join_da_imbalance.py            # joins DA price with imbalance; scatter + stats
  make_heatmaps.py                # hour×weekday heatmaps

```

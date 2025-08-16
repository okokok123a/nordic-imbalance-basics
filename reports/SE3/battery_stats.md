# Battery-lite DA arbitrage — SE3

**Period:** 2025-04-30 20:00:00 → 2025-05-31 19:00:00
**Params:** E=10.0 MWh  |  P=5.0 MW  |  η=0.90  |  SOC₀=0.0 MWh

**PnL:** 16,753 €  (avg/day: 524 €)

**Utilization:**
- Charge hours: 61  |  Discharge hours: 53
- Energy in (grid→bat): 272.1 MWh  |  Energy out (bat→grid): 244.9 MWh
- Approx cycles over period: 24.49  ( = total discharge MWh / E )

_Greedy rule: charge the cheapest H hours, discharge the priciest H hours per day, where H≈ceil(E/P). Efficiency applied on both legs._
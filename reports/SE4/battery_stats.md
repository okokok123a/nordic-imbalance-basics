# Battery-lite DA arbitrage — SE4

**Period:** 2025-04-30 20:00:00 → 2025-05-31 19:00:00
**Params:** E=10.0 MWh  |  P=5.0 MW  |  η=0.90  |  SOC₀=0.0 MWh

**PnL:** 24,525 €  (avg/day: 766 €)

**Utilization:**
- Charge hours: 60  |  Discharge hours: 52
- Energy in (grid→bat): 266.5 MWh  |  Energy out (bat→grid): 239.9 MWh
- Approx cycles over period: 23.99  ( = total discharge MWh / E )

_Greedy rule: charge the cheapest H hours, discharge the priciest H hours per day, where H≈ceil(E/P). Efficiency applied on both legs._
# nordic-imbalance-basics
Fetch, tidy, and visualize Nordic imbalance prices/volumes with hour×weekday patterns and simple risk views.

Nordic imbalance analytics: SE3/SE4/FI prices & volumes with hour-by-weekday patterns and simple deviation-risk views.
Why this exists: Imbalance exposure drives intraday/VPP decisions. This repo fetches and cleans Nordic imbalance data and gives fast visuals that help decide when to rebid vs. accept deviation.

## What’s inside

- data/ – tidy Parquet extracts (prices/volumes).
- src/ – small, typed Python utilities to fetch + QC data.
- notebooks/ – quick EDA: heatmaps, tails, and basic risk views.
- reports/ – lightweight markdown/PNGs for “what moved” this week.

## Data sources

- eSett Open Data – Nordic imbalance prices/volumes.
- (Optional) ENTSO-E – DA prices for context/spread joins.

## Outputs (first drop)
- Hour×weekday heatmaps (price & volume).
- Distributions/tails and quick “deviation-risk” snapshots.

## Roadmap (short)
- Join DA prices → “price vs. imbalance” context.
- Add FI + SE4 side-by-side; weekly markdown report.

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--da", required=True, help="DA parquet (with ts column or index)")
p.add_argument("--out", required=True, help="Output demo imbalance parquet")
args = p.parse_args()

da = pd.read_parquet(args.da)

# Build UTC index from common timestamp names or index
idx = None
if "ts_utc" in da.columns:
    idx = pd.to_datetime(da["ts_utc"], utc=True)
elif da.index.name:
    idx = pd.to_datetime(da.index, utc=True)
else:
    for k in ("ts", "timestamp_utc", "timestamp"):
        if k in da.columns:
            idx = pd.to_datetime(da[k], utc=True)
            break
if idx is None:
    raise SystemExit("Could not find a timestamp column/index in DA parquet")

# Choose a DA price column (fallback: first numeric)
dacol = None
for cand in ("price_eur_mwh", "da_price_eur_mwh", "price"):
    if cand in da.columns:
        dacol = da[cand].astype(float).to_numpy()
        break
if dacol is None:
    for c in da.columns:
        if pd.api.types.is_numeric_dtype(da[c]):
            dacol = da[c].astype(float).to_numpy()
            break
if dacol is None:
    raise SystemExit("No numeric column to base demo imbalance on")

n = len(idx)
x = pd.Series(dacol, index=pd.DatetimeIndex(idx, name="ts_utc"))

# Demo imbalance in €/MWh: DA plus small tilt + sinusoid (deterministic)
imb = x + 0.10 * (x - x.mean()) + 3.0 * np.sin(np.linspace(0, 2*np.pi, n))

out = pd.DataFrame(
    {"price_eur_mwh": imb.values, "imbalance_volume_mwh": 0.0},
    index=x.index,
)
out.index.name = "ts_utc"

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
out.to_parquet(args.out, index=True)
print(f"Wrote {args.out}  rows={len(out)}")

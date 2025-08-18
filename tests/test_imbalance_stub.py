import os
import sys
import subprocess
from pathlib import Path

import pandas as pd


def test_fetch_imbalance_stub_writes_empty_parquet(tmp_path: Path):
    # Ensure token is present for the stub (no real call happens)
    env = os.environ.copy()
    env["ENTSOE_TOKEN"] = "DUMMY_TOKEN"

    out = tmp_path / "demo.parquet"
    cmd = [
        sys.executable,
        "src/fetch_imbalance_entsoe.py",
        "--zone", "SE3",
        "--start", "2025-08-15",
        "--end", "2025-08-17",
        "--out", str(out),
    ]
    subprocess.run(cmd, check=True, env=env)

    assert out.exists(), "stub should produce an output parquet"
    df = pd.read_parquet(out)
    assert list(df.columns) == ["ts_utc", "zone", "imbalance_price_eur_mwh"]
    assert len(df) == 0

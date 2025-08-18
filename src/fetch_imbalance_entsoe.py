#!/usr/bin/env python3
"""Fetch Nordic imbalance prices (ENTSO-E REST) to Parquet — scaffold.

This first cut only validates inputs and your ENTSOE_TOKEN, then writes an
empty Parquet with the expected columns. We’ll add the real API call next.
"""

from __future__ import annotations

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


VALID_ZONES = ("SE3", "SE4", "FI")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch ENTSO-E imbalance prices and save to Parquet."
    )
    p.add_argument("--zone", required=True, choices=VALID_ZONES, help="SE3 | SE4 | FI")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (exclusive)")
    p.add_argument("--out", required=True, type=Path, help="Output Parquet path")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Load token
    load_dotenv()
    token = os.getenv("ENTSOE_TOKEN") or ""
    if not token:
        print("ERROR: ENTSOE_TOKEN not found in environment or .env", file=sys.stderr)
        return 2

    # Validate dates (UTC, end exclusive)
    try:
        start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        print(f"ERROR: bad date: {exc}", file=sys.stderr)
        return 2
    if not (end > start):
        print("ERROR: end must be after start", file=sys.stderr)
        return 2

    # Stub: empty frame with expected columns
    df = pd.DataFrame(columns=["ts_utc", "zone", "imbalance_price_eur_mwh"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out)
    print(f"OK (stub): wrote empty parquet {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

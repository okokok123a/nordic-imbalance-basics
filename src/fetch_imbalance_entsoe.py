#!/usr/bin/env python3
"""Fetch Nordic imbalance prices (ENTSO-E REST) to Parquet — dry-run first.

This step adds:
- --dry-run: build and print the ENTSO-E URL (no network), still writes an
  empty Parquet with expected columns so downstream scripts don’t break.
"""

from __future__ import annotations

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
from dotenv import load_dotenv

VALID_ZONES = ("SE3", "SE4", "FI")

API_BASE = "https://web-api.tp.entsoe.eu/api"
# NB: Codes here are indicative for imbalance prices; we’ll verify next step.
DOC_IMBALANCE_PRICE = "A46"   # Imbalance price document
PROC_REALIZED = "A16"         # Realised


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch ENTSO-E imbalance prices and save to Parquet."
    )
    p.add_argument("--zone", required=True, choices=VALID_ZONES, help="SE3 | SE4 | FI")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (exclusive)")
    p.add_argument("--out", required=True, type=Path, help="Output Parquet path")
    p.add_argument("--dry-run", action="store_true", help="Print URL only; no network")
    return p.parse_args()


def ymd_to_period(s: str) -> str:
    """YYYY-MM-DD -> ENTSO-E period string YYYYMMDDHHMM (00:00)."""
    dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc, hour=0, minute=0)
    return dt.strftime("%Y%m%d%H%M")


def eic_for_zone(zone: str) -> str:
    # Try to import from local eic_codes if available; otherwise placeholder.
    try:
        # Expect a dict like EIC_BY_ZONE = {"SE3": "...", ...}
        from eic_codes import EIC_BY_ZONE  # type: ignore
        return EIC_BY_ZONE[zone]
    except Exception:
        return f"{zone}_EIC"


def main() -> int:
    args = parse_args()

    load_dotenv()
    token = os.getenv("ENTSOE_TOKEN") or ""
    if not token:
        print("ERROR: ENTSOE_TOKEN not found in environment or .env", file=sys.stderr)
        return 2

    # Validate dates (UTC, end exclusive)
    try:
        start_dt = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        print(f"ERROR: bad date: {exc}", file=sys.stderr)
        return 2
    if not (end_dt > start_dt):
        print("ERROR: end must be after start", file=sys.stderr)
        return 2

    # Build URL (no request yet)
    params = {
        "securityToken": token,
        "documentType": DOC_IMBALANCE_PRICE,
        "processType": PROC_REALIZED,
        # Parameter name may vary per dataset; we’ll verify in the next step.
        "outBiddingZone": eic_for_zone(args.zone),
        "periodStart": ymd_to_period(args.start),
        "periodEnd": ymd_to_period(args.end),
    }
    url = f"{API_BASE}?{urlencode(params)}"

    if args.dry_run:
        print(f"DRY-RUN URL: {url}")

    # Write an empty parquet with expected columns for now
    df = pd.DataFrame(columns=["ts_utc", "zone", "imbalance_price_eur_mwh"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out)
    print(f"OK (dry-run): wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

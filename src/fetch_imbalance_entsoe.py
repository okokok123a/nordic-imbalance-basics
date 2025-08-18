#!/usr/bin/env python3
"""Fetch Nordic imbalance prices (ENTSO-E REST, A85) to Parquet.

This step enables REAL HTTP GET and saving the raw XML.
Parsing to a tidy DataFrame comes next.

Usage (UTC dates, end exclusive):
  python src/fetch_imbalance_entsoe.py --zone SE3 --start 2025-08-15 --end 2025-08-17 --out data/SE3_imbalance_api.parquet --dry-run
  python src/fetch_imbalance_entsoe.py --zone SE3 --start 2025-08-15 --end 2025-08-17 --out data/SE3_imbalance_api.parquet
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests
from dotenv import load_dotenv
from eic_codes import EIC_BY_AREA  # control area EICs per zone

VALID_ZONES = ("SE3", "SE4", "FI")

API_BASE = "https://web-api.tp.entsoe.eu/api"
DOC_IMBALANCE_PRICE = "A85"  # Imbalance Prices


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch ENTSO-E imbalance prices (A85). Saves raw XML; parquet is stub for now."
    )
    p.add_argument("--zone", required=True, choices=VALID_ZONES, help="SE3 | SE4 | FI")
    p.add_argument("--start", required=True, help="YYYY-MM-DD (UTC)")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (UTC, exclusive)")
    p.add_argument("--out", required=True, type=Path, help="Output Parquet path")
    p.add_argument("--raw-xml-out", type=Path, help="Optional path to save raw XML")
    p.add_argument("--dry-run", action="store_true", help="Print URL only; no network")
    return p.parse_args()


def ymd_to_period(s: str) -> str:
    """YYYY-MM-DD -> ENTSO-E period string YYYYMMDDHHMM (00:00 UTC)."""
    dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc, hour=0, minute=0, second=0, microsecond=0)
    return dt.strftime("%Y%m%d%H%M")


def _mask(tok: str) -> str:
    return (tok[:6] + "..." + tok[-4:]) if tok and len(tok) > 10 else "***"


def main() -> int:
    args = parse_args()

    # Token
    load_dotenv()
    token = os.getenv("ENTSOE_TOKEN") or ""
    if not token:
        print("ERROR: ENTSOE_TOKEN not found in environment or .env", file=sys.stderr)
        return 2

    # Dates (UTC, end exclusive)
    try:
        start_dt = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        print(f"ERROR: bad date: {exc}", file=sys.stderr)
        return 2
    if not (end_dt > start_dt):
        print("ERROR: end must be after start", file=sys.stderr)
        return 2

    # Build URL for A85 using control area EIC
    area_eic = EIC_BY_AREA.get(args.zone, {}).get("CONTROL_AREA") or EIC_BY_AREA.get(args.zone, {}).get("BIDDING_ZONE") or f"{args.zone}_EIC"
    params = {
        "securityToken": token,
        "documentType": DOC_IMBALANCE_PRICE,     # A85
        "controlArea_Domain": area_eic,          # control area filter
        "periodStart": ymd_to_period(args.start),
        "periodEnd": ymd_to_period(args.end),
    }
    url = f"{API_BASE}?{urlencode(params)}"

    if args.dry_run:
        print(f"DRY-RUN URL: {url.replace(token, _mask(token))}")
        # stub parquet to keep pipeline happy
        _write_empty_parquet(args.out)
        print(f"OK (dry-run): wrote {args.out}")
        return 0

    # --- REAL FETCH (no parsing yet) ---
    try:
        r = requests.get(url, timeout=45)
    except Exception as exc:
        print(f"ERROR: request failed: {exc}", file=sys.stderr)
        return 2

    if r.status_code != 200:
        print(f"ERROR: HTTP {r.status_code}\n{r.text[:1000]}", file=sys.stderr)
        return 2

    raw_xml_path = args.raw_xml_out or Path(f"data/imbalance_A85_{args.zone}_{args.start}_{args.end}.xml")
    raw_xml_path.parent.mkdir(parents=True, exist_ok=True)
    raw_xml_path.write_text(r.text, encoding="utf-8")
    print(f"Saved raw XML: {raw_xml_path}")

    # still write stub parquet (parser comes next)
    _write_empty_parquet(args.out)
    print(f"OK (fetch-only): wrote empty parquet {args.out}")
    return 0


def _write_empty_parquet(out_path: Path) -> None:
    df = pd.DataFrame(columns=["ts_utc", "zone", "imbalance_price_eur_mwh"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path)


if __name__ == "__main__":
    raise SystemExit(main())

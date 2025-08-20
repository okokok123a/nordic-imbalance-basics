"""CLI: fetch A85 (imbalance price) from ENTSO-E and write Parquet.

Step 9.2: real work
- --use-fixture reads tests/fixtures/a85_sample.xml (no token needed)
- otherwise calls ENTSO-E, parses, and writes Parquet
- safe on errors: writes empty Parquet with correct columns
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd  # type: ignore

from eic_map import CONTROL_AREA_EIC
from a85_client import fetch_raw_a85_xml
from a85_parser import parse_a85_xml


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch A85 and write Parquet (UTC; end-exclusive).")
    p.add_argument("--area", required=True, choices=sorted(CONTROL_AREA_EIC.keys()), help="Zone (e.g., SE3, SE4)")
    p.add_argument("--start", required=True, help="Start date (YYYY-MM-DD, UTC midnight)")
    p.add_argument("--end", required=True, help="End date (YYYY-MM-DD, UTC midnight, end-exclusive)")
    p.add_argument("--out", required=True, help="Output Parquet path")
    p.add_argument("--use-fixture", action="store_true", help="Use offline XML fixture instead of calling ENTSO-E")
    return p.parse_args()


def _to_utc_midnight(date_str: str) -> datetime:
    # parse YYYY-MM-DD → tz-aware UTC midnight
    return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)


def _write_parquet(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # ensure columns in empty case
    if df.empty:
        df = pd.DataFrame(columns=["ts_utc", "price_eur_mwh", "control_area_eic"])
    df.to_parquet(out_path, index=False)


def main() -> int:
    args = _parse_args()
    ca_eic = CONTROL_AREA_EIC[args.area]
    start_utc = _to_utc_midnight(args.start)
    end_utc = _to_utc_midnight(args.end)
    out_path = Path(args.out)

    try:
        if args.use_fixture:
            xml_text = Path("tests/fixtures/a85_sample.xml").read_text(encoding="utf-8")
        else:
            xml_text = fetch_raw_a85_xml(ca_eic, start_utc, end_utc)
        df = parse_a85_xml(xml_text)
    except Exception as e:
        print(f"[warn] A85 fetch/parse failed: {e}")
        df = pd.DataFrame()  # safe empty

    _write_parquet(df, out_path)

    print(f"[done] area={args.area} rows={len(df)} out={out_path}")
    if df.empty:
        print("[note] wrote an EMPTY parquet (no data or error).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

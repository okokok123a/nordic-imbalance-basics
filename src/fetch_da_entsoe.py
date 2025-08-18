import argparse
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import pandas as pd
import requests
from dotenv import load_dotenv
from lxml import etree

from eic_codes import EIC_BY_AREA

API_BASE = "https://web-api.tp.entsoe.eu/api"
DOC_TYPE = "A44"   # Price document
PROC_TYPE = "A01"  # Day-ahead

# Local timezones per bidding zone (for clamping the local-day window)
TZ_BY_AREA = {
    "SE3": "Europe/Stockholm",
    "SE4": "Europe/Stockholm",
    "FI": "Europe/Helsinki",
}


def _ymd_to_period(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M")  # UTC yyyymmddHHMM


def _to_utc_day_range(start_str: str, end_str: str):
    # Build UTC day-boundaries for the API; we'll clamp to local later.
    s = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc)
    e = datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc)
    return _ymd_to_period(s), _ymd_to_period(e)


def _resolution_to_timedelta(res: str) -> timedelta:
    if res == "PT60M":
        return timedelta(hours=1)
    if res == "PT15M":
        return timedelta(minutes=15)
    raise ValueError(f"Unsupported resolution: {res}")


def _polite_get(url: str, params: dict, max_tries: int = 5) -> str:
    backoff = 1.0
    r = None
    for _ in range(max_tries):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 200:
            return r.text
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff)
            backoff = min(backoff * 2.0, 16.0)
            continue
        raise RuntimeError(f"ENTSO-E HTTP {r.status_code}: {r.text[:400]}")
    raise RuntimeError(f"ENTSO-E retry limit reached; last status {r.status_code if r else 'n/a'}")


def _parse_price_xml(xml_text: str) -> pd.DataFrame:
    root = etree.fromstring(xml_text.encode("utf-8"))
    ns = {"ns": root.nsmap.get(None)}  # default namespace
    records = []

    for ts in root.findall(".//ns:TimeSeries", namespaces=ns):
        for period in ts.findall("./ns:Period", namespaces=ns):
            start_text = period.findtext("./ns:timeInterval/ns:start", namespaces=ns)
            end_text = period.findtext("./ns:timeInterval/ns:end", namespaces=ns)
            start = datetime.fromisoformat(start_text.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_text.replace("Z", "+00:00"))
            step = _resolution_to_timedelta(period.findtext("./ns:resolution", namespaces=ns) or "PT60M")

            n = int((end - start) / step)
            timeline = [start + i * step for i in range(n)]  # 1-based positions

            for point in period.findall("./ns:Point", namespaces=ns):
                pos_text = point.findtext("./ns:position", namespaces=ns)
                price_text = point.findtext("./ns:price.amount", namespaces=ns)
                if not pos_text or price_text is None:
                    continue
                pos = int(pos_text)
                ts_utc = timeline[pos - 1]
                records.append((ts_utc, float(price_text)))

    df = pd.DataFrame(records, columns=["ts_utc", "da_price_eur_mwh"])
    if df.empty:
        return df.set_index("ts_utc")
    df = df.sort_values("ts_utc").set_index("ts_utc")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    return df


def main():
    p = argparse.ArgumentParser(description="Fetch ENTSO-E Day-Ahead prices (bidding zone) to Parquet.")
    p.add_argument("--area", required=True, choices=sorted(EIC_BY_AREA.keys()))
    p.add_argument("--start", required=True, help="YYYY-MM-DD (local day start)")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (local day start, exclusive)")
    p.add_argument("--out", required=True, help=r"Output Parquet path, e.g. data\DA_SE3_API.parquet")
    p.add_argument("--dry-run", action="store_true", help="Print the request URL and exit (no network call).")
    args = p.parse_args()

    load_dotenv()
    token = os.getenv("ENTSOE_TOKEN") or ""

    eic = EIC_BY_AREA[args.area]
    periodStart, periodEnd = _to_utc_day_range(args.start, args.end)
    params = {
        "securityToken": token,
        "documentType": DOC_TYPE,   # "A44"
        "processType": PROC_TYPE,  # "A01"
        "in_Domain": eic,
        "out_Domain": eic,        # required for DA prices
        "periodStart": periodStart,
        "periodEnd": periodEnd,
    }

    if args.dry_run:
        safe_params = {**params, "securityToken": "***REDACTED***" if token else "(missing)"}
        print("DRY-RUN URL:", f"{API_BASE}?{urlencode(safe_params)}")
        return

    if not token:
        print("ERROR: ENTSOE_TOKEN not found in environment or .env", file=sys.stderr)
        sys.exit(2)

    xml_text = _polite_get(API_BASE, params)
    df = _parse_price_xml(xml_text)

    if df.empty:
        raise RuntimeError("No data returned for the requested window.")
    if df["da_price_eur_mwh"].isna().any():
        raise RuntimeError("Missing prices detected.")

    # --- Clamp to requested local date window (per area timezone) ---
    from zoneinfo import ZoneInfo
    tz_name = TZ_BY_AREA.get(args.area, "UTC")
    local_tz = ZoneInfo(tz_name)
    start_local = pd.Timestamp(args.start).tz_localize(local_tz)
    end_local = pd.Timestamp(args.end).tz_localize(local_tz)
    idx_local = df.index.tz_convert(local_tz)
    mask = (idx_local >= start_local) & (idx_local < end_local)
    df = df.loc[mask].sort_index()
    # ----------------------------------------------------------------

    df["area"] = args.area
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_parquet(args.out)
    print(f"OK: wrote {len(df)} rows to {args.out}")


if __name__ == "__main__":
    main()

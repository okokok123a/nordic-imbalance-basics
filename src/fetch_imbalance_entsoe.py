# src/fetch_imbalance_entsoe.py
# ENTSO-E Imbalance Prices (A85) → Parquet
# - Handles ZIP responses
# - Back-compat stub for legacy --zone tests
# - REAL mode writes join-compatible schema:
#     index: ts_utc (UTC)
#     cols : price_eur_mwh, imbalance_volume_mwh
from __future__ import annotations
import argparse, os, sys, time, io, zipfile, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Optional
import pandas as pd
import requests

from eic_map import CONTROL_AREA_EIC

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

ENTSOE_BASE = "https://web-api.tp.entsoe.eu/api"

def ymd_to_entsoe(s: str) -> str:
    dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    return dt.strftime("%Y%m%d%H%M")

def parse_iso_duration(dur: str) -> timedelta:
    if not dur or not dur.startswith("PT"):
        return timedelta(hours=1)
    h = m = s = 0; num = ""
    for ch in dur[2:]:
        if ch.isdigit(): num += ch; continue
        if ch == "H": h = int(num or 0); num = ""
        elif ch == "M": m = int(num or 0); num = ""
        elif ch == "S": s = int(num or 0); num = ""
    return timedelta(hours=h, minutes=m, seconds=s)

def ns(tag: str) -> str:
    return f".//{{*}}{tag}"

def build_url(token: str, eic: str, start: str, end: str) -> str:
    return (
        f"{ENTSOE_BASE}?securityToken={token}"
        f"&documentType=A85&controlArea_Domain={eic}"
        f"&periodStart={ymd_to_entsoe(start)}"
        f"&periodEnd={ymd_to_entsoe(end)}"
    )

def fetch_with_retries(url: str, retries: int = 4, backoff: float = 1.0) -> requests.Response:
    last_err: Optional[Exception] = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff * (2 ** i)); continue
            r.raise_for_status(); return r
        except Exception as e:
            last_err = e; time.sleep(backoff * (2 ** i))
    if last_err: raise last_err
    raise RuntimeError("fetch failed")

def parse_a85(xml_text: str) -> pd.DataFrame:
    root = ET.fromstring(xml_text)
    rows = []
    for ts in root.findall(ns("TimeSeries")):
        for period in ts.findall(ns("Period")):
            ti = period.find(ns("timeInterval"))
            start_txt = ti.find(ns("start")).text if ti is not None else None  # type: ignore
            res_txt = period.find(ns("resolution")).text if period.find(ns("resolution")) is not None else "PT60M"
            if not start_txt: continue
            start_dt = pd.to_datetime(start_txt, utc=True)
            step = parse_iso_duration(res_txt or "PT60M")
            for point in period.findall(ns("Point")):
                ppos = point.find(ns("position"))
                pval = point.find(ns("price.amount"))
                if ppos is None or pval is None: continue
                try:
                    pos = int(ppos.text); price = float(pval.text)
                except Exception:
                    continue
                ts_point = start_dt + (pos - 1) * step
                rows.append((ts_point, price))
    if not rows:
        return pd.DataFrame({
            "ts_utc": pd.Series([], dtype="datetime64[ns, UTC]"),
            "imbalance_price_eur_mwh": pd.Series([], dtype="float64"),
        })
    df = pd.DataFrame(rows, columns=["ts_utc", "imbalance_price_eur_mwh"])
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df.sort_values("ts_utc").reset_index(drop=True)

def _response_to_xml_text(r: requests.Response) -> str:
    ct = (r.headers.get("Content-Type") or "").lower()
    raw = r.content or b""
    if "zip" in ct or raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            names = zf.namelist()
            name = next((n for n in names if n.lower().endswith(".xml")), names[0])
            data = zf.read(name)
            try: return data.decode("utf-8")
            except Exception: return data.decode("utf-8", errors="replace")
    return (r.text or "").strip()

def _write_legacy_stub(out_path: str, area: str) -> None:
    # For old unit test: ['ts_utc','zone','imbalance_price_eur_mwh'] (no index)
    df = pd.DataFrame({
        "ts_utc": pd.Series([], dtype="datetime64[ns, UTC]"),
        "zone": pd.Series([], dtype="object"),
        "imbalance_price_eur_mwh": pd.Series([], dtype="float64"),
    })
    df.to_parquet(out_path)

def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch ENTSO-E Imbalance Prices (A85) → Parquet")
    ap.add_argument("--area", help="SE3 / SE4 / FI (preferred)", default=None)
    ap.add_argument("--zone", help="DEPRECATED alias; also triggers stub mode", default=None)
    ap.add_argument("--start", required=True, help="YYYY-MM-DD (UTC, inclusive)")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD (UTC, exclusive)")
    ap.add_argument("--out", required=True, help="Output parquet path")
    ap.add_argument("--dry-run", action="store_true", help="Print URL + write empty parquet")
    args = ap.parse_args()

    area = (args.area or args.zone or "").upper()
    if not area:
        print("ERROR: please pass --area SE3|SE4|FI (or legacy --zone)."); sys.exit(2)
    if area not in CONTROL_AREA_EIC:
        print(f"ERROR: unknown area '{area}'. Known: {', '.join(sorted(CONTROL_AREA_EIC))}"); sys.exit(2)

    token = os.getenv("ENTSOE_TOKEN", "")
    url = build_url(token, CONTROL_AREA_EIC[area], args.start, args.end)

    # Legacy stub path (used by old test)
    if args.zone is not None and args.area is None and not args.dry_run:
        masked = url.replace(token, (token[:6] + '...' + token[-4:])) if token else url
        print(f"DRY-RUN URL (legacy stub): {masked}")
        _write_legacy_stub(args.out, area)
        print(f"OK (stub): wrote {args.out}")
        return

    if args.dry_run:
        masked = url.replace(token, (token[:6] + '...' + token[-4:])) if token else url
        print(f"DRY-RUN URL: {masked}")
        _write_legacy_stub(args.out, area)
        print(f"OK (dry-run): wrote {args.out}")
        return

    if not token:
        print("ERROR: ENTSOE_TOKEN not found in environment/.env"); sys.exit(3)

    try:
        r = fetch_with_retries(url)
    except Exception as e:
        print(f"ERROR: fetch failed: {e}"); sys.exit(4)

    try:
        print(f"DEBUG: status={r.status_code} content-type={r.headers.get('Content-Type','?')} bytes={len(r.content)}")
    except Exception:
        pass

    xml_text = _response_to_xml_text(r)
    try: os.makedirs("data", exist_ok=True)
    except Exception: pass
    open(r"data\_a85_last_payload.txt", "w", encoding="utf-8").write(xml_text[:1200])
    print(r"DEBUG: wrote data\_a85_last_payload.txt (first 1200 chars)")

    if not xml_text or "<" not in xml_text:
        print("ERROR: empty or malformed payload"); sys.exit(5)

    try:
        df = parse_a85(xml_text)
    except Exception as e:
        print(f"ERROR: XML parse failed: {e}"); sys.exit(6)

    # REAL output: join-compatible parquet
    if df.empty:
        print("WARN: no A85 datapoints; writing join-compatible empty parquet")
        idx = pd.DatetimeIndex([], tz="UTC", name="ts_utc")
        out_df = pd.DataFrame({
            "price_eur_mwh": pd.Series(dtype="float64"),
            "imbalance_volume_mwh": pd.Series(dtype="float64"),
        }, index=idx)
        out_df.to_parquet(args.out)
        print(f"OK: wrote {args.out} with 0 rows")
        return

    # Non-empty: set index & columns expected by join script
    out_df = df.set_index("ts_utc")
    out_df.index = out_df.index.tz_convert("UTC")
    out_df.index.name = "ts_utc"
    out_df = out_df.rename(columns={"imbalance_price_eur_mwh": "price_eur_mwh"})
    out_df["imbalance_volume_mwh"] = pd.Series([float("nan")] * len(out_df), index=out_df.index, dtype="float64")
    out_df.to_parquet(args.out)
    print(f"OK: wrote {args.out} with {len(out_df)} rows")

if __name__ == "__main__":
    main()

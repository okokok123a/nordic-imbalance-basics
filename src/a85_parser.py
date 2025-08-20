"""A85 parser (open-source only).

Target schema (per 15-min point):
- ts_utc: pandas.Timestamp (timezone-aware UTC)
- price_eur_mwh: float
- control_area_eic: str

Notes:
- Input is ENTSO-E A85 XML (GL_MarketDocument).
- Minimal, explicit parsing (no LLM runtime).
"""
from __future__ import annotations

from datetime import timedelta
from typing import List, Dict
import pandas as pd  # type: ignore
from lxml import etree as ET  # type: ignore


NS = {"ns": "urn:entsoe.eu:wgedi:gl-marketdocument:5:0"}


def _res_minutes(text: str) -> int:
    """Map ISO 8601 durations we expect to minutes (PT15M/PT60M)."""
    text = (text or "").upper()
    if text == "PT15M":
        return 15
    if text in ("PT60M", "PT1H"):
        return 60
    raise ValueError(f"Unsupported resolution: {text!r}")


def parse_a85_xml(xml_text: str) -> pd.DataFrame:
    """Parse raw A85 XML → tidy DataFrame (ts_utc, price_eur_mwh, control_area_eic)."""
    root = ET.fromstring(xml_text.encode("utf-8")) if isinstance(xml_text, str) else ET.fromstring(xml_text)

    # Use the first TimeSeries (most A85 payloads have one per control area)
    ts = root.find(".//ns:TimeSeries", NS)
    if ts is None:
        return pd.DataFrame(columns=["ts_utc", "price_eur_mwh", "control_area_eic"])

    ca_eic_el = ts.find(".//ns:in_Area/ns:mRID", NS)
    control_area_eic = ca_eic_el.text.strip() if ca_eic_el is not None and ca_eic_el.text else ""

    start_el = ts.find(".//ns:Period/ns:timeInterval/ns:start", NS)
    res_el = ts.find(".//ns:Period/ns:resolution", NS)
    if start_el is None or res_el is None or not start_el.text or not res_el.text:
        return pd.DataFrame(columns=["ts_utc", "price_eur_mwh", "control_area_eic"])

    start = pd.to_datetime(start_el.text, utc=True)  # tz-aware UTC
    step_min = _res_minutes(res_el.text)

    rows: List[Dict] = []
    for p in ts.findall(".//ns:Period/ns:Point", NS):
        pos_el = p.find("ns:position", NS)
        price_el = p.find("ns:price.amount", NS)
        if pos_el is None or price_el is None or not pos_el.text or not price_el.text:
            continue
        try:
            pos = int(pos_el.text)
            price = float(price_el.text)
        except ValueError:
            continue

        ts_utc = start + timedelta(minutes=(pos - 1) * step_min)
        rows.append(
            {
                "ts_utc": pd.Timestamp(ts_utc).tz_convert("UTC"),
                "price_eur_mwh": float(price),
                "control_area_eic": control_area_eic,
            }
        )

    df = pd.DataFrame(rows, columns=["ts_utc", "price_eur_mwh", "control_area_eic"])
    if not df.empty:
        df = df.sort_values("ts_utc", kind="stable").reset_index(drop=True)
    return df

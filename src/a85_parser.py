"""A85 parser (open-source only).

Target schema (per 15-min point):
- ts_utc: pandas.Timestamp (timezone-aware UTC)
- price_eur_mwh: float
- control_area_eic: str

Notes:
- Input is ENTSO-E A85 XML (GL_MarketDocument).
- We keep parsing minimal and explicit (no LLM runtime).
"""
from __future__ import annotations

import pandas as pd  # type: ignore


def parse_a85_xml(xml_text: str) -> pd.DataFrame:
    """Parse raw A85 XML into a tidy DataFrame (see schema above)."""
    raise NotImplementedError("Parsing not implemented yet (step 8.2).")

"""Open-source A85 client (requests-based). No LLM runtime.
Manual code from 2025-08-20.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict

from dotenv import load_dotenv

API_URL = "https://transparency.entsoe.eu/api"


def get_token() -> str:
    """Load ENTSOE_TOKEN from .env/environment; raise clear error if missing."""
    load_dotenv()
    token = os.getenv("ENTSOE_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing ENTSOE_TOKEN. Create a local .env with ENTSOE_TOKEN=..."
            " (see README)."
        )
    return token


def to_entsoe_period(dt: datetime) -> str:
    """UTC datetime -> 'YYYYMMDDHHMM'"""
    return dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M")


def build_a85_params(
    control_area_eic: str, start_utc: datetime, end_utc: datetime
) -> Dict[str, str]:
    """Make minimal query params for A85 (imbalance price)."""
    return {
        "securityToken": get_token(),
        "documentType": "A85",
        "controlArea": control_area_eic,
        "periodStart": to_entsoe_period(start_utc),
        "periodEnd": to_entsoe_period(end_utc),
    }

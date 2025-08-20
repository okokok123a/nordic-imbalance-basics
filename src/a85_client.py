"""Open-source A85 client (requests-based). No LLM runtime. Manual code from 2025-08-20."""
from __future__ import annotations
import os
from dotenv import load_dotenv

API_URL = "https://transparency.entsoe.eu/api"

def get_token() -> str:
    """Load ENTSOE_TOKEN from .env/environment; raise clear error if missing."""
    load_dotenv()
    token = os.getenv("ENTSOE_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing ENTSOE_TOKEN. Create a local .env with ENTSOE_TOKEN=... (see README)."
        )
    return token

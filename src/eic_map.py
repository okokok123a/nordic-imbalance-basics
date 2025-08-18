# src/eic_map.py
# Single source of truth for EICs

# Control Area EICs (used by A85 Imbalance Prices)
CONTROL_AREA_EIC = {
    "SE3": "10YSE-1--------K",  # Sweden (Svk)
    "SE4": "10YSE-1--------K",  # Sweden (Svk)
    "FI":  "10YFI-1--------U",  # Finland (Fingrid)
}

# Bidding Zone EICs (used by Day-Ahead prices etc.)
BIDDING_ZONE_EIC = {
    "SE3": "10Y1001A1001A46L",
    "SE4": "10Y1001A1001A47J",
}

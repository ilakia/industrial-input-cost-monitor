"""Settings for ingestion. Every value can be overridden with an environment variable."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Where raw files (as received) and landing files (parsed CSVs for dbt) are written
DATA_DIR = PROJECT_ROOT / os.getenv("LOCAL_DATA_DIR", "data")
RAW_DIR = DATA_DIR / "raw"
LANDING_DIR = DATA_DIR / "landing"

# World Bank Pink Sheet. The URL contains a document id that changes between editions,
# so check https://www.worldbank.org/en/research/commodity-markets if downloads start failing.
PINK_SHEET_URL = os.getenv(
    "PINK_SHEET_URL",
    "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/"
    "related/CMO-Historical-Data-Monthly.xlsx",
)
PINK_SHEET_NAME = "Monthly Prices"

# Column header in the Pink Sheet -> our commodity id
COMMODITY_COLUMNS = {
    "Copper": "copper",
    "Aluminum": "aluminium",
    "Iron ore, cfr spot": "iron_ore",
    "Crude oil, Brent": "brent_crude",
}

# Frankfurter v2, restricted to the ECB as the only provider (v1 is deprecated)
FX_API_URL = os.getenv("FX_API_URL", "https://api.frankfurter.dev/v2/providers/ecb/rates")
FX_BASE = "USD"
FX_QUOTE = "EUR"
FX_START_DATE = os.getenv("FX_START_DATE", "1999-01-04")  # first ECB euro reference rate

# HTTP behaviour
HTTP_TIMEOUT_SECONDS = 60
HTTP_RETRIES = 3

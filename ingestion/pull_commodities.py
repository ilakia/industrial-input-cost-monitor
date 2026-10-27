"""Download the World Bank Pink Sheet and turn the four series we need into a long table.

Run:  python -m ingestion.pull_commodities
Output: data/raw/world_bank/ (file as received) and
        data/landing/commodities/commodity_prices.csv (parsed, for dbt)
"""

import io
import logging
import re
from datetime import date
from pathlib import Path

import pandas as pd

from ingestion import config, storage
from ingestion.http_client import fetch_bytes, make_session

log = logging.getLogger(__name__)

SOURCE = "world_bank"
LOGICAL_NAME = "CMO-Historical-Data-Monthly.xlsx"
MONTH_LABEL = re.compile(r"^(\d{4})M(\d{2})$")
MISSING_MARKERS = {"…", "...", ""}  # how the Pink Sheet shows "no value"


def parse_month(label: str) -> date:
    """'1960M01' -> date(1960, 1, 1). Anything else raises ValueError."""
    match = MONTH_LABEL.match(str(label).strip())
    if match is None:
        raise ValueError(f"not a Pink Sheet month label: {label!r}")
    year = int(match.group(1))
    month = int(match.group(2))
    if not 1 <= month <= 12:
        raise ValueError(f"month out of range in label: {label!r}")
    return date(year, month, 1)


def parse_price(value) -> float | None:
    """Number -> float; the '…' marker or an empty cell -> None (never 0)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str):
        if value.strip() in MISSING_MARKERS:
            return None
        return float(value.replace(",", ""))
    return float(value)


def parse_pink_sheet(content: bytes) -> pd.DataFrame:
    """Read the 'Monthly Prices' sheet and return month, commodity, price_usd, unit."""
    sheet = pd.read_excel(
        io.BytesIO(content), sheet_name=config.PINK_SHEET_NAME, header=None, dtype=object
    )

    # The header row is the one that names our series; units sit on the row below it.
    # Searching for it (instead of hard-coding row 4) survives small layout changes.
    header_row = None
    for i in range(min(20, len(sheet))):
        if "Copper" in sheet.iloc[i].tolist():
            header_row = i
            break
    if header_row is None:
        raise ValueError("could not find the header row with 'Copper' in the first 20 rows")

    headers = sheet.iloc[header_row].tolist()
    units = sheet.iloc[header_row + 1].tolist()
    missing = [name for name in config.COMMODITY_COLUMNS if name not in headers]
    if missing:
        raise ValueError(f"expected columns not found in Pink Sheet: {missing}")

    rows = []
    for _, line in sheet.iloc[header_row + 2 :].iterrows():
        label = line.iloc[0]
        if label is None or (isinstance(label, float) and pd.isna(label)):
            continue  # blank spacer rows
        month = parse_month(label)
        for column_name, commodity in config.COMMODITY_COLUMNS.items():
            col = headers.index(column_name)
            rows.append(
                {
                    "month": month,
                    "commodity": commodity,
                    "price_usd": parse_price(line.iloc[col]),
                    "unit": str(units[col]).strip("()"),
                    "source_column": column_name,
                }
            )

    table = pd.DataFrame(rows)
    if table.empty:
        raise ValueError("no data rows found in Pink Sheet")
    return table


def build_landing(raw_dir: Path | None = None, landing_dir: Path | None = None) -> Path:
    """Parse the newest stored Pink Sheet and write the landing CSV (overwritten each run)."""
    newest = storage.latest_files(SOURCE, raw_dir)
    if not newest:
        raise FileNotFoundError("no Pink Sheet stored yet, run the download first")
    meta = newest[0]
    table = parse_pink_sheet(meta["path"].read_bytes())
    table["source_file"] = meta["file"]
    table["ingested_at"] = meta["ingested_at"]

    out_dir = (landing_dir or config.LANDING_DIR) / "commodities"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "commodity_prices.csv"
    table.to_csv(out_path, index=False)
    log.info(
        "wrote %d rows (%s to %s) to %s",
        len(table),
        table["month"].min(),
        table["month"].max(),
        out_path,
    )
    return out_path


def main() -> None:
    session = make_session()
    content = fetch_bytes(session, config.PINK_SHEET_URL)
    storage.save_raw(SOURCE, LOGICAL_NAME, content, config.PINK_SHEET_URL)
    build_landing()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    main()

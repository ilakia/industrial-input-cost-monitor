"""Download daily USD->EUR reference rates (ECB, via the Frankfurter API), one file per year.

Run:  python -m ingestion.pull_fx
Output: data/raw/frankfurter/ (JSON as received) and
        data/landing/fx/fx_usd_eur_daily.csv (parsed, for dbt)

Monthly averages are calculated later in dbt, not here: ingestion only fetches and stores.
"""

import json
import logging
from datetime import date
from pathlib import Path

import pandas as pd

from ingestion import config, storage
from ingestion.http_client import fetch_bytes, make_session

log = logging.getLogger(__name__)

SOURCE = "frankfurter"
REQUIRED_FIELDS = ("date", "base", "quote", "rate")


def year_ranges(start: date, today: date) -> list[tuple[int, date, date]]:
    """Split start..today into (year, first_day, last_day) chunks, one per calendar year."""
    ranges = []
    for year in range(start.year, today.year + 1):
        first = max(start, date(year, 1, 1))
        last = min(today, date(year, 12, 31))
        ranges.append((year, first, last))
    return ranges


def logical_name(year: int) -> str:
    return f"fx_{config.FX_BASE.lower()}_{config.FX_QUOTE.lower()}_{year}.json"


def parse_fx_json(content: bytes) -> pd.DataFrame:
    """Frankfurter v2 returns a list of {date, base, quote, rate}. Check it, then tabulate."""
    payload = json.loads(content)
    if not isinstance(payload, list):
        raise ValueError(f"expected a JSON list of rates, got {type(payload).__name__}")
    for row in payload:
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            raise ValueError(f"rate row is missing fields {missing}: {row}")
    table = pd.DataFrame(payload, columns=list(REQUIRED_FIELDS))
    table["date"] = pd.to_datetime(table["date"], format="%Y-%m-%d").dt.date
    table["rate"] = table["rate"].astype(float)
    return table


def download(today: date | None = None, raw_dir: Path | None = None) -> None:
    today = today or date.today()
    start = date.fromisoformat(config.FX_START_DATE)
    session = make_session()
    for year, first, last in year_ranges(start, today):
        name = logical_name(year)
        # Past years are final once stored; only the current year is fetched again
        if year < today.year and storage.has_logical_file(SOURCE, name, raw_dir):
            log.info("%s already stored, skipping", name)
            continue
        params = {
            "from": first.isoformat(),
            "to": last.isoformat(),
            "base": config.FX_BASE,
            "quotes": config.FX_QUOTE,
        }
        content = fetch_bytes(session, config.FX_API_URL, params)
        parse_fx_json(content)  # refuse to store a response we cannot read
        storage.save_raw(SOURCE, name, content, config.FX_API_URL, raw_dir)


def build_landing(raw_dir: Path | None = None, landing_dir: Path | None = None) -> Path:
    """Combine the newest version of every yearly file into one CSV (overwritten each run)."""
    frames = []
    for meta in storage.latest_files(SOURCE, raw_dir):
        table = parse_fx_json(meta["path"].read_bytes())
        # The API adds the last rate *before* the start date when the start is a holiday
        # (asking from 1 Jan returns 29 Dec too). Keep only this file's own year so the
        # yearly files never overlap.
        year = int(meta["logical_name"].rsplit("_", 1)[1].split(".")[0])
        table = table[[d.year == year for d in table["date"]]].copy()
        table["source_file"] = meta["file"]
        table["ingested_at"] = meta["ingested_at"]
        frames.append(table)
    if not frames:
        raise FileNotFoundError("no FX files stored yet, run the download first")
    combined = pd.concat(frames, ignore_index=True).sort_values("date")

    out_dir = (landing_dir or config.LANDING_DIR) / "fx"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fx_usd_eur_daily.csv"
    combined.to_csv(out_path, index=False)
    log.info(
        "wrote %d rows (%s to %s) to %s",
        len(combined),
        combined["date"].min(),
        combined["date"].max(),
        out_path,
    )
    return out_path


def main() -> None:
    download()
    build_landing()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    main()

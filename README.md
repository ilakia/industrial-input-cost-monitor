# Industrial Input Cost Monitor

> Work in progress. Milestone 1 of 9: project skeleton.

A local, free data engineering pipeline that answers one question:

**How do raw material prices and the US dollar to euro exchange rate change the cost of
building an industrial product, and in which months did the cost move enough to need attention?**

## Planned output

- A monthly euro cost index for an illustrative product (a 50 MVA power transformer).
- Each month's change split into a commodity effect, an FX effect and an interaction term.
- A flag for months where the index moved by more than a configurable threshold (5 percent to start).

## Data sources (planned)

- World Bank Commodity Markets ("Pink Sheet"), monthly prices in US dollars.
- Frankfurter API (ECB reference rates), daily USD/EUR rates averaged per month.

**The bill of materials is invented. All quantities are illustrative, not company data.**

## Stack

Python, DuckDB, dbt (`dbt-duckdb`), Dagster, MinIO, PostgreSQL, Metabase, Docker, GitHub Actions, ruff.

## Setup (so far)

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Check everything works:

```bash
ruff check .
pytest
cd dbt_project && dbt debug --profiles-dir .
```

## Limits

- Bill of materials quantities are illustrative.
- Iron ore and Brent crude are proxies for electrical steel and transformer oil.
- Monthly data only. No hedging, contracts, surcharges or supplier-specific prices.
- A local prototype, not a production system.

## Licence

Code: MIT (see `LICENSE`). Data comes from its original sources under their own terms and is
not stored in this repository.

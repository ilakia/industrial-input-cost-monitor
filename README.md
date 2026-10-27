# Industrial Input Cost Monitor

> Work in progress. Milestone 2 of 9: ingestion.

A local, free data engineering pipeline that answers one question:

**How do raw material prices and the US dollar to euro exchange rate change the cost of
building an industrial product, and in which months did the cost move enough to need attention?**

## Planned output

- A monthly euro cost index for an illustrative product (a 50 MVA power transformer).
- Each month's change split into a commodity effect, an FX effect and an interaction term.
- A flag for months where the index moved by more than a configurable threshold (5 percent to start).

## Data sources

| Source | What we use | Licence / terms |
|---|---|---|
| [World Bank Commodity Markets ("Pink Sheet")](https://www.worldbank.org/en/research/commodity-markets) | Monthly prices in nominal US dollars: copper, aluminium, iron ore, Brent crude | Source: World Bank. CC BY 4.0 (World Bank default for open datasets). |
| [ECB euro foreign exchange reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html), via the [Frankfurter API](https://frankfurter.dev) (ECB provider only) | Daily USD to EUR rates since 1999-01-04 | Source: ECB. Free reuse with source cited; this project averages the daily rates per month. |

Downloaded data is not stored in this repository. Test fixtures contain a few real rows for offline tests.

**The bill of materials is invented. All quantities are illustrative, not company data.**

## Stack

Python, DuckDB, dbt (`dbt-duckdb`), Dagster, MinIO, PostgreSQL, Metabase, Docker, GitHub Actions, ruff.

## Setup and run (so far)

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Download the data (no Docker needed; writes to `data/`, safe to run repeatedly):

```bash
python -m ingestion.pull_commodities
python -m ingestion.pull_fx
```

Check everything works (offline):

```bash
ruff check .
pytest
cd dbt_project && dbt build --profiles-dir .
```

## Limits

- Bill of materials quantities are illustrative.
- Iron ore and Brent crude are proxies for electrical steel and transformer oil.
- Monthly data only. No hedging, contracts, surcharges or supplier-specific prices.
- A local prototype, not a production system.

## Licence

Code: MIT (see `LICENSE`). Data comes from its original sources under their own terms and is
not stored in this repository.

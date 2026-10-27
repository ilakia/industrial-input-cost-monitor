# Decisions log

Every important choice or problem, with the reason.

| Date | Decision or problem | Reason |
|---|---|---|
| 2026-10-27 | Use Python 3.12, not the system Python 3.15 | dbt and Dagster lag behind new Python releases; 3.12 is widely supported. Installed with Homebrew. |
| 2026-10-27 | Keep `profiles.yml` inside `dbt_project/` | Same dbt setup on every laptop and in CI; DuckDB needs no credentials, so nothing secret is stored. |
| 2026-10-27 | DuckDB path read from `DUCKDB_PATH` with a default | Lets CI point at a throwaway file without editing config. |
| 2026-10-27 | Pin exact versions in `requirements.txt` | A fresh clone installs exactly what was tested. Libraries are added milestone by milestone. |
| 2026-10-27 | Data and `.duckdb` files are git-ignored | They are rebuilt by the pipeline; only seeds and test fixtures are committed. |
| 2026-10-27 | Frankfurter **v2** with `/providers/ecb/rates`, not v1 | v1 is deprecated. v2 blends many central banks by default; the provider route keeps the series pure ECB, as the README promises. |
| 2026-10-27 | FX fetched in one request per calendar year from 1999-01-04 | Small, polite requests (~28 on first run). Past years are final and skipped on later runs; only the current year is re-fetched. |
| 2026-10-27 | Problem: a yearly FX request also returned the previous year's last rate (asking from 2024-01-01 returned 2023-12-29) | The API fills a holiday start date with the last earlier rate. Fix: when combining files, keep only rows from each file's own year. Covered by a test. |
| 2026-10-27 | Raw files stored as received, named with a 12-character SHA-256 prefix, plus a `.meta.json` (URL, hash, `ingested_at`) | Idempotent: identical content is stored once. Changed content becomes a new version, so history is never overwritten. |
| 2026-10-27 | Monthly FX averages computed in dbt, not in Python | Ingestion only fetches and stores; all transformation lives in one place (dbt). |
| 2026-10-27 | Pink Sheet header row found by searching for "Copper", not hard-coded as row 5 | Survives small layout changes; if a needed column disappears the parser raises an error instead of loading partial data. |
| 2026-10-27 | Month labels like `1960M01` parsed strictly (4-digit year, month 01–12) into the first day of the month | Anything else raises an error rather than being guessed. The `…` marker becomes NULL, never 0. |
| 2026-10-27 | Note: Pink Sheet labels iron ore as `$/dmtu`, but its description sheet says the spot series (Dec 2008 onwards) is in US dollars per dry ton | Kept as received in raw/landing; to be handled as a documented assumption in silver (Milestone 4). |
| 2026-10-27 | Licences: World Bank data assumed CC BY 4.0 (World Bank default for open datasets; the catalogue entry for this exact file was not found). ECB rates: free reuse with the ECB cited as source and changes stated. Frankfurter code: MIT. | Non-commercial portfolio use; raw data is not redistributed in the repo. Sources credited in the README. |
| 2026-10-27 | Test fixtures copied from real responses: 5 real months of the Pink Sheet in its real layout, and the real API response for 2024-01-01..10 | Tests run offline and never use invented numbers. |
| 2026-10-27 | Problem: pytest could not import `ingestion` | pytest only adds `tests/` to the import path. Fix: `pythonpath = ["."]` in `pyproject.toml`. |
| 2026-10-27 | Observation: two FX requests in the first full run took about 60 s each before succeeding | Consistent with the 60 s timeout followed by a successful retry. The retry logic worked as intended. |

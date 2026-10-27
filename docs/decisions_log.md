# Decisions log

Every important choice or problem, with the reason.

| Date | Decision or problem | Reason |
|---|---|---|
| 2026-10-27 | Use Python 3.12, not the system Python 3.15 | dbt and Dagster lag behind new Python releases; 3.12 is widely supported. Installed with Homebrew. |
| 2026-10-27 | Keep `profiles.yml` inside `dbt_project/` | Same dbt setup on every laptop and in CI; DuckDB needs no credentials, so nothing secret is stored. |
| 2026-10-27 | DuckDB path read from `DUCKDB_PATH` with a default | Lets CI point at a throwaway file without editing config. |
| 2026-10-27 | Pin exact versions in `requirements.txt` | A fresh clone installs exactly what was tested. Libraries are added milestone by milestone. |
| 2026-10-27 | Data and `.duckdb` files are git-ignored | They are rebuilt by the pipeline; only seeds and test fixtures are committed. |

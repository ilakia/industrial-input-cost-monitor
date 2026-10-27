"""Placeholder test so pytest has something to run until real tests arrive in Milestone 2."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_dbt_project_exists():
    assert (PROJECT_ROOT / "dbt_project" / "dbt_project.yml").is_file()


def test_fixtures_folder_exists():
    # Tests must run offline from small files kept here
    assert (PROJECT_ROOT / "tests" / "fixtures").is_dir()

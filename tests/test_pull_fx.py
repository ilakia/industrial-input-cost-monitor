"""Offline tests for the FX parser and yearly chunking, using a real saved API response."""

import json
from datetime import date
from pathlib import Path

import pytest

from ingestion import storage
from ingestion.pull_fx import SOURCE, build_landing, logical_name, parse_fx_json, year_ranges

FIXTURE = Path(__file__).parent / "fixtures" / "fx_usd_eur_sample.json"


def test_parse_fx_json_fixture():
    table = parse_fx_json(FIXTURE.read_bytes())
    assert len(table) == 8
    assert list(table.columns) == ["date", "base", "quote", "rate"]
    first = table.iloc[1]
    assert first["date"] == date(2024, 1, 2)
    assert first["rate"] == 0.91274


def test_parse_fx_json_rejects_missing_field():
    bad = json.dumps([{"date": "2024-01-02", "base": "USD", "quote": "EUR"}]).encode()
    with pytest.raises(ValueError, match="rate"):
        parse_fx_json(bad)


def test_parse_fx_json_rejects_error_object():
    # An API error comes back as an object, not a list; it must never be stored as data
    error = json.dumps({"status": 422, "message": "invalid currency"}).encode()
    with pytest.raises(ValueError):
        parse_fx_json(error)


def test_year_ranges_cover_every_day_once():
    ranges = year_ranges(date(1999, 1, 4), date(2001, 3, 15))
    assert ranges == [
        (1999, date(1999, 1, 4), date(1999, 12, 31)),
        (2000, date(2000, 1, 1), date(2000, 12, 31)),
        (2001, date(2001, 1, 1), date(2001, 3, 15)),
    ]


def test_build_landing_drops_rows_from_previous_year(tmp_path):
    # The fixture (requested from 2024-01-01) also contains 2023-12-29
    raw_dir = tmp_path / "raw"
    storage.save_raw(SOURCE, logical_name(2024), FIXTURE.read_bytes(), "fixture", raw_dir)
    out = build_landing(raw_dir=raw_dir, landing_dir=tmp_path / "landing")
    lines = out.read_text().splitlines()
    assert len(lines) == 1 + 7  # header + the seven 2024 rows
    assert "2023-12-29" not in out.read_text()

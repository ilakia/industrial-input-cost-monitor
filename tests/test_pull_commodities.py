"""Offline tests for the Pink Sheet parser, using a tiny copy of the real layout."""

import io
from datetime import date
from pathlib import Path

import openpyxl
import pytest

from ingestion import storage
from ingestion.pull_commodities import (
    LOGICAL_NAME,
    SOURCE,
    build_landing,
    parse_month,
    parse_pink_sheet,
    parse_price,
)

FIXTURE = Path(__file__).parent / "fixtures" / "pink_sheet_sample.xlsx"


# --- month labels -------------------------------------------------------------


def test_parse_month_valid():
    assert parse_month("1960M01") == date(1960, 1, 1)
    assert parse_month("2026M09") == date(2026, 9, 1)


@pytest.mark.parametrize("label", ["1960M13", "1960M00", "1960-01", "60M01", "", "Notes"])
def test_parse_month_rejects_bad_labels(label):
    with pytest.raises(ValueError):
        parse_month(label)


# --- prices -------------------------------------------------------------------


def test_parse_price_missing_marker_is_none_not_zero():
    assert parse_price("…") is None
    assert parse_price(None) is None


def test_parse_price_numbers():
    assert parse_price(14474) == 14474.0
    assert parse_price("1.6") == 1.6


# --- whole sheet ----------------------------------------------------------------


def test_parse_pink_sheet_fixture():
    table = parse_pink_sheet(FIXTURE.read_bytes())
    # 5 months x 4 commodities
    assert len(table) == 20
    assert set(table["commodity"]) == {"copper", "aluminium", "iron_ore", "brent_crude"}
    assert table["month"].min() == date(1960, 1, 1)
    assert table["month"].max() == date(2026, 9, 1)

    copper_latest = table[(table["commodity"] == "copper") & (table["month"] == date(2026, 9, 1))]
    assert copper_latest["price_usd"].item() == 14474.0
    assert copper_latest["unit"].item() == "$/mt"


def test_parse_pink_sheet_fails_loudly_on_missing_column():
    workbook = openpyxl.load_workbook(FIXTURE)
    sheet = workbook["Monthly Prices"]
    for cell in sheet[5]:  # Excel row 5 = header row
        if cell.value == "Copper":
            cell.value = "Copper (renamed)"
    buffer = io.BytesIO()
    workbook.save(buffer)
    with pytest.raises(ValueError, match="Copper"):
        parse_pink_sheet(buffer.getvalue())


def test_build_landing_adds_lineage_columns(tmp_path):
    raw_dir = tmp_path / "raw"
    storage.save_raw(SOURCE, LOGICAL_NAME, FIXTURE.read_bytes(), "fixture", raw_dir)
    out = build_landing(raw_dir=raw_dir, landing_dir=tmp_path / "landing")
    header = out.read_text().splitlines()[0]
    assert header == "month,commodity,price_usd,unit,source_column,source_file,ingested_at"

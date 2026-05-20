from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
from polars.exceptions import ComputeError, NoDataError

from whooshql.core.frame_io import scan_any

DATA = Path(__file__).resolve().parents[2] / "data"

EMPTY_FIXTURES = {
    "colors_empty.csv",
    "empty.csv",
}

MALFORMED_DIALECT_FIXTURES = {
    "dialect_quoteall_escaped_quote.csv",
    "dialect_quoteall_skipspace.csv",
    "dialect_quotenone_escaped_delimiter.csv",
    "dialect_quotenone_escaped_quote.csv",
}

EXPECTED_SHAPES = {
    "3x3_header.csv": (3, 3),
    "colors.csv": (28, 3),
    "colors_quoted.csv": (28, 3),
    "decimals.csv": (4, 3),
    "empty_header.csv": (0, 3),
    "japan_station_radiation_partial.csv": (99, 4),
    "mixed_types.csv": (3, 4),
    "sensor_new.csv": (7, 9),
    "sensor_old.csv": (10, 9),
    "us_presidents.csv": (44, 6),
    "us_state_crime.csv": (52, 14),
}


@pytest.mark.parametrize("path", sorted(DATA.glob("*.csv")), ids=lambda path: path.name)
def test_data_folder_csv_fixture_reader_behavior(path: Path) -> None:
    if path.name in EMPTY_FIXTURES:
        with pytest.raises(NoDataError):
            scan_any(path).collect(engine="streaming")
        return

    if path.name in MALFORMED_DIALECT_FIXTURES:
        with pytest.raises(ComputeError):
            scan_any(path).collect(engine="streaming")
        return

    df = scan_any(path).collect(engine="streaming")

    assert df.width > 0
    if path.name in EXPECTED_SHAPES:
        assert df.shape == EXPECTED_SHAPES[path.name]


def test_explicit_pipe_dialect_reads_headerless_grid_fixture() -> None:
    df = scan_any(DATA / "7x7.csv", delimiter="|", has_header=False).collect(engine="streaming")

    assert df.shape == (7, 7)
    assert df.row(0) == ("0-0", "0-1", "0-2", "0-3", "0-4", "0-5", "0-6")


def test_core_scan_options_on_real_data_fixture() -> None:
    schema = scan_any(
        DATA / "mixed_types.csv",
        all_string=True,
        schema_overrides={"f_int": pl.Int64},
    ).collect_schema()

    assert schema["f_int"] == pl.Int64
    assert schema["f_float"] == pl.String
    assert schema[" f_date"] == pl.String

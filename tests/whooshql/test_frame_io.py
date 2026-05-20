from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from whooshql.core.frame_io import scan_any, sink_any


def test_scan_csv_and_sink_parquet(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    lf = scan_any(str(input_csv))
    assert lf.collect(engine="streaming").shape == (2, 2)

    output_parquet = tmp_path / "output.parquet"
    sink_any(str(output_parquet), lf)
    roundtrip = scan_any(str(output_parquet)).collect(engine="streaming")
    assert roundtrip.shape == (2, 2)


def test_scan_csv_auto_detects_pipe_delimiter(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("color|count\nblue|1\nred|2\n", encoding="utf-8")

    df = scan_any(str(input_csv)).collect(engine="streaming")

    assert df.columns == ["color", "count"]
    assert df["count"].to_list() == [1, 2]


def test_sink_stdout_defaults_to_csv(tmp_path: Path, capsys) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("a,b\n1,2\n", encoding="utf-8")

    sink_any("-", scan_any(str(input_csv)))

    captured = capsys.readouterr()
    assert captured.out == "a,b\n1,2\n"


def test_scan_csv_all_string_collects_string_schema(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("a,b\n1,true\n2,false\n", encoding="utf-8")

    schema = scan_any(str(input_csv), all_string=True).collect_schema()

    assert schema == {"a": pl.String, "b": pl.String}


def test_scan_parquet_ignores_csv_read_options(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    input_parquet = tmp_path / "input.parquet"
    pl.DataFrame({"a": [1, 2]}).write_parquet(input_parquet)

    with caplog.at_level("DEBUG", logger="whooshql.core.frame_io"):
        schema = scan_any(str(input_parquet), all_string=True).collect_schema()

    assert schema == {"a": pl.Int64}
    assert "Ignoring CSV read options for parquet input" in caplog.text


def test_schema_overrides_accept_string_aliases_and_polars_dtypes(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("zip,count\n70448,1\nMO,2\n", encoding="utf-8")

    schema = scan_any(
        str(input_csv),
        schema_overrides={"zip": "String", "count": pl.Int64},
    ).collect_schema()

    assert schema == {"zip": pl.String, "count": pl.Int64}


def test_all_string_warns_when_infer_schema_length_is_also_set(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("a\n1\n", encoding="utf-8")

    with pytest.warns(UserWarning, match="all_string=True overrides infer_schema_length"):
        schema = scan_any(str(input_csv), all_string=True, infer_schema_length=10).collect_schema()

    assert schema == {"a": pl.String}

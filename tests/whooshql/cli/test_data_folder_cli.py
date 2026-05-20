from __future__ import annotations

import csv
import json
import shutil
from io import StringIO
from math import isclose
from pathlib import Path

from typer.testing import CliRunner

from whooshql.cli import app
from whooshql.core.frame_io import scan_any

DATA = Path(__file__).resolve().parents[3] / "data"


def _rows(output: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(output)))


def test_slicer_filters_real_header_csv_rows_and_columns() -> None:
    result = CliRunner().invoke(
        app,
        [
            "slicer",
            "-i",
            str(DATA / "3x3_header.csv"),
            "-c",
            "alphas,integers",
            "-r",
            "1:3",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "alphas,integers\nbbb-bbb,10\nccc-ccc-ccc,100\n"


def test_freaker_counts_and_percentages_on_pipe_fixture() -> None:
    result = CliRunner().invoke(
        app,
        [
            "freaker",
            "-i",
            str(DATA / "colors.csv"),
            "-c",
            "color",
            "--top",
            "3",
            "--as-percent",
        ],
    )

    assert result.exit_code == 0
    rows = _rows(result.output)
    assert rows[0]["color"] == "blue"
    assert rows[0]["count"] == "5"
    assert isclose(float(rows[0]["pct"]), 5 / 28)


def test_profiler_json_reports_schema_and_metrics_on_mixed_types() -> None:
    result = CliRunner().invoke(
        app,
        ["profiler", "-i", str(DATA / "mixed_types.csv"), "--report", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["rows"] == 3
    assert payload["columns"] == 4
    assert {field["name"]: field["dtype"] for field in payload["schema"]["fields"]} == {
        "f_int": "Int64",
        "f_str": "String",
        "f_float": "Float64",
        " f_date": "String",
    }


def test_validator_passes_and_fails_field_count_checks() -> None:
    good = CliRunner().invoke(
        app,
        ["validator", "-i", str(DATA / "3x3_header.csv"), "--field-cnt", "3"],
    )
    bad = CliRunner().invoke(
        app,
        ["validator", "-i", str(DATA / "3x3_header.csv"), "--field-cnt", "99"],
    )

    assert good.exit_code == 0
    assert good.output == "rows=3 failed=0\n"
    assert bad.exit_code == 1
    assert bad.output == "rows=3 failed=3\n"


def test_viewer_transposes_a_real_record() -> None:
    result = CliRunner().invoke(
        app,
        ["viewer", "-i", str(DATA / "us_presidents.csv"), "-r", "0"],
    )

    assert result.exit_code == 0
    assert "George Washington" in result.output
    assert "Virginia" in result.output
    assert "Wikipedia Entry" in result.output


def test_sorter_orders_real_csv_by_numeric_column() -> None:
    result = CliRunner().invoke(
        app,
        ["sorter", "-i", str(DATA / "3x3_header.csv"), "--by", "integers:desc"],
    )

    assert result.exit_code == 0
    assert result.output.splitlines()[:2] == [
        "alphas,integers, floats",
        "ccc-ccc-ccc,100,100.001",
    ]


def test_converter_round_trips_real_csv_to_parquet(tmp_path: Path) -> None:
    outfile = tmp_path / "mixed.parquet"

    result = CliRunner().invoke(
        app,
        ["converter", "-i", str(DATA / "mixed_types.csv"), "-o", str(outfile)],
    )

    assert result.exit_code == 0
    assert outfile.exists()
    df = scan_any(outfile).collect(engine="streaming")
    assert df.shape == (3, 4)
    assert df["f_int"].to_list() == [2, 4, 7]


def test_differ_writes_expected_sensor_change_sets(tmp_path: Path) -> None:
    out_dir = tmp_path / "diff"

    result = CliRunner().invoke(
        app,
        [
            "differ",
            "--old",
            str(DATA / "sensor_old.csv"),
            "--new",
            str(DATA / "sensor_new.csv"),
            "--key-cols",
            "column_1",
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0
    assert len((out_dir / "same.csv").read_text(encoding="utf-8").splitlines()) == 6
    assert len((out_dir / "insert.csv").read_text(encoding="utf-8").splitlines()) == 2
    assert len((out_dir / "delete.csv").read_text(encoding="utf-8").splitlines()) == 5
    assert "4.3" in (out_dir / "chgold.csv").read_text(encoding="utf-8")
    assert "4.4" in (out_dir / "chgnew.csv").read_text(encoding="utf-8")


def test_sql_aggregates_real_pipe_delimited_fixture() -> None:
    result = CliRunner().invoke(
        app,
        [
            "sql",
            "-i",
            str(DATA / "colors.csv"),
            "--query",
            "select color, count(*) as n from colors group by color order by n desc, color asc",
        ],
    )

    assert result.exit_code == 0
    rows = _rows(result.output)
    assert rows[:4] == [
        {"color": "blue", "n": "5"},
        {"color": "black", "n": "3"},
        {"color": "green", "n": "3"},
        {"color": "pink", "n": "3"},
    ]


def test_sample_supports_head_fraction_and_stratified_modes() -> None:
    runner = CliRunner()

    head = runner.invoke(app, ["sample", "-i", str(DATA / "colors.csv"), "--rows", "2"])
    fraction = runner.invoke(
        app,
        ["sample", "-i", str(DATA / "colors.csv"), "--fraction", "0.5", "--seed", "0"],
    )
    stratified = runner.invoke(
        app,
        [
            "sample",
            "-i",
            str(DATA / "colors.csv"),
            "--stratify-by",
            "color",
            "--per-bucket",
            "1",
        ],
    )

    assert head.exit_code == 0
    assert len(_rows(head.output)) == 2
    assert fraction.exit_code == 0
    assert len(_rows(fraction.output)) == 14
    assert stratified.exit_code == 0
    assert len(_rows(stratified.output)) == 12


def test_pivot_unpivots_real_mixed_type_fixture() -> None:
    result = CliRunner().invoke(
        app,
        [
            "pivot",
            "-i",
            str(DATA / "mixed_types.csv"),
            "--unpivot-id-vars",
            "f_int",
            "--unpivot-value-vars",
            "f_str,f_float",
        ],
    )

    assert result.exit_code == 0
    rows = _rows(result.output)
    assert rows[0] == {"f_int": "2", "variable": "f_str", "value": "abc"}
    assert rows[-1] == {"f_int": "7", "variable": "f_float", "value": "5.0"}


def test_explore_reports_local_data_folder_samples() -> None:
    result = CliRunner().invoke(
        app,
        [
            "explore",
            str(DATA),
            "--report",
            "json",
            "--sample-files",
            "2",
            "--include",
            "*colors.csv",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["targets"] == [str(DATA)]
    groups = payload["groups"]
    assert any(group["sample"]["key"].endswith("colors.csv") for group in groups if group["sample"])
    assert any(
        [field["name"] for field in group["schema"]["fields"]] == ["color", "name", "location"]
        for group in groups
        if group.get("schema")
    )


def test_merger_copies_missing_and_changed_data_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    shutil.copy2(DATA / "colors.csv", source / "colors.csv")
    (source / "nested").mkdir()
    shutil.copy2(DATA / "3x3_header.csv", source / "nested" / "3x3_header.csv")
    (dest / "colors.csv").write_text("changed\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "merger",
            "--source-dir",
            str(source),
            "--dest-dir",
            str(dest),
            "--hash",
            "sha256",
        ],
    )

    assert result.exit_code == 0
    assert "planned=2 applied=2" in result.output
    assert (dest / "colors.csv").read_text(encoding="utf-8").startswith("color|name|location")
    assert (dest / "nested" / "3x3_header.csv").exists()

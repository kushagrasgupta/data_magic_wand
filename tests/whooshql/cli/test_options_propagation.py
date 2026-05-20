from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from whooshql.cli import app

CSV_FLAGS = [
    "--infer-schema-length",
    "1",
    "--all-string",
    "--schema-override",
    "zip=String",
    "--null-value",
    "NA",
    "--ignore-errors",
]


def _tiny_csv(tmp_path: Path) -> Path:
    path = tmp_path / "tiny.csv"
    path.write_text("id,zip,value\n1,70448,10\n2,90210,20\n", encoding="utf-8")
    return path


def _command_cases(tmp_path: Path, csv_path: Path) -> list[tuple[str, list[str]]]:
    out_dir = tmp_path / "diff"
    out_dir.mkdir()
    return [
        ("slicer", ["slicer", "-i", str(csv_path), "-c", "id"]),
        ("freaker", ["freaker", "-i", str(csv_path), "-c", "zip"]),
        ("profiler", ["profiler", "-i", str(csv_path), "--report", "json"]),
        ("validator", ["validator", "-i", str(csv_path), "--field-cnt", "3"]),
        ("viewer", ["viewer", "-i", str(csv_path), "-r", "0"]),
        (
            "differ",
            [
                "differ",
                "--old",
                str(csv_path),
                "--new",
                str(csv_path),
                "--key-cols",
                "id",
                "--out-dir",
                str(out_dir),
            ],
        ),
        ("sorter", ["sorter", "-i", str(csv_path), "--by", "id:asc"]),
        (
            "converter",
            ["converter", "-i", str(csv_path), "-o", str(tmp_path / "converted.parquet")],
        ),
        ("sample", ["sample", "-i", str(csv_path), "--rows", "1"]),
        (
            "pivot",
            [
                "pivot",
                "-i",
                str(csv_path),
                "--unpivot-id-vars",
                "id",
                "--unpivot-value-vars",
                "value",
            ],
        ),
        ("sql", ["sql", "-i", str(csv_path), "--query", "select * from tiny"]),
        ("explore", ["explore", str(tmp_path), "--report", "json"]),
    ]


@pytest.mark.parametrize("case_index", range(12))
def test_csv_read_options_are_accepted_by_tabular_commands(
    tmp_path: Path,
    case_index: int,
) -> None:
    csv_path = _tiny_csv(tmp_path)
    command_name, base_args = _command_cases(tmp_path, csv_path)[case_index]

    result = CliRunner().invoke(app, [*base_args, *CSV_FLAGS])

    assert result.exit_code == 0, f"{command_name} failed:\n{result.output}\n{result.exception}"

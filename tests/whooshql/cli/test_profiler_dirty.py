from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from whooshql.cli.profiler import app
from whooshql.core.errors import CSVParseError

FIXTURE = Path(__file__).parents[1] / "fixtures" / "dirty_zip.csv"


def test_default_dirty_csv_raises_csv_parse_error_with_hints() -> None:
    result = CliRunner().invoke(app, ["-i", str(FIXTURE)], catch_exceptions=True)

    assert isinstance(result.exception, CSVParseError)
    message = str(result.exception)
    assert "CSV parse error: could not parse 'MO' as Int64 at column 'Zip'" in message
    assert "whooshql viewer -i" in message
    assert "--all-string" in message
    assert "--schema-override Zip=String" in message
    assert "--ignore-errors" in message
    assert "--null-value GA" in message


def test_all_string_profiles_dirty_zip_as_string() -> None:
    result = CliRunner().invoke(
        app,
        ["-i", str(FIXTURE), "--all-string", "--top-values", "200", "--report", "md"],
    )

    assert result.exit_code == 0
    assert "| Zip | String |" in result.output
    assert "| MO | 1 |" in result.output


def test_schema_override_profiles_dirty_zip_as_string() -> None:
    result = CliRunner().invoke(
        app,
        ["-i", str(FIXTURE), "--schema-override", "Zip=String", "--report", "md"],
    )

    assert result.exit_code == 0
    assert "| Zip | String |" in result.output


def test_ignore_errors_with_short_inference_nulls_malformed_rows() -> None:
    result = CliRunner().invoke(
        app,
        [
            "-i",
            str(FIXTURE),
            "--infer-schema-length",
            "1",
            "--ignore-errors",
            "--report",
            "md",
        ],
    )

    assert result.exit_code == 0
    assert "| Zip | Int64 | 95.5% | 5 |" in result.output


def test_null_values_and_ignore_errors_null_malformed_rows() -> None:
    result = CliRunner().invoke(
        app,
        [
            "-i",
            str(FIXTURE),
            "--infer-schema-length",
            "1",
            "--null-value",
            "GA",
            "--null-value",
            "MO",
            "--null-value",
            "CA",
            "--null-value",
            "TX",
            "--ignore-errors",
            "--report",
            "md",
        ],
    )

    assert result.exit_code == 0
    assert "| Zip | Int64 | 95.5% | 5 |" in result.output

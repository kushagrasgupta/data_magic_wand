from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from whooshql.cli.viewer import app


def test_viewer_prints_all_transposed_fields(tmp_path: Path) -> None:
    input_csv = tmp_path / "wide.csv"
    input_csv.write_text(
        ",".join(f"c{idx}" for idx in range(18))
        + "\n"
        + ",".join(str(idx) for idx in range(18))
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["-i", str(input_csv), "-r", "0"])

    assert result.exit_code == 0
    assert "shape: (18, 2)" in result.output
    assert "c0" in result.output
    assert "c9" in result.output
    assert "c17" in result.output

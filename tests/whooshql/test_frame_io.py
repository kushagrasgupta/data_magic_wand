from __future__ import annotations

from pathlib import Path

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

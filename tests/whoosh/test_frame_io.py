from __future__ import annotations

from pathlib import Path

from whoosh.core.frame_io import scan_any, sink_any


def test_scan_csv_and_sink_parquet(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    lf = scan_any(str(input_csv))
    assert lf.collect(engine="streaming").shape == (2, 2)

    output_parquet = tmp_path / "output.parquet"
    sink_any(str(output_parquet), lf)
    roundtrip = scan_any(str(output_parquet)).collect(engine="streaming")
    assert roundtrip.shape == (2, 2)

from __future__ import annotations

from pathlib import Path

import typer

from whoosh.api.differ import diff_frames
from whoosh.cli.common import comma_list
from whoosh.core.frame_io import scan_any, sink_any

app = typer.Typer(help="Compare keyed old/new files and emit same/insert/delete/change sets.")


@app.command()
def run(
    old: str = typer.Option(..., "--old"),
    new: str = typer.Option(..., "--new"),
    key_cols: str = typer.Option(..., "--key-cols"),
    compare_cols: str | None = typer.Option(None, "--compare-cols"),
    ignore_cols: str | None = typer.Option(None, "--ignore-cols"),
    out_dir: str = typer.Option(".", "--out-dir"),
    to_format: str = typer.Option("csv", "--to-format"),
) -> None:
    result = diff_frames(
        scan_any(old),
        scan_any(new),
        key_cols=comma_list(key_cols),
        compare_cols=comma_list(compare_cols) if compare_cols else None,
        ignore_cols=comma_list(ignore_cols) if ignore_cols else None,
    )

    out = Path(out_dir)
    sink_any(str(out / "same.csv"), result.same, to_format=to_format)
    sink_any(str(out / "insert.csv"), result.insert, to_format=to_format)
    sink_any(str(out / "delete.csv"), result.delete, to_format=to_format)
    sink_any(str(out / "chgold.csv"), result.chgold, to_format=to_format)
    sink_any(str(out / "chgnew.csv"), result.chgnew, to_format=to_format)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

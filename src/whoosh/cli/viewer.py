from __future__ import annotations

import polars as pl
import typer

from whoosh.core.frame_io import scan_any

app = typer.Typer(help="View single records in a readable format.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    row: int = typer.Option(0, "--row", "-r"),
) -> None:
    df = scan_any(infile).slice(row, 1).collect(engine="streaming")
    record = df.transpose(include_header=True)
    with pl.Config(tbl_rows=record.height, tbl_cols=record.width):
        typer.echo(record)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

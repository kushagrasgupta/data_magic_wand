from __future__ import annotations

import typer

from whoosh.api.sql import run_sql
from whoosh.core.frame_io import sink_any

app = typer.Typer(help="Run SQL queries over one or more files with Polars SQLContext.")


@app.command()
def run(
    infile: list[str] = typer.Option(..., "--infile", "-i"),
    query: str = typer.Option(..., "--query"),
    outfile: str = typer.Option("-", "--outfile", "-o"),
    to_format: str = typer.Option("auto", "--to-format"),
) -> None:
    out = run_sql(infile, query)
    sink_any(outfile, out, to_format=to_format)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

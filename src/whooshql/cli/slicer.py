from __future__ import annotations

import typer

from whooshql.api.slice import slice_frame
from whooshql.cli.common import DialectArgs, build_dialect, exit_with_error
from whooshql.core.errors import WhooshQLError
from whooshql.core.frame_io import scan_any, sink_any

app = typer.Typer(help="Slice rows/columns from tabular files using DataGristle-compatible specs.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i", help="Input file path/URI"),
    outfile: str = typer.Option("-", "--outfile", "-o", help="Output path (default stdout)"),
    cols: str | None = typer.Option(None, "--cols", "-c", help="Include column slice spec"),
    exclude_cols: str | None = typer.Option(None, "--exclude-cols", "-C"),
    rows: str | None = typer.Option(None, "--rows", "-r", help="Include row slice spec"),
    exclude_rows: str | None = typer.Option(None, "--exclude-rows", "-R"),
    where: str | None = typer.Option(None, "--where", help="Filter expression (Polars SQL expr)"),
    has_header: bool | None = typer.Option(None, "--has-header/--no-has-header"),
    delimiter: str = typer.Option(",", "--delimiter", "-d"),
    quotechar: str = typer.Option('"', "--quotechar", "-q"),
    encoding: str = typer.Option("utf-8", "--encoding"),
    in_format: str = typer.Option("auto", "--in-format"),
    to_format: str = typer.Option("auto", "--to-format"),
    streaming: bool = typer.Option(True, "--streaming/--no-streaming"),
    seed: int = typer.Option(42, "--seed"),
) -> None:
    dialect = build_dialect(DialectArgs(delimiter=delimiter, quotechar=quotechar, has_header=has_header, encoding=encoding))
    try:
        lf = scan_any(infile, hints={"in_format": in_format}, dialect=dialect)
        out = slice_frame(
            lf,
            include_cols=cols,
            exclude_cols=exclude_cols,
            include_rows=rows,
            exclude_rows=exclude_rows,
            where=where,
            seed=seed,
        )
        sink_any(outfile, out, to_format=to_format, streaming=streaming)
    except WhooshQLError as exc:
        exit_with_error(str(exc))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

from __future__ import annotations

import typer

from whooshql.api.convert import convert
from whooshql.cli.common import DialectArgs, build_dialect, exit_with_error
from whooshql.core.errors import WhooshQLError

app = typer.Typer(help="Convert between csv/tsv/parquet/jsonl/ipc formats.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    outfile: str = typer.Option(..., "--outfile", "-o"),
    in_format: str = typer.Option("auto", "--in-format"),
    out_format: str = typer.Option("auto", "--out-format"),
    has_header: bool | None = typer.Option(None, "--has-header/--no-has-header"),
    delimiter: str = typer.Option(",", "--delimiter", "-d"),
    quotechar: str = typer.Option('"', "--quotechar", "-q"),
    encoding: str = typer.Option("utf-8", "--encoding"),
    streaming: bool = typer.Option(True, "--streaming/--no-streaming"),
    compression: str | None = typer.Option(None, "--compression"),
) -> None:
    dialect = build_dialect(DialectArgs(delimiter=delimiter, quotechar=quotechar, has_header=has_header, encoding=encoding))
    try:
        convert(
            infile,
            outfile,
            in_format=in_format,
            out_format=out_format,
            dialect=dialect,
            streaming=streaming,
            compression=compression,
        )
    except WhooshQLError as exc:
        exit_with_error(str(exc))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

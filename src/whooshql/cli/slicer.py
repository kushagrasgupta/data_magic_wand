from __future__ import annotations

import typer
from polars.exceptions import ComputeError

from whooshql.api.slice import slice_frame
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.cli.common import DialectArgs, build_dialect, exit_with_error
from whooshql.core.errors import WhooshQLError
from whooshql.core.frame_io import raise_csv_parse_error, scan_any, sink_any

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
    infer_schema_length: InferSchemaLengthOption = None,
    all_string: AllStringOption = False,
    schema_override: SchemaOverrideOption = None,
    null_value: NullValueOption = None,
    ignore_errors: IgnoreErrorsOption = False,
) -> None:
    dialect = build_dialect(DialectArgs(delimiter=delimiter, quotechar=quotechar, has_header=has_header, encoding=encoding))
    csv_options = add_csv_read_options(
        infer_schema_length=infer_schema_length,
        all_string=all_string,
        schema_override=schema_override,
        null_value=null_value,
        ignore_errors=ignore_errors,
    )
    try:
        lf = scan_any(infile, hints={"in_format": in_format}, dialect=dialect, **csv_options.to_scan_kwargs())
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
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile)
    except WhooshQLError as exc:
        exit_with_error(str(exc))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

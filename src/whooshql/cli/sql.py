from __future__ import annotations

import typer
from polars.exceptions import ComputeError

from whooshql.api.sql import run_sql
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.core.frame_io import raise_csv_parse_error, sink_any

app = typer.Typer(help="Run SQL queries over one or more files with Polars SQLContext.")


@app.command()
def run(
    infile: list[str] = typer.Option(..., "--infile", "-i"),
    query: str = typer.Option(..., "--query"),
    outfile: str = typer.Option("-", "--outfile", "-o"),
    to_format: str = typer.Option("auto", "--to-format"),
    infer_schema_length: InferSchemaLengthOption = None,
    all_string: AllStringOption = False,
    schema_override: SchemaOverrideOption = None,
    null_value: NullValueOption = None,
    ignore_errors: IgnoreErrorsOption = False,
) -> None:
    csv_options = add_csv_read_options(
        infer_schema_length=infer_schema_length,
        all_string=all_string,
        schema_override=schema_override,
        null_value=null_value,
        ignore_errors=ignore_errors,
    )
    try:
        out = run_sql(infile, query, csv_read_options=csv_options.to_scan_kwargs())
        sink_any(outfile, out, to_format=to_format)
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile[0] if len(infile) == 1 else None)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

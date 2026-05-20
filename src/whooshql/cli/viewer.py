from __future__ import annotations

import polars as pl
import typer
from polars.exceptions import ComputeError

from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.core.frame_io import raise_csv_parse_error, scan_any

app = typer.Typer(help="View single records in a readable format.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    row: int = typer.Option(0, "--row", "-r"),
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
        df = (
            scan_any(infile, **csv_options.to_scan_kwargs())
            .slice(row, 1)
            .collect(engine="streaming")
        )
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile)
    record = df.transpose(include_header=True)
    with pl.Config(tbl_rows=record.height, tbl_cols=record.width):
        typer.echo(record)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

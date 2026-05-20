from __future__ import annotations

import typer
from polars.exceptions import ComputeError

from whooshql.api.convert import convert
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
from whooshql.core.frame_io import raise_csv_parse_error

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
        convert(
            infile,
            outfile,
            in_format=in_format,
            out_format=out_format,
            dialect=dialect,
            streaming=streaming,
            compression=compression,
            csv_read_options=csv_options.to_scan_kwargs(),
        )
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile)
    except WhooshQLError as exc:
        exit_with_error(str(exc))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

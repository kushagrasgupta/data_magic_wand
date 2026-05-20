from __future__ import annotations

import typer
from polars.exceptions import ComputeError

from whooshql.api.freak import freak
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.cli.common import comma_list, exit_with_error
from whooshql.core.errors import WhooshQLError
from whooshql.core.frame_io import raise_csv_parse_error, scan_any, sink_any

app = typer.Typer(help="Frequency distributions by column(s).")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    cols: str = typer.Option(..., "--cols", "-c", help="Comma-separated columns"),
    outfile: str = typer.Option("-", "--outfile", "-o"),
    sortcol: str = typer.Option("count", "--sortcol"),
    sortorder: str = typer.Option("desc", "--sortorder"),
    top: int | None = typer.Option(None, "--top"),
    as_percent: bool = typer.Option(False, "--as-percent"),
    as_cumulative: bool = typer.Option(False, "--as-cumulative"),
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
        lf = scan_any(infile, **csv_options.to_scan_kwargs())
        out = freak(
            lf,
            comma_list(cols),
            sort_col=sortcol,
            descending=sortorder.lower() != "asc",
            top=top,
            as_percent=as_percent,
            as_cumulative=as_cumulative,
        )
        sink_any(outfile, out, to_format=to_format)
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile)
    except WhooshQLError as exc:
        exit_with_error(str(exc))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

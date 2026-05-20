from __future__ import annotations

import typer
from polars.exceptions import ComputeError

from whooshql.api.pivot import pivot_or_unpivot
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.cli.common import comma_list
from whooshql.core.frame_io import raise_csv_parse_error, scan_any, sink_any

app = typer.Typer(help="Pivot/unpivot datasets via Polars.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    outfile: str = typer.Option("-", "--outfile", "-o"),
    pivot_index: str | None = typer.Option(None, "--pivot-index"),
    pivot_columns: str | None = typer.Option(None, "--pivot-columns"),
    pivot_values: str | None = typer.Option(None, "--pivot-values"),
    agg: str = typer.Option("sum", "--agg"),
    unpivot_id_vars: str | None = typer.Option(None, "--unpivot-id-vars"),
    unpivot_value_vars: str | None = typer.Option(None, "--unpivot-value-vars"),
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
        out = pivot_or_unpivot(
            lf,
            pivot_index=comma_list(pivot_index),
            pivot_columns=comma_list(pivot_columns),
            pivot_values=comma_list(pivot_values),
            agg=agg,
            unpivot_id_vars=comma_list(unpivot_id_vars) if unpivot_id_vars is not None else None,
            unpivot_value_vars=comma_list(unpivot_value_vars) if unpivot_value_vars is not None else None,
        )
        sink_any(outfile, out, to_format=to_format)
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

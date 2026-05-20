from __future__ import annotations

import typer
from polars.exceptions import ComputeError

from whooshql.api.sample import sample
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.core.frame_io import raise_csv_parse_error, scan_any, sink_any

app = typer.Typer(help="Sample large files using row count, fraction, or stratification.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    outfile: str = typer.Option("-", "--outfile", "-o"),
    rows: int | None = typer.Option(None, "--rows"),
    fraction: float | None = typer.Option(None, "--fraction"),
    stratify_by: str | None = typer.Option(None, "--stratify-by"),
    per_bucket: int | None = typer.Option(None, "--per-bucket"),
    seed: int = typer.Option(42, "--seed"),
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
        out = sample(
            lf,
            rows=rows,
            fraction=fraction,
            stratify_by=stratify_by,
            per_bucket=per_bucket,
            seed=seed,
        )
        sink_any(outfile, out, to_format=to_format)
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

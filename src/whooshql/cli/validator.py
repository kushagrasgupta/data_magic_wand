from __future__ import annotations

import typer
from polars.exceptions import ComputeError

from whooshql.api.validate import load_json_schema, validate_frame
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.core.errors import SchemaError
from whooshql.core.frame_io import raise_csv_parse_error, scan_any, sink_any

app = typer.Typer(help="Validate records against JSON Schema-style constraints.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    outfile: str | None = typer.Option(None, "--outfile", "-o", help="Good rows output"),
    errfile: str | None = typer.Option(None, "--errfile", "-e", help="Failed rows output"),
    validschema: str | None = typer.Option(None, "--validschema"),
    field_count: int | None = typer.Option(None, "--field-cnt", "-f"),
    err_out_fields: bool = typer.Option(True, "--err-out-fields/--no-err-out-fields"),
    to_format: str = typer.Option("csv", "--to-format"),
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
        schema = load_json_schema(validschema) if validschema else None
        result = validate_frame(
            scan_any(infile, **csv_options.to_scan_kwargs()),
            schema=schema,
            field_count=field_count,
            append_errors=err_out_fields,
        )
        if outfile:
            sink_any(outfile, result.good, to_format=to_format)
        if errfile:
            sink_any(errfile, result.bad, to_format=to_format)
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile)
    except SchemaError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"rows={result.total_rows} failed={result.failed_rows}")
    if result.failed_rows:
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

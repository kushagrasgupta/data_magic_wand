from __future__ import annotations

import typer

from whoosh.api.validate import load_json_schema, validate_frame
from whoosh.core.errors import SchemaError
from whoosh.core.frame_io import scan_any, sink_any

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
) -> None:
    try:
        schema = load_json_schema(validschema) if validschema else None
        result = validate_frame(
            scan_any(infile),
            schema=schema,
            field_count=field_count,
            append_errors=err_out_fields,
        )
    except SchemaError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    if outfile:
        sink_any(outfile, result.good, to_format=to_format)
    if errfile:
        sink_any(errfile, result.bad, to_format=to_format)

    typer.echo(f"rows={result.total_rows} failed={result.failed_rows}")
    if result.failed_rows:
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

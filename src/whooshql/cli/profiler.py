from __future__ import annotations

import json

import polars as pl
import typer
from polars.exceptions import ComputeError

from whooshql.api.profile import profile_table
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.cli.common import exit_with_error
from whooshql.core.frame_io import raise_csv_parse_error, scan_any
from whooshql.reports.markdown import profile_to_markdown
from whooshql.reports.text import profile_to_text

app = typer.Typer(help="Profile table shape, column quality, and common values.")

_REPORT_FORMATS = {"text", "json", "md", "markdown"}


@app.command()
def run(
    infile: list[str] = typer.Option(..., "--infile", "-i", help="Input file. Repeat for many files."),
    report: str = typer.Option("text", "--report", help="Report format: text, md, markdown, json."),
    report_out: str | None = typer.Option(None, "--report-out", help="Write report to this path."),
    top_values: int = typer.Option(5, "--top-values", min=0, help="Top values per column."),
    infer_schema_length: InferSchemaLengthOption = None,
    all_string: AllStringOption = False,
    schema_override: SchemaOverrideOption = None,
    null_value: NullValueOption = None,
    ignore_errors: IgnoreErrorsOption = False,
) -> None:
    report_format = report.lower()
    if report_format not in _REPORT_FORMATS:
        exit_with_error(f"Unknown report format '{report}'. Choose one of: json, markdown, md, text.")

    csv_options = add_csv_read_options(
        infer_schema_length=infer_schema_length,
        all_string=all_string,
        schema_override=schema_override,
        null_value=null_value,
        ignore_errors=ignore_errors,
    )
    try:
        frames = [scan_any(path, **csv_options.to_scan_kwargs()) for path in infile]
        merged = pl.concat(frames)
        payload = profile_table(merged, top_k=top_values)
    except ComputeError as exc:
        raise_csv_parse_error(exc, path=infile[0] if len(infile) == 1 else None)

    if report_format == "json":
        content = json.dumps(payload, indent=2)
    elif report_format in {"md", "markdown"}:
        content = profile_to_markdown(payload).rstrip()
    else:
        content = profile_to_text(payload).rstrip()

    if report_out:
        with open(report_out, "w", encoding="utf-8") as fobj:
            fobj.write(content + "\n")
    else:
        typer.echo(content)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

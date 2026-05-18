from __future__ import annotations

import json

import polars as pl
import typer

from whoosh.api.profile import profile_table
from whoosh.cli.common import exit_with_error
from whoosh.core.frame_io import scan_any
from whoosh.reports.markdown import profile_to_markdown
from whoosh.reports.text import profile_to_text

app = typer.Typer(help="Profile table shape, column quality, and common values.")

_REPORT_FORMATS = {"text", "json", "md", "markdown"}


@app.command()
def run(
    infile: list[str] = typer.Option(..., "--infile", "-i", help="Input file. Repeat for many files."),
    report: str = typer.Option("text", "--report", help="Report format: text, md, markdown, json."),
    report_out: str | None = typer.Option(None, "--report-out", help="Write report to this path."),
    top_values: int = typer.Option(5, "--top-values", min=0, help="Top values per column."),
) -> None:
    report_format = report.lower()
    if report_format not in _REPORT_FORMATS:
        exit_with_error(f"Unknown report format '{report}'. Choose one of: json, markdown, md, text.")

    frames = [scan_any(path) for path in infile]
    merged = pl.concat(frames)

    payload = profile_table(merged, top_k=top_values)

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

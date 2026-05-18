from __future__ import annotations

import json

import polars as pl
import typer

from whoosh.api.profile import profile_table
from whoosh.core.frame_io import scan_any
from whoosh.reports.markdown import profile_to_markdown

app = typer.Typer(help="Profile column statistics and emit text/json reports.")


@app.command()
def run(
    infile: list[str] = typer.Option(..., "--infile", "-i"),
    report: str = typer.Option("text", "--report"),
    report_out: str | None = typer.Option(None, "--report-out"),
) -> None:
    frames = [scan_any(path) for path in infile]
    merged = pl.concat(frames)

    payload = profile_table(merged)

    if report == "json":
        content = json.dumps(payload, indent=2)
    elif report in {"md", "markdown"}:
        content = profile_to_markdown(payload).rstrip()
    else:
        lines = [f"rows={payload['rows']} columns={payload['columns']}"]
        for field in payload["fields"]:
            lines.append(
                f"- {field['field']}: dtype={field['dtype']} nulls={field['null_count']} unique={field['n_unique']}"
            )
        content = "\n".join(lines)

    if report_out:
        with open(report_out, "w", encoding="utf-8") as fobj:
            fobj.write(content + "\n")
    else:
        typer.echo(content)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

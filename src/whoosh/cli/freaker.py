from __future__ import annotations

import typer

from whoosh.api.freak import freak
from whoosh.cli.common import comma_list, exit_with_error
from whoosh.core.errors import WhooshError
from whoosh.core.frame_io import scan_any, sink_any

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
) -> None:
    try:
        lf = scan_any(infile)
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
    except WhooshError as exc:
        exit_with_error(str(exc))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

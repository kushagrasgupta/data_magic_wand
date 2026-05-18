from __future__ import annotations

import typer

from whoosh.api.sort import sort_frame
from whoosh.core.frame_io import scan_any, sink_any

app = typer.Typer(help="Sort data with multi-key expressions.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    outfile: str = typer.Option("-", "--outfile", "-o"),
    by: list[str] = typer.Option(..., "--by", "-k", help="Sort key, e.g. name:asc"),
    dedup: bool = typer.Option(False, "--dedup", "-D"),
    case_insensitive: bool = typer.Option(False, "--case-insensitive"),
    to_format: str = typer.Option("auto", "--to-format"),
) -> None:
    lf = scan_any(infile)
    out = sort_frame(lf, keys=by, dedup=dedup, case_insensitive=case_insensitive)
    sink_any(outfile, out, to_format=to_format)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

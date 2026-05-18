from __future__ import annotations

import typer

from whoosh.core.frame_io import scan_any

app = typer.Typer(help="View single records in a readable format.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    row: int = typer.Option(0, "--row", "-r"),
) -> None:
    df = scan_any(infile).slice(row, 1).collect(engine="streaming")
    typer.echo(df.transpose(include_header=True))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

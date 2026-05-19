from __future__ import annotations

import typer

from whooshql.api.sample import sample
from whooshql.core.frame_io import scan_any, sink_any

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
) -> None:
    lf = scan_any(infile)
    out = sample(
        lf,
        rows=rows,
        fraction=fraction,
        stratify_by=stratify_by,
        per_bucket=per_bucket,
        seed=seed,
    )
    sink_any(outfile, out, to_format=to_format)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

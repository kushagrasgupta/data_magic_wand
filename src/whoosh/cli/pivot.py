from __future__ import annotations

import typer

from whoosh.api.pivot import pivot_or_unpivot
from whoosh.cli.common import comma_list
from whoosh.core.frame_io import scan_any, sink_any

app = typer.Typer(help="Pivot/unpivot datasets via Polars.")


@app.command()
def run(
    infile: str = typer.Option(..., "--infile", "-i"),
    outfile: str = typer.Option("-", "--outfile", "-o"),
    pivot_index: str | None = typer.Option(None, "--pivot-index"),
    pivot_columns: str | None = typer.Option(None, "--pivot-columns"),
    pivot_values: str | None = typer.Option(None, "--pivot-values"),
    agg: str = typer.Option("sum", "--agg"),
    unpivot_id_vars: str | None = typer.Option(None, "--unpivot-id-vars"),
    unpivot_value_vars: str | None = typer.Option(None, "--unpivot-value-vars"),
    to_format: str = typer.Option("auto", "--to-format"),
) -> None:
    lf = scan_any(infile)
    out = pivot_or_unpivot(
        lf,
        pivot_index=comma_list(pivot_index),
        pivot_columns=comma_list(pivot_columns),
        pivot_values=comma_list(pivot_values),
        agg=agg,
        unpivot_id_vars=comma_list(unpivot_id_vars) if unpivot_id_vars is not None else None,
        unpivot_value_vars=comma_list(unpivot_value_vars) if unpivot_value_vars is not None else None,
    )
    sink_any(outfile, out, to_format=to_format)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

from __future__ import annotations

import typer

from whooshql import __version__
from whooshql.cli import (
    converter,
    differ,
    explore,
    freaker,
    merger,
    pivot,
    profiler,
    sample,
    slicer,
    sorter,
    sql,
    validator,
    viewer,
)

app = typer.Typer(help="whooshql: polars-native data processing toolbox")


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show whooshql version"),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit(code=0)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.command(name="slicer")(slicer.run)
app.command(name="freaker")(freaker.run)
app.command(name="profiler")(profiler.run)
app.command(name="validator")(validator.run)
app.command(name="viewer")(viewer.run)
app.command(name="differ")(differ.run)
app.command(name="sorter")(sorter.run)
app.command(name="converter")(converter.run)
app.command(name="merger")(merger.run)
app.command(name="explore")(explore.run)
app.command(name="sql")(sql.run)
app.command(name="sample")(sample.run)
app.command(name="pivot")(pivot.run)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

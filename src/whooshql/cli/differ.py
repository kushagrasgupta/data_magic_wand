from __future__ import annotations

from pathlib import Path

import typer
from polars.exceptions import ComputeError

from whooshql.api.differ import diff_frames
from whooshql.cli._csv_options import (
    AllStringOption,
    IgnoreErrorsOption,
    InferSchemaLengthOption,
    NullValueOption,
    SchemaOverrideOption,
    add_csv_read_options,
)
from whooshql.cli.common import comma_list
from whooshql.core.frame_io import raise_csv_parse_error, scan_any, sink_any

app = typer.Typer(help="Compare keyed old/new files and emit same/insert/delete/change sets.")


@app.command()
def run(
    old: str = typer.Option(..., "--old"),
    new: str = typer.Option(..., "--new"),
    key_cols: str = typer.Option(..., "--key-cols"),
    compare_cols: str | None = typer.Option(None, "--compare-cols"),
    ignore_cols: str | None = typer.Option(None, "--ignore-cols"),
    out_dir: str = typer.Option(".", "--out-dir"),
    to_format: str = typer.Option("csv", "--to-format"),
    infer_schema_length: InferSchemaLengthOption = None,
    all_string: AllStringOption = False,
    schema_override: SchemaOverrideOption = None,
    null_value: NullValueOption = None,
    ignore_errors: IgnoreErrorsOption = False,
) -> None:
    csv_options = add_csv_read_options(
        infer_schema_length=infer_schema_length,
        all_string=all_string,
        schema_override=schema_override,
        null_value=null_value,
        ignore_errors=ignore_errors,
    )
    try:
        result = diff_frames(
            scan_any(old, **csv_options.to_scan_kwargs()),
            scan_any(new, **csv_options.to_scan_kwargs()),
            key_cols=comma_list(key_cols),
            compare_cols=comma_list(compare_cols) if compare_cols else None,
            ignore_cols=comma_list(ignore_cols) if ignore_cols else None,
        )

        out = Path(out_dir)
        sink_any(str(out / "same.csv"), result.same, to_format=to_format)
        sink_any(str(out / "insert.csv"), result.insert, to_format=to_format)
        sink_any(str(out / "delete.csv"), result.delete, to_format=to_format)
        sink_any(str(out / "chgold.csv"), result.chgold, to_format=to_format)
        sink_any(str(out / "chgnew.csv"), result.chgnew, to_format=to_format)
    except ComputeError as exc:
        raise_csv_parse_error(exc)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

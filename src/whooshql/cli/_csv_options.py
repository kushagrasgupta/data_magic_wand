from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

import typer


@dataclass(slots=True, frozen=True)
class CSVReadOptions:
    infer_schema_length: int | None
    all_string: bool
    schema_overrides: dict[str, str]
    null_values: list[str]
    ignore_errors: bool

    def to_scan_kwargs(self) -> dict[str, Any]:
        return {
            "infer_schema_length": self.infer_schema_length,
            "all_string": self.all_string,
            "schema_overrides": self.schema_overrides or None,
            "null_values": self.null_values or None,
            "ignore_errors": self.ignore_errors,
        }


InferSchemaLengthOption = Annotated[
    int | None,
    typer.Option(
        "--infer-schema-length",
        min=0,
        help="Rows Polars scans for CSV type inference. Omit to keep Polars' default.",
    ),
]
AllStringOption = Annotated[
    bool,
    typer.Option(
        "--all-string/--no-all-string",
        help="Read CSV columns as strings by setting infer_schema_length=0.",
    ),
]
SchemaOverrideOption = Annotated[
    list[str] | None,
    typer.Option(
        "--schema-override",
        "-X",
        help="CSV dtype override as col=Type. Repeatable, e.g. -X Zip=String.",
    ),
]
NullValueOption = Annotated[
    list[str] | None,
    typer.Option(
        "--null-value",
        help="Additional CSV null value. Repeatable.",
    ),
]
IgnoreErrorsOption = Annotated[
    bool,
    typer.Option(
        "--ignore-errors/--no-ignore-errors",
        help="Let Polars continue when CSV values fail to parse.",
    ),
]


def add_csv_read_options(
    infer_schema_length: InferSchemaLengthOption = None,
    all_string: AllStringOption = False,
    schema_override: SchemaOverrideOption = None,
    null_value: NullValueOption = None,
    ignore_errors: IgnoreErrorsOption = False,
) -> CSVReadOptions:
    """Inject shared CSV read flags into a Typer command.

    Commands expose:

    * ``--infer-schema-length INT``
    * ``--all-string`` / ``--no-all-string``
    * ``--schema-override col=Type`` (repeatable, e.g. ``-X Zip=String``)
    * ``--null-value VALUE`` (repeatable)
    * ``--ignore-errors`` / ``--no-ignore-errors``
    """
    overrides: dict[str, str] = {}
    for item in schema_override or []:
        column, separator, dtype = item.partition("=")
        if not separator or not column.strip() or not dtype.strip():
            raise typer.BadParameter(
                "--schema-override must use col=Type syntax, e.g. Zip=String"
            )
        overrides[column.strip()] = dtype.strip()

    return CSVReadOptions(
        infer_schema_length=infer_schema_length,
        all_string=all_string,
        schema_overrides=overrides,
        null_values=list(null_value or []),
        ignore_errors=ignore_errors,
    )

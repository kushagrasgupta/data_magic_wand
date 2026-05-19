from __future__ import annotations

from dataclasses import dataclass

import typer

from whooshql.core.dialect import CSVDialect, QuotingMode


@dataclass(frozen=True, slots=True)
class DialectArgs:
    delimiter: str = ","
    quotechar: str = '"'
    has_header: bool | None = None
    encoding: str = "utf-8"


def build_dialect(args: DialectArgs) -> CSVDialect:
    return CSVDialect(
        delimiter=args.delimiter,
        quotechar=args.quotechar,
        has_header=args.has_header,
        encoding=args.encoding,
        quoting=QuotingMode.MINIMAL,
    )


def comma_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def exit_with_error(message: str, *, code: int = 1) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(code=code)

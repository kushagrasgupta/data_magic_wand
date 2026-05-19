from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from whooshql.core.errors import DialectError


class QuotingMode(StrEnum):
    MINIMAL = "minimal"
    ALL = "all"
    NONNUMERIC = "nonnumeric"
    NONE = "none"

    def to_csv_constant(self) -> int:
        mapping = {
            QuotingMode.MINIMAL: csv.QUOTE_MINIMAL,
            QuotingMode.ALL: csv.QUOTE_ALL,
            QuotingMode.NONNUMERIC: csv.QUOTE_NONNUMERIC,
            QuotingMode.NONE: csv.QUOTE_NONE,
        }
        return mapping[self]


@dataclass(frozen=True, slots=True)
class CSVDialect:
    delimiter: str = ","
    quotechar: str = '"'
    doublequote: bool = True
    escapechar: str | None = None
    lineterminator: str = "\n"
    quoting: QuotingMode = QuotingMode.MINIMAL
    has_header: bool | None = None
    skip_initial_space: bool = False
    encoding: str = "utf-8"
    null_values: tuple[str, ...] = ("", "NULL", "NA")

    def to_polars_kwargs(self) -> dict[str, Any]:
        has_header = self.has_header if self.has_header is not None else True
        encoding = "utf8" if self.encoding.lower() in {"utf-8", "utf8"} else self.encoding
        return {
            "separator": self.delimiter,
            "quote_char": self.quotechar,
            "has_header": has_header,
            "encoding": encoding,
            "null_values": list(self.null_values),
            "truncate_ragged_lines": False,
            "ignore_errors": False,
        }

    def to_arrow_options(self) -> dict[str, Any]:
        return {
            "delimiter": self.delimiter,
            "quote_char": self.quotechar,
            "double_quote": self.doublequote,
            "escape_char": self.escapechar,
        }

    def to_snowflake_format(self) -> str:
        quoted_escape = f"'{self.escapechar}'" if self.escapechar else "NONE"
        return (
            f"TYPE = CSV FIELD_DELIMITER = '{self.delimiter}' "
            f"FIELD_OPTIONALLY_ENCLOSED_BY = '{self.quotechar}' "
            f"ESCAPE = {quoted_escape} SKIP_HEADER = {1 if self.has_header else 0}"
        )

    @classmethod
    def auto(cls, path: str | Path, *, sample_bytes: int = 131_072) -> CSVDialect:
        text = Path(path).read_text(encoding="utf-8", errors="replace")[:sample_bytes]
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(text)
            has_header = sniffer.has_header(text)
        except csv.Error as exc:
            raise DialectError(f"Could not infer CSV dialect from {path}: {exc}") from exc

        quoting_map = {
            csv.QUOTE_MINIMAL: QuotingMode.MINIMAL,
            csv.QUOTE_ALL: QuotingMode.ALL,
            csv.QUOTE_NONNUMERIC: QuotingMode.NONNUMERIC,
            csv.QUOTE_NONE: QuotingMode.NONE,
        }
        return cls(
            delimiter=dialect.delimiter,
            quotechar=dialect.quotechar or '"',
            doublequote=dialect.doublequote,
            escapechar=dialect.escapechar,
            lineterminator=dialect.lineterminator,
            quoting=quoting_map.get(dialect.quoting, QuotingMode.MINIMAL),
            has_header=has_header,
            skip_initial_space=dialect.skipinitialspace,
        )

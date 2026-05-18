from __future__ import annotations

from whoosh.core.dialect import CSVDialect
from whoosh.core.frame_io import scan_any, sink_any


def convert(
    infile: str,
    outfile: str,
    *,
    in_format: str = "auto",
    out_format: str = "auto",
    dialect: CSVDialect | None = None,
    streaming: bool = True,
    compression: str | None = None,
) -> None:
    lf = scan_any(infile, hints={"in_format": in_format}, dialect=dialect)
    sink_any(
        outfile,
        lf,
        to_format=out_format,
        streaming=streaming,
        compression=compression,
    )

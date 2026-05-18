from __future__ import annotations

import polars as pl

from whoosh.core.frame_io import name_from_path, scan_any


def run_sql(infiles: list[str], query: str) -> pl.LazyFrame:
    ctx = pl.SQLContext()
    for infile in infiles:
        ctx.register(name_from_path(infile), scan_any(infile))
    return ctx.execute(query)

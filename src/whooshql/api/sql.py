from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import polars as pl

from whooshql.core.frame_io import name_from_path, scan_any


def run_sql(
    infiles: list[str],
    query: str,
    *,
    csv_read_options: Mapping[str, Any] | None = None,
) -> pl.LazyFrame:
    ctx = pl.SQLContext()
    for infile in infiles:
        ctx.register(name_from_path(infile), scan_any(infile, **dict(csv_read_options or {})))
    return ctx.execute(query)

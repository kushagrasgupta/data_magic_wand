from __future__ import annotations

import polars as pl


def freak(
    lf: pl.LazyFrame,
    cols: list[str],
    *,
    sort_col: str = "count",
    descending: bool = True,
    top: int | None = None,
    as_percent: bool = False,
    as_cumulative: bool = False,
) -> pl.LazyFrame:
    out = lf.group_by(cols).agg(pl.len().alias("count"))

    if as_percent or as_cumulative:
        out = out.with_columns((pl.col("count") / pl.col("count").sum()).alias("pct"))

    if as_cumulative:
        out = out.sort("count", descending=True).with_columns(pl.col("pct").cum_sum().alias("pct_cum"))

    out = out.sort(sort_col, descending=descending)
    if top is not None and top > 0:
        out = out.head(top)
    return out

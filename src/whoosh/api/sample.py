from __future__ import annotations

import math

import polars as pl


def sample(
    lf: pl.LazyFrame,
    *,
    rows: int | None = None,
    fraction: float | None = None,
    stratify_by: str | None = None,
    per_bucket: int | None = None,
    seed: int = 42,
) -> pl.LazyFrame:
    if rows is not None and rows > 0:
        return lf.head(rows)

    if fraction is not None:
        if not 0 < fraction <= 1:
            raise ValueError("--fraction must be between 0 and 1")
        bucket = max(1, math.floor(1.0 / fraction))
        return lf.with_row_index("__idx").filter((pl.col("__idx") + seed) % bucket == 0).drop("__idx")

    if stratify_by and per_bucket:
        return (
            lf.with_columns(pl.int_range(pl.len()).over(stratify_by).alias("__rn"))
            .filter(pl.col("__rn") < per_bucket)
            .drop("__rn")
        )

    return lf

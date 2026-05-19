from __future__ import annotations

import polars as pl

from whooshql.core.slice_spec import Axis, SliceSpec, apply_col_slices, apply_row_slices


def slice_frame(
    lf: pl.LazyFrame,
    *,
    include_cols: str | None = None,
    exclude_cols: str | None = None,
    include_rows: str | None = None,
    exclude_rows: str | None = None,
    where: str | None = None,
    seed: int = 42,
) -> pl.LazyFrame:
    col_inc = SliceSpec.parse(include_cols, axis=Axis.COL)
    col_exc = SliceSpec.parse(exclude_cols, axis=Axis.COL)
    row_inc = SliceSpec.parse(include_rows, axis=Axis.ROW)
    row_exc = SliceSpec.parse(exclude_rows, axis=Axis.ROW)

    out = apply_col_slices(lf, col_inc, col_exc)
    out = apply_row_slices(out, row_inc, row_exc, seed=seed)

    if where:
        out = out.filter(pl.sql_expr(where))
    return out

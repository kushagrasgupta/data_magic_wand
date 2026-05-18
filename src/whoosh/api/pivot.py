from __future__ import annotations

from typing import Literal

import polars as pl


def pivot_or_unpivot(
    lf: pl.LazyFrame,
    *,
    pivot_index: list[str] | None = None,
    pivot_columns: list[str] | None = None,
    pivot_values: list[str] | None = None,
    agg: str = "sum",
    unpivot_id_vars: list[str] | None = None,
    unpivot_value_vars: list[str] | None = None,
) -> pl.LazyFrame:
    if pivot_index and pivot_columns and pivot_values:
        fn: Literal["sum", "mean", "min", "max", "first"] = {
            "sum": "sum",
            "mean": "mean",
            "min": "min",
            "max": "max",
            "first": "first",
        }.get(agg, "sum")  # type: ignore[assignment]
        return (
            lf.collect(engine="streaming")
            .pivot(index=pivot_index, on=pivot_columns, values=pivot_values, aggregate_function=fn)
            .lazy()
        )

    if unpivot_id_vars is not None:
        df = lf.collect(engine="streaming")
        out = df.unpivot(index=unpivot_id_vars, on=unpivot_value_vars)
        return out.lazy()

    return lf

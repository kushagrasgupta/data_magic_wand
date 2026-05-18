from __future__ import annotations

from typing import Any

import polars as pl

from whoosh.core.schema import TableSchema


def profile_table(lf: pl.LazyFrame, *, top_k: int = 10) -> dict[str, Any]:
    schema = TableSchema.from_polars(lf)
    total_rows = int(lf.select(pl.len().alias("rows")).collect().item())

    fields: list[dict[str, Any]] = []
    for field in schema.fields:
        col = pl.col(field.name)
        exprs = [
            pl.len().alias("rows"),
            col.null_count().alias("null_count"),
            col.n_unique().alias("n_unique"),
        ]

        if field.dtype.startswith(("Int", "UInt", "Float")):
            exprs.extend([
                col.min().alias("min"),
                col.max().alias("max"),
                col.mean().alias("mean"),
            ])
        else:
            exprs.extend([
                col.cast(pl.String).str.len_chars().min().alias("min_length"),
                col.cast(pl.String).str.len_chars().max().alias("max_length"),
            ])

        metrics = lf.select(exprs).collect().to_dicts()[0]
        top_values = (
            lf.group_by(field.name)
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(top_k)
            .collect()
            .to_dicts()
        )

        fields.append({"field": field.name, "dtype": field.dtype, **metrics, "top_values": top_values})

    return {
        "rows": total_rows,
        "columns": len(schema.fields),
        "schema": schema.model_dump(),
        "fields": fields,
    }

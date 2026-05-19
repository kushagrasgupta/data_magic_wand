from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True, slots=True)
class DiffResult:
    same: pl.LazyFrame
    insert: pl.LazyFrame
    delete: pl.LazyFrame
    chgold: pl.LazyFrame
    chgnew: pl.LazyFrame


def diff_frames(
    old: pl.LazyFrame,
    new: pl.LazyFrame,
    *,
    key_cols: list[str],
    compare_cols: list[str] | None = None,
    ignore_cols: list[str] | None = None,
) -> DiffResult:
    if not key_cols:
        raise ValueError("At least one key column is required")

    old_cols = old.collect_schema().names()
    new_cols = new.collect_schema().names()
    missing = [col for col in key_cols if col not in old_cols or col not in new_cols]
    if missing:
        raise ValueError(f"Key columns missing from one or both inputs: {', '.join(missing)}")

    if compare_cols:
        cols = compare_cols
    else:
        ignored = set(ignore_cols or []) | set(key_cols)
        cols = [col for col in old_cols if col in new_cols and col not in ignored]

    inserts = new.join(old.select(key_cols), on=key_cols, how="anti")
    deletes = old.join(new.select(key_cols), on=key_cols, how="anti")

    common = new.join(old, on=key_cols, how="inner", suffix="__old")
    if cols:
        changed_expr = pl.any_horizontal(
            [
                pl.col(col).fill_null("__WHOOSH_NULL__")
                != pl.col(f"{col}__old").fill_null("__WHOOSH_NULL__")
                for col in cols
            ]
        )
    else:
        changed_expr = pl.lit(False)

    changed = common.filter(changed_expr)
    same_joined = common.filter(~changed_expr)

    same = same_joined.select(new_cols)
    chgnew = changed.select(new_cols)
    chgold_selects = [
        pl.col(col) if col in key_cols else pl.col(f"{col}__old").alias(col) for col in old_cols
    ]
    chgold = changed.select(chgold_selects)

    return DiffResult(same=same, insert=inserts, delete=deletes, chgold=chgold, chgnew=chgnew)

from __future__ import annotations

import polars as pl


def parse_sort_keys(keys: list[str]) -> tuple[list[str], list[bool]]:
    by: list[str] = []
    descending: list[bool] = []

    for raw in keys:
        for item in raw.split(","):
            token = item.strip()
            if not token:
                continue
            parts = token.split(":")
            name = parts[0].strip()
            order = parts[1].strip().lower() if len(parts) > 1 else "asc"
            if not name:
                continue
            by.append(name)
            descending.append(order in {"desc", "descending", "d", "-1"})

    if not by:
        raise ValueError("At least one sort key is required")
    return by, descending


def sort_frame(
    lf: pl.LazyFrame,
    *,
    keys: list[str],
    dedup: bool = False,
    case_insensitive: bool = False,
) -> pl.LazyFrame:
    by, descending = parse_sort_keys(keys)

    if case_insensitive:
        helper_cols = [f"__whooshql_sort_{idx}" for idx, _ in enumerate(by)]
        out = lf.with_columns(
            [
                pl.col(name).cast(pl.String).str.to_lowercase().alias(helper)
                for name, helper in zip(by, helper_cols, strict=True)
            ]
        ).sort(helper_cols, descending=descending)
        if dedup:
            out = out.unique(subset=helper_cols, keep="first")
        return out.drop(helper_cols)

    out = lf.sort(by, descending=descending)
    if dedup:
        out = out.unique(subset=by, keep="first")
    return out

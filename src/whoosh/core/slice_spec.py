from __future__ import annotations

import math
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

import polars as pl

from whoosh.core.errors import SliceSpecError


class Axis(StrEnum):
    ROW = "row"
    COL = "col"


@dataclass(frozen=True, slots=True)
class SliceClause:
    start: int
    stop: int
    step: float = 1.0


@dataclass(frozen=True, slots=True)
class _ParsedToken:
    raw: str
    start: int | None
    stop: int | None
    step: float | None
    name: str | None


class SliceSpec:
    """Parse and apply DataGristle-like row/column slice expressions."""

    def __init__(self, axis: Axis, tokens: list[_ParsedToken]) -> None:
        self.axis = axis
        self.tokens = tokens

    @classmethod
    def parse(cls, s: str | None, *, axis: Axis) -> SliceSpec | None:
        if s is None:
            return None
        text = s.strip()
        if not text:
            return None

        tokens: list[_ParsedToken] = []
        for item in (part.strip() for part in text.split(",")):
            if not item:
                continue
            tokens.append(cls._parse_one(item, axis=axis))
        if not tokens:
            return None
        return cls(axis=axis, tokens=tokens)

    @staticmethod
    def _parse_one(item: str, *, axis: Axis) -> _ParsedToken:
        if ":" not in item:
            if axis == Axis.COL and not _looks_numeric(item):
                return _ParsedToken(raw=item, start=None, stop=None, step=None, name=item)
            val = _to_int(item)
            return _ParsedToken(raw=item, start=val, stop=val + 1, step=1.0, name=None)

        parts = item.split(":")
        if len(parts) > 3:
            raise SliceSpecError(f"Invalid slice token {item!r}: too many ':' separators")

        while len(parts) < 3:
            parts.append("")

        start_s, stop_s, step_s = parts
        start = _to_int(start_s) if start_s else None
        stop = _to_int(stop_s) if stop_s else None
        step = _to_float(step_s) if step_s else 1.0
        if step == 0:
            raise SliceSpecError(f"Invalid slice token {item!r}: step cannot be zero")

        return _ParsedToken(raw=item, start=start, stop=stop, step=step, name=None)

    def has_random_fraction(self) -> bool:
        for token in self.tokens:
            if token.step is not None and -1 < token.step < 1 and token.step != 0:
                return True
        return False

    def apply_rows(
        self,
        lf: pl.LazyFrame,
        *,
        item_count: int | None = None,
        seed: int = 42,
        include: bool = True,
        row_col: str = "__whoosh_rownum__",
        assume_indexed: bool = False,
        keep_index: bool = False,
    ) -> pl.LazyFrame:
        if not self.tokens:
            return lf

        framed = lf if assume_indexed else lf.with_row_index(row_col)
        if item_count is None and any(_needs_item_count(t) for t in self.tokens):
            item_count = _compute_item_count(framed)

        exprs: list[pl.Expr] = []
        for token in self.tokens:
            clause = _normalize_row_token(token, item_count=item_count)
            exprs.append(_row_expr(clause=clause, row_col=row_col, seed=seed))

        combined = pl.any_horizontal(exprs)
        if include:
            filtered = framed.filter(combined)
        else:
            filtered = framed.filter(~combined)

        if keep_index:
            return filtered
        return filtered.drop(row_col)

    def select_columns(self, columns: list[str], *, item_count: int | None = None) -> list[str]:
        if not self.tokens:
            return list(columns)

        col_count = item_count if item_count is not None else len(columns)
        selected: list[str] = []

        for token in self.tokens:
            if token.name is not None:
                if token.name not in columns:
                    raise SliceSpecError(f"Unknown column name in slice spec: {token.name!r}")
                selected.append(token.name)
                continue

            clause = _normalize_col_token(token, item_count=col_count)
            for idx in _iter_clause_indices(clause):
                if 0 <= idx < len(columns):
                    selected.append(columns[idx])
        return selected


def apply_row_slices(
    lf: pl.LazyFrame,
    include_rows: SliceSpec | None,
    exclude_rows: SliceSpec | None,
    *,
    seed: int = 42,
) -> pl.LazyFrame:
    if include_rows is None and exclude_rows is None:
        return lf

    row_col = "__whoosh_rownum__"
    out = lf.with_row_index(row_col)
    item_count = None
    if (include_rows and any(_needs_item_count(t) for t in include_rows.tokens)) or (
        exclude_rows and any(_needs_item_count(t) for t in exclude_rows.tokens)
    ):
        item_count = _compute_item_count(out)

    if include_rows is not None:
        out = include_rows.apply_rows(
            out,
            seed=seed,
            include=True,
            row_col=row_col,
            assume_indexed=True,
            keep_index=True,
            item_count=item_count,
        )
    if exclude_rows is not None:
        out = exclude_rows.apply_rows(
            out,
            seed=seed,
            include=False,
            row_col=row_col,
            assume_indexed=True,
            keep_index=True,
            item_count=item_count,
        )
    return out.drop(row_col)


def apply_col_slices(
    lf: pl.LazyFrame,
    include_cols: SliceSpec | None,
    exclude_cols: SliceSpec | None,
) -> pl.LazyFrame:
    columns = list(lf.collect_schema().names())
    included = include_cols.select_columns(columns) if include_cols is not None else columns

    if exclude_cols is not None:
        excluded = set(exclude_cols.select_columns(columns))
        included = [name for name in included if name not in excluded]

    return lf.select([pl.col(name) for name in included])


def _iter_clause_indices(clause: SliceClause) -> Iterable[int]:
    step = int(clause.step)
    if step > 0:
        yield from range(clause.start, clause.stop, step)
    else:
        yield from range(clause.start, clause.stop, step)


def _row_expr(*, clause: SliceClause, row_col: str, seed: int) -> pl.Expr:
    step = clause.step
    if -1 < step < 1 and step != 0:
        pct = abs(step)
        bucket = max(1, int(math.floor(1 / pct)))
        return ((pl.col(row_col) + seed) % bucket) == 0

    step_i = int(step)
    if step_i > 0:
        return (
            (pl.col(row_col) >= clause.start)
            & (pl.col(row_col) < clause.stop)
            & (((pl.col(row_col) - clause.start) % step_i) == 0)
        )

    abs_step = abs(step_i)
    return (
        (pl.col(row_col) <= clause.start)
        & (pl.col(row_col) > clause.stop)
        & (((clause.start - pl.col(row_col)) % abs_step) == 0)
    )


def _normalize_row_token(token: _ParsedToken, *, item_count: int | None) -> SliceClause:
    step = token.step if token.step is not None else 1.0
    if token.name is not None:
        raise SliceSpecError(f"Invalid row token {token.raw!r}: names are only valid for column slices")

    if -1 < step < 1 and step != 0:
        if token.start is None and token.stop is None:
            start = 0
            stop = item_count if item_count is not None else sys.maxsize
        else:
            start = _norm_index(token.start, item_count, default=0)
            stop = _norm_index(token.stop, item_count, default=(item_count or sys.maxsize))
        return SliceClause(start=start, stop=stop, step=step)

    step_i = int(step)
    if step_i > 0:
        if token.start is not None and token.start < 0 and token.stop == 0 and token.raw.count(":") == 0:
            start = _norm_index(token.start, item_count, default=0)
            return SliceClause(start=start, stop=start + 1, step=1.0)
        start = _norm_index(token.start, item_count, default=0)
        stop_default = item_count if item_count is not None else sys.maxsize
        stop = _norm_index(token.stop, item_count, default=stop_default)
        if start > stop:
            raise SliceSpecError(f"Invalid slice token {token.raw!r}: start > stop for positive step")
        return SliceClause(start=start, stop=stop, step=float(step_i))

    if item_count is None and token.start is None:
        raise SliceSpecError(
            f"Invalid slice token {token.raw!r}: negative step needs known row count when start is omitted"
        )

    default_start = (item_count - 1) if item_count is not None else 0
    start = _norm_index(token.start, item_count, default=default_start)
    stop = _norm_index(token.stop, item_count, default=-1)
    if start < stop:
        raise SliceSpecError(f"Invalid slice token {token.raw!r}: start < stop for negative step")
    return SliceClause(start=start, stop=stop, step=float(step_i))


def _normalize_col_token(token: _ParsedToken, *, item_count: int) -> SliceClause:
    if token.name is not None:
        raise SliceSpecError("Internal error: named column token passed to _normalize_col_token")

    step = token.step if token.step is not None else 1.0
    if int(step) != step:
        raise SliceSpecError(f"Invalid column slice token {token.raw!r}: fractional steps are not supported")

    step_i = int(step)
    if step_i == 0:
        raise SliceSpecError(f"Invalid column slice token {token.raw!r}: step cannot be zero")

    if step_i > 0:
        if token.start is not None and token.start < 0 and token.stop == 0 and token.raw.count(":") == 0:
            start = _norm_index(token.start, item_count, default=0)
            return SliceClause(start=start, stop=start + 1, step=1.0)
        start = _norm_index(token.start, item_count, default=0)
        stop = _norm_index(token.stop, item_count, default=item_count)
        if start > stop:
            raise SliceSpecError(f"Invalid column slice token {token.raw!r}: start > stop")
        return SliceClause(start=start, stop=stop, step=float(step_i))

    start = _norm_index(token.start, item_count, default=item_count - 1)
    stop = _norm_index(token.stop, item_count, default=-1)
    if start < stop:
        raise SliceSpecError(f"Invalid column slice token {token.raw!r}: start < stop for negative step")
    return SliceClause(start=start, stop=stop, step=float(step_i))


def _norm_index(val: int | None, item_count: int | None, *, default: int) -> int:
    if val is None:
        return default
    if val >= 0:
        return val
    if item_count is None:
        raise SliceSpecError("Negative indexes require known item count")
    return item_count + val


def _needs_item_count(token: _ParsedToken) -> bool:
    if token.name is not None:
        return False
    if (token.start is not None and token.start < 0) or (token.stop is not None and token.stop < 0):
        return True
    if token.step is not None and token.step < 0 and token.start is None:
        return True
    return False


def _compute_item_count(lf: pl.LazyFrame) -> int:
    return int(lf.select(pl.len().alias("n")).collect().item())


def _looks_numeric(item: str) -> bool:
    if item.startswith("-"):
        return item[1:].isdigit()
    return item.isdigit()


def _to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise SliceSpecError(f"Invalid integer in slice token: {value!r}") from exc


def _to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise SliceSpecError(f"Invalid step value in slice token: {value!r}") from exc

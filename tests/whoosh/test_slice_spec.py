from __future__ import annotations

import polars as pl

from whoosh.core.slice_spec import Axis, SliceSpec, apply_col_slices, apply_row_slices


def test_column_slice_by_index_and_name() -> None:
    lf = pl.LazyFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
    include = SliceSpec.parse(":2,c", axis=Axis.COL)
    out = apply_col_slices(lf, include, None).collect(engine="streaming")
    assert out.columns == ["a", "b", "c"]


def test_row_slice_with_step_and_exclusion() -> None:
    lf = pl.LazyFrame({"x": list(range(10))})
    include = SliceSpec.parse("1:9:2", axis=Axis.ROW)
    exclude = SliceSpec.parse("5", axis=Axis.ROW)
    out = apply_row_slices(lf, include, exclude).collect(engine="streaming")
    assert out["x"].to_list() == [1, 3, 7]


def test_negative_row_index() -> None:
    lf = pl.LazyFrame({"x": list(range(5))})
    include = SliceSpec.parse("-1", axis=Axis.ROW)
    out = apply_row_slices(lf, include, None).collect(engine="streaming")
    assert out["x"].to_list() == [4]

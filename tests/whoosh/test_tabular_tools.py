from __future__ import annotations

from pathlib import Path

import polars as pl

from whoosh.api.differ import diff_frames
from whoosh.api.merger import execute_local_merge, plan_local_merge
from whoosh.api.sort import sort_frame
from whoosh.api.validate import validate_frame
from whoosh.infer import (
    classify_manifest_key,
    detect_compression,
    detect_format,
    has_header,
    infer_delimiter,
)
from whoosh.reports.markdown import profile_to_markdown
from whoosh.reports.text import profile_to_text


def test_sort_frame_multi_key() -> None:
    lf = pl.LazyFrame({"name": ["b", "a", "a"], "score": [1, 2, 3]})
    out = sort_frame(lf, keys=["name:asc", "score:desc"]).collect(engine="streaming")
    assert out["score"].to_list() == [3, 2, 1]


def test_diff_frames_outputs_same_insert_delete_changed() -> None:
    old = pl.LazyFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})
    new = pl.LazyFrame({"id": [1, 2, 4], "value": ["a", "bb", "d"]})

    result = diff_frames(old, new, key_cols=["id"])

    assert result.same.collect(engine="streaming")["id"].to_list() == [1]
    assert result.insert.collect(engine="streaming")["id"].to_list() == [4]
    assert result.delete.collect(engine="streaming")["id"].to_list() == [3]
    assert result.chgold.collect(engine="streaming")["value"].to_list() == ["b"]
    assert result.chgnew.collect(engine="streaming")["value"].to_list() == ["bb"]


def test_validate_frame_json_schema() -> None:
    lf = pl.LazyFrame({"id": ["1", "x"], "name": ["Ada", ""]})
    schema = {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string", "minLength": 1},
        },
    }

    result = validate_frame(lf, schema=schema)

    assert result.total_rows == 2
    assert result.failed_rows == 1
    assert result.good.collect(engine="streaming")["id"].to_list() == ["1"]
    assert "_whoosh_errors" in result.bad.collect(engine="streaming").columns


def test_plan_and_execute_local_merge(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    (source / "a.csv").write_text("a\n1\n", encoding="utf-8")

    actions = plan_local_merge(str(source), str(dest))

    assert len(actions) == 1
    execute_local_merge(actions)
    assert (dest / "a.csv").read_text(encoding="utf-8") == "a\n1\n"


def test_infer_helpers_and_markdown_report() -> None:
    assert infer_delimiter("a|b\n1|2\n") == "|"
    assert has_header("a,b\n1,2\n") is True
    assert detect_format("x.parquet", b"PAR1") == "parquet"
    assert detect_compression("x.csv.gz", b"\x1f\x8b") == "gzip"
    assert classify_manifest_key("table/_delta_log/000.json") == "delta"

    markdown = profile_to_markdown(
        {
            "rows": 1,
            "columns": 1,
            "fields": [
                {
                    "field": "id",
                    "dtype": "Int64",
                    "null_count": 0,
                    "n_unique": 1,
                    "min": 1,
                    "max": 1,
                    "mean": 1.0,
                    "top_values": [{"id": 1, "count": 1}],
                }
            ],
        }
    )
    assert "# Whoosh Profile" in markdown
    assert "| id | Int64 | 100.0% | 0 | 1 | 100.0% | 1 to 1, mean 1 |" in markdown
    assert "| 1 | 1 | 100.0% |" in markdown

    text = profile_to_text(
        {
            "rows": 1,
            "columns": 1,
            "fields": [
                {
                    "field": "id",
                    "dtype": "Int64",
                    "null_count": 0,
                    "n_unique": 1,
                    "min": 1,
                    "max": 1,
                    "mean": 1.0,
                    "top_values": [{"id": 1, "count": 1}],
                }
            ],
        }
    )
    assert "id (Int64)" in text
    assert "top: 1 (1)" in text

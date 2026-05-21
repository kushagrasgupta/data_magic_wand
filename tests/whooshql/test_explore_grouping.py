from __future__ import annotations

from datetime import UTC, datetime

from whooshql.cli.explore import _apply_filters, _detect_cadence, _group_key_for
from whooshql.io.store import ObjectMeta


def test_group_key_depth() -> None:
    assert _group_key_for("a/b/c/d.csv", "depth:2") == "a/b"


def test_detect_daily_cadence() -> None:
    cadence = _detect_cadence(["2026-01-01", "2026-01-02", "2026-01-03"])
    assert cadence["label"] == "daily"


def test_since_flag_does_not_raise_on_aware_last_modified() -> None:
    """--since must not crash when S3 returns tz-aware LastModified."""
    aware_dt = datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC)
    old_aware_dt = datetime(2025, 12, 1, 0, 0, 0, tzinfo=UTC)

    items = [
        ObjectMeta(
            key="a/b/new.parquet",
            size=100,
            last_modified=aware_dt,
            etag=None,
            content_type=None,
        ),
        ObjectMeta(
            key="a/b/old.parquet",
            size=100,
            last_modified=old_aware_dt,
            etag=None,
            content_type=None,
        ),
    ]
    since = datetime(2026, 1, 1, tzinfo=UTC)

    result = _apply_filters(items, include=None, exclude=None, since=since)
    assert len(result) == 1
    assert result[0].key == "a/b/new.parquet"

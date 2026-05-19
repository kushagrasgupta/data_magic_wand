from __future__ import annotations

from whooshql.cli.explore import _detect_cadence, _group_key_for


def test_group_key_depth() -> None:
    assert _group_key_for("a/b/c/d.csv", "depth:2") == "a/b"


def test_detect_daily_cadence() -> None:
    cadence = _detect_cadence(["2026-01-01", "2026-01-02", "2026-01-03"])
    assert cadence["label"] == "daily"

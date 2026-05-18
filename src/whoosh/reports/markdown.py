from __future__ import annotations

from typing import Any


def _fmt_percent(numerator: int | float, denominator: int | float) -> str:
    if denominator == 0:
        return "n/a"
    return f"{(numerator / denominator) * 100:.1f}%"


def _md(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _column_detail(field: dict[str, Any]) -> str:
    if "min" in field or "max" in field or "mean" in field:
        parts = []
        if field.get("min") is not None or field.get("max") is not None:
            parts.append(f"{field.get('min', '')} to {field.get('max', '')}")
        if field.get("mean") is not None:
            parts.append(f"mean {field['mean']:.3g}")
        return ", ".join(parts)
    if "min_length" in field or "max_length" in field:
        return f"length {field.get('min_length', '')} to {field.get('max_length', '')}"
    return ""


def profile_to_markdown(profile: dict[str, Any]) -> str:
    rows = int(profile["rows"])
    fields = profile.get("fields", [])
    fields_with_nulls = sum(1 for field in fields if field.get("null_count", 0) > 0)

    lines = [
        "# Whoosh Profile",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Rows | {rows} |",
        f"| Columns | {profile['columns']} |",
        f"| Fields with nulls | {fields_with_nulls} |",
        "",
        "## Columns",
        "",
        "| Field | Type | Complete | Nulls | Unique | Cardinality | Detail |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for field in fields:
        nulls = int(field.get("null_count", 0))
        unique = int(field.get("n_unique", 0))
        non_null = rows - nulls
        lines.append(
            "| {field} | {dtype} | {complete} | {nulls} | {unique} | {cardinality} | {detail} |".format(
                field=_md(field["field"]),
                dtype=_md(field["dtype"]),
                complete=_fmt_percent(non_null, rows),
                nulls=nulls,
                unique=unique,
                cardinality=_fmt_percent(unique, rows),
                detail=_md(_column_detail(field)),
            )
        )

    if any(field.get("top_values") for field in fields):
        lines.extend(["", "## Top Values"])
        for field in fields:
            top_values = field.get("top_values") or []
            if not top_values:
                continue
            lines.extend(
                [
                    "",
                    f"### {_md(field['field'])}",
                    "",
                    "| Value | Count | Share |",
                    "| --- | ---: | ---: |",
                ]
            )
            for item in top_values:
                value = item.get(field["field"])
                count = int(item.get("count", 0))
                lines.append(f"| {_md(value)} | {count} | {_fmt_percent(count, rows)} |")
    return "\n".join(lines) + "\n"


def explore_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Whoosh Explore Report",
        "",
        f"- Targets: {', '.join(report.get('targets', []))}",
        f"- Grouping: {report.get('group_by')}",
        f"- Groups: {len(report.get('groups', []))}",
        "",
        "| Group | Objects | Data Objects | Size | Latest Partition | Cadence |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for group in report.get("groups", []):
        cadence = group.get("delivery_cadence", {}).get("label", "unknown")
        lines.append(
            "| {group} | {objects} | {data_objects} | {size} | {latest} | {cadence} |".format(
                group=group["group_key"],
                objects=group["object_count"],
                data_objects=group["data_object_count"],
                size=group["total_size"],
                latest=group.get("latest_partition") or "",
                cadence=cadence,
            )
        )
    return "\n".join(lines) + "\n"

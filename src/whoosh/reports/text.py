from __future__ import annotations

from typing import Any


def _fmt_percent(numerator: int | float, denominator: int | float) -> str:
    if denominator == 0:
        return "n/a"
    return f"{(numerator / denominator) * 100:.1f}%"


def _column_detail(field: dict[str, Any]) -> str:
    if "min" in field or "max" in field or "mean" in field:
        parts = []
        if field.get("min") is not None or field.get("max") is not None:
            parts.append(f"{field.get('min', '')}..{field.get('max', '')}")
        if field.get("mean") is not None:
            parts.append(f"mean={field['mean']:.3g}")
        return ", ".join(parts)
    if "min_length" in field or "max_length" in field:
        return f"len={field.get('min_length', '')}..{field.get('max_length', '')}"
    return ""


def _top_values(field: dict[str, Any]) -> str:
    values = []
    field_name = field["field"]
    for item in field.get("top_values") or []:
        values.append(f"{item.get(field_name)} ({item.get('count', 0)})")
    return ", ".join(values)


def profile_to_text(profile: dict[str, Any]) -> str:
    rows = int(profile["rows"])
    fields = profile.get("fields", [])
    fields_with_nulls = sum(1 for field in fields if field.get("null_count", 0) > 0)

    lines = [
        "Whoosh profile",
        f"Rows: {rows} | Columns: {profile['columns']} | Fields with nulls: {fields_with_nulls}",
    ]

    for field in fields:
        nulls = int(field.get("null_count", 0))
        unique = int(field.get("n_unique", 0))
        non_null = rows - nulls
        unique_display = f"{unique} ({_fmt_percent(unique, rows)})"
        stats = (
            f"complete={_fmt_percent(non_null, rows)} | "
            f"nulls={nulls} | "
            f"unique={unique_display}"
        )
        detail = _column_detail(field)
        if detail:
            stats = f"{stats} | {detail}"

        lines.extend(["", f"{field['field']} ({field['dtype']})", f"  {stats}"])
        top_values = _top_values(field)
        if top_values:
            lines.append(f"  top: {top_values}")

    return "\n".join(lines) + "\n"


def to_text(report: dict[str, Any]) -> str:
    lines = ["WHOOSH EXPLORE REPORT", ""]
    lines.append(f"targets: {', '.join(report.get('targets', []))}")
    lines.append(f"group_count: {len(report.get('groups', []))}")
    lines.append("")

    for group in report.get("groups", []):
        lines.append(f"[{group['group_key']}]")
        lines.append(f"objects={group['object_count']} data_objects={group['data_object_count']} total_size={group['total_size']}")
        if group.get("sample"):
            sample = group["sample"]
            lines.append(f"sample={sample.get('key')} format={sample.get('format')} compression={sample.get('compression')}")
        if group.get("schema"):
            lines.append(f"schema_fields={len(group['schema'].get('fields', []))}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

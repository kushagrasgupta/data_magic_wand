from __future__ import annotations

from typing import Any


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

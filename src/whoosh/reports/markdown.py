from __future__ import annotations

from typing import Any


def profile_to_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# Whoosh Profile",
        "",
        f"- Rows: {profile['rows']}",
        f"- Columns: {profile['columns']}",
        "",
        "| Field | Type | Nulls | Unique |",
        "| --- | --- | ---: | ---: |",
    ]
    for field in profile.get("fields", []):
        lines.append(
            f"| {field['field']} | {field['dtype']} | {field['null_count']} | {field['n_unique']} |"
        )
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

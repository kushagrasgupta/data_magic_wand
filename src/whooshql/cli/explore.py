from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import typer

from whooshql.core.frame_io import scan_any
from whooshql.core.schema import TableSchema
from whooshql.ddl.base import emit_basic_ddl
from whooshql.infer.partition import detect_partition_values
from whooshql.io.store import ObjectMeta, resolve_store
from whooshql.reports.json import to_json
from whooshql.reports.markdown import explore_to_markdown
from whooshql.reports.text import to_text

app = typer.Typer(help="Explore object stores and infer dataset group metadata.")

_DATA_SUFFIXES = {
    ".csv",
    ".tsv",
    ".txt",
    ".parquet",
    ".jsonl",
    ".ndjson",
    ".json",
    ".arrow",
    ".feather",
    ".ipc",
    ".avro",
    ".orc",
    ".csv.gz",
    ".csv.zst",
    ".jsonl.gz",
}

_PRESETS = {
    "semcasting": {"group_by": "depth:3", "sample_strategy": "smallest"},
    "liveintent": {"group_by": "depth:3", "sample_strategy": "newest"},
}


def _is_data_file(key: str) -> bool:
    name = key.lower()
    if name.startswith("."):
        return False
    if "/." in name or name.endswith("/_success") or name.endswith("/_format"):
        return False
    return any(name.endswith(suffix) for suffix in _DATA_SUFFIXES)


def _group_key_for(key: str, mode: str) -> str:
    if mode.startswith("depth:"):
        depth_raw = mode.split(":", maxsplit=1)[1]
        depth = int(depth_raw)
        parts = [part for part in key.split("/") if part]
        return "/".join(parts[:depth]) if parts else key
    return str(Path(key).parent)


def _pick_samples(candidates: list[ObjectMeta], strategy: str, count: int) -> list[ObjectMeta]:
    if not candidates:
        return []

    if strategy == "smallest":
        ordered = sorted(candidates, key=lambda x: x.size)
    elif strategy == "newest":
        ordered = sorted(
            candidates,
            key=lambda x: x.last_modified or datetime(1970, 1, 1),
            reverse=True,
        )
    else:
        ordered = sorted(candidates, key=lambda x: x.key)

    return ordered[: max(1, count)]


def _detect_cadence(values: list[str]) -> dict[str, Any]:
    parsed_dates: list[date] = []
    for value in values:
        for fmt in ("%Y-%m-%d", "%Y%m%d"):
            try:
                parsed_dates.append(datetime.strptime(value, fmt).date())
                break
            except ValueError:
                continue

    if len(parsed_dates) < 2:
        return {
            "label": "unknown",
            "avg_gap_days": None,
            "min_gap_days": None,
            "max_gap_days": None,
            "gaps": [],
        }

    parsed_dates = sorted(parsed_dates)
    gaps = [(b - a).days for a, b in zip(parsed_dates[:-1], parsed_dates[1:])]
    avg = sum(gaps) / len(gaps)

    if 0.8 <= avg <= 1.3:
        label = "daily"
    elif 6 <= avg <= 8:
        label = "weekly"
    elif 27 <= avg <= 32:
        label = "monthly"
    else:
        label = "irregular"

    return {
        "label": label,
        "avg_gap_days": round(avg, 3),
        "min_gap_days": min(gaps),
        "max_gap_days": max(gaps),
        "gaps": gaps,
    }


def _apply_filters(
    objects: list[ObjectMeta],
    *,
    include: list[str],
    exclude: list[str],
    since: datetime | None,
) -> list[ObjectMeta]:
    output: list[ObjectMeta] = []
    for item in objects:
        if include and not any(fnmatch(item.key, pattern) for pattern in include):
            continue
        if exclude and any(fnmatch(item.key, pattern) for pattern in exclude):
            continue
        if since and item.last_modified and item.last_modified < since:
            continue
        output.append(item)
    return output


def _infer_local_schema(path: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        lf = scan_any(path)
        schema = TableSchema.from_polars(lf).model_dump()
        sample_rows = lf.head(5).collect(engine="streaming").to_dicts()
        return schema, sample_rows
    except Exception:
        return None, []


def _render(report: dict[str, Any], report_format: str) -> str:
    if report_format == "json":
        return to_json(report)
    if report_format in {"md", "markdown"}:
        return explore_to_markdown(report)
    return to_text(report)


@app.command()
def run(
    targets: list[str] = typer.Argument(..., help="One or more URIs or preset names"),
    profile: str | None = typer.Option(None, "--profile"),
    region: str | None = typer.Option(None, "--region"),
    group_by: str = typer.Option("depth:3", "--group-by"),
    sample_files: int = typer.Option(1, "--sample-files"),
    sample_strategy: str = typer.Option("smallest", "--sample-strategy"),
    infer_schema: bool = typer.Option(True, "--infer-schema/--no-infer-schema"),
    emit_ddl: str = typer.Option("none", "--emit-ddl"),
    target_db: str | None = typer.Option(None, "--target-db"),
    target_schema: str | None = typer.Option(None, "--target-schema"),
    report: str = typer.Option("text", "--report"),
    report_out: str | None = typer.Option(None, "--report-out"),
    include: list[str] = typer.Option([], "--include"),
    exclude: list[str] = typer.Option([], "--exclude"),
    since: str | None = typer.Option(None, "--since", help="YYYY-MM-DD"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    partition_pattern: list[str] = typer.Option([], "--partition-pattern"),
) -> None:
    resolved_targets = list(targets)
    active_presets = [t for t in targets if t in _PRESETS]
    if active_presets:
        # Keep preset support transitional and explicit.
        first = active_presets[0]
        preset = _PRESETS[first]
        group_by = preset["group_by"]
        sample_strategy = preset["sample_strategy"]
        resolved_targets = [t for t in targets if t not in _PRESETS]
        if not resolved_targets:
            raise typer.BadParameter(
                f"Preset '{first}' was selected. Provide at least one concrete URI after it."
            )

    since_dt = datetime.strptime(since, "%Y-%m-%d") if since else None

    groups: dict[tuple[str, str], list[ObjectMeta]] = defaultdict(list)

    for uri in resolved_targets:
        store, prefix = resolve_store(uri, profile=profile, region=region)
        objects = store.list(prefix)
        filtered = _apply_filters(objects, include=include, exclude=exclude, since=since_dt)

        for obj in filtered:
            gkey = _group_key_for(obj.key, group_by)
            groups[(uri, gkey)].append(obj)

    payload_groups: list[dict[str, Any]] = []

    for (uri, group_key), items in sorted(groups.items(), key=lambda x: x[0]):
        data_candidates = [item for item in items if _is_data_file(item.key)]
        selected = _pick_samples(data_candidates, sample_strategy, sample_files)

        partition_values = detect_partition_values((obj.key for obj in items), partition_pattern)
        cadence = _detect_cadence(partition_values)

        sample_report: dict[str, Any] | None = None
        schema: dict[str, Any] | None = None
        ddl: dict[str, str] = {}

        if selected:
            sample_obj = selected[0]
            sample_report = {
                "key": sample_obj.key,
                "size": sample_obj.size,
                "compression": "gzip" if sample_obj.key.endswith(".gz") else "none",
                "format": Path(sample_obj.key).suffix.lower().lstrip("."),
            }

            if infer_schema and not dry_run and uri.startswith("s3://") is False:
                schema, rows = _infer_local_schema(sample_obj.key)
                if sample_report is not None:
                    sample_report["sample_rows"] = rows

            if emit_ddl != "none" and schema:
                model = TableSchema.model_validate(schema)
                table_name = group_key.replace("/", "_") or "dataset"
                if target_db and target_schema:
                    table_name = f"{target_db}.{target_schema}.{table_name}"
                ddl[emit_ddl] = emit_basic_ddl(model, table_name=table_name, target=emit_ddl)

        payload_groups.append(
            {
                "group_key": group_key,
                "prefix": group_key,
                "object_count": len(items),
                "data_object_count": len(data_candidates),
                "total_size": sum(item.size for item in items),
                "partition_pattern": "auto" if partition_values else None,
                "partition_values": partition_values,
                "latest_partition": partition_values[-1] if partition_values else None,
                "delivery_cadence": cadence,
                "sample": sample_report,
                "manifest": None,
                "schema": schema,
                "ddl": ddl,
            }
        )

    final_report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "targets": resolved_targets,
        "group_by": group_by,
        "groups": payload_groups,
    }

    output = _render(final_report, report)
    if report_out:
        Path(report_out).write_text(output, encoding="utf-8")
    else:
        typer.echo(output, nl=False)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

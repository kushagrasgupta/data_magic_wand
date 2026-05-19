from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import polars as pl

from whooshql.core.errors import SchemaError


@dataclass(frozen=True, slots=True)
class ValidationResult:
    good: pl.LazyFrame
    bad: pl.LazyFrame
    total_rows: int
    failed_rows: int


def load_json_schema(path: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], json.loads(Path(path).read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"Could not parse JSON schema {path}: {exc}") from exc


def validate_frame(
    lf: pl.LazyFrame,
    *,
    schema: dict[str, Any] | None = None,
    field_count: int | None = None,
    append_errors: bool = True,
) -> ValidationResult:
    checks: list[pl.Expr] = []
    error_exprs: list[pl.Expr] = []
    columns = lf.collect_schema().names()

    if field_count is not None and field_count != len(columns):
        bad = lf.with_columns(pl.lit(f"field_count expected {field_count}, found {len(columns)}").alias("_whooshql_errors"))
        total = int(lf.select(pl.len()).collect().item())
        return ValidationResult(good=lf.head(0), bad=bad, total_rows=total, failed_rows=total)

    if schema:
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        if not isinstance(props, dict):
            raise SchemaError("JSON schema `properties` must be an object")

        for name in required:
            if name not in columns:
                raise SchemaError(f"Required field missing from input: {name}")

        for name, spec in props.items():
            if name not in columns or not isinstance(spec, dict):
                continue
            ok, err = _field_expr(name, spec, required=name in required)
            checks.append(ok)
            error_exprs.append(err)

    if not checks:
        total = int(lf.select(pl.len()).collect().item())
        empty_bad = lf.head(0)
        if append_errors:
            empty_bad = empty_bad.with_columns(pl.lit("").alias("_whooshql_errors"))
        return ValidationResult(good=lf, bad=empty_bad, total_rows=total, failed_rows=0)

    ok_expr = pl.all_horizontal(checks).alias("__whooshql_ok")
    framed = lf.with_columns(ok_expr)

    good = framed.filter(pl.col("__whooshql_ok")).drop("__whooshql_ok")
    bad = framed.filter(~pl.col("__whooshql_ok")).drop("__whooshql_ok")
    if append_errors:
        bad = bad.with_columns(pl.concat_str(error_exprs, separator="; ").alias("_whooshql_errors"))

    total = int(framed.select(pl.len()).collect().item())
    failed = int(framed.filter(~pl.col("__whooshql_ok")).select(pl.len()).collect().item())
    return ValidationResult(good=good, bad=bad, total_rows=total, failed_rows=failed)


def _field_expr(name: str, spec: dict[str, Any], *, required: bool) -> tuple[pl.Expr, pl.Expr]:
    col = pl.col(name)
    checks: list[pl.Expr] = []
    messages: list[pl.Expr] = []

    if required:
        ok = col.is_not_null()
        checks.append(ok)
        messages.append(pl.when(ok).then(pl.lit("")).otherwise(pl.lit(f"{name}: required")))

    type_name = spec.get("type")
    if isinstance(type_name, list):
        type_name = next((item for item in type_name if item != "null"), None)

    if isinstance(type_name, str):
        ok = _type_check(col, type_name)
        checks.append(ok)
        messages.append(pl.when(ok).then(pl.lit("")).otherwise(pl.lit(f"{name}: type {type_name}")))

    if "minimum" in spec:
        ok = col.cast(pl.Float64, strict=False) >= float(spec["minimum"])
        checks.append(ok.fill_null(not required))
        messages.append(pl.when(ok.fill_null(not required)).then(pl.lit("")).otherwise(pl.lit(f"{name}: below minimum")))

    if "maximum" in spec:
        ok = col.cast(pl.Float64, strict=False) <= float(spec["maximum"])
        checks.append(ok.fill_null(not required))
        messages.append(pl.when(ok.fill_null(not required)).then(pl.lit("")).otherwise(pl.lit(f"{name}: above maximum")))

    if "minLength" in spec:
        ok = col.cast(pl.String).str.len_chars() >= int(spec["minLength"])
        checks.append(ok.fill_null(not required))
        messages.append(pl.when(ok.fill_null(not required)).then(pl.lit("")).otherwise(pl.lit(f"{name}: too short")))

    if "maxLength" in spec:
        ok = col.cast(pl.String).str.len_chars() <= int(spec["maxLength"])
        checks.append(ok.fill_null(not required))
        messages.append(pl.when(ok.fill_null(not required)).then(pl.lit("")).otherwise(pl.lit(f"{name}: too long")))

    if isinstance(spec.get("enum"), list):
        ok = col.is_in(spec["enum"])
        checks.append(ok.fill_null(not required))
        messages.append(pl.when(ok.fill_null(not required)).then(pl.lit("")).otherwise(pl.lit(f"{name}: not in enum")))

    if isinstance(spec.get("pattern"), str):
        re.compile(spec["pattern"])
        ok = col.cast(pl.String).str.contains(spec["pattern"])
        checks.append(ok.fill_null(not required))
        messages.append(pl.when(ok.fill_null(not required)).then(pl.lit("")).otherwise(pl.lit(f"{name}: pattern")))

    final_ok = pl.all_horizontal(checks) if checks else pl.lit(True)
    final_err = pl.concat_str(messages, separator="").str.replace_all(r";\s*$", "") if messages else pl.lit("")
    return final_ok, final_err


def _type_check(col: pl.Expr, type_name: str) -> pl.Expr:
    nullable_ok = col.is_null()
    if type_name == "integer":
        return nullable_ok | col.cast(pl.Int64, strict=False).is_not_null()
    if type_name == "number":
        return nullable_ok | col.cast(pl.Float64, strict=False).is_not_null()
    if type_name == "boolean":
        lowered = col.cast(pl.String).str.to_lowercase()
        return nullable_ok | lowered.is_in(["true", "false", "t", "f", "0", "1", "yes", "no"])
    if type_name == "string":
        return pl.lit(True)
    return pl.lit(True)

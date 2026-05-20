from __future__ import annotations

import logging
import re
import sys
import warnings
from collections.abc import Mapping, Sequence
from os import PathLike
from pathlib import Path
from typing import Any, Literal, NoReturn, cast

import polars as pl
from polars._typing import PolarsDataType
from polars.exceptions import ComputeError

from whooshql.core.dialect import CSVDialect
from whooshql.core.errors import CSVParseError, DialectError, FrameIOError

logger = logging.getLogger(__name__)

_CSV_EXTS = {".csv", ".tsv", ".txt"}
_JSON_EXTS = {".jsonl", ".ndjson"}
_PARQUET_EXTS = {".parquet"}
_IPC_EXTS = {".arrow", ".feather", ".ipc"}

_CSV_DTYPE_ALIASES: dict[str, PolarsDataType] = {
    "bool": pl.Boolean,
    "boolean": pl.Boolean,
    "date": pl.Date,
    "datetime": pl.Datetime,
    "f32": pl.Float32,
    "f64": pl.Float64,
    "float32": pl.Float32,
    "float64": pl.Float64,
    "i8": pl.Int8,
    "i16": pl.Int16,
    "i32": pl.Int32,
    "i64": pl.Int64,
    "int8": pl.Int8,
    "int16": pl.Int16,
    "int32": pl.Int32,
    "int64": pl.Int64,
    "str": pl.String,
    "string": pl.String,
    "u8": pl.UInt8,
    "u16": pl.UInt16,
    "u32": pl.UInt32,
    "u64": pl.UInt64,
    "uint8": pl.UInt8,
    "uint16": pl.UInt16,
    "uint32": pl.UInt32,
    "uint64": pl.UInt64,
    "utf8": pl.String,
}


def _basename_without_compression(path: str) -> str:
    name = path.lower()
    for suffix in (".gz", ".zst", ".snappy", ".lz4", ".bz2"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _infer_format(path: str, fmt_override: str | None = None) -> str:
    if fmt_override and fmt_override != "auto":
        return fmt_override.lower()

    base = _basename_without_compression(path)
    suffix = Path(base).suffix.lower()

    if suffix in _CSV_EXTS:
        return "csv"
    if suffix in _JSON_EXTS:
        return "jsonl"
    if suffix in _PARQUET_EXTS:
        return "parquet"
    if suffix in _IPC_EXTS:
        return "ipc"
    if suffix == ".avro":
        return "avro"
    if suffix == ".orc":
        return "orc"
    if suffix == ".json":
        return "json"

    raise FrameIOError(f"Could not infer input format from path: {path}")


def scan_any(
    path: str | PathLike[str],
    *,
    infer_schema_length: int | None = None,
    all_string: bool = False,
    schema_overrides: Mapping[str, str | PolarsDataType] | None = None,
    null_values: Sequence[str] | Mapping[str, str] | None = None,
    ignore_errors: bool = False,
    delimiter: str | None = None,
    quotechar: str | None = None,
    encoding: str = "utf-8",
    has_header: bool | None = None,
    hints: dict[str, Any] | None = None,
    dialect: CSVDialect | None = None,
) -> pl.LazyFrame:
    """Scan a tabular file into a Polars LazyFrame.

    CSV inputs accept inference controls and parser-relaxation options.
    NDJSON accepts only ``ignore_errors``. Parquet, IPC, Avro, ORC, and JSON
    inputs have explicit schemas or eager readers, so CSV-specific controls are
    intentionally ignored.
    """
    uri = str(path)
    hints = hints or {}
    fmt = _infer_format(uri, fmt_override=hints.get("in_format"))

    if fmt == "csv":
        d = dialect or _dialect_for_local_csv(uri)
        csv_kwargs = d.to_polars_kwargs()
        csv_kwargs.update(_csv_read_kwargs(
            infer_schema_length=infer_schema_length,
            all_string=all_string,
            schema_overrides=schema_overrides,
            null_values=null_values,
            ignore_errors=ignore_errors,
        ))
        if delimiter is not None:
            csv_kwargs["separator"] = delimiter
        if quotechar is not None:
            csv_kwargs["quote_char"] = quotechar
        if has_header is not None:
            csv_kwargs["has_header"] = has_header
        if encoding:
            csv_kwargs["encoding"] = _polars_encoding(encoding)
        return pl.scan_csv(uri, **csv_kwargs)
    if fmt == "jsonl":
        return pl.scan_ndjson(uri, ignore_errors=ignore_errors)
    if fmt == "parquet":
        _log_ignored_csv_options(
            fmt,
            infer_schema_length=infer_schema_length,
            all_string=all_string,
            schema_overrides=schema_overrides,
            null_values=null_values,
            ignore_errors=ignore_errors,
        )
        return pl.scan_parquet(uri)
    if fmt == "ipc":
        _log_ignored_csv_options(
            fmt,
            infer_schema_length=infer_schema_length,
            all_string=all_string,
            schema_overrides=schema_overrides,
            null_values=null_values,
            ignore_errors=ignore_errors,
        )
        return pl.scan_ipc(uri)

    # These paths are intentionally eager then lazified until Polars adds full lazy readers.
    if fmt == "avro":
        _log_ignored_csv_options(
            fmt,
            infer_schema_length=infer_schema_length,
            all_string=all_string,
            schema_overrides=schema_overrides,
            null_values=null_values,
            ignore_errors=ignore_errors,
        )
        import pyarrow.avro as pa_avro

        table = pa_avro.read_table(uri)
        return cast(pl.DataFrame, pl.from_arrow(table)).lazy()
    if fmt == "orc":
        _log_ignored_csv_options(
            fmt,
            infer_schema_length=infer_schema_length,
            all_string=all_string,
            schema_overrides=schema_overrides,
            null_values=null_values,
            ignore_errors=ignore_errors,
        )
        import pyarrow.orc as pa_orc

        table = pa_orc.ORCFile(uri).read()  # type: ignore[no-untyped-call]
        return cast(pl.DataFrame, pl.from_arrow(table)).lazy()
    if fmt == "json":
        _log_ignored_csv_options(
            fmt,
            infer_schema_length=infer_schema_length,
            all_string=all_string,
            schema_overrides=schema_overrides,
            null_values=null_values,
            ignore_errors=ignore_errors,
        )
        return pl.read_json(uri).lazy()

    raise FrameIOError(f"Unsupported input format: {fmt}")


def _dialect_for_local_csv(uri: str) -> CSVDialect:
    path = Path(uri)
    if uri == "-" or not path.exists():
        return CSVDialect()
    try:
        return CSVDialect.auto(path)
    except DialectError:
        return CSVDialect()


def _polars_encoding(encoding: str) -> str:
    return "utf8" if encoding.lower() in {"utf-8", "utf8"} else encoding


def _resolve_schema_overrides(
    schema_overrides: Mapping[str, str | PolarsDataType] | None,
) -> dict[str, PolarsDataType] | None:
    if schema_overrides is None:
        return None

    resolved: dict[str, PolarsDataType] = {}
    for column, dtype in schema_overrides.items():
        if isinstance(dtype, str):
            key = dtype.strip().lower()
            try:
                resolved[column] = _CSV_DTYPE_ALIASES[key]
            except KeyError as exc:
                valid = ", ".join(sorted({name for name in _CSV_DTYPE_ALIASES if len(name) > 2}))
                raise FrameIOError(
                    f"Unknown schema override dtype '{dtype}' for column '{column}'. "
                    f"Known aliases include: {valid}."
                ) from exc
        else:
            resolved[column] = dtype
    return resolved


def _csv_read_kwargs(
    *,
    infer_schema_length: int | None,
    all_string: bool,
    schema_overrides: Mapping[str, str | PolarsDataType] | None,
    null_values: Sequence[str] | Mapping[str, str] | None,
    ignore_errors: bool,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"ignore_errors": ignore_errors}

    if all_string:
        if infer_schema_length is not None:
            warnings.warn(
                "all_string=True overrides infer_schema_length; using infer_schema_length=0.",
                UserWarning,
                stacklevel=3,
            )
        kwargs["infer_schema_length"] = 0
    elif infer_schema_length is not None:
        kwargs["infer_schema_length"] = infer_schema_length

    resolved_overrides = _resolve_schema_overrides(schema_overrides)
    if resolved_overrides is not None:
        kwargs["schema_overrides"] = resolved_overrides
    if null_values is not None:
        kwargs["null_values"] = null_values

    return kwargs


def _log_ignored_csv_options(
    fmt: str,
    *,
    infer_schema_length: int | None,
    all_string: bool,
    schema_overrides: Mapping[str, str | PolarsDataType] | None,
    null_values: Sequence[str] | Mapping[str, str] | None,
    ignore_errors: bool,
) -> None:
    if any((
        infer_schema_length is not None,
        all_string,
        schema_overrides is not None,
        null_values is not None,
        ignore_errors,
    )):
        logger.debug("Ignoring CSV read options for %s input", fmt)


def csv_parse_error(exc: ComputeError, *, path: str | None = None) -> CSVParseError:
    first_line = _clean_csv_compute_error(str(exc).splitlines()[0])
    viewer_target = path or "FILE"
    return CSVParseError(
        "\n".join([
            f"CSV parse error: {first_line}",
            "Hints:",
            f"  * Inspect the column with: whooshql viewer -i {viewer_target} -r N",
            "  * Force string-only reads:  --all-string",
            "  * Pin one column type:      --schema-override Zip=String",
            "  * Drop bad rows silently:   --ignore-errors",
            "  * Treat 'GA' as null:       --null-value GA",
        ])
    )


def _clean_csv_compute_error(message: str) -> str:
    match = re.search(
        r"could not parse [`'](?P<value>.*?)[`'] as dtype [`'](?P<dtype>.*?)[`'] "
        r"at column [`'](?P<column>.*?)[`']",
        message,
    )
    if not match:
        return message.replace("`", "'")

    dtype = {
        "i64": "Int64",
        "i32": "Int32",
        "i16": "Int16",
        "i8": "Int8",
        "u64": "UInt64",
        "u32": "UInt32",
        "u16": "UInt16",
        "u8": "UInt8",
        "f64": "Float64",
        "f32": "Float32",
        "str": "String",
    }.get(match.group("dtype"), match.group("dtype"))
    return (
        f"could not parse '{match.group('value')}' as {dtype} "
        f"at column '{match.group('column')}'"
    )


def raise_csv_parse_error(exc: ComputeError, *, path: str | None = None) -> NoReturn:
    raise csv_parse_error(exc, path=path) from exc


def _write_stdout(df: pl.DataFrame, out_format: str) -> None:
    if out_format == "csv":
        sys.stdout.write(df.write_csv())
        return
    if out_format == "jsonl":
        sys.stdout.write(df.write_ndjson())
        return
    if out_format == "json":
        sys.stdout.write(df.write_json())
        return
    raise FrameIOError(f"Writing {out_format} to stdout is not supported")


def sink_any(
    out_uri: str,
    lf: pl.LazyFrame,
    *,
    to_format: str | None = None,
    streaming: bool = True,
    compression: str | None = None,
) -> None:
    engine: Literal["streaming", "auto"] = "streaming" if streaming else "auto"
    df = lf.collect(engine=engine)

    if out_uri == "-":
        stdout_format = "csv" if to_format in (None, "auto") else str(to_format)
        _write_stdout(df, stdout_format)
        return

    fmt = _infer_format(out_uri, fmt_override=to_format or "auto")

    out_path = Path(out_uri)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        sep = "\t" if out_path.suffix.lower() == ".tsv" else ","
        df.write_csv(out_uri, separator=sep)
        return
    if fmt == "jsonl":
        df.write_ndjson(out_uri)
        return
    if fmt == "parquet":
        if compression is None:
            df.write_parquet(out_uri)
        else:
            parquet_compression = cast(
                Literal["lz4", "uncompressed", "snappy", "gzip", "brotli", "zstd"],
                compression,
            )
            df.write_parquet(out_uri, compression=parquet_compression)
        return
    if fmt == "ipc":
        df.write_ipc(out_uri)
        return
    if fmt == "json":
        out_path.write_text(df.write_json(), encoding="utf-8")
        return

    raise FrameIOError(f"Unsupported output format: {fmt}")


def name_from_path(path: str) -> str:
    stem = Path(path).stem
    if not stem:
        stem = "input"
    safe = "".join(ch if ch.isalnum() else "_" for ch in stem)
    if safe and safe[0].isdigit():
        safe = f"t_{safe}"
    return safe or "input"

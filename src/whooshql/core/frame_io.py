from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal, cast

import polars as pl

from whooshql.core.dialect import CSVDialect
from whooshql.core.errors import DialectError, FrameIOError

_CSV_EXTS = {".csv", ".tsv", ".txt"}
_JSON_EXTS = {".jsonl", ".ndjson"}
_PARQUET_EXTS = {".parquet"}
_IPC_EXTS = {".arrow", ".feather", ".ipc"}


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


def scan_any(uri: str, hints: dict[str, Any] | None = None, dialect: CSVDialect | None = None) -> pl.LazyFrame:
    hints = hints or {}
    fmt = _infer_format(uri, fmt_override=hints.get("in_format"))

    if fmt == "csv":
        d = dialect or _dialect_for_local_csv(uri)
        return pl.scan_csv(uri, **d.to_polars_kwargs())
    if fmt == "jsonl":
        return pl.scan_ndjson(uri)
    if fmt == "parquet":
        return pl.scan_parquet(uri)
    if fmt == "ipc":
        return pl.scan_ipc(uri)

    # These paths are intentionally eager then lazified until Polars adds full lazy readers.
    if fmt == "avro":
        import pyarrow.avro as pa_avro

        table = pa_avro.read_table(uri)
        return cast(pl.DataFrame, pl.from_arrow(table)).lazy()
    if fmt == "orc":
        import pyarrow.orc as pa_orc

        table = pa_orc.ORCFile(uri).read()  # type: ignore[no-untyped-call]
        return cast(pl.DataFrame, pl.from_arrow(table)).lazy()
    if fmt == "json":
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

from __future__ import annotations

from pathlib import Path


def detect_format(path: str, sample: bytes | None = None) -> str:
    name = path.lower()
    for compression in (".gz", ".zst", ".snappy", ".lz4", ".bz2"):
        if name.endswith(compression):
            name = name[: -len(compression)]

    suffix = Path(name).suffix.lower()
    if suffix == ".parquet" or (sample or b"").startswith(b"PAR1"):
        return "parquet"
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    if suffix == ".json":
        return "json"
    if suffix == ".tsv":
        return "tsv"
    if suffix in {".arrow", ".ipc", ".feather"}:
        return "ipc"
    if suffix == ".avro":
        return "avro"
    if suffix == ".orc":
        return "orc"
    return "csv"


def detect_compression(path: str, sample: bytes | None = None) -> str:
    data = sample or b""
    if path.endswith(".gz") or data.startswith(b"\x1f\x8b"):
        return "gzip"
    if path.endswith(".zst") or data.startswith(b"\x28\xb5\x2f\xfd"):
        return "zstd"
    if path.endswith(".bz2") or data.startswith(b"BZh"):
        return "bz2"
    if path.endswith(".lz4"):
        return "lz4"
    if path.endswith(".snappy"):
        return "snappy"
    return "none"

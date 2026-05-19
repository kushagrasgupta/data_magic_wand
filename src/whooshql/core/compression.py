from __future__ import annotations

import gzip
import io
from typing import Any, cast

try:
    import zstandard as zstd
except ImportError:  # pragma: no cover - optional dependency
    zstd = None

from whooshql.core.errors import CompressionError

MAGIC_GZIP = b"\x1f\x8b"
MAGIC_ZSTD = b"\x28\xb5\x2f\xfd"


def detect_compression(data: bytes) -> str | None:
    if data.startswith(MAGIC_GZIP):
        return "gzip"
    if data.startswith(MAGIC_ZSTD):
        return "zstd"
    return None


def decompress_best_effort(data: bytes) -> bytes:
    kind = detect_compression(data)
    if kind is None:
        return data

    if kind == "gzip":
        try:
            return gzip.decompress(data)
        except EOFError:
            # S3 range-GET may truncate member. This mirrors the legacy explorer behavior.
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as fobj:
                return fobj.read()
        except OSError as exc:
            raise CompressionError(f"Failed to decompress gzip payload: {exc}") from exc

    if kind == "zstd":
        if zstd is None:
            raise CompressionError("zstd payload found but `zstandard` is not installed")
        try:
            dctx = zstd.ZstdDecompressor()
            return cast(bytes, dctx.decompress(data))
        except cast(Any, zstd).ZstdError as exc:
            raise CompressionError(f"Failed to decompress zstd payload: {exc}") from exc

    return data

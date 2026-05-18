from __future__ import annotations

from typing import Literal

ManifestKind = Literal["success", "format", "committed", "iceberg", "delta", "unknown"]


def classify_manifest_key(key: str) -> ManifestKind:
    name = key.rsplit("/", maxsplit=1)[-1].lower()
    if name == "_success":
        return "success"
    if name == "_format":
        return "format"
    if name.startswith("_committed"):
        return "committed"
    if name.endswith("metadata.json") and "/metadata/" in key.lower():
        return "iceberg"
    if "/_delta_log/" in key.lower():
        return "delta"
    return "unknown"

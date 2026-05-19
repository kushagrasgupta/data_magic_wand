from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ObjectMeta:
    key: str
    size: int
    last_modified: datetime | None = None
    etag: str | None = None
    content_type: str | None = None


class ObjectStore(Protocol):
    def list(self, prefix: str, *, recursive: bool = True, page_size: int = 1000) -> list[ObjectMeta]:
        raise NotImplementedError

    def head(self, key: str) -> ObjectMeta:
        raise NotImplementedError

    def get_range(self, key: str, start: int, end: int) -> bytes:
        raise NotImplementedError


def resolve_store(uri: str, *, profile: str | None = None, region: str | None = None) -> tuple[ObjectStore, str]:
    parsed = urlparse(uri)
    scheme = parsed.scheme.lower()

    if scheme in ("", "file"):
        from whooshql.io.local import LocalStore

        path = parsed.path if scheme == "file" else uri
        return LocalStore(), path
    if scheme == "s3":
        from whooshql.io.s3 import S3Store

        bucket = parsed.netloc
        prefix = parsed.path.lstrip("/")
        return S3Store(bucket=bucket, profile=profile, region=region), prefix

    raise ValueError(f"Unsupported URI scheme for explore: {scheme or 'local'}")

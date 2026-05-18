from __future__ import annotations

from typing import Any, cast

from whoosh.io.store import ObjectMeta


class S3Store:
    def __init__(self, *, bucket: str, profile: str | None = None, region: str | None = None) -> None:
        self.bucket = bucket
        self.profile = profile
        self.region = region
        self._client = self._build_client()

    def _build_client(self) -> Any:
        import boto3  # type: ignore[import-untyped]

        session_kwargs = {}
        if self.profile:
            session_kwargs["profile_name"] = self.profile
        session = boto3.Session(**session_kwargs)
        return session.client("s3", region_name=self.region)

    def list(self, prefix: str, *, recursive: bool = True, page_size: int = 1000) -> list[ObjectMeta]:
        paginator = self._client.get_paginator("list_objects_v2")
        items: list[ObjectMeta] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix, PaginationConfig={"PageSize": page_size}):
            for obj in page.get("Contents", []):
                items.append(
                    ObjectMeta(
                        key=str(obj["Key"]),
                        size=int(obj.get("Size", 0)),
                        last_modified=obj.get("LastModified"),
                        etag=obj.get("ETag"),
                    )
                )
        return items

    def head(self, key: str) -> ObjectMeta:
        info = self._client.head_object(Bucket=self.bucket, Key=key)
        return ObjectMeta(
            key=key,
            size=int(info.get("ContentLength", 0)),
            last_modified=info.get("LastModified"),
            etag=info.get("ETag"),
            content_type=info.get("ContentType"),
        )

    def get_range(self, key: str, start: int, end: int) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=key, Range=f"bytes={start}-{end}")
        return cast(bytes, response["Body"].read())

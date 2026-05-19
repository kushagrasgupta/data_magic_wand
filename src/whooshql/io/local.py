from __future__ import annotations

from datetime import datetime
from pathlib import Path

from whooshql.io.store import ObjectMeta


class LocalStore:
    def list(self, prefix: str, *, recursive: bool = True, page_size: int = 1000) -> list[ObjectMeta]:
        root = Path(prefix)
        paths = root.rglob("*") if recursive else root.glob("*")
        out: list[ObjectMeta] = []
        for path in paths:
            if path.is_file():
                st = path.stat()
                out.append(
                    ObjectMeta(
                        key=str(path),
                        size=st.st_size,
                        last_modified=datetime.fromtimestamp(st.st_mtime),
                    )
                )
        return out

    def head(self, key: str) -> ObjectMeta:
        path = Path(key)
        st = path.stat()
        return ObjectMeta(key=str(path), size=st.st_size, last_modified=datetime.fromtimestamp(st.st_mtime))

    def get_range(self, key: str, start: int, end: int) -> bytes:
        path = Path(key)
        with path.open("rb") as fobj:
            fobj.seek(start)
            return fobj.read(max(0, end - start + 1))

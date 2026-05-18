from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MergeAction:
    action: str
    source: str
    destination: str
    reason: str


def plan_local_merge(
    source_dir: str,
    dest_dir: str,
    *,
    recursive: bool = True,
    hash_name: str = "md5",
) -> list[MergeAction]:
    source = Path(source_dir)
    dest = Path(dest_dir)
    if not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source_dir}")

    pattern = "**/*" if recursive else "*"
    actions: list[MergeAction] = []
    for src in sorted(path for path in source.glob(pattern) if path.is_file()):
        rel = src.relative_to(source)
        dst = dest / rel
        if not dst.exists():
            actions.append(MergeAction("copy", str(src), str(dst), "missing"))
            continue
        if src.stat().st_size != dst.stat().st_size:
            actions.append(MergeAction("copy", str(src), str(dst), "size differs"))
            continue
        if _hash_file(src, hash_name) != _hash_file(dst, hash_name):
            actions.append(MergeAction("copy", str(src), str(dst), f"{hash_name} differs"))

    return actions


def execute_local_merge(actions: list[MergeAction]) -> None:
    for action in actions:
        if action.action != "copy":
            continue
        dst = Path(action.destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.source, dst)


def _hash_file(path: Path, hash_name: str) -> str:
    if hash_name == "sha256":
        digest = hashlib.sha256()
    else:
        digest = hashlib.md5()
    with path.open("rb") as fobj:
        for chunk in iter(lambda: fobj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

from __future__ import annotations

import re
from collections.abc import Iterable

_PATTERNS = [
    re.compile(r"year=(?P<y>\d{4})/month=(?P<m>\d{2})/day=(?P<d>\d{2})"),
    re.compile(r"(?P<date>\d{8})"),
    re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})"),
]


def detect_partition_values(keys: Iterable[str], extra_patterns: list[str] | None = None) -> list[str]:
    patterns = list(_PATTERNS)
    for raw in extra_patterns or []:
        patterns.append(re.compile(raw))

    values: set[str] = set()
    for key in keys:
        for pat in patterns:
            match = pat.search(key)
            if match:
                if "date" in match.groupdict() and match.group("date"):
                    values.add(match.group("date"))
                elif {"y", "m", "d"}.issubset(match.groupdict()):
                    values.add(f"{match.group('y')}-{match.group('m')}-{match.group('d')}")
                break
    return sorted(values)

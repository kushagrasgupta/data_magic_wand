from __future__ import annotations

import time
from pathlib import Path

import polars as pl

from whooshql.api.freak import freak
from whooshql.api.sort import sort_frame


def main() -> None:
    path = Path("data/3x3_header.csv")
    if not path.exists():
        raise SystemExit("benchmark fixture missing: data/3x3_header.csv")

    lf = pl.scan_csv(path)

    start = time.perf_counter()
    sort_frame(lf, keys=["alphas:asc"]).collect(engine="streaming")
    sort_seconds = time.perf_counter() - start

    start = time.perf_counter()
    freak(lf, ["alphas"]).collect(engine="streaming")
    freak_seconds = time.perf_counter() - start

    print(f"sort_seconds={sort_seconds:.6f}")
    print(f"freak_seconds={freak_seconds:.6f}")


if __name__ == "__main__":
    main()

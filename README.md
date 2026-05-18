# Whoosh CLI

Whoosh is a Polars-native command line toolkit for fast local and object-store
data exploration. The implementation is a modern Python package built around
LazyFrames, typed internals, and a single `whoosh` dispatcher.

## Install For Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,s3,sql]"
```

## Commands

```bash
whoosh --version
whoosh slicer -i data/3x3_header.csv -c alphas,integers
whoosh freaker -i data/colors.csv -c color
whoosh converter -i data/3x3_header.csv -o /tmp/rows.parquet
whoosh profiler -i data/3x3_header.csv --report md
whoosh validator -i data/3x3_header.csv --field-cnt 3
whoosh sorter -i data/3x3_header.csv --by alphas:asc
whoosh differ --old old.csv --new new.csv --key-cols id --out-dir /tmp/diff
whoosh merger --source-dir /tmp/source --dest-dir /tmp/dest --dry-run
whoosh explore data --report md
```

The package also exposes compatibility-style entry points such as
`whoosh_slicer`, `whoosh_freaker`, and `whoosh_explore`.

## Project Status

The repo is mid-rewrite. Core tabular CLIs, schema validation, local merge,
baseline object exploration, markdown/text/json reports, linting, typing, tests,
and CI are in place. Larger roadmap items still planned include the fully async
S3 explorer pipeline, richer warehouse DDL emitters, Textual viewer mode, and
release packaging polish.

## Quality Checks

```bash
python -m ruff check src/whoosh tests/whoosh benchmarks
python -m mypy src/whoosh
python -m pytest
python benchmarks/tabular_baseline.py
```

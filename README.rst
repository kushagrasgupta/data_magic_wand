whooshql
========

whooshql is a Polars-native command line toolkit for tabular files, local
directories, and object stores. It ships as a single ``whooshql`` dispatcher
with a set of focused ``whooshql_*`` console scripts for direct use from the
shell.

The package name on PyPI is ``whooshql``. The project currently requires
Python 3.13 or newer.

Install
-------

Install the published package::

  python -m pip install whooshql

Install optional extras when you need them::

  python -m pip install "whooshql[s3]"
  python -m pip install "whooshql[sql]"
  python -m pip install "whooshql[dev]"

The ``s3`` extra pulls in ``boto3`` for object-store exploration. The ``sql``
extra pulls in ``duckdb`` for SQL-oriented workflows. The ``dev`` extra installs
build, lint, type-check, test, and release tooling.

For local development from a checkout::

  python -m venv .venv
  source .venv/bin/activate
  python -m pip install -e ".[dev,s3,sql]"

What Ships
----------

The install exposes:

* ``whooshql`` for the main dispatcher
* ``whooshql_slicer``, ``whooshql_freaker``, ``whooshql_profiler``
* ``whooshql_validator``, ``whooshql_viewer``, ``whooshql_differ``
* ``whooshql_sorter``, ``whooshql_converter``, ``whooshql_merger``
* ``whooshql_explore``, ``whooshql_sql``, ``whooshql_sample``, ``whooshql_pivot``

The Python package is also importable as ``whooshql``.

Quick Start
-----------

See the top-level help::

  whooshql --help
  whooshql <command> --help

A few common commands::

  whooshql slicer -i data/3x3_header.csv -c alphas,integers
  whooshql freaker -i data/colors.csv -c color
  whooshql profiler -i data/3x3_header.csv --report md
  whooshql converter -i data/3x3_header.csv -o /tmp/rows.parquet
  whooshql validator -i data/3x3_header.csv --field-cnt 3
  whooshql sorter -i data/3x3_header.csv --by alphas:asc
  whooshql differ --old old.csv --new new.csv --key-cols id --out-dir /tmp/diff
  whooshql merger --source-dir /tmp/source --dest-dir /tmp/dest --dry-run
  whooshql sql -i data/3x3_header.csv --query "select * from t_3x3_header"
  whooshql explore data --report md

Supported Formats
-----------------

Input auto-detection works from file extensions. Supported inputs include:

* ``csv``, ``tsv``, ``txt``
* ``jsonl``, ``ndjson``
* ``parquet``
* ``ipc``, ``arrow``, ``feather``
* ``json``
* ``avro``
* ``orc``

Output auto-detection supports:

* ``csv``
* ``tsv``
* ``jsonl``
* ``parquet``
* ``ipc``
* ``json``

Compression suffixes such as ``.gz``, ``.zst``, ``.snappy``, ``.lz4``, and
``.bz2`` are ignored when inferring the input format. CSV output uses tab
separation when the target path ends in ``.tsv``.

Command Reference
-----------------

slicer
^^^^^^

Slice rows and columns from a tabular file. Use ``--cols`` / ``-c`` to include
column slices, ``--exclude-cols`` / ``-C`` to remove columns, ``--rows`` / ``-r``
to select row slices, and ``--exclude-rows`` / ``-R`` to remove row ranges. The
``--where`` flag accepts a Polars SQL expression. CSV dialect options are
available through ``--delimiter``, ``--quotechar``, ``--encoding``, and the
``--has-header/--no-has-header`` toggle.

Example::

  whooshql slicer -i data/3x3_header.csv -c alphas,integers -r 1:3

freaker
^^^^^^^

Build frequency distributions by one or more columns. Use ``--cols`` / ``-c`` to
name the grouping columns, ``--sortcol`` and ``--sortorder`` to control
ordering, ``--top`` to limit the result, and ``--as-percent`` or
``--as-cumulative`` for relative metrics.

Example::

  whooshql freaker -i data/colors.csv -c color --top 10

profiler
^^^^^^^^

Profile one or more inputs and emit text, Markdown, or JSON. Repeat
``--infile`` / ``-i`` to merge multiple inputs before profiling. Use ``--report``
to choose ``text``, ``md``, ``markdown``, or ``json``, and ``--top-values`` to
control how many frequent values appear in the column breakdown.

Example::

  whooshql profiler -i data/3x3_header.csv -i data/colors.csv --report json

validator
^^^^^^^^^

Validate rows against a JSON Schema file and/or a simple field-count check. Use
``--validschema`` to point at a schema document and ``--field-cnt`` to enforce a
column count. Good rows and failed rows can be written separately with
``--outfile`` and ``--errfile``. The command exits with:

* ``0`` when everything passes
* ``1`` when validation finds failed rows
* ``2`` when the schema itself is invalid or cannot be read

Example::

  whooshql validator -i data/3x3_header.csv --validschema schema.json

converter
^^^^^^^^^

Convert between ``csv``, ``tsv``, ``parquet``, ``jsonl``, ``ipc``, ``json``,
``avro``, and ``orc``. Use ``--in-format`` and ``--out-format`` when extension
inference is not enough. CSV dialect flags are the same as for ``slicer``.
Parquet output accepts ``--compression``.

Example::

  whooshql converter -i data/3x3_header.csv -o /tmp/rows.parquet

sorter
^^^^^^

Sort by one or more keys. Keys accept ``name:asc`` and ``name:desc`` style
syntax. You can repeat ``--by`` / ``-k`` or separate multiple keys with commas.
The command also supports ``--dedup`` and ``--case-insensitive``.

Example::

  whooshql sorter -i data/3x3_header.csv -k alphas:asc -k integers:desc

differ
^^^^^^

Compare an ``--old`` file with a ``--new`` file using key columns from
``--key-cols``. You can narrow the comparison with ``--compare-cols`` or
exclude columns with ``--ignore-cols``. The output directory receives
``same.csv``, ``insert.csv``, ``delete.csv``, ``chgold.csv``, and
``chgnew.csv``.

Example::

  whooshql differ --old old.csv --new new.csv --key-cols id --out-dir /tmp/diff

merger
^^^^^^

Plan and execute a local directory merge. The command compares source and
destination files by size and hash, then copies only missing or changed files.
Use ``--hash`` for ``md5`` or ``sha256``, ``--recursive/--no-recursive`` to
control tree walking, and ``--dry-run`` to inspect the plan without copying.

Example::

  whooshql merger --source-dir /tmp/source --dest-dir /tmp/dest --dry-run

sample
^^^^^^

Take a sample from a file by row count, fraction, or stratification. Use
``--rows`` for a simple head sample, ``--fraction`` for approximate sampling,
or ``--stratify-by`` together with ``--per-bucket`` for grouped sampling. The
``--seed`` option affects deterministic sampling.

Example::

  whooshql sample -i data/3x3_header.csv --rows 100

pivot
^^^^^

Pivot or unpivot data through Polars. When ``--pivot-index``,
``--pivot-columns``, and ``--pivot-values`` are present, the command performs a
pivot. When ``--unpivot-id-vars`` is provided, it performs an unpivot. The
pivot aggregation supports ``sum``, ``mean``, ``min``, ``max``, and ``first``.

Example::

  whooshql pivot -i data/3x3_header.csv --pivot-index id --pivot-columns kind --pivot-values value

sql
^^^

Register each input under a name derived from the file stem and execute a SQL
query with Polars ``SQLContext``. Use repeated ``--infile`` flags, provide the
SQL with ``--query``, and write to a file or stdout with ``--outfile`` and
``--to-format``.

Registered names come from the file stem and are normalized to a valid table
name. If a stem starts with a digit, the command prefixes it with ``t_``.

Example::

  whooshql sql -i data/3x3_header.csv -i data/colors.csv --query "select * from t_3x3_header"

viewer
^^^^^^

Render a single row in a readable transposed layout. Pass the row index with
``--row``.

Example::

  whooshql viewer -i data/3x3_header.csv -r 0

explore
^^^^^^^

Explore local paths or ``s3://bucket/prefix`` targets. This command groups
objects, samples representative files, optionally infers schema from local
samples, and can emit DDL or Markdown/JSON/text reports.

Useful flags:

* ``--profile`` and ``--region`` for S3 access
* ``--group-by depth:3`` or a parent-path grouping
* ``--sample-files`` and ``--sample-strategy smallest|newest``
* ``--infer-schema/--no-infer-schema``
* ``--emit-ddl snowflake|bigquery|duckdb|athena``
* ``--target-db`` and ``--target-schema``
* ``--report text|md|markdown|json``
* ``--report-out``
* ``--include`` and ``--exclude`` glob filters
* ``--since YYYY-MM-DD``
* ``--dry-run``
* ``--partition-pattern``

The command also understands the preset names ``semcasting`` and
``liveintent``. Those presets set the grouping and sample strategy, but you
still need to pass a real URI after the preset name.

Example::

  whooshql explore s3://my-bucket/data --report md --emit-ddl duckdb

Python API
----------

The package exposes a small Python API for scripting and integration work.
Common entry points live under ``whooshql.api`` and ``whooshql.core``::

  from whooshql.api import diff_frames, profile_table, run_sql, sample, sort_frame, validate_frame
  from whooshql.core.frame_io import scan_any, sink_any

  lf = scan_any("data/3x3_header.csv")
  result = profile_table(lf)

You can also import the report helpers when you want to render profile or
explore payloads yourself::

  from whooshql.reports import explore_to_markdown, profile_to_markdown, profile_to_text, to_json, to_text

Build And Publish
-----------------

Build the distribution locally with::

  python -m build

Check the packaged metadata and long description before upload::

  python -m twine check dist/*

Publish to PyPI with::

  python -m twine upload dist/*

The repository is configured to use ``README.rst`` as the PyPI long
description.

Development
-----------

The project targets Python 3.13 and newer. The active quality gates are::

  python -m ruff check src/whooshql tests/whooshql benchmarks
  python -m mypy src/whooshql
  python -m pytest
  python benchmarks/tabular_baseline.py

License
-------

BSD-3-Clause

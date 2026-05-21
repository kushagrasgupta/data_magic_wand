# Changelog

## [Unreleased]

### Added

- `--infer-schema-length`, `--all-string`, `--schema-override`,
  `--null-value`, and `--ignore-errors` on all tabular-reading CLIs.

### Changed

- CSV parse errors now surface an actionable hint list with workaround flags.

## [0.1.2]

### Fixed

- `--since` flag raised TypeError on offset-naive vs offset-aware datetime comparison.
  The parsed `since_dt` is now UTC-aware.

## 0.1.0

- Created the `whooshql` package scaffold with Hatchling.
- Added the `whooshql` dispatcher and individual `whooshql_*` console scripts.
- Implemented baseline slicer, freaker, converter, profiler, validator, sorter,
  differ, merger, sample, pivot, SQL, and explore commands.
- Added Polars-based frame IO, schema models, slice specs, CSV dialect helpers,
  object-store abstractions, inference helpers, reports, DDL mapping, tests, CI,
  Ruff, and strict mypy configuration.

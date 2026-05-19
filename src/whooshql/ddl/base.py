from __future__ import annotations

from whooshql.core.schema import TableSchema

_TYPE_MAP = {
    "snowflake": {
        "Int": "NUMBER",
        "UInt": "NUMBER",
        "Float": "FLOAT",
        "Boolean": "BOOLEAN",
        "Date": "DATE",
        "Datetime": "TIMESTAMP_NTZ",
        "String": "VARCHAR",
    },
    "bigquery": {
        "Int": "INT64",
        "UInt": "INT64",
        "Float": "FLOAT64",
        "Boolean": "BOOL",
        "Date": "DATE",
        "Datetime": "TIMESTAMP",
        "String": "STRING",
    },
    "duckdb": {
        "Int": "BIGINT",
        "UInt": "UBIGINT",
        "Float": "DOUBLE",
        "Boolean": "BOOLEAN",
        "Date": "DATE",
        "Datetime": "TIMESTAMP",
        "String": "VARCHAR",
    },
    "athena": {
        "Int": "bigint",
        "UInt": "bigint",
        "Float": "double",
        "Boolean": "boolean",
        "Date": "date",
        "Datetime": "timestamp",
        "String": "string",
    },
}


def _map_dtype(dtype: str, target: str) -> str:
    mapping = _TYPE_MAP.get(target, _TYPE_MAP["duckdb"])
    for prefix, out in mapping.items():
        if dtype.startswith(prefix):
            return out
    return mapping["String"]


def emit_basic_ddl(schema: TableSchema, *, table_name: str, target: str) -> str:
    cols = []
    for field in schema.fields:
        cols.append(f"  {field.name} {_map_dtype(field.dtype, target)}")
    cols_sql = ",\n".join(cols)
    return f"CREATE TABLE {table_name} (\n{cols_sql}\n);"

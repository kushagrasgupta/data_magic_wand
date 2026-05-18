from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict

from whoosh.core.errors import SchemaError


class FieldSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    dtype: str
    nullable: bool = True
    unique: bool = False
    min: Any | None = None
    max: Any | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[Any] | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SchemaDiff:
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]


class TableSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[FieldSchema]
    primary_key: list[str] | None = None

    @classmethod
    def from_json_schema(cls, obj: Mapping[str, Any]) -> TableSchema:
        props = obj.get("properties")
        if not isinstance(props, Mapping):
            raise SchemaError("JSON schema must define `properties`")

        required = set(obj.get("required", []))
        fields: list[FieldSchema] = []
        for name, spec in props.items():
            if not isinstance(spec, Mapping):
                continue
            raw_type = spec.get("type", "string")
            type_name = raw_type if isinstance(raw_type, str) else "string"
            fields.append(
                FieldSchema(
                    name=name,
                    dtype=type_name,
                    nullable=name not in required,
                    min=spec.get("minimum"),
                    max=spec.get("maximum"),
                    min_length=spec.get("minLength"),
                    max_length=spec.get("maxLength"),
                    pattern=spec.get("pattern"),
                    enum=list(spec["enum"]) if isinstance(spec.get("enum"), list) else None,
                    description=spec.get("description"),
                )
            )
        return cls(fields=fields)

    @classmethod
    def from_polars(cls, lf: pl.LazyFrame) -> TableSchema:
        schema = lf.collect_schema()
        fields = [
            FieldSchema(
                name=name,
                dtype=str(dtype),
                nullable=True,
            )
            for name, dtype in schema.items()
        ]
        return cls(fields=fields)

    def diff(self, other: TableSchema) -> SchemaDiff:
        mine = {field.name: field for field in self.fields}
        theirs = {field.name: field for field in other.fields}

        added = tuple(sorted(theirs.keys() - mine.keys()))
        removed = tuple(sorted(mine.keys() - theirs.keys()))

        changed = []
        for key in mine.keys() & theirs.keys():
            if mine[key].dtype != theirs[key].dtype or mine[key].nullable != theirs[key].nullable:
                changed.append(key)
        return SchemaDiff(added=added, removed=removed, changed=tuple(sorted(changed)))

    def to_pyarrow(self) -> Any:
        import pyarrow as pa

        mapping = {
            "Int8": pa.int8(),
            "Int16": pa.int16(),
            "Int32": pa.int32(),
            "Int64": pa.int64(),
            "UInt8": pa.uint8(),
            "UInt16": pa.uint16(),
            "UInt32": pa.uint32(),
            "UInt64": pa.uint64(),
            "Float32": pa.float32(),
            "Float64": pa.float64(),
            "Boolean": pa.bool_(),
            "String": pa.string(),
            "Datetime": pa.timestamp("us"),
            "Date": pa.date32(),
        }
        arrow_fields = []
        for field in self.fields:
            arrow_type = mapping.get(field.dtype, pa.string())
            arrow_fields.append(pa.field(field.name, arrow_type, nullable=field.nullable))
        return pa.schema(arrow_fields)

    def to_json_schema(self) -> dict[str, Any]:
        props: dict[str, Any] = {}
        required: list[str] = []

        type_map = {
            "Boolean": "boolean",
            "Int8": "integer",
            "Int16": "integer",
            "Int32": "integer",
            "Int64": "integer",
            "UInt8": "integer",
            "UInt16": "integer",
            "UInt32": "integer",
            "UInt64": "integer",
            "Float32": "number",
            "Float64": "number",
            "Date": "string",
            "Datetime": "string",
            "String": "string",
        }

        for field in self.fields:
            node: dict[str, Any] = {"type": type_map.get(field.dtype, "string")}
            if field.min is not None:
                node["minimum"] = field.min
            if field.max is not None:
                node["maximum"] = field.max
            if field.min_length is not None:
                node["minLength"] = field.min_length
            if field.max_length is not None:
                node["maxLength"] = field.max_length
            if field.pattern:
                node["pattern"] = field.pattern
            if field.enum:
                node["enum"] = field.enum
            if field.description:
                node["description"] = field.description
            props[field.name] = node
            if not field.nullable:
                required.append(field.name)

        out: dict[str, Any] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": props,
        }
        if required:
            out["required"] = required
        return out

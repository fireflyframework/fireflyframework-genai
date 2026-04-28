# Copyright 2026 Firefly Software Solutions Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DuckDB sink: builds an in-memory normalized database from typed records."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from fireflyframework_agentic.ingestion.domain import (
    ColumnSpec,
    ColumnType,
    IngestionError,
    TableSpec,
    TargetSchema,
    TypedRecord,
)

if TYPE_CHECKING:
    import duckdb

logger = logging.getLogger(__name__)


_DUCKDB_TYPES: dict[ColumnType, str] = {
    "string": "VARCHAR",
    "integer": "BIGINT",
    "float": "DOUBLE",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "json": "JSON",
}


class DuckDBSink:
    """In-memory DuckDB sink with idempotent rebuild on every run.

    Each call to :meth:`begin` drops any pre-existing tables and recreates
    them from *schema*. Rows are validated against :class:`ColumnSpec`
    before insertion; invalid rows are skipped and accumulated in
    :attr:`validation_errors`.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        try:
            import duckdb as _duckdb
        except ImportError as exc:
            raise ImportError(
                "DuckDBSink requires the 'ingestion-duckdb' extra: "
                "pip install fireflyframework-agentic[ingestion-duckdb]"
            ) from exc
        self._duckdb_module = _duckdb
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._db_path = db_path
        self._schema: TargetSchema | None = None
        self._counts: dict[str, int] = {}
        self.validation_errors: list[IngestionError] = []

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            raise RuntimeError("DuckDBSink: begin() must be called first")
        return self._conn

    def begin(self, schema: TargetSchema) -> None:
        if self._conn is None:
            self._conn = self._duckdb_module.connect(self._db_path)
        self._schema = schema
        self._counts = {t.name: 0 for t in schema.tables}
        self.validation_errors = []
        for table in schema.tables:
            self._conn.execute(f"DROP TABLE IF EXISTS {self._quote(table.name)}")
            self._conn.execute(self._create_table_sql(table))

    def write(self, records: Iterable[TypedRecord]) -> None:
        if self._conn is None or self._schema is None:
            raise RuntimeError("DuckDBSink: begin() must be called first")
        for record in records:
            try:
                table = self._schema.table(record.table)
            except KeyError:
                self.validation_errors.append(
                    IngestionError(
                        kind="UnknownTable",
                        message=f"record references unknown table {record.table!r}",
                        details={"row": record.row},
                    )
                )
                continue
            coerced = self._validate_and_coerce(table, record.row)
            if coerced is None:
                continue
            placeholders = ", ".join(["?"] * len(table.columns))
            cols = ", ".join(self._quote(c.name) for c in table.columns)
            sql = (
                f"INSERT INTO {self._quote(table.name)} ({cols}) "
                f"VALUES ({placeholders})"
            )
            self._conn.execute(sql, [coerced[c.name] for c in table.columns])
            self._counts[table.name] += 1

    def finalize(self) -> dict[str, int]:
        return dict(self._counts)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _validate_and_coerce(
        self, table: TableSpec, row: dict[str, Any]
    ) -> dict[str, Any] | None:
        coerced: dict[str, Any] = {}
        for column in table.columns:
            value = row.get(column.name)
            if value is None:
                if column.nullable:
                    coerced[column.name] = None
                    continue
                self.validation_errors.append(
                    IngestionError(
                        kind="RowValidationError",
                        message=(
                            f"column {table.name}.{column.name} is non-nullable "
                            f"but row provided no value"
                        ),
                        details={"row": row},
                    )
                )
                return None
            try:
                coerced[column.name] = self._coerce(column, value)
            except (TypeError, ValueError) as exc:
                self.validation_errors.append(
                    IngestionError(
                        kind="RowValidationError",
                        message=(
                            f"column {table.name}.{column.name} ({column.type}): "
                            f"{exc}"
                        ),
                        details={"row": row, "value": repr(value)},
                    )
                )
                return None
        unknown = set(row) - {c.name for c in table.columns}
        if unknown:
            self.validation_errors.append(
                IngestionError(
                    kind="RowValidationError",
                    message=(
                        f"row contains unknown columns for table {table.name}: "
                        f"{sorted(unknown)}"
                    ),
                    details={"row": row},
                )
            )
            return None
        return coerced

    @staticmethod
    def _coerce(column: ColumnSpec, value: Any) -> Any:
        if column.enum_values is not None and value not in column.enum_values:
            raise ValueError(
                f"value {value!r} not in enum {column.enum_values}"
            )
        ctype = column.type
        if ctype == "string":
            return str(value)
        if ctype == "integer":
            if isinstance(value, bool):
                raise TypeError("bool is not a valid integer")
            return int(value)
        if ctype == "float":
            if isinstance(value, bool):
                raise TypeError("bool is not a valid float")
            return float(value)
        if ctype == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                low = value.strip().lower()
                if low in {"true", "1", "yes", "y"}:
                    return True
                if low in {"false", "0", "no", "n"}:
                    return False
                raise ValueError(f"cannot parse boolean from {value!r}")
            raise TypeError(f"cannot coerce {type(value).__name__} to boolean")
        if ctype == "date":
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                return date.fromisoformat(value)
            raise TypeError(f"cannot coerce {type(value).__name__} to date")
        if ctype == "datetime":
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            raise TypeError(f"cannot coerce {type(value).__name__} to datetime")
        if ctype == "json":
            return value
        raise ValueError(f"unknown column type {ctype!r}")

    def _create_table_sql(self, table: TableSpec) -> str:
        cols = []
        for c in table.columns:
            duck_type = _DUCKDB_TYPES[c.type]
            constraints: list[str] = []
            if not c.nullable:
                constraints.append("NOT NULL")
            if c.primary_key:
                constraints.append("PRIMARY KEY")
            constraint_clause = (" " + " ".join(constraints)) if constraints else ""
            cols.append(f"{self._quote(c.name)} {duck_type}{constraint_clause}")
        return f"CREATE TABLE {self._quote(table.name)} ({', '.join(cols)})"

    @staticmethod
    def _quote(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

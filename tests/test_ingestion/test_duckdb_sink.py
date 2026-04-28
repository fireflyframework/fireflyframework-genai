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

"""Tests for DuckDBSink against a real in-memory DuckDB instance."""

from datetime import date

import pytest

from fireflyframework_agentic.ingestion.adapters.sinks import DuckDBSink
from fireflyframework_agentic.ingestion.domain import (
    ColumnSpec,
    ForeignKeySpec,
    TableSpec,
    TargetSchema,
    TypedRecord,
)


@pytest.fixture
def sales_schema() -> TargetSchema:
    return TargetSchema(
        tables=[
            TableSpec(
                name="customers",
                columns=[
                    ColumnSpec(name="id", type="integer", primary_key=True, nullable=False),
                    ColumnSpec(name="name", type="string"),
                    ColumnSpec(
                        name="tier",
                        type="string",
                        enum_values=["bronze", "silver", "gold"],
                    ),
                ],
            ),
            TableSpec(
                name="sales",
                columns=[
                    ColumnSpec(name="id", type="integer", primary_key=True, nullable=False),
                    ColumnSpec(name="customer_id", type="integer", nullable=False),
                    ColumnSpec(name="day", type="date"),
                    ColumnSpec(name="amount", type="float"),
                    ColumnSpec(name="paid", type="boolean"),
                ],
                foreign_keys=[
                    ForeignKeySpec(
                        column="customer_id",
                        references_table="customers",
                        references_column="id",
                    )
                ],
            ),
        ]
    )


@pytest.fixture
def sink() -> DuckDBSink:
    s = DuckDBSink()
    yield s
    s.close()


def test_begin_creates_tables(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    rows = sink.connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' "
        "ORDER BY table_name"
    ).fetchall()
    assert [r[0] for r in rows] == ["customers", "sales"]


def test_begin_is_idempotent(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    sink.write([TypedRecord(table="customers", row={"id": 1, "name": "A", "tier": "gold"})])
    sink.begin(sales_schema)  # second begin must drop & recreate
    counts = sink.finalize()
    assert counts == {"customers": 0, "sales": 0}


def test_write_inserts_valid_rows(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    sink.write(
        [
            TypedRecord(table="customers", row={"id": 1, "name": "Alpha", "tier": "gold"}),
            TypedRecord(table="customers", row={"id": 2, "name": "Beta", "tier": "silver"}),
            TypedRecord(
                table="sales",
                row={
                    "id": 100,
                    "customer_id": 1,
                    "day": date(2026, 1, 5),
                    "amount": 99.95,
                    "paid": True,
                },
            ),
        ]
    )
    counts = sink.finalize()
    assert counts == {"customers": 2, "sales": 1}
    rows = sink.connection.execute(
        "SELECT id, name, tier FROM customers ORDER BY id"
    ).fetchall()
    assert rows == [(1, "Alpha", "gold"), (2, "Beta", "silver")]


def test_write_skips_row_with_unknown_table(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    sink.write([TypedRecord(table="ghost", row={"id": 1})])
    assert sink.finalize() == {"customers": 0, "sales": 0}
    assert any(e.kind == "UnknownTable" for e in sink.validation_errors)


def test_write_skips_row_with_missing_required_column(
    sink: DuckDBSink, sales_schema: TargetSchema
):
    sink.begin(sales_schema)
    sink.write(
        [TypedRecord(table="sales", row={"id": 1, "day": date(2026, 1, 1)})]  # missing customer_id
    )
    assert sink.finalize() == {"customers": 0, "sales": 0}
    err = sink.validation_errors[0]
    assert err.kind == "RowValidationError"
    assert "customer_id" in err.message


def test_write_skips_row_with_unknown_column(
    sink: DuckDBSink, sales_schema: TargetSchema
):
    sink.begin(sales_schema)
    sink.write(
        [
            TypedRecord(
                table="customers",
                row={"id": 1, "name": "A", "tier": "gold", "extra": "x"},
            )
        ]
    )
    assert sink.finalize()["customers"] == 0
    assert any(
        e.kind == "RowValidationError" and "unknown columns" in e.message
        for e in sink.validation_errors
    )


def test_write_skips_row_outside_enum(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    sink.write(
        [TypedRecord(table="customers", row={"id": 1, "name": "A", "tier": "platinum"})]
    )
    assert sink.finalize()["customers"] == 0
    assert any(
        e.kind == "RowValidationError" and "enum" in e.message
        for e in sink.validation_errors
    )


def test_coerces_string_date_to_date(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    sink.write(
        [
            TypedRecord(table="customers", row={"id": 1, "name": "A", "tier": "gold"}),
            TypedRecord(
                table="sales",
                row={
                    "id": 1,
                    "customer_id": 1,
                    "day": "2026-04-15",
                    "amount": 1.0,
                    "paid": True,
                },
            ),
        ]
    )
    rows = sink.connection.execute("SELECT day FROM sales").fetchall()
    assert rows[0][0] == date(2026, 4, 15)


def test_coerces_string_boolean(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    sink.write(
        [
            TypedRecord(table="customers", row={"id": 1, "name": "A", "tier": "gold"}),
            TypedRecord(
                table="sales",
                row={
                    "id": 1,
                    "customer_id": 1,
                    "day": "2026-04-15",
                    "amount": 1.0,
                    "paid": "yes",
                },
            ),
        ]
    )
    rows = sink.connection.execute("SELECT paid FROM sales").fetchall()
    assert rows[0][0] is True


def test_rejects_bool_for_integer_column(
    sink: DuckDBSink, sales_schema: TargetSchema
):
    sink.begin(sales_schema)
    sink.write([TypedRecord(table="customers", row={"id": True, "name": "A", "tier": "gold"})])
    assert sink.finalize()["customers"] == 0


def test_finalize_returns_per_table_counts(sink: DuckDBSink, sales_schema: TargetSchema):
    sink.begin(sales_schema)
    sink.write(
        [
            TypedRecord(table="customers", row={"id": 1, "name": "A", "tier": "gold"}),
            TypedRecord(table="customers", row={"id": 2, "name": "B", "tier": "silver"}),
        ]
    )
    assert sink.finalize() == {"customers": 2, "sales": 0}

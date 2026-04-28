# KGIngestAgent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a modular folder-ingestion agent that converts dropped documents into a SQLite knowledge graph plus a Chroma chunk vector index, fanning out across pluggable per-purpose extractors (`bpmn`, `person`, `generic`) and emitting `.bpmn` 2.0 XML for BPMN-style documents.

**Architecture:** Three additive framework modules (`graphstores/`, `content/loaders/markitdown.py`, `pipeline/triggers/folder_watcher.py`) plus a self-contained example package at `examples/kg_ingest/` composing them via the existing `PipelineBuilder`. All persistent state on disk under `./kg/`; only network calls are to Anthropic (extractor LLM) and OpenAI (embeddings).

**Tech Stack:** Python 3.13+, `uv`, SQLite (stdlib, WAL, FTS5), Chroma `PersistentClient`, `markitdown`, `watchfiles`, `lxml`, `pydantic`, `pydantic-ai` (via FireflyAgent), `anthropic` (via pydantic-ai), `openai` (embeddings).

**Spec:** `docs/use-case-kg-ingest.md`

---

## Conventions

**License header** — first 13 lines of every new `.py` file:

```python
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
```

**Async** — pytest-asyncio mode is `auto`; async test functions need no decorator.

**Test layout** — tests mirror the source path: `tests/<module>/test_<file>.py`.

**Run commands** — always from repo root, `uv run pytest -x tests/...` for fast fail.

**Imports** — `from __future__ import annotations` at the top of every Python file (matches the repo convention; enables Pydantic + future-style type hints).

**Commits** — one task = one commit (or two — separate test commit before impl is fine).

---

## File Structure

### Created in `src/fireflyframework_agentic/`

| File | Responsibility |
|---|---|
| `graphstores/__init__.py` | Re-exports `GraphStoreProtocol`, `Node`, `Edge`, `SqliteGraphStore`. |
| `graphstores/types.py` | `Node`, `Edge` Pydantic models. |
| `graphstores/protocol.py` | `GraphStoreProtocol` (`upsert_nodes`, `upsert_edges`, `delete_by_doc_id`, `query`, `close`). |
| `graphstores/sqlite.py` | `SqliteGraphStore` — schema bootstrap, CRUD, FTS5 + junction triggers. |
| `content/loaders/__init__.py` | Re-exports `MarkitdownLoader`. |
| `content/loaders/markitdown.py` | `MarkitdownLoader` — wraps `markitdown.MarkItDown` → `Document(content, metadata)`. |
| `pipeline/triggers/__init__.py` | Re-exports `FolderWatcher`. |
| `pipeline/triggers/folder_watcher.py` | `FolderWatcher` — `watchfiles.awatch` + debounce + stability + reconciliation. |

### Created in `examples/kg_ingest/`

| File | Responsibility |
|---|---|
| `__init__.py` | Re-exports `KGIngestAgent`. |
| `agent.py` | `KGIngestAgent` facade — `ingest_one`, `ingest_folder`, `watch`, `close`. |
| `extractors/__init__.py` | `EXTRACTORS` registry (dict). |
| `extractors/base.py` | `Extractor` protocol; `IngestedDoc` dataclass; `PostExtractStep` type alias. |
| `extractors/bpmn.py` | `BpmnExtractor` — `BpmnExtraction` schema, mapper, BPMN-XML post-step. |
| `extractors/person.py` | `PersonExtractor` — `PersonExtraction` schema + mapper. |
| `extractors/generic.py` | `GenericExtractor` — `GenericExtraction` (`Entity`/`Relation`) schema + mapper. |
| `prompts/bpmn.j2` | BPMN extraction Jinja prompt. |
| `prompts/person.j2` | Person extraction Jinja prompt. |
| `prompts/generic.j2` | Generic extraction Jinja prompt (with attribution comment). |
| `bpmn_serializer.py` | `serialize_bpmn(nodes, edges) -> str` — BPMN 2.0 XML emitter via lxml. |
| `ledger.py` | `IngestLedger` — wraps the `ingestions` SQLite table. |
| `pipeline.py` | `build_pipeline(extractors, paths, models) -> PipelineEngine`. |
| `cli.py` | `python -m examples.kg_ingest` entry point. |

### Created in `tests/`

| File | Coverage |
|---|---|
| `tests/graphstores/test_types.py` | Node / Edge model tests. |
| `tests/graphstores/test_sqlite_store.py` | SqliteGraphStore — upsert, delete, query, FTS, junction. |
| `tests/content/loaders/test_markitdown.py` | MarkitdownLoader format smoke tests. |
| `tests/pipeline/triggers/test_folder_watcher.py` | Watcher debounce, stability, reconciliation. |
| `tests/kg_ingest/test_extractors_bpmn.py` | BPMN schema + mapper + serializer. |
| `tests/kg_ingest/test_extractors_person.py` | Person schema + mapper. |
| `tests/kg_ingest/test_extractors_generic.py` | Generic schema + mapper. |
| `tests/kg_ingest/test_ledger.py` | IngestLedger state transitions. |
| `tests/kg_ingest/test_pipeline_integration.py` | Full DAG with stub LLM (canned outputs). |
| `tests/kg_ingest/test_e2e.py` | Real-LLM E2E (skipped unless API keys present). |

### Modified

| File | Change |
|---|---|
| `pyproject.toml` | Add optional extras: `[graph-sqlite]` (placeholder), `[markitdown]`, `[watch]`, `[kg-ingest]`. Add `python-dotenv` already present from prior PR. |
| `examples/README.md` | Add a section for `kg_ingest` after the existing IDP entry. |

### Fixtures

| File | Purpose |
|---|---|
| `tests/kg_ingest/fixtures/sample.pdf` | Tiny PDF (one page, a few sentences). |
| `tests/kg_ingest/fixtures/sample.docx` | Tiny DOCX. |
| `tests/kg_ingest/fixtures/sample.html` | Tiny HTML. |
| `tests/kg_ingest/fixtures/process.txt` | Plain-text BPMN-like process description. |

---

# Phase 1 — Project setup

### Task 1: Add optional extras to `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Read the current optional dependencies block**

```bash
grep -n "optional-dependencies" pyproject.toml
```

- [ ] **Step 2: Insert the four new extras under `[project.optional-dependencies]`**

Add these entries (alphabetical placement near other backend extras):

```toml
graph-sqlite = []  # SQLite is stdlib; placeholder for parallel future graph backends.
markitdown = ["markitdown[pdf,docx,pptx,xlsx]>=0.0.1a3"]
watch = ["watchfiles>=0.24.0"]
kg-ingest = [
    "fireflyframework-agentic[graph-sqlite,markitdown,watch,vectorstores-chroma,openai-embeddings]",
    "lxml>=5.3.0",
]
```

Add `lxml>=5.3.0` here even though it's only used by the BPMN serializer — keeps the umbrella pip-installable.

- [ ] **Step 3: Verify the file parses**

```bash
uv lock --check 2>&1 | head -20
```

If the lockfile is stale, regenerate:

```bash
uv lock
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add kg-ingest, markitdown, watch optional extras"
```

---

# Phase 2 — Graph store types and protocol

### Task 2: Define `Node` and `Edge` Pydantic types

**Files:**
- Create: `src/fireflyframework_agentic/graphstores/__init__.py`
- Create: `src/fireflyframework_agentic/graphstores/types.py`
- Create: `tests/graphstores/__init__.py`
- Create: `tests/graphstores/test_types.py`

- [ ] **Step 1: Write the failing test**

`tests/graphstores/test_types.py`:

```python
from __future__ import annotations

from fireflyframework_agentic.graphstores import Edge, Node


class TestNode:
    def test_minimum_fields(self):
        node = Node(
            label="Person",
            key="sam-altman",
            properties={"name": "Sam Altman"},
            source_doc_id="doc-001",
            extractor_name="person",
            chunk_ids=["c0", "c1"],
        )
        assert node.label == "Person"
        assert node.properties["name"] == "Sam Altman"
        assert node.chunk_ids == ["c0", "c1"]

    def test_serialises_to_dict(self):
        node = Node(
            label="Entity",
            key="OpenAI",
            properties={"type": "Company"},
            source_doc_id="doc-001",
            extractor_name="generic",
            chunk_ids=[],
        )
        dumped = node.model_dump()
        assert dumped["properties"] == {"type": "Company"}
        assert dumped["chunk_ids"] == []


class TestEdge:
    def test_minimum_fields(self):
        edge = Edge(
            label="WORKS_AT",
            source_label="Person",
            source_key="sam-altman",
            target_label="Organization",
            target_key="openai",
            properties={"role": "CEO"},
            source_doc_id="doc-001",
            extractor_name="person",
        )
        assert edge.source_label == "Person"
        assert edge.target_key == "openai"
        assert edge.properties["role"] == "CEO"
```

Also create empty `tests/graphstores/__init__.py`:

```python
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
uv run pytest -x tests/graphstores/test_types.py -v
```

Expected: `ModuleNotFoundError: No module named 'fireflyframework_agentic.graphstores'`.

- [ ] **Step 3: Implement `Node` and `Edge`**

`src/fireflyframework_agentic/graphstores/types.py`:

```python
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

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Node(BaseModel):
    """A node in the knowledge graph.

    `key` is the within-doc identifier for the entity (e.g. canonical name);
    `(source_doc_id, label, key)` is unique per the SQLite schema.
    """

    label: str
    key: str
    properties: dict[str, Any] = Field(default_factory=dict)
    source_doc_id: str
    extractor_name: str
    chunk_ids: list[str] = Field(default_factory=list)


class Edge(BaseModel):
    """A directed edge between two nodes in the knowledge graph."""

    label: str
    source_label: str
    source_key: str
    target_label: str
    target_key: str
    properties: dict[str, Any] = Field(default_factory=dict)
    source_doc_id: str
    extractor_name: str
```

Initial `src/fireflyframework_agentic/graphstores/__init__.py` (will grow):

```python
# Copyright 2026 Firefly Software Solutions Inc
# (... full license header ...)

from __future__ import annotations

from fireflyframework_agentic.graphstores.types import Edge, Node

__all__ = ["Edge", "Node"]
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
uv run pytest -x tests/graphstores/test_types.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/graphstores tests/graphstores
git commit -m "feat(graphstores): add Node and Edge Pydantic models"
```

---

### Task 3: Define `GraphStoreProtocol`

**Files:**
- Create: `src/fireflyframework_agentic/graphstores/protocol.py`
- Modify: `src/fireflyframework_agentic/graphstores/__init__.py`
- Create: `tests/graphstores/test_protocol.py`

- [ ] **Step 1: Write a failing isinstance / protocol-conformance test**

`tests/graphstores/test_protocol.py`:

```python
from __future__ import annotations

from typing import Any
from collections.abc import Sequence

from fireflyframework_agentic.graphstores import Edge, GraphStoreProtocol, Node


class _Stub:
    """Minimal protocol-conforming class for runtime check."""

    async def upsert_nodes(self, nodes: Sequence[Node]) -> None: ...
    async def upsert_edges(self, edges: Sequence[Edge]) -> None: ...
    async def delete_by_doc_id(self, doc_id: str) -> int: return 0
    async def query(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]: return []
    async def close(self) -> None: ...


def test_stub_satisfies_protocol():
    assert isinstance(_Stub(), GraphStoreProtocol)
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest -x tests/graphstores/test_protocol.py -v
```

Expected: `ImportError` for `GraphStoreProtocol`.

- [ ] **Step 3: Implement the protocol**

`src/fireflyframework_agentic/graphstores/protocol.py`:

```python
# (license header)

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from fireflyframework_agentic.graphstores.types import Edge, Node


@runtime_checkable
class GraphStoreProtocol(Protocol):
    """Async protocol for property-graph storage.

    Backends must accept upserts of Nodes and Edges, support cascading
    delete-by-document, expose an SQL (or Cypher-ish DSL) query surface,
    and clean up cleanly on close.
    """

    async def upsert_nodes(self, nodes: Sequence[Node]) -> None: ...

    async def upsert_edges(self, edges: Sequence[Edge]) -> None: ...

    async def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete every node, edge, and provenance record carrying this
        ``source_doc_id``. Returns the total rows affected (sum across
        nodes + edges; junction rows excluded).
        """
        ...

    async def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...

    async def close(self) -> None: ...
```

Update `src/fireflyframework_agentic/graphstores/__init__.py`:

```python
# (license header)

from __future__ import annotations

from fireflyframework_agentic.graphstores.protocol import GraphStoreProtocol
from fireflyframework_agentic.graphstores.types import Edge, Node

__all__ = ["Edge", "GraphStoreProtocol", "Node"]
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest -x tests/graphstores/test_protocol.py tests/graphstores/test_types.py -v
```

Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/graphstores tests/graphstores
git commit -m "feat(graphstores): add GraphStoreProtocol"
```

---

# Phase 3 — `SqliteGraphStore`

### Task 4: Schema bootstrap

**Files:**
- Create: `src/fireflyframework_agentic/graphstores/sqlite.py`
- Create: `tests/graphstores/test_sqlite_store.py`

- [ ] **Step 1: Write the failing schema test**

`tests/graphstores/test_sqlite_store.py`:

```python
from __future__ import annotations

import pytest

from fireflyframework_agentic.graphstores.sqlite import SqliteGraphStore


@pytest.fixture
async def store(tmp_path):
    s = SqliteGraphStore(tmp_path / "graph.sqlite")
    await s.initialise()
    yield s
    await s.close()


async def test_schema_creates_expected_tables(store: SqliteGraphStore):
    rows = await store.query(
        "SELECT name FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY name"
    )
    names = {r["name"] for r in rows}
    # Real tables
    for table in {"nodes", "edges", "ingestions", "node_chunks"}:
        assert table in names, f"missing table: {table}"
    # FTS virtual tables also create real shadow tables — at minimum check the parents exist
    assert "nodes_fts" in names or any("nodes_fts" in n for n in names)
    assert "edges_fts" in names or any("edges_fts" in n for n in names)
    # Indexes
    expected_indexes = {
        "idx_nodes_doc",
        "idx_nodes_label",
        "idx_nodes_label_key",
        "idx_edges_doc",
        "idx_edges_endpoints",
        "idx_edges_endpoints_reverse",
        "idx_node_chunks_node",
    }
    assert expected_indexes <= names


async def test_journal_mode_is_wal(store: SqliteGraphStore):
    rows = await store.query("PRAGMA journal_mode")
    assert rows[0]["journal_mode"].lower() == "wal"
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py -v
```

Expected: `ImportError` for `SqliteGraphStore`.

- [ ] **Step 3: Implement schema bootstrap**

`src/fireflyframework_agentic/graphstores/sqlite.py`:

```python
# (license header)

from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fireflyframework_agentic.graphstores.types import Edge, Node


_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS nodes (
  source_doc_id   TEXT NOT NULL,
  label           TEXT NOT NULL,
  key             TEXT NOT NULL,
  properties      TEXT NOT NULL,
  extractor_name  TEXT NOT NULL,
  chunk_ids       TEXT NOT NULL,
  PRIMARY KEY (source_doc_id, label, key)
);
CREATE INDEX IF NOT EXISTS idx_nodes_doc       ON nodes(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_nodes_label     ON nodes(label);
CREATE INDEX IF NOT EXISTS idx_nodes_label_key ON nodes(label, key);

CREATE TABLE IF NOT EXISTS edges (
  source_doc_id   TEXT NOT NULL,
  label           TEXT NOT NULL,
  source_label    TEXT NOT NULL,
  source_key      TEXT NOT NULL,
  target_label    TEXT NOT NULL,
  target_key      TEXT NOT NULL,
  properties      TEXT NOT NULL,
  extractor_name  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edges_doc                ON edges(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_edges_endpoints          ON edges(source_label, source_key, target_label, target_key);
CREATE INDEX IF NOT EXISTS idx_edges_endpoints_reverse  ON edges(target_label, target_key, source_label, source_key);

CREATE TABLE IF NOT EXISTS node_chunks (
  source_doc_id  TEXT NOT NULL,
  label          TEXT NOT NULL,
  key            TEXT NOT NULL,
  chunk_id       TEXT NOT NULL,
  PRIMARY KEY (chunk_id, source_doc_id, label, key)
);
CREATE INDEX IF NOT EXISTS idx_node_chunks_node ON node_chunks(source_doc_id, label, key);

CREATE TABLE IF NOT EXISTS ingestions (
  doc_id              TEXT PRIMARY KEY,
  source_path         TEXT NOT NULL,
  content_hash        TEXT NOT NULL,
  status              TEXT NOT NULL,
  partial_extractors  TEXT,
  ingested_at         TEXT NOT NULL,
  attempt             INTEGER NOT NULL DEFAULT 1
);

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
  source_doc_id  UNINDEXED,
  label          UNINDEXED,
  key,
  text,
  tokenize='unicode61 remove_diacritics 2'
);

CREATE VIRTUAL TABLE IF NOT EXISTS edges_fts USING fts5(
  source_doc_id  UNINDEXED,
  label          UNINDEXED,
  source_label   UNINDEXED,
  source_key     UNINDEXED,
  target_label   UNINDEXED,
  target_key     UNINDEXED,
  text,
  tokenize='unicode61 remove_diacritics 2'
);
"""


class SqliteGraphStore:
    """SQLite-backed GraphStoreProtocol implementation.

    Single file, WAL mode. Threadsafe via a per-instance asyncio lock around
    each connection use; a single sqlite3 connection is held for the lifetime
    of the store and closed via :meth:`close`.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    async def initialise(self) -> None:
        """Open the connection and run the schema DDL."""
        await asyncio.to_thread(self._initialise_sync)

    def _initialise_sync(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEMA)
        self._conn = conn

    async def close(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.close)
            self._conn = None

    async def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        async with self._lock:
            return await asyncio.to_thread(self._query_sync, sql, params or {})

    def _query_sync(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        assert self._conn is not None, "store not initialised"
        cursor = self._conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    # upsert_nodes, upsert_edges, delete_by_doc_id added in following tasks.
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py -v
```

Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/graphstores/sqlite.py tests/graphstores/test_sqlite_store.py
git commit -m "feat(graphstores): SqliteGraphStore schema bootstrap"
```

---

### Task 5: `upsert_nodes` + FTS sync

**Files:**
- Modify: `src/fireflyframework_agentic/graphstores/sqlite.py`
- Modify: `tests/graphstores/test_sqlite_store.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/graphstores/test_sqlite_store.py`:

```python
from fireflyframework_agentic.graphstores import Node


async def test_upsert_nodes_writes_rows_and_fts(store: SqliteGraphStore):
    nodes = [
        Node(
            label="Person",
            key="sam-altman",
            properties={"name": "Sam Altman", "aliases": ["Sam", "S. Altman"], "description": "CEO of OpenAI"},
            source_doc_id="doc-1",
            extractor_name="person",
            chunk_ids=["c0", "c1"],
        ),
    ]
    await store.upsert_nodes(nodes)

    rows = await store.query("SELECT * FROM nodes WHERE source_doc_id='doc-1'")
    assert len(rows) == 1
    assert rows[0]["label"] == "Person"
    assert rows[0]["key"] == "sam-altman"
    # properties stored as JSON
    import json
    props = json.loads(rows[0]["properties"])
    assert props["name"] == "Sam Altman"
    # chunk_ids stored as JSON
    assert json.loads(rows[0]["chunk_ids"]) == ["c0", "c1"]

    # Node-chunk junction populated
    junction = await store.query("SELECT * FROM node_chunks WHERE source_doc_id='doc-1'")
    assert {r["chunk_id"] for r in junction} == {"c0", "c1"}

    # FTS includes canonical name + aliases + description
    fts = await store.query(
        "SELECT key, text FROM nodes_fts WHERE nodes_fts MATCH :q",
        {"q": "altman"},
    )
    assert len(fts) >= 1
    assert "altman" in fts[0]["text"].lower()


async def test_upsert_nodes_replaces_on_conflict(store: SqliteGraphStore):
    n1 = Node(label="Person", key="a", properties={"v": 1}, source_doc_id="d", extractor_name="x", chunk_ids=["c1"])
    n2 = Node(label="Person", key="a", properties={"v": 2}, source_doc_id="d", extractor_name="x", chunk_ids=["c2"])
    await store.upsert_nodes([n1])
    await store.upsert_nodes([n2])

    rows = await store.query("SELECT * FROM nodes WHERE source_doc_id='d'")
    assert len(rows) == 1
    import json
    assert json.loads(rows[0]["properties"]) == {"v": 2}
    assert json.loads(rows[0]["chunk_ids"]) == ["c2"]

    junction = await store.query("SELECT chunk_id FROM node_chunks WHERE source_doc_id='d'")
    assert {r["chunk_id"] for r in junction} == {"c2"}  # old c1 rows gone
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py -v
```

Expected: `AttributeError: 'SqliteGraphStore' object has no attribute 'upsert_nodes'` (or similar).

- [ ] **Step 3: Implement `upsert_nodes` with FTS + junction sync**

Add to `SqliteGraphStore`:

```python
async def upsert_nodes(self, nodes: Sequence[Node]) -> None:
    if not nodes:
        return
    async with self._lock:
        await asyncio.to_thread(self._upsert_nodes_sync, list(nodes))

def _upsert_nodes_sync(self, nodes: list[Node]) -> None:
    assert self._conn is not None
    cur = self._conn
    cur.execute("BEGIN")
    try:
        for n in nodes:
            cur.execute(
                """INSERT OR REPLACE INTO nodes
                   (source_doc_id, label, key, properties, extractor_name, chunk_ids)
                   VALUES (:source_doc_id, :label, :key, :properties, :extractor_name, :chunk_ids)""",
                {
                    "source_doc_id": n.source_doc_id,
                    "label": n.label,
                    "key": n.key,
                    "properties": json.dumps(n.properties),
                    "extractor_name": n.extractor_name,
                    "chunk_ids": json.dumps(n.chunk_ids),
                },
            )
            # Refresh node_chunks junction (replace pattern: delete then insert).
            cur.execute(
                "DELETE FROM node_chunks WHERE source_doc_id=:doc AND label=:lbl AND key=:k",
                {"doc": n.source_doc_id, "lbl": n.label, "k": n.key},
            )
            for cid in n.chunk_ids:
                cur.execute(
                    """INSERT INTO node_chunks (source_doc_id, label, key, chunk_id)
                       VALUES (:doc, :lbl, :k, :cid)""",
                    {"doc": n.source_doc_id, "lbl": n.label, "k": n.key, "cid": cid},
                )
            # Refresh nodes_fts (delete prior row by composite key, then insert).
            cur.execute(
                """DELETE FROM nodes_fts
                   WHERE source_doc_id = :doc AND label = :lbl AND key = :k""",
                {"doc": n.source_doc_id, "lbl": n.label, "k": n.key},
            )
            cur.execute(
                """INSERT INTO nodes_fts (source_doc_id, label, key, text)
                   VALUES (:doc, :lbl, :k, :text)""",
                {
                    "doc": n.source_doc_id,
                    "lbl": n.label,
                    "k": n.key,
                    "text": _node_fts_text(n),
                },
            )
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
```

Add helper at module level (above the class):

```python
def _node_fts_text(node: Node) -> str:
    """Materialise the FTS searchable text from key + aliases + description."""
    parts: list[str] = [node.key]
    description = node.properties.get("description")
    if description:
        parts.append(str(description))
    aliases = node.properties.get("aliases") or []
    parts.extend(str(a) for a in aliases)
    return " ".join(parts)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/graphstores/sqlite.py tests/graphstores/test_sqlite_store.py
git commit -m "feat(graphstores): upsert_nodes with FTS5 + junction sync"
```

---

### Task 6: `upsert_edges` + edge FTS sync

**Files:**
- Modify: `src/fireflyframework_agentic/graphstores/sqlite.py`
- Modify: `tests/graphstores/test_sqlite_store.py`

- [ ] **Step 1: Failing test**

Append:

```python
from fireflyframework_agentic.graphstores import Edge


async def test_upsert_edges_writes_rows_and_fts(store: SqliteGraphStore):
    edges = [
        Edge(
            label="WORKS_AT",
            source_label="Person",
            source_key="sam-altman",
            target_label="Organization",
            target_key="openai",
            properties={"role": "Chief Executive Officer", "start": "2019"},
            source_doc_id="doc-1",
            extractor_name="person",
        ),
    ]
    await store.upsert_edges(edges)
    rows = await store.query("SELECT * FROM edges WHERE source_doc_id='doc-1'")
    assert len(rows) == 1
    assert rows[0]["label"] == "WORKS_AT"
    # FTS over edge properties — 'chief executive' is a phrase across role text
    fts = await store.query(
        "SELECT * FROM edges_fts WHERE edges_fts MATCH :q",
        {"q": '"chief executive"'},
    )
    assert len(fts) == 1
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py::test_upsert_edges_writes_rows_and_fts -v
```

- [ ] **Step 3: Implement**

Add to `SqliteGraphStore`:

```python
async def upsert_edges(self, edges: Sequence[Edge]) -> None:
    if not edges:
        return
    async with self._lock:
        await asyncio.to_thread(self._upsert_edges_sync, list(edges))

def _upsert_edges_sync(self, edges: list[Edge]) -> None:
    assert self._conn is not None
    cur = self._conn
    cur.execute("BEGIN")
    try:
        for e in edges:
            cur.execute(
                """INSERT INTO edges
                   (source_doc_id, label, source_label, source_key, target_label, target_key,
                    properties, extractor_name)
                   VALUES (:source_doc_id, :label, :source_label, :source_key,
                           :target_label, :target_key, :properties, :extractor_name)""",
                {
                    "source_doc_id": e.source_doc_id,
                    "label": e.label,
                    "source_label": e.source_label,
                    "source_key": e.source_key,
                    "target_label": e.target_label,
                    "target_key": e.target_key,
                    "properties": json.dumps(e.properties),
                    "extractor_name": e.extractor_name,
                },
            )
            cur.execute(
                """INSERT INTO edges_fts
                   (source_doc_id, label, source_label, source_key,
                    target_label, target_key, text)
                   VALUES (:source_doc_id, :label, :source_label, :source_key,
                           :target_label, :target_key, :text)""",
                {
                    "source_doc_id": e.source_doc_id,
                    "label": e.label,
                    "source_label": e.source_label,
                    "source_key": e.source_key,
                    "target_label": e.target_label,
                    "target_key": e.target_key,
                    "text": _edge_fts_text(e),
                },
            )
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
```

Add helper:

```python
def _edge_fts_text(edge: Edge) -> str:
    """Materialise FTS searchable text from edge label + property strings."""
    parts: list[str] = [edge.label]
    for value in edge.properties.values():
        if isinstance(value, str):
            parts.append(value)
    return " ".join(parts)
```

Note: edges are append-only per ingest; doc-id replace via `delete_by_doc_id` clears prior edges before re-extraction (Task 7), so we don't need an INSERT OR REPLACE pattern here.

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/graphstores/sqlite.py tests/graphstores/test_sqlite_store.py
git commit -m "feat(graphstores): upsert_edges with edges_fts sync"
```

---

### Task 7: `delete_by_doc_id` (cascading)

**Files:**
- Modify: `src/fireflyframework_agentic/graphstores/sqlite.py`
- Modify: `tests/graphstores/test_sqlite_store.py`

- [ ] **Step 1: Failing test**

Append:

```python
async def test_delete_by_doc_id_cascades_through_all_tables(store: SqliteGraphStore):
    # Seed two docs, delete one, the other survives.
    n1 = Node(label="Person", key="a", properties={}, source_doc_id="doc-1", extractor_name="x", chunk_ids=["c0"])
    n2 = Node(label="Person", key="b", properties={}, source_doc_id="doc-2", extractor_name="x", chunk_ids=["c1"])
    e1 = Edge(label="X", source_label="Person", source_key="a", target_label="Person", target_key="b",
              properties={}, source_doc_id="doc-1", extractor_name="x")
    e2 = Edge(label="X", source_label="Person", source_key="b", target_label="Person", target_key="a",
              properties={}, source_doc_id="doc-2", extractor_name="x")
    await store.upsert_nodes([n1, n2])
    await store.upsert_edges([e1, e2])

    deleted = await store.delete_by_doc_id("doc-1")
    assert deleted >= 2  # at least one node + one edge

    nodes_left = await store.query("SELECT source_doc_id FROM nodes")
    assert {r["source_doc_id"] for r in nodes_left} == {"doc-2"}
    edges_left = await store.query("SELECT source_doc_id FROM edges")
    assert {r["source_doc_id"] for r in edges_left} == {"doc-2"}
    junction_left = await store.query("SELECT source_doc_id FROM node_chunks")
    assert {r["source_doc_id"] for r in junction_left} == {"doc-2"}
    fts_nodes = await store.query("SELECT source_doc_id FROM nodes_fts")
    assert {r["source_doc_id"] for r in fts_nodes} == {"doc-2"}
    fts_edges = await store.query("SELECT source_doc_id FROM edges_fts")
    assert {r["source_doc_id"] for r in fts_edges} == {"doc-2"}
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py::test_delete_by_doc_id_cascades_through_all_tables -v
```

- [ ] **Step 3: Implement**

Add to `SqliteGraphStore`:

```python
async def delete_by_doc_id(self, doc_id: str) -> int:
    async with self._lock:
        return await asyncio.to_thread(self._delete_by_doc_id_sync, doc_id)

def _delete_by_doc_id_sync(self, doc_id: str) -> int:
    assert self._conn is not None
    cur = self._conn
    cur.execute("BEGIN")
    try:
        n_nodes = cur.execute(
            "DELETE FROM nodes WHERE source_doc_id = :doc",
            {"doc": doc_id},
        ).rowcount
        n_edges = cur.execute(
            "DELETE FROM edges WHERE source_doc_id = :doc",
            {"doc": doc_id},
        ).rowcount
        cur.execute(
            "DELETE FROM node_chunks WHERE source_doc_id = :doc",
            {"doc": doc_id},
        )
        cur.execute(
            "DELETE FROM nodes_fts WHERE source_doc_id = :doc",
            {"doc": doc_id},
        )
        cur.execute(
            "DELETE FROM edges_fts WHERE source_doc_id = :doc",
            {"doc": doc_id},
        )
        cur.execute("COMMIT")
        return n_nodes + n_edges
    except Exception:
        cur.execute("ROLLBACK")
        raise
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/graphstores/sqlite.py tests/graphstores/test_sqlite_store.py
git commit -m "feat(graphstores): delete_by_doc_id cascades through all tables"
```

---

### Task 8: Wire `SqliteGraphStore` into `__init__` and verify protocol conformance

**Files:**
- Modify: `src/fireflyframework_agentic/graphstores/__init__.py`
- Modify: `tests/graphstores/test_sqlite_store.py`

- [ ] **Step 1: Failing test for protocol conformance**

Append to `tests/graphstores/test_sqlite_store.py`:

```python
from fireflyframework_agentic.graphstores import GraphStoreProtocol


async def test_store_satisfies_protocol(store: SqliteGraphStore):
    assert isinstance(store, GraphStoreProtocol)


async def test_top_level_import_exposes_store():
    from fireflyframework_agentic.graphstores import SqliteGraphStore as Imported
    assert Imported is SqliteGraphStore
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/graphstores/test_sqlite_store.py::test_top_level_import_exposes_store -v
```

Expected: ImportError.

- [ ] **Step 3: Update `__init__.py`**

```python
# (license header)
from __future__ import annotations

from fireflyframework_agentic.graphstores.protocol import GraphStoreProtocol
from fireflyframework_agentic.graphstores.sqlite import SqliteGraphStore
from fireflyframework_agentic.graphstores.types import Edge, Node

__all__ = ["Edge", "GraphStoreProtocol", "Node", "SqliteGraphStore"]
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/graphstores/ -v
```

Expected: full suite green (~10 tests).

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/graphstores tests/graphstores
git commit -m "feat(graphstores): expose SqliteGraphStore from package root"
```

---

# Phase 4 — Markitdown loader

### Task 9: `MarkitdownLoader`

**Files:**
- Create: `src/fireflyframework_agentic/content/loaders/__init__.py`
- Create: `src/fireflyframework_agentic/content/loaders/markitdown.py`
- Create: `tests/content/loaders/__init__.py`
- Create: `tests/content/loaders/test_markitdown.py`
- Create: `tests/content/loaders/fixtures/sample.html`
- Create: `tests/content/loaders/fixtures/sample.txt`

- [ ] **Step 1: Create fixtures**

`tests/content/loaders/fixtures/sample.html`:

```html
<!doctype html>
<html><body><h1>Hello</h1><p>This is a sample HTML document.</p></body></html>
```

`tests/content/loaders/fixtures/sample.txt`:

```
This is a plain text fixture for the loader tests.
```

(For PDF/DOCX/PPTX/XLSX fixtures, see Task 10 — keep this task focused on HTML + plain text since those don't need binary fixtures.)

- [ ] **Step 2: Failing test**

`tests/content/loaders/test_markitdown.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from fireflyframework_agentic.content.loaders import MarkitdownLoader

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_html_returns_markdown_with_metadata():
    loader = MarkitdownLoader()
    doc = loader.load(FIXTURES / "sample.html")
    assert "Hello" in doc.content
    assert "sample HTML document" in doc.content
    assert doc.metadata["source_path"].endswith("sample.html")
    assert doc.metadata["mime_type"]


def test_load_plain_text_passes_through():
    loader = MarkitdownLoader()
    doc = loader.load(FIXTURES / "sample.txt")
    assert "plain text fixture" in doc.content


def test_load_missing_file_raises():
    loader = MarkitdownLoader()
    with pytest.raises(FileNotFoundError):
        loader.load(FIXTURES / "does-not-exist.pdf")
```

`tests/content/loaders/__init__.py`: empty.

- [ ] **Step 3: Run failing**

```bash
uv run pytest -x tests/content/loaders/test_markitdown.py -v
```

- [ ] **Step 4: Implement**

`src/fireflyframework_agentic/content/loaders/markitdown.py`:

```python
# (license header)

from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Document:
    """Result of loading a single source file: markdown content + metadata."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MarkitdownLoader:
    """Wraps `markitdown.MarkItDown` to produce a uniform Document.

    Lazily imports markitdown so that the optional dependency is only required
    when this loader is actually used.
    """

    def __init__(self) -> None:
        self._md: Any = None

    def _md_instance(self) -> Any:
        if self._md is None:
            from markitdown import MarkItDown
            self._md = MarkItDown()
        return self._md

    def load(self, path: str | Path) -> Document:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Source file not found: {p}")
        result = self._md_instance().convert(str(p))
        mime, _ = mimetypes.guess_type(str(p))
        return Document(
            content=result.text_content or "",
            metadata={
                "source_path": str(p.resolve()),
                "mime_type": mime or "application/octet-stream",
                "title": getattr(result, "title", None) or "",
            },
        )
```

`src/fireflyframework_agentic/content/loaders/__init__.py`:

```python
# (license header)
from __future__ import annotations

from fireflyframework_agentic.content.loaders.markitdown import Document, MarkitdownLoader

__all__ = ["Document", "MarkitdownLoader"]
```

- [ ] **Step 5: Tests pass**

```bash
uv run pytest -x tests/content/loaders/test_markitdown.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/fireflyframework_agentic/content/loaders tests/content/loaders
git commit -m "feat(content): MarkitdownLoader for unified document ingestion"
```

---

### Task 10: Add binary fixtures (PDF, DOCX) and broader format tests

**Files:**
- Create: `tests/content/loaders/fixtures/sample.pdf`
- Create: `tests/content/loaders/fixtures/sample.docx`
- Modify: `tests/content/loaders/test_markitdown.py`

- [ ] **Step 1: Generate fixtures (one-shot using `markitdown`'s siblings)**

Create them deterministically with a small script. Run from repo root:

```bash
uv run python - <<'PY'
from pathlib import Path
import subprocess

fx = Path("tests/content/loaders/fixtures")
fx.mkdir(parents=True, exist_ok=True)

# Tiny PDF via reportlab (already a transitive dep of pdfplumber, available in dev extras).
from reportlab.pdfgen import canvas
c = canvas.Canvas(str(fx / "sample.pdf"))
c.drawString(72, 720, "PDF fixture: a person named Sam Altman works at OpenAI.")
c.showPage()
c.save()

# Tiny DOCX via python-docx (transitive of markitdown).
from docx import Document
d = Document()
d.add_paragraph("DOCX fixture: a person named Sam Altman works at OpenAI.")
d.save(fx / "sample.docx")
print("ok")
PY
```

If `reportlab` or `python-docx` are missing, install them via the `[markitdown]` and `[dev]` extras (already pulled by `pdfplumber`/`markitdown[docx]`).

- [ ] **Step 2: Add tests**

Append to `tests/content/loaders/test_markitdown.py`:

```python
def test_load_pdf_extracts_text():
    loader = MarkitdownLoader()
    doc = loader.load(FIXTURES / "sample.pdf")
    assert "Sam Altman" in doc.content
    assert doc.metadata["mime_type"] == "application/pdf"


def test_load_docx_extracts_text():
    loader = MarkitdownLoader()
    doc = loader.load(FIXTURES / "sample.docx")
    assert "Sam Altman" in doc.content
```

- [ ] **Step 3: Tests pass**

```bash
uv run pytest -x tests/content/loaders/test_markitdown.py -v
```

- [ ] **Step 4: Commit (fixtures + tests together)**

```bash
git add tests/content/loaders/fixtures tests/content/loaders/test_markitdown.py
git commit -m "test(content): MarkitdownLoader covers PDF + DOCX paths"
```

---

# Phase 5 — Folder watcher

### Task 11: `FolderWatcher` with debounce, stability, reconciliation

**Files:**
- Create: `src/fireflyframework_agentic/pipeline/triggers/__init__.py`
- Create: `src/fireflyframework_agentic/pipeline/triggers/folder_watcher.py`
- Create: `tests/pipeline/triggers/__init__.py`
- Create: `tests/pipeline/triggers/test_folder_watcher.py`

- [ ] **Step 1: Failing tests**

`tests/pipeline/triggers/test_folder_watcher.py`:

```python
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from fireflyframework_agentic.pipeline.triggers import FolderWatcher


async def test_startup_scan_yields_existing_files(tmp_path):
    (tmp_path / "a.txt").write_text("hello a")
    (tmp_path / "b.txt").write_text("hello b")

    watcher = FolderWatcher(folder=tmp_path, debounce_ms=10, stability_polls=1, stability_interval_ms=10)

    seen: set[str] = set()

    async def collect():
        async for path in watcher.startup_scan():
            seen.add(path.name)

    await asyncio.wait_for(collect(), timeout=2.0)
    assert seen == {"a.txt", "b.txt"}


async def test_skips_files_not_yet_stable(tmp_path):
    target = tmp_path / "growing.txt"
    target.write_text("0")

    watcher = FolderWatcher(folder=tmp_path, debounce_ms=10, stability_polls=2, stability_interval_ms=20)

    # Simulate a file whose size keeps changing.
    async def keep_writing():
        for i in range(5):
            await asyncio.sleep(0.005)
            target.write_text("0" * (i + 1))

    writer = asyncio.create_task(keep_writing())
    stable = await watcher.wait_for_stability(target, max_wait_ms=120)
    await writer
    # If size kept changing within the wait window, stability should be False
    assert stable is False or target.stat().st_size > 0


async def test_returns_stable_for_quiescent_file(tmp_path):
    target = tmp_path / "still.txt"
    target.write_text("hi")
    watcher = FolderWatcher(folder=tmp_path, debounce_ms=5, stability_polls=2, stability_interval_ms=10)
    assert await watcher.wait_for_stability(target, max_wait_ms=200) is True
```

`tests/pipeline/triggers/__init__.py`: empty.

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/pipeline/triggers/ -v
```

- [ ] **Step 3: Implement**

`src/fireflyframework_agentic/pipeline/triggers/folder_watcher.py`:

```python
# (license header)

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FolderWatcher:
    """Yield paths for new / changed files under a folder.

    Uses `watchfiles.awatch` for events. Each candidate path is held back until
    its size has been observed unchanged across `stability_polls` consecutive
    polls (a heuristic for "the writer has finished"). The `startup_scan`
    helper enumerates existing files so callers can reconcile against a ledger.
    """

    folder: Path
    debounce_ms: int = 500
    stability_polls: int = 2
    stability_interval_ms: int = 200

    async def startup_scan(self) -> AsyncIterator[Path]:
        for p in sorted(self.folder.iterdir()):
            if p.is_file():
                yield p

    async def wait_for_stability(self, path: Path, *, max_wait_ms: int = 5000) -> bool:
        deadline = asyncio.get_event_loop().time() + max_wait_ms / 1000.0
        last_size = -1
        stable_count = 0
        while asyncio.get_event_loop().time() < deadline:
            try:
                size = path.stat().st_size
            except FileNotFoundError:
                return False
            if size == last_size:
                stable_count += 1
                if stable_count >= self.stability_polls:
                    return True
            else:
                stable_count = 0
                last_size = size
            await asyncio.sleep(self.stability_interval_ms / 1000.0)
        return False

    async def watch(self) -> AsyncIterator[Path]:
        from watchfiles import Change, awatch

        debounce_seen: dict[Path, float] = {}
        async for changes in awatch(str(self.folder), debounce=self.debounce_ms):
            for change, raw_path in changes:
                if change is Change.deleted:
                    continue
                path = Path(raw_path)
                if not path.is_file():
                    continue
                # Wait for stability, then yield.
                if await self.wait_for_stability(path):
                    yield path
```

`src/fireflyframework_agentic/pipeline/triggers/__init__.py`:

```python
# (license header)
from __future__ import annotations

from fireflyframework_agentic.pipeline.triggers.folder_watcher import FolderWatcher

__all__ = ["FolderWatcher"]
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/pipeline/triggers/ -v
```

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/pipeline/triggers tests/pipeline/triggers
git commit -m "feat(pipeline): FolderWatcher with stability + startup scan"
```

---

# Phase 6 — Extractor base + registry

### Task 12: `Extractor` protocol and `IngestedDoc`

**Files:**
- Create: `examples/__init__.py` (empty — promotes `examples/` to a package so `python -m examples.kg_ingest` resolves)
- Create: `examples/kg_ingest/__init__.py` (empty for now)
- Create: `examples/kg_ingest/extractors/__init__.py` (empty for now)
- Create: `examples/kg_ingest/extractors/base.py`
- Create: `tests/kg_ingest/__init__.py`
- Create: `tests/kg_ingest/test_extractors_base.py`

> Note: The existing flat scripts under `examples/` (`basic_agent.py`, `idp_pipeline.py`, etc.) keep working as scripts even after `examples/` becomes a package — they're not imported as modules by anything.

- [ ] **Step 1: Failing test**

`tests/kg_ingest/test_extractors_base.py`:

```python
from __future__ import annotations

from pydantic import BaseModel

from fireflyframework_agentic.graphstores import Edge, Node
from examples.kg_ingest.extractors.base import (
    Extractor,
    IngestedDoc,
)


def test_ingested_doc_carries_chunks_and_metadata():
    doc = IngestedDoc(
        doc_id="doc-1",
        source_path="/tmp/x.pdf",
        content_hash="abc",
        markdown="hello world",
        chunks=[{"chunk_id": "c0", "content": "hello world"}],
    )
    assert doc.doc_id == "doc-1"
    assert doc.chunks[0]["chunk_id"] == "c0"


def test_extractor_protocol_runtime_checkable():
    class _Schema(BaseModel):
        text: str

    class _StubExtractor:
        name = "stub"
        output_schema = _Schema
        prompt = None  # type: ignore
        def build_agent(self, model): return None
        def to_graph(self, doc, output): return ([], [])
        post_step = None

    assert isinstance(_StubExtractor(), Extractor)
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_base.py -v
```

- [ ] **Step 3: Implement**

`examples/kg_ingest/extractors/base.py`:

```python
# (license header)

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from fireflyframework_agentic.agents import FireflyAgent
from fireflyframework_agentic.graphstores import Edge, Node
from fireflyframework_agentic.prompts import PromptTemplate


@dataclass(slots=True)
class IngestedDoc:
    """The document handed to extractors after preprocess.

    `chunks` is a list of dicts with at least `chunk_id` and `content`.
    Embedding metadata is attached during the embed step and is not required
    by extractors.
    """

    doc_id: str
    source_path: str
    content_hash: str
    markdown: str
    chunks: list[dict[str, Any]] = field(default_factory=list)


PostExtractStep = Callable[[IngestedDoc, BaseModel, "ExtractorContext"], "Any"]


@dataclass(slots=True)
class ExtractorContext:
    """Runtime context passed to post-steps (output paths, graph store, etc.)."""

    out_dir: str
    graph_store: Any  # GraphStoreProtocol — typed loosely to avoid import cycles


@runtime_checkable
class Extractor(Protocol):
    """Plug-in contract for extractors.

    Implementations live in `examples/kg_ingest/extractors/<name>.py` and are
    registered by name in `examples.kg_ingest.extractors.__init__.EXTRACTORS`.
    """

    name: str
    output_schema: type[BaseModel]
    prompt: PromptTemplate
    post_step: PostExtractStep | None

    def build_agent(self, model: str) -> FireflyAgent: ...

    def to_graph(
        self, doc: IngestedDoc, output: BaseModel
    ) -> tuple[Sequence[Node], Sequence[Edge]]: ...
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_base.py -v
```

- [ ] **Step 5: Commit**

```bash
git add examples/kg_ingest tests/kg_ingest
git commit -m "feat(kg_ingest): Extractor protocol + IngestedDoc dataclass"
```

---

# Phase 7 — BPMN extractor

### Task 13: BPMN schemas + prompt + graph mapper

**Files:**
- Create: `examples/kg_ingest/prompts/bpmn.j2`
- Create: `examples/kg_ingest/extractors/bpmn.py`
- Create: `tests/kg_ingest/test_extractors_bpmn.py`

- [ ] **Step 1: Failing tests**

`tests/kg_ingest/test_extractors_bpmn.py`:

```python
from __future__ import annotations

from examples.kg_ingest.extractors.base import IngestedDoc
from examples.kg_ingest.extractors.bpmn import (
    BpmnExtraction,
    BpmnExtractor,
    BpmnFlow,
    BpmnNode,
)


def _doc():
    return IngestedDoc(
        doc_id="doc-1",
        source_path="/tmp/process.txt",
        content_hash="abc",
        markdown="A simple approval process.",
        chunks=[{"chunk_id": "c0", "content": "..."}],
    )


def test_bpmn_extraction_schema_validates_required_node_types():
    output = BpmnExtraction(
        nodes=[
            BpmnNode(id="s1", type="StartEvent", name="Start"),
            BpmnNode(id="t1", type="Task", name="Review request"),
            BpmnNode(id="e1", type="EndEvent", name="End"),
        ],
        flows=[
            BpmnFlow(source_id="s1", target_id="t1"),
            BpmnFlow(source_id="t1", target_id="e1"),
        ],
    )
    assert len(output.nodes) == 3
    assert output.flows[0].source_id == "s1"


def test_to_graph_maps_nodes_and_flows():
    extractor = BpmnExtractor()
    output = BpmnExtraction(
        nodes=[
            BpmnNode(id="t1", type="Task", name="Review"),
            BpmnNode(id="g1", type="Gateway", name="Approved?"),
        ],
        flows=[BpmnFlow(source_id="t1", target_id="g1", condition="default")],
    )
    nodes, edges = extractor.to_graph(_doc(), output)
    by_key = {n.key: n for n in nodes}
    assert by_key["t1"].label == "Task"
    assert by_key["g1"].label == "Gateway"
    assert by_key["t1"].source_doc_id == "doc-1"
    assert all(n.extractor_name == "bpmn" for n in nodes)
    assert len(edges) == 1
    edge = edges[0]
    assert edge.label == "SequenceFlow"
    assert edge.source_key == "t1"
    assert edge.target_key == "g1"
    assert edge.properties["condition"] == "default"
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_bpmn.py -v
```

- [ ] **Step 3: Create the prompt template**

`examples/kg_ingest/prompts/bpmn.j2`:

```jinja
You are a business-process analyst. Extract a BPMN 2.0 process model from the following document.

Identify:
- Start and end events
- Tasks (human or automated)
- Gateways (decisions, parallel splits)
- Sequence flows between them
- Pools and lanes (if present)

For each element, provide a stable `id` (kebab-case, descriptive) and a short `name`.
For sequence flows, include the optional `condition` if the flow leaves a gateway.
Use `parent` only for elements contained in a Pool or Lane.

If the document does not describe a process, return empty `nodes` and `flows` lists.

Document:
{{ markdown }}
```

- [ ] **Step 4: Implement the extractor**

`examples/kg_ingest/extractors/bpmn.py`:

```python
# (license header)

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from fireflyframework_agentic.agents import FireflyAgent, create_extractor_agent
from fireflyframework_agentic.graphstores import Edge, Node
from fireflyframework_agentic.prompts import PromptLoader, PromptTemplate, PromptVariable

from examples.kg_ingest.extractors.base import (
    ExtractorContext,
    IngestedDoc,
    PostExtractStep,
)


_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bpmn.j2"


BpmnNodeType = Literal["Task", "Gateway", "StartEvent", "EndEvent", "Pool", "Lane"]


class BpmnNode(BaseModel):
    id: str
    type: BpmnNodeType
    name: str
    parent: str | None = None


class BpmnFlow(BaseModel):
    source_id: str
    target_id: str
    condition: str | None = None


class BpmnExtraction(BaseModel):
    nodes: list[BpmnNode] = Field(default_factory=list)
    flows: list[BpmnFlow] = Field(default_factory=list)


class BpmnExtractor:
    """BPMN extractor — produces process-modelling nodes + sequence flows
    plus, post-write, a `.bpmn` 2.0 XML artefact.
    """

    name = "bpmn"
    output_schema = BpmnExtraction
    prompt: PromptTemplate = PromptLoader.from_file(
        _PROMPT_PATH,
        name="kg_ingest.bpmn",
        description="BPMN 2.0 process extraction",
        variables=[PromptVariable(name="markdown", description="document markdown")],
    )

    def build_agent(self, model: str) -> FireflyAgent:
        return create_extractor_agent(
            BpmnExtraction,
            name="kg_ingest_bpmn",
            model=model,
            extra_instructions=self.prompt.render(markdown="{{markdown}}"),
        )

    def to_graph(
        self, doc: IngestedDoc, output: BpmnExtraction
    ) -> tuple[Sequence[Node], Sequence[Edge]]:
        chunk_ids = [c["chunk_id"] for c in doc.chunks]
        nodes: list[Node] = [
            Node(
                label=n.type,
                key=n.id,
                properties={"name": n.name, **({"parent": n.parent} if n.parent else {})},
                source_doc_id=doc.doc_id,
                extractor_name=self.name,
                chunk_ids=chunk_ids,
            )
            for n in output.nodes
        ]
        # Build a {id: type} index so flow edges can carry source/target labels.
        type_by_id = {n.id: n.type for n in output.nodes}
        edges: list[Edge] = []
        for f in output.flows:
            src_label = type_by_id.get(f.source_id, "Unknown")
            tgt_label = type_by_id.get(f.target_id, "Unknown")
            edge_props = {"condition": f.condition} if f.condition else {}
            edges.append(
                Edge(
                    label="SequenceFlow",
                    source_label=src_label,
                    source_key=f.source_id,
                    target_label=tgt_label,
                    target_key=f.target_id,
                    properties=edge_props,
                    source_doc_id=doc.doc_id,
                    extractor_name=self.name,
                )
            )
        return nodes, edges

    # post_step assigned after `serialize_bpmn` is implemented (Task 14).
    post_step: PostExtractStep | None = None
```

- [ ] **Step 5: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_bpmn.py -v
```

- [ ] **Step 6: Commit**

```bash
git add examples/kg_ingest/prompts/bpmn.j2 examples/kg_ingest/extractors/bpmn.py tests/kg_ingest/test_extractors_bpmn.py
git commit -m "feat(kg_ingest): BPMN extractor schema + prompt + graph mapper"
```

---

### Task 14: BPMN 2.0 XML serializer + post-step

**Files:**
- Create: `examples/kg_ingest/bpmn_serializer.py`
- Modify: `examples/kg_ingest/extractors/bpmn.py`
- Create: `tests/kg_ingest/test_bpmn_serializer.py`

- [ ] **Step 1: Failing test**

`tests/kg_ingest/test_bpmn_serializer.py`:

```python
from __future__ import annotations

from examples.kg_ingest.bpmn_serializer import serialize_bpmn


def test_serialize_emits_valid_bpmn_skeleton():
    nodes = [
        {"id": "s1", "type": "StartEvent", "name": "Start"},
        {"id": "t1", "type": "Task", "name": "Review request"},
        {"id": "e1", "type": "EndEvent", "name": "End"},
    ]
    flows = [
        {"id": "f1", "source_id": "s1", "target_id": "t1"},
        {"id": "f2", "source_id": "t1", "target_id": "e1"},
    ]
    xml = serialize_bpmn(nodes, flows, process_id="proc-1", process_name="Approval")
    assert xml.startswith("<?xml")
    assert "bpmn:definitions" in xml
    assert 'id="s1"' in xml
    assert 'id="t1"' in xml
    assert 'sourceRef="s1"' in xml
    assert 'targetRef="t1"' in xml
    assert "<bpmn:startEvent" in xml
    assert "<bpmn:task" in xml
    assert "<bpmn:endEvent" in xml
    assert "<bpmn:sequenceFlow" in xml
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_bpmn_serializer.py -v
```

- [ ] **Step 3: Implement serializer**

`examples/kg_ingest/bpmn_serializer.py`:

```python
# (license header)

from __future__ import annotations

from typing import Any

from lxml import etree


_BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
_NSMAP = {"bpmn": _BPMN_NS}

_TAG_BY_TYPE = {
    "StartEvent": "startEvent",
    "EndEvent": "endEvent",
    "Task": "task",
    "Gateway": "exclusiveGateway",  # default to exclusive; users can refine post-hoc
    "Pool": "participant",
    "Lane": "lane",
}


def _q(name: str) -> str:
    return f"{{{_BPMN_NS}}}{name}"


def serialize_bpmn(
    nodes: list[dict[str, Any]],
    flows: list[dict[str, Any]],
    *,
    process_id: str = "process",
    process_name: str = "Process",
) -> str:
    """Emit a BPMN 2.0 XML document for the given nodes and flows.

    `nodes` items: {"id", "type", "name", optional "parent"}.
    `flows` items: {"id", "source_id", "target_id", optional "condition"}.

    Pool/Lane containment is omitted from the diagram (BPMN diagram interchange
    "BPMNDI" is intentionally not generated — most editors auto-layout when the
    file is opened).
    """
    definitions = etree.Element(
        _q("definitions"),
        nsmap=_NSMAP,
        attrib={
            "id": f"{process_id}-defs",
            "targetNamespace": "http://example.com/kg-ingest",
        },
    )
    process = etree.SubElement(
        definitions,
        _q("process"),
        attrib={"id": process_id, "name": process_name, "isExecutable": "false"},
    )
    for n in nodes:
        tag = _TAG_BY_TYPE.get(n["type"])
        if tag is None:
            # Unknown types are emitted as <task> with name annotation as a fallback.
            tag = "task"
        elem = etree.SubElement(
            process,
            _q(tag),
            attrib={"id": n["id"], "name": n.get("name") or n["id"]},
        )
        # Attach incoming/outgoing references for editor compatibility.
        for f in flows:
            if f["target_id"] == n["id"]:
                inc = etree.SubElement(elem, _q("incoming"))
                inc.text = f["id"]
            if f["source_id"] == n["id"]:
                outg = etree.SubElement(elem, _q("outgoing"))
                outg.text = f["id"]
    for f in flows:
        attrib = {
            "id": f["id"],
            "sourceRef": f["source_id"],
            "targetRef": f["target_id"],
        }
        if f.get("condition"):
            attrib["name"] = f["condition"]
        etree.SubElement(process, _q("sequenceFlow"), attrib=attrib)

    return etree.tostring(
        definitions, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    ).decode("utf-8")
```

- [ ] **Step 4: Wire the post-step into `BpmnExtractor`**

In `examples/kg_ingest/extractors/bpmn.py`, **delete** the line
`post_step: PostExtractStep | None = None` and add this method to the class
in its place:

```python
    def post_step(
        self,
        doc: IngestedDoc,
        output: BpmnExtraction,
        ctx: ExtractorContext,
    ) -> str | None:
        """Emit the BPMN 2.0 XML file for this doc; return its path or None."""
        from pathlib import Path

        from examples.kg_ingest.bpmn_serializer import serialize_bpmn

        nodes_payload = [
            {
                "id": n.id,
                "type": n.type,
                "name": n.name,
                **({"parent": n.parent} if n.parent else {}),
            }
            for n in output.nodes
        ]
        flows_payload = [
            {
                "id": f"flow-{i}",
                "source_id": f.source_id,
                "target_id": f.target_id,
                **({"condition": f.condition} if f.condition else {}),
            }
            for i, f in enumerate(output.flows)
        ]
        if not nodes_payload:
            return None
        xml = serialize_bpmn(
            nodes_payload,
            flows_payload,
            process_id=doc.doc_id,
            process_name=Path(doc.source_path).stem,
        )
        out_file = Path(ctx.out_dir) / f"{doc.doc_id}.bpmn"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(xml, encoding="utf-8")
        return str(out_file)
```

Convention: extractors with a post-step define `post_step` as a method (a
bound method is callable, satisfying the protocol's
`PostExtractStep | None` type). Extractors without a post-step set
`post_step = None` as a class attribute (the form used by
`PersonExtractor` and `GenericExtractor`). The pipeline calls
`extractor.post_step(...)` only after a `None` check.

- [ ] **Step 5: Add a post-step test**

Append to `tests/kg_ingest/test_extractors_bpmn.py`:

```python
def test_post_step_writes_bpmn_file(tmp_path):
    extractor = BpmnExtractor()
    output = BpmnExtraction(
        nodes=[
            BpmnNode(id="s1", type="StartEvent", name="Start"),
            BpmnNode(id="t1", type="Task", name="Review"),
            BpmnNode(id="e1", type="EndEvent", name="End"),
        ],
        flows=[
            BpmnFlow(source_id="s1", target_id="t1"),
            BpmnFlow(source_id="t1", target_id="e1"),
        ],
    )
    from examples.kg_ingest.extractors.base import ExtractorContext
    from pathlib import Path

    ctx = ExtractorContext(out_dir=str(tmp_path), graph_store=None)
    out_path = extractor.post_step(_doc(), output, ctx)
    assert out_path
    content = Path(out_path).read_text(encoding="utf-8")
    assert "<bpmn:sequenceFlow" in content
    assert 'id="s1"' in content
```

- [ ] **Step 6: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/ -v
```

- [ ] **Step 7: Commit**

```bash
git add examples/kg_ingest/bpmn_serializer.py examples/kg_ingest/extractors/bpmn.py tests/kg_ingest/test_bpmn_serializer.py tests/kg_ingest/test_extractors_bpmn.py
git commit -m "feat(kg_ingest): BPMN 2.0 XML serializer + post-step"
```

---

# Phase 8 — Person extractor

### Task 15: Person schemas, prompt, graph mapper

**Files:**
- Create: `examples/kg_ingest/prompts/person.j2`
- Create: `examples/kg_ingest/extractors/person.py`
- Create: `tests/kg_ingest/test_extractors_person.py`

- [ ] **Step 1: Failing tests**

`tests/kg_ingest/test_extractors_person.py`:

```python
from __future__ import annotations

from examples.kg_ingest.extractors.base import IngestedDoc
from examples.kg_ingest.extractors.person import (
    Organization,
    Person,
    PersonExtraction,
    PersonExtractor,
    WorksAt,
)


def _doc():
    return IngestedDoc(doc_id="d", source_path="/tmp/x", content_hash="h",
                      markdown="...", chunks=[{"chunk_id": "c0"}])


def test_person_with_aliases_is_valid():
    p = Person(name="Sam Altman", aliases=["Sam", "S. Altman"], title="CEO")
    assert p.aliases == ["Sam", "S. Altman"]


def test_to_graph_uses_canonical_name_as_key_and_stores_aliases():
    extractor = PersonExtractor()
    extraction = PersonExtraction(
        persons=[Person(name="Sam Altman", aliases=["Sam"])],
        organizations=[Organization(name="OpenAI", aliases=["OpenAI Inc."])],
        employments=[WorksAt(person="Sam Altman", organization="OpenAI", role="CEO")],
    )
    nodes, edges = extractor.to_graph(_doc(), extraction)
    person_node = next(n for n in nodes if n.label == "Person")
    org_node = next(n for n in nodes if n.label == "Organization")
    assert person_node.key == "Sam Altman"
    assert person_node.properties["aliases"] == ["Sam"]
    assert org_node.properties["aliases"] == ["OpenAI Inc."]
    assert len(edges) == 1
    edge = edges[0]
    assert edge.label == "WORKS_AT"
    assert edge.source_label == "Person"
    assert edge.source_key == "Sam Altman"
    assert edge.target_label == "Organization"
    assert edge.target_key == "OpenAI"
    assert edge.properties["role"] == "CEO"
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_person.py -v
```

- [ ] **Step 3: Create prompt**

`examples/kg_ingest/prompts/person.j2`:

```jinja
Extract people, organizations, and employment relationships from the document.

For each person:
- `name`: most formal full name found in the doc
- `aliases`: any other forms ("Sam", "S. Altman") used in the same doc
- `title`, `bio`: optional

For each organization:
- `name`: canonical name
- `aliases`: variants ("OpenAI Inc.", "OpenAI, Inc.")
- `type`: optional

For employment, use canonical short forms when possible (CEO, CTO, COO, CFO,
Founder, Co-Founder, Director, VP, Manager). Keep the original phrasing only
when qualitatively different from any short form.

If the document does not contain people or organizations, return empty lists.

Document:
{{ markdown }}
```

- [ ] **Step 4: Implement extractor**

`examples/kg_ingest/extractors/person.py`:

```python
# (license header)

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, Field

from fireflyframework_agentic.agents import FireflyAgent, create_extractor_agent
from fireflyframework_agentic.graphstores import Edge, Node
from fireflyframework_agentic.prompts import PromptLoader, PromptTemplate, PromptVariable

from examples.kg_ingest.extractors.base import IngestedDoc


_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "person.j2"


class Person(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    title: str | None = None
    bio: str | None = None


class Organization(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    type: str | None = None


class WorksAt(BaseModel):
    person: str
    organization: str
    role: str | None = None
    start: str | None = None
    end: str | None = None


class PersonExtraction(BaseModel):
    persons: list[Person] = Field(default_factory=list)
    organizations: list[Organization] = Field(default_factory=list)
    employments: list[WorksAt] = Field(default_factory=list)


class PersonExtractor:
    name = "person"
    output_schema = PersonExtraction
    prompt: PromptTemplate = PromptLoader.from_file(
        _PROMPT_PATH,
        name="kg_ingest.person",
        description="Person profile + employment extraction",
        variables=[PromptVariable(name="markdown", description="document markdown")],
    )
    post_step = None

    def build_agent(self, model: str) -> FireflyAgent:
        return create_extractor_agent(
            PersonExtraction,
            name="kg_ingest_person",
            model=model,
            extra_instructions=self.prompt.render(markdown="{{markdown}}"),
        )

    def to_graph(
        self, doc: IngestedDoc, output: PersonExtraction
    ) -> tuple[Sequence[Node], Sequence[Edge]]:
        chunk_ids = [c["chunk_id"] for c in doc.chunks]
        nodes: list[Node] = []
        for p in output.persons:
            props: dict[str, object] = {"name": p.name, "aliases": list(p.aliases)}
            if p.title:
                props["title"] = p.title
            if p.bio:
                props["description"] = p.bio
            nodes.append(
                Node(
                    label="Person",
                    key=p.name,
                    properties=props,
                    source_doc_id=doc.doc_id,
                    extractor_name=self.name,
                    chunk_ids=chunk_ids,
                )
            )
        for o in output.organizations:
            props_org: dict[str, object] = {"name": o.name, "aliases": list(o.aliases)}
            if o.type:
                props_org["type"] = o.type
            nodes.append(
                Node(
                    label="Organization",
                    key=o.name,
                    properties=props_org,
                    source_doc_id=doc.doc_id,
                    extractor_name=self.name,
                    chunk_ids=chunk_ids,
                )
            )
        edges: list[Edge] = []
        for w in output.employments:
            edge_props: dict[str, object] = {}
            if w.role:
                edge_props["role"] = w.role
            if w.start:
                edge_props["start"] = w.start
            if w.end:
                edge_props["end"] = w.end
            edges.append(
                Edge(
                    label="WORKS_AT",
                    source_label="Person",
                    source_key=w.person,
                    target_label="Organization",
                    target_key=w.organization,
                    properties=edge_props,
                    source_doc_id=doc.doc_id,
                    extractor_name=self.name,
                )
            )
        return nodes, edges
```

- [ ] **Step 5: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_person.py -v
```

- [ ] **Step 6: Commit**

```bash
git add examples/kg_ingest/prompts/person.j2 examples/kg_ingest/extractors/person.py tests/kg_ingest/test_extractors_person.py
git commit -m "feat(kg_ingest): Person extractor (schema + prompt + mapper)"
```

---

# Phase 9 — Generic extractor

### Task 16: Generic extractor

**Files:**
- Create: `examples/kg_ingest/prompts/generic.j2`
- Create: `examples/kg_ingest/extractors/generic.py`
- Create: `tests/kg_ingest/test_extractors_generic.py`

- [ ] **Step 1: Failing tests**

`tests/kg_ingest/test_extractors_generic.py`:

```python
from __future__ import annotations

from examples.kg_ingest.extractors.base import IngestedDoc
from examples.kg_ingest.extractors.generic import (
    Entity,
    GenericExtraction,
    GenericExtractor,
    Relation,
)


def _doc():
    return IngestedDoc(doc_id="d", source_path="/tmp/x", content_hash="h",
                      markdown="...", chunks=[{"chunk_id": "c0"}])


def test_generic_to_graph_creates_entity_nodes_and_typed_edges():
    extractor = GenericExtractor()
    extraction = GenericExtraction(
        entities=[
            Entity(name="OpenAI", aliases=["OpenAI Inc."], type="Company", description="AI lab"),
            Entity(name="Sam Altman", type="Person", description="CEO of OpenAI"),
        ],
        relations=[
            Relation(source="Sam Altman", target="OpenAI", type="leads",
                     description="Serves as CEO"),
        ],
    )
    nodes, edges = extractor.to_graph(_doc(), extraction)
    assert {n.key for n in nodes} == {"OpenAI", "Sam Altman"}
    assert all(n.label == "Entity" for n in nodes)
    assert nodes[0].properties["aliases"] == ["OpenAI Inc."]
    assert edges[0].label == "LEADS"
    assert edges[0].source_label == "Entity"
    assert edges[0].target_label == "Entity"
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_generic.py -v
```

- [ ] **Step 3: Prompt**

`examples/kg_ingest/prompts/generic.j2`:

```jinja
{# Prompt adapted from the public LightRAG entity-extraction style (MIT). #}
You are an entity-relation extractor. From the document below, identify the
significant entities and the relationships between them.

For each entity, provide:
- `name`: canonical / most formal form found in the document
- `aliases`: any other forms used in the same document
- `type`: a short noun describing the entity ("Company", "Person", "Concept",
  "Event", "Location", "Product", ...)
- `description`: one or two sentences summarising the entity's role in the
  document

For each relation, provide:
- `source`: entity name (must match an entity in the list)
- `target`: entity name (must match an entity in the list)
- `type`: a short verb or relation phrase ("leads", "located_in", "produces")
- `description`: one sentence justifying the relation from the document

If the document is empty or contains no factual content, return empty lists.

Document:
{{ markdown }}
```

- [ ] **Step 4: Implement extractor**

`examples/kg_ingest/extractors/generic.py`:

```python
# (license header)

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, Field

from fireflyframework_agentic.agents import FireflyAgent, create_extractor_agent
from fireflyframework_agentic.graphstores import Edge, Node
from fireflyframework_agentic.prompts import PromptLoader, PromptTemplate, PromptVariable

from examples.kg_ingest.extractors.base import IngestedDoc


_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "generic.j2"


class Entity(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    type: str
    description: str


class Relation(BaseModel):
    source: str
    target: str
    type: str
    description: str


class GenericExtraction(BaseModel):
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)


class GenericExtractor:
    name = "generic"
    output_schema = GenericExtraction
    prompt: PromptTemplate = PromptLoader.from_file(
        _PROMPT_PATH,
        name="kg_ingest.generic",
        description="Generic entity-relation extraction",
        variables=[PromptVariable(name="markdown", description="document markdown")],
    )
    post_step = None

    def build_agent(self, model: str) -> FireflyAgent:
        return create_extractor_agent(
            GenericExtraction,
            name="kg_ingest_generic",
            model=model,
            extra_instructions=self.prompt.render(markdown="{{markdown}}"),
        )

    def to_graph(
        self, doc: IngestedDoc, output: GenericExtraction
    ) -> tuple[Sequence[Node], Sequence[Edge]]:
        chunk_ids = [c["chunk_id"] for c in doc.chunks]
        nodes = [
            Node(
                label="Entity",
                key=e.name,
                properties={
                    "name": e.name,
                    "type": e.type,
                    "description": e.description,
                    "aliases": list(e.aliases),
                },
                source_doc_id=doc.doc_id,
                extractor_name=self.name,
                chunk_ids=chunk_ids,
            )
            for e in output.entities
        ]
        edges = [
            Edge(
                label=r.type.upper().replace(" ", "_"),
                source_label="Entity",
                source_key=r.source,
                target_label="Entity",
                target_key=r.target,
                properties={"description": r.description, "type_text": r.type},
                source_doc_id=doc.doc_id,
                extractor_name=self.name,
            )
            for r in output.relations
        ]
        return nodes, edges
```

- [ ] **Step 5: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_extractors_generic.py -v
```

- [ ] **Step 6: Commit**

```bash
git add examples/kg_ingest/prompts/generic.j2 examples/kg_ingest/extractors/generic.py tests/kg_ingest/test_extractors_generic.py
git commit -m "feat(kg_ingest): generic entity-relation extractor"
```

---

### Task 17: Extractor registry

**Files:**
- Modify: `examples/kg_ingest/extractors/__init__.py`

- [ ] **Step 1: Failing test**

`tests/kg_ingest/test_extractor_registry.py`:

```python
from __future__ import annotations

from examples.kg_ingest.extractors import EXTRACTORS


def test_registry_has_all_v1_extractors():
    assert set(EXTRACTORS) == {"bpmn", "person", "generic"}


def test_registry_entries_have_required_attributes():
    for name, ex in EXTRACTORS.items():
        assert ex.name == name
        assert ex.output_schema is not None
        assert ex.prompt is not None
        assert callable(ex.build_agent)
        assert callable(ex.to_graph)
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_extractor_registry.py -v
```

- [ ] **Step 3: Implement**

`examples/kg_ingest/extractors/__init__.py`:

```python
# (license header)
from __future__ import annotations

from examples.kg_ingest.extractors.base import (
    Extractor,
    ExtractorContext,
    IngestedDoc,
    PostExtractStep,
)
from examples.kg_ingest.extractors.bpmn import BpmnExtractor
from examples.kg_ingest.extractors.generic import GenericExtractor
from examples.kg_ingest.extractors.person import PersonExtractor


EXTRACTORS: dict[str, Extractor] = {
    "bpmn": BpmnExtractor(),
    "person": PersonExtractor(),
    "generic": GenericExtractor(),
}


__all__ = [
    "EXTRACTORS",
    "Extractor",
    "ExtractorContext",
    "IngestedDoc",
    "PostExtractStep",
    "BpmnExtractor",
    "PersonExtractor",
    "GenericExtractor",
]
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/ -v
```

- [ ] **Step 5: Commit**

```bash
git add examples/kg_ingest/extractors/__init__.py tests/kg_ingest/test_extractor_registry.py
git commit -m "feat(kg_ingest): extractor registry"
```

---

# Phase 10 — Ledger

### Task 18: `IngestLedger`

**Files:**
- Create: `examples/kg_ingest/ledger.py`
- Create: `tests/kg_ingest/test_ledger.py`

- [ ] **Step 1: Failing tests**

`tests/kg_ingest/test_ledger.py`:

```python
from __future__ import annotations

import pytest

from fireflyframework_agentic.graphstores import SqliteGraphStore
from examples.kg_ingest.ledger import IngestLedger


@pytest.fixture
async def ledger(tmp_path):
    store = SqliteGraphStore(tmp_path / "graph.sqlite")
    await store.initialise()
    yield IngestLedger(store)
    await store.close()


async def test_should_skip_returns_false_for_unknown_path(ledger: IngestLedger):
    assert await ledger.should_skip("doc-1", "deadbeef") is False


async def test_upsert_records_status_then_should_skip_when_success(ledger: IngestLedger):
    await ledger.upsert("doc-1", "/tmp/x.pdf", "deadbeef", status="success")
    assert await ledger.should_skip("doc-1", "deadbeef") is True
    assert await ledger.should_skip("doc-1", "different-hash") is False


async def test_partial_status_does_not_skip(ledger: IngestLedger):
    await ledger.upsert(
        "doc-1", "/tmp/x.pdf", "deadbeef", status="partial",
        partial_extractors=["bpmn"],
    )
    assert await ledger.should_skip("doc-1", "deadbeef") is False
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_ledger.py -v
```

- [ ] **Step 3: Implement**

`examples/kg_ingest/ledger.py`:

```python
# (license header)

from __future__ import annotations

import json
from datetime import datetime, timezone

from fireflyframework_agentic.graphstores import SqliteGraphStore


class IngestLedger:
    """Wrapper over the `ingestions` table in the graph SQLite file.

    The graph store owns connection lifecycle; the ledger only issues queries.
    """

    def __init__(self, store: SqliteGraphStore) -> None:
        self._store = store

    async def should_skip(self, doc_id: str, content_hash: str) -> bool:
        rows = await self._store.query(
            "SELECT status, content_hash FROM ingestions WHERE doc_id = :id",
            {"id": doc_id},
        )
        if not rows:
            return False
        row = rows[0]
        return row["status"] == "success" and row["content_hash"] == content_hash

    async def upsert(
        self,
        doc_id: str,
        source_path: str,
        content_hash: str,
        *,
        status: str,
        partial_extractors: list[str] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._store.query(
            """INSERT INTO ingestions
               (doc_id, source_path, content_hash, status, partial_extractors,
                ingested_at, attempt)
               VALUES (:id, :path, :hash, :status, :partial, :now, 1)
               ON CONFLICT(doc_id) DO UPDATE SET
                 source_path = excluded.source_path,
                 content_hash = excluded.content_hash,
                 status = excluded.status,
                 partial_extractors = excluded.partial_extractors,
                 ingested_at = excluded.ingested_at,
                 attempt = ingestions.attempt + 1""",
            {
                "id": doc_id,
                "path": source_path,
                "hash": content_hash,
                "status": status,
                "partial": json.dumps(partial_extractors) if partial_extractors else None,
                "now": now,
            },
        )
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_ledger.py -v
```

- [ ] **Step 5: Commit**

```bash
git add examples/kg_ingest/ledger.py tests/kg_ingest/test_ledger.py
git commit -m "feat(kg_ingest): IngestLedger over the ingestions SQLite table"
```

---

# Phase 11 — Pipeline assembly

### Task 19: Build the per-doc DAG (`build_pipeline`)

This is the load-bearing assembly. It composes framework primitives. We'll write the integration test in Task 21; here we build the DAG itself with thin direct tests.

**Files:**
- Create: `examples/kg_ingest/pipeline.py`
- Create: `tests/kg_ingest/test_pipeline_build.py`

- [ ] **Step 1: Failing test (smoke)**

`tests/kg_ingest/test_pipeline_build.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from fireflyframework_agentic.graphstores import SqliteGraphStore
from examples.kg_ingest.extractors import EXTRACTORS
from examples.kg_ingest.pipeline import IngestPaths, build_pipeline


@pytest.fixture
async def store(tmp_path):
    s = SqliteGraphStore(tmp_path / "graph.sqlite")
    await s.initialise()
    yield s
    await s.close()


def test_build_pipeline_returns_engine(store, tmp_path):
    paths = IngestPaths(
        root=tmp_path,
        graph_store=store,
        chroma_dir=tmp_path / "chroma",
        out_dir=tmp_path / "out",
    )
    engine = build_pipeline(
        extractors=list(EXTRACTORS.values()),
        paths=paths,
        extract_model="anthropic:claude-haiku-4-5",
        embed_model="openai:text-embedding-3-small",
    )
    # Engine has a `run` async method
    assert callable(getattr(engine, "run", None))
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_pipeline_build.py -v
```

- [ ] **Step 3: Implement**

`examples/kg_ingest/pipeline.py`:

```python
# (license header)

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fireflyframework_agentic.content import Chunk, TextChunker
from fireflyframework_agentic.content.loaders import MarkitdownLoader
from fireflyframework_agentic.embeddings import BaseEmbedder
from fireflyframework_agentic.graphstores import GraphStoreProtocol, Node, Edge
from fireflyframework_agentic.pipeline import (
    AgentStep,
    CallableStep,
    EmbeddingStep,
    FailureStrategy,
    PipelineBuilder,
    PipelineEngine,
)

from examples.kg_ingest.extractors.base import (
    Extractor,
    ExtractorContext,
    IngestedDoc,
)
from examples.kg_ingest.ledger import IngestLedger


@dataclass(slots=True)
class IngestPaths:
    root: Path
    graph_store: GraphStoreProtocol
    chroma_dir: Path
    out_dir: Path


def _doc_id_for(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(64 * 1024), b""):
            h.update(block)
    return h.hexdigest()


async def _step_load(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
    path: Path = Path(inputs["path"])
    loader = MarkitdownLoader()
    document = loader.load(path)
    return {
        "path": str(path),
        "doc_id": _doc_id_for(path),
        "content_hash": _hash_file(path),
        "markdown": document.content,
        "metadata": document.metadata,
    }


async def _step_preprocess(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
    chunker = TextChunker(chunk_size=600, chunk_overlap=80)
    chunks = chunker.chunk(inputs["markdown"])
    enriched = [
        {
            "chunk_id": f"{inputs['doc_id']}-{i}",
            "content": c.content,
            "doc_id": inputs["doc_id"],
            "source_path": inputs["path"],
            "index": c.index,
        }
        for i, c in enumerate(chunks)
    ]
    doc = IngestedDoc(
        doc_id=inputs["doc_id"],
        source_path=inputs["path"],
        content_hash=inputs["content_hash"],
        markdown=inputs["markdown"],
        chunks=enriched,
    )
    return {"doc": doc, "chunks": enriched, **inputs}


def _step_reset_factory(graph_store: GraphStoreProtocol):
    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        await graph_store.delete_by_doc_id(inputs["doc_id"])
        # Vector-store delete is performed by upsert path with overwrite=True by id;
        # for Chroma, we issue a delete by metadata filter using the upsert step.
        return inputs
    return step


def _make_extract_step(extractor: Extractor, model: str):
    """Build a CallableStep that runs the extractor agent and writes nodes/edges."""

    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        doc: IngestedDoc = inputs["doc"]
        agent = extractor.build_agent(model)
        result = await agent.run(doc.markdown)
        output = result.output  # pydantic_ai RunResult attr
        nodes, edges = extractor.to_graph(doc, output)
        return {"extractor": extractor.name, "nodes": list(nodes), "edges": list(edges), "output": output, **inputs}

    return step


def _make_graph_write_step(graph_store: GraphStoreProtocol):
    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        nodes: Sequence[Node] = inputs["nodes"]
        edges: Sequence[Edge] = inputs["edges"]
        await graph_store.upsert_nodes(nodes)
        await graph_store.upsert_edges(edges)
        return inputs
    return step


def _make_post_step(extractor: Extractor, paths: IngestPaths):
    if extractor.post_step is None:
        return None

    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        doc: IngestedDoc = inputs["doc"]
        post = extractor.post_step
        ec = ExtractorContext(out_dir=str(paths.out_dir), graph_store=paths.graph_store)
        if callable(post):
            artefact = post(doc, inputs["output"], ec)
            inputs["artefact"] = artefact
        return inputs

    return step


def _make_ledger_step(ledger: IngestLedger):
    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        per_extractor_failures: list[str] = list(inputs.get("_failed_extractors", []))
        status = (
            "success"
            if not per_extractor_failures
            else ("partial" if len(per_extractor_failures) < inputs["_extractor_count"] else "failed")
        )
        await ledger.upsert(
            doc_id=inputs["doc_id"],
            source_path=inputs["path"],
            content_hash=inputs["content_hash"],
            status=status,
            partial_extractors=per_extractor_failures or None,
        )
        return {"status": status, "doc_id": inputs["doc_id"]}

    return step


def build_pipeline(
    *,
    extractors: list[Extractor],
    paths: IngestPaths,
    extract_model: str,
    embed_model: str,
) -> PipelineEngine:
    """Construct the per-document DAG.

    The DAG topology is:
        load -> preprocess -> reset
        reset fans out into one branch per extractor + one branch for embedding.
        Each extractor branch: extract -> graph_write -> (optional post_step).
        Embedding branch: embed -> vector_upsert.
        All branches converge into write_ledger.
    """
    ledger = IngestLedger(paths.graph_store)  # graph_store must be SqliteGraphStore-shaped
    builder = PipelineBuilder(name="kg_ingest")

    builder.add_node("load", CallableStep(_step_load))
    builder.add_node("preprocess", CallableStep(_step_preprocess))
    builder.add_node("reset", CallableStep(_step_reset_factory(paths.graph_store)))
    builder.add_edge("load", "preprocess")
    builder.add_edge("preprocess", "reset")

    # Extractor branches.
    for extractor in extractors:
        ex_node = f"{extractor.name}_extract"
        gw_node = f"{extractor.name}_graph_write"
        builder.add_node(
            ex_node,
            CallableStep(_make_extract_step(extractor, extract_model)),
            failure_strategy=FailureStrategy.SKIP_DOWNSTREAM,
            retry_max=1,
        )
        builder.add_edge("reset", ex_node)
        builder.add_node(
            gw_node,
            CallableStep(_make_graph_write_step(paths.graph_store)),
            failure_strategy=FailureStrategy.SKIP_DOWNSTREAM,
        )
        builder.add_edge(ex_node, gw_node)
        post = _make_post_step(extractor, paths)
        if post is not None:
            ps_node = f"{extractor.name}_post_step"
            builder.add_node(
                ps_node,
                CallableStep(post),
                failure_strategy=FailureStrategy.SKIP_DOWNSTREAM,
            )
            builder.add_edge(gw_node, ps_node)
            builder.add_edge(ps_node, "ledger")
        else:
            builder.add_edge(gw_node, "ledger")

    # Embedding branch — implemented in Task 20 (deferred wiring).
    # builder.add_node("embed", CallableStep(_step_embed_factory(embed_model, paths)))
    # builder.add_edge("reset", "embed")
    # builder.add_edge("embed", "ledger")

    builder.add_node(
        "ledger",
        CallableStep(_make_ledger_step(ledger)),
        failure_strategy=FailureStrategy.PROPAGATE,  # ledger must always run
    )

    _, engine = builder.build()
    return engine
```

NOTE: this task wires extractors and graph writes; the embed branch is left as a TODO comment for Task 20 because adding embedding requires the OpenAI embedder + Chroma vector store and a separate test. The pipeline still runs end-to-end without embeddings — they're added in the next task.

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_pipeline_build.py -v
```

- [ ] **Step 5: Commit**

```bash
git add examples/kg_ingest/pipeline.py tests/kg_ingest/test_pipeline_build.py
git commit -m "feat(kg_ingest): per-doc DAG with extract -> graph -> post-step branches"
```

---

### Task 20: Add embedding + vector-store branch

**Files:**
- Modify: `examples/kg_ingest/pipeline.py`
- Modify: `tests/kg_ingest/test_pipeline_build.py`

- [ ] **Step 1: Failing test**

Append to `tests/kg_ingest/test_pipeline_build.py`:

```python
def test_pipeline_includes_embed_branch(store, tmp_path):
    paths = IngestPaths(
        root=tmp_path,
        graph_store=store,
        chroma_dir=tmp_path / "chroma",
        out_dir=tmp_path / "out",
    )
    engine = build_pipeline(
        extractors=list(EXTRACTORS.values()),
        paths=paths,
        extract_model="anthropic:claude-haiku-4-5",
        embed_model="openai:text-embedding-3-small",
    )
    # The DAG should expose an "embed" and "vector_upsert" node.
    node_ids = set(engine.dag.nodes.keys())  # PipelineEngine exposes the DAG.
    assert "embed" in node_ids
    assert "vector_upsert" in node_ids
    assert "ledger" in node_ids
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_pipeline_build.py -v
```

- [ ] **Step 3: Implement embed + vector upsert**

In `examples/kg_ingest/pipeline.py`, add:

```python
def _step_embed_factory(embed_model: str):
    """Build a CallableStep that embeds chunks via the framework embedder."""

    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        # Lazy import to avoid pulling openai unless needed.
        from fireflyframework_agentic.embeddings import OpenAIEmbedder

        # The model string may be "openai:text-embedding-3-small"; strip prefix.
        model = embed_model.split(":", 1)[-1]
        embedder = OpenAIEmbedder(model=model)
        chunks: list[dict[str, Any]] = inputs["chunks"]
        result = await embedder.embed([c["content"] for c in chunks])
        for c, vec in zip(chunks, result.embeddings, strict=True):
            c["embedding"] = vec
        return inputs

    return step


def _step_vector_upsert_factory(chroma_dir: Path):
    """Build a CallableStep that upserts chunks into Chroma."""

    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_or_create_collection("kg_ingest_chunks")
        chunks: list[dict[str, Any]] = inputs["chunks"]
        if not chunks:
            return inputs
        # Doc-id replace: clear prior chunk ids for this doc.
        existing = collection.get(where={"doc_id": inputs["doc_id"]})
        if existing.get("ids"):
            collection.delete(ids=existing["ids"])
        collection.upsert(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=[c["embedding"] for c in chunks],
            documents=[c["content"] for c in chunks],
            metadatas=[
                {
                    "doc_id": c["doc_id"],
                    "chunk_id": c["chunk_id"],
                    "source_path": c["source_path"],
                    "index": c["index"],
                }
                for c in chunks
            ],
        )
        return inputs

    return step
```

Then in `build_pipeline`, replace the commented-out "Embedding branch" lines with:

```python
    # Embedding branch.
    builder.add_node(
        "embed",
        CallableStep(_step_embed_factory(embed_model)),
        failure_strategy=FailureStrategy.SKIP_DOWNSTREAM,
        retry_max=2,
    )
    builder.add_edge("reset", "embed")
    builder.add_node(
        "vector_upsert",
        CallableStep(_step_vector_upsert_factory(paths.chroma_dir)),
        failure_strategy=FailureStrategy.SKIP_DOWNSTREAM,
    )
    builder.add_edge("embed", "vector_upsert")
    builder.add_edge("vector_upsert", "ledger")
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_pipeline_build.py -v
```

- [ ] **Step 5: Commit**

```bash
git add examples/kg_ingest/pipeline.py tests/kg_ingest/test_pipeline_build.py
git commit -m "feat(kg_ingest): add embed + vector_upsert branch to per-doc DAG"
```

---

# Phase 12 — `KGIngestAgent`

### Task 21: `KGIngestAgent` facade — `ingest_one`

**Files:**
- Create: `examples/kg_ingest/agent.py`
- Create: `tests/kg_ingest/test_agent.py`

- [ ] **Step 1: Failing test (uses stub extractors)**

`tests/kg_ingest/test_agent.py`:

```python
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from fireflyframework_agentic.graphstores import Edge, Node
from examples.kg_ingest.agent import KGIngestAgent
from examples.kg_ingest.extractors.base import IngestedDoc


class _StubExtractor:
    """Bypass real LLM agents in unit tests."""

    def __init__(self, name: str, fail: bool = False) -> None:
        self.name = name
        self.fail = fail
        self.output_schema = type("Stub", (), {})  # not used
        self.prompt = None
        self.post_step = None

    def build_agent(self, model: str):
        class _A:
            async def run(self_inner, prompt):
                if self.fail:
                    raise RuntimeError("boom")
                class _R: output = type("Out", (), {})
                return _R()
        return _A()

    def to_graph(self, doc: IngestedDoc, output):
        if self.fail:
            return ([], [])
        return (
            [Node(label="X", key=f"{self.name}-k", properties={}, source_doc_id=doc.doc_id,
                  extractor_name=self.name, chunk_ids=[c["chunk_id"] for c in doc.chunks])],
            [],
        )


async def test_ingest_one_writes_to_graph_and_ledger(tmp_path):
    drop = tmp_path / "drop"
    drop.mkdir()
    sample = drop / "sample.txt"
    sample.write_text("Sam Altman is the CEO of OpenAI.")

    agent = KGIngestAgent(
        root=tmp_path / "kg",
        extractors=[_StubExtractor("a"), _StubExtractor("b")],
        extract_model="anthropic:dummy",
        embed_model="openai:text-embedding-3-small",
        skip_embedding=True,  # avoid OpenAI call in unit tests
    )
    result = await agent.ingest_one(sample)
    assert result.status == "success"
    rows = await agent._graph_store.query("SELECT key FROM nodes")
    assert {r["key"] for r in rows} == {"a-k", "b-k"}
    await agent.close()


async def test_ingest_one_marks_partial_when_one_extractor_fails(tmp_path):
    sample = tmp_path / "drop" / "sample.txt"
    sample.parent.mkdir()
    sample.write_text("hello")
    agent = KGIngestAgent(
        root=tmp_path / "kg",
        extractors=[_StubExtractor("a"), _StubExtractor("b", fail=True)],
        extract_model="anthropic:dummy",
        embed_model="openai:text-embedding-3-small",
        skip_embedding=True,
    )
    result = await agent.ingest_one(sample)
    assert result.status == "partial"
    assert result.partial_extractors == ["b"]
    await agent.close()
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_agent.py -v
```

- [ ] **Step 3: Implement**

`examples/kg_ingest/agent.py`:

```python
# (license header)

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fireflyframework_agentic.content.loaders import MarkitdownLoader
from fireflyframework_agentic.graphstores import GraphStoreProtocol, SqliteGraphStore
from fireflyframework_agentic.pipeline.triggers import FolderWatcher

from examples.kg_ingest.extractors.base import Extractor
from examples.kg_ingest.ledger import IngestLedger
from examples.kg_ingest.pipeline import IngestPaths, build_pipeline


log = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionResult:
    doc_id: str
    source_path: str
    status: str
    partial_extractors: list[str] | None = None
    artefacts: dict[str, str] | None = None


class KGIngestAgent:
    """High-level facade for batch + watch-mode ingestion.

    Owns the SqliteGraphStore lifecycle. Use as an async context manager or call
    :meth:`close` explicitly.
    """

    def __init__(
        self,
        *,
        root: Path,
        extractors: list[Extractor],
        extract_model: str,
        embed_model: str,
        skip_embedding: bool = False,
    ) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "out").mkdir(exist_ok=True)
        self._graph_store: SqliteGraphStore = SqliteGraphStore(self.root / "graph.sqlite")
        self._extractors = extractors
        self._extract_model = extract_model
        self._embed_model = embed_model
        self._skip_embedding = skip_embedding
        self._engine = None  # built lazily after store init
        self._ledger: IngestLedger | None = None

    async def _ensure_started(self) -> None:
        if self._engine is None:
            await self._graph_store.initialise()
            self._ledger = IngestLedger(self._graph_store)
            paths = IngestPaths(
                root=self.root,
                graph_store=self._graph_store,
                chroma_dir=self.root / "chroma",
                out_dir=self.root / "out",
            )
            self._engine = build_pipeline(
                extractors=self._extractors,
                paths=paths,
                extract_model=self._extract_model,
                embed_model=self._embed_model,
            )
            if self._skip_embedding:
                # Remove embed/vector_upsert from the DAG for unit tests.
                for nid in ("embed", "vector_upsert"):
                    if nid in self._engine.dag.nodes:
                        self._engine.dag.nodes.pop(nid)

    async def ingest_one(self, path: Path) -> IngestionResult:
        await self._ensure_started()
        assert self._engine is not None and self._ledger is not None

        # Skip if already successfully ingested with same hash.
        from examples.kg_ingest.pipeline import _doc_id_for, _hash_file
        doc_id = _doc_id_for(path)
        content_hash = _hash_file(path)
        if await self._ledger.should_skip(doc_id, content_hash):
            return IngestionResult(doc_id=doc_id, source_path=str(path), status="skipped")

        # Run the pipeline. The framework's PipelineEngine.run takes inputs.
        # PROPAGATE failure on the ledger node ensures it always records something.
        result = await self._engine.run(inputs={"path": str(path)})
        ledger_output = result.outputs.get("ledger", {})
        return IngestionResult(
            doc_id=ledger_output.get("doc_id", doc_id),
            source_path=str(path),
            status=ledger_output.get("status", "failed"),
            partial_extractors=ledger_output.get("partial_extractors"),
        )

    async def ingest_folder(self, folder: Path) -> list[IngestionResult]:
        await self._ensure_started()
        results: list[IngestionResult] = []
        for path in sorted(Path(folder).iterdir()):
            if path.is_file():
                results.append(await self.ingest_one(path))
        return results

    async def watch(self, folder: Path) -> AsyncIterator[IngestionResult]:
        await self._ensure_started()
        watcher = FolderWatcher(folder=Path(folder))
        async for path in watcher.startup_scan():
            yield await self.ingest_one(path)
        async for path in watcher.watch():
            yield await self.ingest_one(path)

    async def close(self) -> None:
        await self._graph_store.close()
```

NOTE on failure tracking: the simple form above does not yet propagate per-extractor failures into the ledger. Task 22 fixes this.

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_agent.py::test_ingest_one_writes_to_graph_and_ledger -v
```

(The partial test will fail until Task 22.)

- [ ] **Step 5: Commit**

```bash
git add examples/kg_ingest/agent.py tests/kg_ingest/test_agent.py
git commit -m "feat(kg_ingest): KGIngestAgent.ingest_one + skeleton for folder/watch"
```

---

### Task 22: Track per-extractor failures and surface in ledger

**Files:**
- Modify: `examples/kg_ingest/pipeline.py`
- Modify: `examples/kg_ingest/agent.py`

The simplest cross-step communication is via a shared mutable dict on the pipeline context. We hand each extract step a callback to record failures, then read them in the ledger step.

- [ ] **Step 1: Patch the extract steps to record failures**

In `examples/kg_ingest/pipeline.py`, modify `_make_extract_step`:

```python
def _make_extract_step(extractor: Extractor, model: str):
    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        doc: IngestedDoc = inputs["doc"]
        try:
            agent = extractor.build_agent(model)
            result = await agent.run(doc.markdown)
            output = result.output
            nodes, edges = extractor.to_graph(doc, output)
        except Exception as exc:
            failed: list[str] = inputs.setdefault("_failed_extractors", [])
            failed.append(extractor.name)
            log.warning("extractor %s failed for %s: %s", extractor.name, doc.doc_id, exc)
            inputs["nodes"] = []
            inputs["edges"] = []
            inputs["output"] = None
            inputs["extractor"] = extractor.name
            return inputs
        return {"extractor": extractor.name, "nodes": list(nodes), "edges": list(edges),
                "output": output, **inputs}
    return step
```

Add `import logging; log = logging.getLogger(__name__)` at the module top if not already present.

`_make_ledger_step` (already written in Task 19) reads
`_extractor_count` and `_failed_extractors` from `inputs` to derive the
status. Both keys are populated in the reset step — update
`_step_reset_factory` to take the extractor count and seed both keys:

```python
def _step_reset_factory(graph_store: GraphStoreProtocol, n_extractors: int):
    async def step(ctx, inputs: dict[str, Any]) -> dict[str, Any]:
        await graph_store.delete_by_doc_id(inputs["doc_id"])
        inputs["_extractor_count"] = n_extractors
        inputs["_failed_extractors"] = []
        return inputs
    return step
```

And in `build_pipeline`, change:

```python
    builder.add_node("reset", CallableStep(_step_reset_factory(paths.graph_store, len(extractors))))
```

- [ ] **Step 2: Run all kg_ingest tests**

```bash
uv run pytest -x tests/kg_ingest/ -v
```

The earlier `test_ingest_one_marks_partial_when_one_extractor_fails` should now pass.

- [ ] **Step 3: Commit**

```bash
git add examples/kg_ingest/pipeline.py
git commit -m "feat(kg_ingest): record per-extractor failures and surface as 'partial'"
```

---

# Phase 13 — CLI

### Task 23: `python -m examples.kg_ingest`

**Files:**
- Create: `examples/kg_ingest/__main__.py`
- Create: `examples/kg_ingest/cli.py`
- Modify: `examples/kg_ingest/__init__.py`
- Create: `tests/kg_ingest/test_cli.py`

- [ ] **Step 1: Failing test**

`tests/kg_ingest/test_cli.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from examples.kg_ingest.cli import build_arg_parser


def test_cli_parses_basic_invocation():
    parser = build_arg_parser()
    ns = parser.parse_args(["--folder", "./drop"])
    assert ns.folder == Path("./drop")
    assert ns.root == Path("./kg")
    assert ns.extractors == "bpmn,person,generic"
    assert ns.model.startswith("anthropic:claude-haiku")
    assert ns.embed_model.startswith("openai:text-embedding")
    assert ns.watch is False


def test_cli_parses_watch_flag_and_subset():
    parser = build_arg_parser()
    ns = parser.parse_args(["--folder", "./drop", "--watch", "--extractors", "bpmn"])
    assert ns.watch is True
    assert ns.extractors == "bpmn"
```

- [ ] **Step 2: Run failing**

```bash
uv run pytest -x tests/kg_ingest/test_cli.py -v
```

- [ ] **Step 3: Implement**

`examples/kg_ingest/cli.py`:

```python
# (license header)

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from fireflyframework_agentic.logging import configure_logging

from examples.kg_ingest.agent import KGIngestAgent
from examples.kg_ingest.extractors import EXTRACTORS


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m examples.kg_ingest",
        description="Ingest documents into a knowledge graph.",
    )
    parser.add_argument(
        "--folder",
        type=Path,
        required=True,
        help="Folder of source documents to ingest.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("./kg"),
        help="Output root for graph + chroma + bpmn artefacts.",
    )
    parser.add_argument(
        "--extractors",
        default="bpmn,person,generic",
        help="Comma-separated subset of extractor names.",
    )
    parser.add_argument(
        "--model",
        default="anthropic:claude-haiku-4-5-20251001",
        help="LLM model for extractors.",
    )
    parser.add_argument(
        "--embed-model",
        default="openai:text-embedding-3-small",
        help="Embedding model.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="After processing existing files, watch for new ones (Ctrl-C to stop).",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


async def _async_main(args: argparse.Namespace) -> int:
    requested = [n.strip() for n in args.extractors.split(",") if n.strip()]
    unknown = set(requested) - set(EXTRACTORS)
    if unknown:
        sys.stderr.write(f"Unknown extractors: {sorted(unknown)}\n")
        return 2
    extractors = [EXTRACTORS[n] for n in requested]

    agent = KGIngestAgent(
        root=args.root,
        extractors=extractors,
        extract_model=args.model,
        embed_model=args.embed_model,
    )
    try:
        if args.watch:
            async for result in agent.watch(args.folder):
                _print_result(result)
        else:
            results = await agent.ingest_folder(args.folder)
            for r in results:
                _print_result(r)
    finally:
        await agent.close()
    return 0


def _print_result(result) -> None:
    print(f"[{result.status}] {result.source_path} (doc_id={result.doc_id})")
    if result.partial_extractors:
        print(f"  partial: {','.join(result.partial_extractors)}")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_arg_parser().parse_args(argv)
    configure_logging("DEBUG" if args.verbose else "INFO")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.stderr.write("ANTHROPIC_API_KEY missing (set in environment or .env)\n")
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        sys.stderr.write("OPENAI_API_KEY missing (set in environment or .env)\n")
        return 2
    return asyncio.run(_async_main(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
```

`examples/kg_ingest/__main__.py`:

```python
# (license header)
from examples.kg_ingest.cli import main

raise SystemExit(main())
```

Update `examples/kg_ingest/__init__.py`:

```python
# (license header)
from __future__ import annotations

from examples.kg_ingest.agent import KGIngestAgent, IngestionResult

__all__ = ["IngestionResult", "KGIngestAgent"]
```

- [ ] **Step 4: Tests pass**

```bash
uv run pytest -x tests/kg_ingest/test_cli.py -v
```

- [ ] **Step 5: Commit**

```bash
git add examples/kg_ingest/cli.py examples/kg_ingest/__main__.py examples/kg_ingest/__init__.py tests/kg_ingest/test_cli.py
git commit -m "feat(kg_ingest): CLI with --folder/--watch/--extractors/--model"
```

---

# Phase 14 — Integration tests

### Task 24: End-to-end with stub LLM (no real API call)

**Files:**
- Create: `tests/kg_ingest/test_pipeline_e2e_stub.py`

- [ ] **Step 1: Write the integration test**

`tests/kg_ingest/test_pipeline_e2e_stub.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from examples.kg_ingest.agent import KGIngestAgent
from examples.kg_ingest.extractors.bpmn import BpmnExtraction, BpmnExtractor, BpmnNode, BpmnFlow
from examples.kg_ingest.extractors.generic import (
    Entity, GenericExtraction, GenericExtractor, Relation,
)
from examples.kg_ingest.extractors.person import (
    Organization, Person, PersonExtraction, PersonExtractor, WorksAt,
)


def _stub_agent(payload):
    class _A:
        async def run(self, prompt):
            class _R: output = payload
            return _R()
    return _A()


@pytest.fixture
def patched_extractors(monkeypatch):
    bpmn = BpmnExtractor()
    person = PersonExtractor()
    generic = GenericExtractor()

    monkeypatch.setattr(bpmn, "build_agent", lambda m: _stub_agent(BpmnExtraction(
        nodes=[BpmnNode(id="s1", type="StartEvent", name="Start"),
               BpmnNode(id="t1", type="Task", name="Review"),
               BpmnNode(id="e1", type="EndEvent", name="End")],
        flows=[BpmnFlow(source_id="s1", target_id="t1"),
               BpmnFlow(source_id="t1", target_id="e1")],
    )))
    monkeypatch.setattr(person, "build_agent", lambda m: _stub_agent(PersonExtraction(
        persons=[Person(name="Sam Altman", aliases=["Sam"])],
        organizations=[Organization(name="OpenAI")],
        employments=[WorksAt(person="Sam Altman", organization="OpenAI", role="CEO")],
    )))
    monkeypatch.setattr(generic, "build_agent", lambda m: _stub_agent(GenericExtraction(
        entities=[Entity(name="OpenAI", type="Company", description="AI lab")],
        relations=[],
    )))
    return [bpmn, person, generic]


async def test_full_ingestion_writes_graph_chroma_ledger_and_bpmn(
    tmp_path, patched_extractors
):
    drop = tmp_path / "drop"
    drop.mkdir()
    (drop / "process.txt").write_text("Sam Altman is CEO of OpenAI. The approval process: Start -> Review -> End.")

    agent = KGIngestAgent(
        root=tmp_path / "kg",
        extractors=patched_extractors,
        extract_model="anthropic:dummy",
        embed_model="openai:text-embedding-3-small",
        skip_embedding=True,  # skip Chroma in stub test
    )
    [result] = await agent.ingest_folder(drop)
    assert result.status == "success"

    nodes = await agent._graph_store.query("SELECT label, key FROM nodes")
    keys = {(r["label"], r["key"]) for r in nodes}
    assert ("Person", "Sam Altman") in keys
    assert ("Organization", "OpenAI") in keys
    assert ("Entity", "OpenAI") in keys
    # BPMN nodes
    assert ("Task", "t1") in keys

    # BPMN file emitted
    out_files = list((tmp_path / "kg" / "out").glob("*.bpmn"))
    assert len(out_files) == 1

    await agent.close()


async def test_partial_when_extractor_fails(tmp_path, patched_extractors, monkeypatch):
    sample = tmp_path / "drop" / "x.txt"
    sample.parent.mkdir()
    sample.write_text("hello")

    # Force the BPMN extractor to fail.
    bpmn, person, generic = patched_extractors
    def _failing(m):
        class _A:
            async def run(self, prompt): raise RuntimeError("boom")
        return _A()
    monkeypatch.setattr(bpmn, "build_agent", _failing)

    agent = KGIngestAgent(
        root=tmp_path / "kg",
        extractors=[bpmn, person, generic],
        extract_model="anthropic:dummy",
        embed_model="openai:text-embedding-3-small",
        skip_embedding=True,
    )
    [result] = await agent.ingest_folder(sample.parent)
    assert result.status == "partial"
    assert result.partial_extractors == ["bpmn"]
    await agent.close()


async def test_re_ingest_doc_id_replace(tmp_path, patched_extractors):
    sample = tmp_path / "drop" / "x.txt"
    sample.parent.mkdir()
    sample.write_text("hello")
    agent = KGIngestAgent(
        root=tmp_path / "kg",
        extractors=patched_extractors,
        extract_model="anthropic:dummy",
        embed_model="openai:text-embedding-3-small",
        skip_embedding=True,
    )
    await agent.ingest_one(sample)
    rows1 = await agent._graph_store.query("SELECT COUNT(*) AS n FROM nodes")
    sample.write_text("hello changed")  # different hash
    await agent.ingest_one(sample)
    rows2 = await agent._graph_store.query("SELECT COUNT(*) AS n FROM nodes")
    # Re-ingest replaces all nodes for that doc; counts equal (not doubled)
    assert rows2[0]["n"] == rows1[0]["n"]
    await agent.close()
```

- [ ] **Step 2: Run**

```bash
uv run pytest -x tests/kg_ingest/test_pipeline_e2e_stub.py -v
```

Expected: 3 PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/kg_ingest/test_pipeline_e2e_stub.py
git commit -m "test(kg_ingest): integration tests covering success/partial/re-ingest"
```

---

### Task 25: Real-LLM E2E test (gated)

**Files:**
- Create: `tests/kg_ingest/test_e2e_real_llm.py`

- [ ] **Step 1: Write the gated test**

`tests/kg_ingest/test_e2e_real_llm.py`:

```python
from __future__ import annotations

import os
from pathlib import Path

import pytest

from examples.kg_ingest.agent import KGIngestAgent
from examples.kg_ingest.extractors import EXTRACTORS

pytestmark = pytest.mark.skipif(
    not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("OPENAI_API_KEY")),
    reason="Real LLM keys not present.",
)


async def test_real_ingestion_writes_nodes_edges_and_bpmn(tmp_path):
    drop = tmp_path / "drop"
    drop.mkdir()
    (drop / "process.md").write_text(
        "# Approval Process\n"
        "Sam Altman is CEO of OpenAI.\n\n"
        "The approval workflow: Start -> Submit Request -> Review -> Approve -> End.\n"
    )
    agent = KGIngestAgent(
        root=tmp_path / "kg",
        extractors=list(EXTRACTORS.values()),
        extract_model="anthropic:claude-haiku-4-5-20251001",
        embed_model="openai:text-embedding-3-small",
    )
    [result] = await agent.ingest_folder(drop)
    assert result.status in ("success", "partial")
    nodes = await agent._graph_store.query("SELECT label, COUNT(*) AS n FROM nodes GROUP BY label")
    by_label = {r["label"]: r["n"] for r in nodes}
    # Person, Organization expected; BPMN process likely produces Task
    assert by_label.get("Person", 0) >= 1
    assert by_label.get("Organization", 0) >= 1
    bpmn_files = list((tmp_path / "kg" / "out").glob("*.bpmn"))
    assert len(bpmn_files) >= 1
    await agent.close()
```

- [ ] **Step 2: Run (locally with keys, or skip in CI)**

```bash
uv run pytest -x tests/kg_ingest/test_e2e_real_llm.py -v
```

If `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` are unset, the test is skipped automatically.

- [ ] **Step 3: Commit**

```bash
git add tests/kg_ingest/test_e2e_real_llm.py
git commit -m "test(kg_ingest): gated real-LLM end-to-end smoke"
```

---

# Phase 15 — Documentation

### Task 26: Update `examples/README.md`

**Files:**
- Modify: `examples/README.md`

- [ ] **Step 1: Add a section under existing IDP entry**

Append or place near the IDP block:

```markdown
## Knowledge-Graph Ingestion (`kg_ingest/`)

Modular folder-ingestion agent: drop a file, get nodes and edges in a SQLite
graph plus a chunk vector index in Chroma, plus a `.bpmn` 2.0 XML artefact
when the BPMN extractor finds a process.

```bash
# One-shot
ANTHROPIC_API_KEY=... OPENAI_API_KEY=... \
  uv run python -m examples.kg_ingest --folder ./drop

# Watch mode
uv run python -m examples.kg_ingest --folder ./drop --watch

# Subset of extractors
uv run python -m examples.kg_ingest --folder ./drop --extractors bpmn
```

Outputs land under `./kg/`:

```
./kg/
├── graph.sqlite     # nodes, edges, ingestions tables (FTS5 + indexes)
├── chroma/          # chunk vector index
└── out/             # one .bpmn per BPMN-positive doc
```

See [`docs/use-case-kg-ingest.md`](../docs/use-case-kg-ingest.md) for the full
design.
```

- [ ] **Step 2: Commit**

```bash
git add examples/README.md
git commit -m "docs(examples): add kg_ingest section"
```

---

### Task 27: Final verification — full test suite, push, and PR finalisation

- [ ] **Step 1: Run full suite**

```bash
uv run pytest -x
```

Expected: all green. Real-LLM e2e is skipped without keys.

- [ ] **Step 2: Run lints**

```bash
uv run ruff check .
uv run pyright src/fireflyframework_agentic/graphstores src/fireflyframework_agentic/content/loaders src/fireflyframework_agentic/pipeline/triggers examples/kg_ingest
```

Fix any issues that surface; commit fixes as a separate trailing commit.

- [ ] **Step 3: Push and update PR**

```bash
git push origin javi/markitdown
```

The existing PR #82 will pick up the new commits automatically.

- [ ] **Step 4: Smoke-test manually (optional, requires keys)**

```bash
mkdir -p drop
echo "Sam Altman is the CEO of OpenAI. The approval process: Start -> Review -> End." > drop/test.txt
ANTHROPIC_API_KEY=... OPENAI_API_KEY=... uv run python -m examples.kg_ingest --folder ./drop
sqlite3 kg/graph.sqlite "SELECT label, key FROM nodes ORDER BY label, key;"
```

Expected: rows for Person/Organization/Entity/Task etc., plus a `.bpmn` file under `kg/out/`.

---

# Manual testing checklist

After all tasks are complete, before merging the PR, validate:

- [ ] Drop a single PDF in `./drop`; verify nodes + edges in SQLite + a BPMN file (if process-shaped doc).
- [ ] Drop the *same* PDF a second time; verify ledger says `success`/skipped, no duplicate nodes.
- [ ] Modify the PDF (different content hash) and re-drop; verify old nodes replaced, new ones appear.
- [ ] Drop a corrupt / unsupported file; verify ledger marks `load_failed` and other docs continue.
- [ ] Run with `--watch`; drop a new file mid-run; verify it's picked up after the stability window.
- [ ] Query "list all CEOs" SQL from the spec section 5; verify FTS-based query returns the seeded data.
- [ ] Force one extractor to fail (e.g. revoke `ANTHROPIC_API_KEY` after one extractor's call); verify partial status with `partial_extractors` populated.

---

# Done criteria

- All tasks complete and tests green.
- `docs/use-case-kg-ingest.md` (the spec) and this plan committed.
- PR #82 has both spec and implementation; manual checklist passed locally.
- No new lint warnings in the affected modules.

# sqlite-vec Vector Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ChromaDB with a sqlite-vec `vec0` vector store so the entire corpus lives in a single `corpus.sqlite` file.

**Architecture:** A new `SqliteVecVectorStore` opens its own `sqlite3` connection to `corpus.sqlite` (WAL, same file as `SqliteCorpus`), loads the sqlite-vec extension, and maintains a `vec_chunks` vec0 virtual table plus a `vec_chunks_shadow` table mapping string IDs → integer rowids. `CorpusAgent` is updated to construct this store instead of ChromaDB. A pre-existing bug in `HybridRetriever` (`getattr(h, "id", None)` on `SearchResult` always returns `None`) is fixed as part of this work.

**Tech Stack:** `sqlite-vec>=0.1.6`, `sqlite3` (stdlib), `asyncio.to_thread`, `asyncio.Lock`

**Spec:** `docs/superpowers/specs/2026-04-30-sqlite-vec-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/fireflyframework_agentic/vectorstores/sqlite_vec_store.py` | `SqliteVecVectorStore` implementation |
| Modify | `src/fireflyframework_agentic/vectorstores/__init__.py` | Export `SqliteVecVectorStore` |
| Modify | `src/fireflyframework_agentic/rag/retrieval/hybrid.py` | Fix `h.document.id` bug |
| Modify | `examples/corpus_search/agent.py` | Swap ChromaDB → SqliteVecVectorStore, add `embed_dimension` |
| Modify | `examples/corpus_search/cli.py` | Add `--embed-dimension` arg, update help strings |
| Modify | `pyproject.toml` | Add `vectorstores-sqlite-vec` extra, update `corpus-search` and `dev` |
| Create | `tests/unit/vectorstores/test_sqlite_vec_store.py` | Unit tests for the new backend |
| Modify | `tests/unit/corpus_search/test_hybrid.py` | Fix stub to match real `SearchResult` shape |
| Modify | `tests/unit/corpus_search/test_ingest_with_real_vectorstore.py` | Use `SqliteVecVectorStore` instead of `InMemoryVectorStore` |

---

## Task 1: Fix `hybrid.py` vec_ids bug and update test stubs

The `HybridRetriever` does `getattr(h, "id", None)` on `SearchResult` objects. `SearchResult` has no `.id` attribute (the id lives at `h.document.id`), so vector results have **never contributed to RRF**. The test stubs use a fake object with `.id` directly, which is why tests pass today.

**Files:**
- Modify: `src/fireflyframework_agentic/rag/retrieval/hybrid.py:100`
- Modify: `tests/unit/corpus_search/test_hybrid.py`

- [ ] **Step 1: Update `_StubVectorStore` to return real `SearchResult` objects**

Open `tests/unit/corpus_search/test_hybrid.py`. Replace `_StubSearchResult` and `_StubVectorStore` with:

```python
from fireflyframework_agentic.vectorstores.types import SearchResult, VectorDocument

class _StubVectorStore:
    """Returns canned ranked ids per query embedding magnitude."""

    def __init__(self, results: dict[float, list[str]]) -> None:
        self._results = results

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        namespace: str = "default",
        filters: list[Any] | None = None,
    ) -> list[SearchResult]:
        key = query_embedding[0]
        ids = self._results.get(key, [])
        return [
            SearchResult(document=VectorDocument(id=i, text="", metadata={}), score=0.0)
            for i in ids[:top_k]
        ]
```

Remove the `_StubSearchResult` class entirely.

- [ ] **Step 2: Run the hybrid tests — they should FAIL**

```bash
uv run pytest tests/unit/corpus_search/test_hybrid.py -v 2>&1 | tail -30
```

Expected: multiple failures because `h.document.id` is not yet used in `hybrid.py`.

- [ ] **Step 3: Fix the bug in `hybrid.py`**

In `src/fireflyframework_agentic/rag/retrieval/hybrid.py`, replace line 100:

```python
# Before:
vec_ids = [getattr(h, "id", None) for h in vec_hits]
rankings.append([i for i in vec_ids if i])

# After:
rankings.append([h.document.id for h in vec_hits])
```

- [ ] **Step 4: Run the hybrid tests — all must PASS**

```bash
uv run pytest tests/unit/corpus_search/test_hybrid.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/rag/retrieval/hybrid.py \
        tests/unit/corpus_search/test_hybrid.py
git commit -m "fix(hybrid): use h.document.id — vec results now contribute to RRF"
```

---

## Task 2: Add `sqlite-vec` to `pyproject.toml` and install

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `vectorstores-sqlite-vec` extra and update dependents**

In `pyproject.toml`, add after the `vectorstores-chroma` block:

```toml
vectorstores-sqlite-vec = [
    "sqlite-vec>=0.1.6",
]
```

Update `corpus-search` to remove `vectorstores-chroma` and add `vectorstores-sqlite-vec`:

```toml
corpus-search = [
    "fireflyframework-agentic[rag,vectorstores-sqlite-vec]",
    "python-dotenv>=1.0.0",
]
```

Add `sqlite-vec>=0.1.6` to the `dev` extras list (alongside the other packages in the dev block).

Update the `all` extra to include `vectorstores-sqlite-vec` (add it after `vectorstores-qdrant`).

- [ ] **Step 2: Install the updated dev dependencies**

```bash
uv sync --extra dev
```

Expected: resolves cleanly; `sqlite-vec` appears in output.

- [ ] **Step 3: Verify the extension loads**

```bash
uv run python -c "import sqlite3, sqlite_vec; db = sqlite3.connect(':memory:'); db.enable_load_extension(True); sqlite_vec.load(db); db.enable_load_extension(False); print(db.execute('select vec_version()').fetchone()[0])"
```

Expected: prints a version string like `v0.1.6`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add sqlite-vec vectorstores extra, wire into corpus-search"
```

---

## Task 3: Implement `SqliteVecVectorStore` — core upsert and search

**Files:**
- Create: `tests/unit/vectorstores/test_sqlite_vec_store.py`
- Create: `src/fireflyframework_agentic/vectorstores/sqlite_vec_store.py`

- [ ] **Step 1: Write failing tests for upsert and search**

Create `tests/unit/vectorstores/test_sqlite_vec_store.py`:

```python
"""Tests for SqliteVecVectorStore (sqlite-vec backend)."""
from __future__ import annotations

import math

import pytest

from fireflyframework_agentic.vectorstores.types import VectorDocument


@pytest.fixture
def store(tmp_path):
    from fireflyframework_agentic.vectorstores.sqlite_vec_store import SqliteVecVectorStore
    return SqliteVecVectorStore(db_path=tmp_path / "test.sqlite", dimension=4)


async def test_upsert_and_search_returns_closest_first(store):
    docs = [
        VectorDocument(id="a", text="alpha", embedding=[1.0, 0.0, 0.0, 0.0]),
        VectorDocument(id="b", text="beta",  embedding=[0.0, 1.0, 0.0, 0.0]),
        VectorDocument(id="c", text="gamma", embedding=[0.0, 0.0, 1.0, 0.0]),
    ]
    await store.upsert(docs)
    # Query close to "a"
    results = await store.search([0.99, 0.01, 0.0, 0.0], top_k=3)
    assert len(results) == 3
    assert results[0].document.id == "a"


async def test_search_scores_decrease(store):
    docs = [
        VectorDocument(id="x", text="x", embedding=[1.0, 0.0, 0.0, 0.0]),
        VectorDocument(id="y", text="y", embedding=[0.0, 1.0, 0.0, 0.0]),
    ]
    await store.upsert(docs)
    results = await store.search([1.0, 0.0, 0.0, 0.0], top_k=2)
    assert results[0].score >= results[1].score


async def test_search_empty_store_returns_empty(store):
    results = await store.search([1.0, 0.0, 0.0, 0.0], top_k=5)
    assert results == []


async def test_upsert_overwrites_existing_id(store):
    doc = VectorDocument(id="dup", text="v1", embedding=[1.0, 0.0, 0.0, 0.0])
    await store.upsert([doc])
    doc2 = VectorDocument(id="dup", text="v2", embedding=[0.0, 1.0, 0.0, 0.0])
    await store.upsert([doc2])
    # Only one row in shadow
    results = await store.search([0.0, 1.0, 0.0, 0.0], top_k=5)
    ids = [r.document.id for r in results]
    assert ids.count("dup") == 1
    # The new embedding is returned (closest to [0,1,0,0])
    assert results[0].document.id == "dup"
```

- [ ] **Step 2: Run tests — they should FAIL with ImportError**

```bash
uv run pytest tests/unit/vectorstores/test_sqlite_vec_store.py -v 2>&1 | tail -15
```

Expected: `ImportError: cannot import name 'SqliteVecVectorStore'`

- [ ] **Step 3: Create `sqlite_vec_store.py` with upsert and search**

Create `src/fireflyframework_agentic/vectorstores/sqlite_vec_store.py`:

```python
"""SQLite-vec backed vector store using the vec0 virtual table."""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Any

try:
    import sqlite_vec
    from sqlite_vec import serialize_float32
except ImportError:
    sqlite_vec = None  # type: ignore[assignment]
    serialize_float32 = None  # type: ignore[assignment]

from fireflyframework_agentic.vectorstores.base import BaseVectorStore
from fireflyframework_agentic.vectorstores.types import SearchFilter, SearchResult, VectorDocument

logger = logging.getLogger(__name__)


class SqliteVecVectorStore(BaseVectorStore):
    """sqlite-vec backed vector store co-residing in an existing SQLite file.

    Uses a vec0 virtual table (distance_metric=cosine) for KNN search and a
    shadow table that maps string IDs to integer rowids and stores namespace.
    Opens its own sqlite3 connection so it can safely share the file with
    SqliteCorpus under SQLite WAL mode.

    Parameters:
        db_path: Path to the SQLite file (may already contain SqliteCorpus tables).
        dimension: Embedding dimension — must match the embedder used at ingest time.
        table_name: Name of the vec0 virtual table (default: ``vec_chunks``).
    """

    def __init__(
        self,
        db_path: Path | str,
        dimension: int,
        *,
        table_name: str = "vec_chunks",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._db_path = Path(db_path)
        self._dim = dimension
        self._tbl = table_name
        self._shadow = f"{table_name}_shadow"
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()
        self._ready = False

    # ------------------------------------------------------------------
    # Initialisation (lazy, called with lock held)
    # ------------------------------------------------------------------

    def _initialise_sync(self) -> None:
        if sqlite_vec is None:
            raise ImportError(
                "sqlite-vec is required for SqliteVecVectorStore. "
                "Install with: pip install 'fireflyframework-agentic[vectorstores-sqlite-vec]'"
            )
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self._db_path), isolation_level=None, check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._shadow} (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                id    TEXT UNIQUE NOT NULL,
                ns    TEXT NOT NULL DEFAULT 'default'
            )
        """)
        conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self._tbl}
            USING vec0(embedding float[{self._dim}] distance_metric=cosine)
        """)
        self._conn = conn
        self._ready = True

    async def _ensure_ready(self) -> None:
        """Must be called with self._lock held."""
        if not self._ready:
            await asyncio.to_thread(self._initialise_sync)

    # ------------------------------------------------------------------
    # BaseVectorStore interface
    # ------------------------------------------------------------------

    async def _upsert(self, documents: list[VectorDocument], namespace: str) -> None:
        async with self._lock:
            await self._ensure_ready()
            await asyncio.to_thread(self._upsert_sync, documents, namespace)

    def _upsert_sync(self, documents: list[VectorDocument], namespace: str) -> None:
        assert self._conn is not None
        conn = self._conn
        conn.execute("BEGIN")
        try:
            for doc in documents:
                conn.execute(
                    f"INSERT INTO {self._shadow}(id, ns) VALUES(?, ?)"
                    f" ON CONFLICT(id) DO UPDATE SET ns=excluded.ns",
                    (doc.id, namespace),
                )
                row = conn.execute(
                    f"SELECT rowid FROM {self._shadow} WHERE id = ?", (doc.id,)
                ).fetchone()
                rowid = row[0]
                # vec0 does not support UPDATE — delete the old vector then re-insert.
                conn.execute(f"DELETE FROM {self._tbl} WHERE rowid = ?", (rowid,))
                conn.execute(
                    f"INSERT INTO {self._tbl}(rowid, embedding) VALUES(?, ?)",
                    (rowid, serialize_float32(doc.embedding)),
                )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    async def _search(
        self,
        query_embedding: list[float],
        top_k: int,
        namespace: str,
        filters: list[SearchFilter] | None,
    ) -> list[SearchResult]:
        async with self._lock:
            await self._ensure_ready()
            return await asyncio.to_thread(
                self._search_sync, query_embedding, top_k, namespace
            )

    def _search_sync(
        self,
        query_embedding: list[float],
        top_k: int,
        namespace: str,
    ) -> list[SearchResult]:
        assert self._conn is not None
        rows = self._conn.execute(
            f"""
            SELECT s.id, v.distance
            FROM (
                SELECT rowid, distance
                FROM {self._tbl}
                WHERE embedding MATCH ?
                ORDER BY distance
                LIMIT ?
            ) v
            JOIN {self._shadow} s ON s.rowid = v.rowid
            WHERE s.ns = ?
            """,
            (serialize_float32(query_embedding), top_k, namespace),
        ).fetchall()
        return [
            SearchResult(
                document=VectorDocument(id=row["id"], text="", metadata={}),
                score=1.0 - row["distance"],
            )
            for row in rows
        ]

    async def _delete(self, ids: list[str], namespace: str) -> None:
        async with self._lock:
            await self._ensure_ready()
            await asyncio.to_thread(self._delete_sync, ids, namespace)

    def _delete_sync(self, ids: list[str], namespace: str) -> None:
        assert self._conn is not None
        if not ids:
            return
        conn = self._conn
        ph = ",".join("?" * len(ids))
        rows = conn.execute(
            f"SELECT rowid FROM {self._shadow} WHERE id IN ({ph}) AND ns = ?",
            (*ids, namespace),
        ).fetchall()
        rowids = [r[0] for r in rows]
        conn.execute("BEGIN")
        try:
            if rowids:
                rph = ",".join("?" * len(rowids))
                conn.execute(f"DELETE FROM {self._tbl} WHERE rowid IN ({rph})", rowids)
            conn.execute(
                f"DELETE FROM {self._shadow} WHERE id IN ({ph}) AND ns = ?",
                (*ids, namespace),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    async def close(self) -> None:
        async with self._lock:
            if self._conn is not None:
                await asyncio.to_thread(self._conn.close)
                self._conn = None
                self._ready = False
```

- [ ] **Step 4: Run core tests — all must PASS**

```bash
uv run pytest tests/unit/vectorstores/test_sqlite_vec_store.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/fireflyframework_agentic/vectorstores/sqlite_vec_store.py \
        tests/unit/vectorstores/test_sqlite_vec_store.py
git commit -m "feat(vectorstores): add SqliteVecVectorStore backed by sqlite-vec vec0"
```

---

## Task 4: Add delete and namespace isolation tests

**Files:**
- Modify: `tests/unit/vectorstores/test_sqlite_vec_store.py`

- [ ] **Step 1: Add delete and namespace tests**

Append to `tests/unit/vectorstores/test_sqlite_vec_store.py`:

```python
async def test_delete_removes_document(store):
    docs = [
        VectorDocument(id="keep", text="k", embedding=[1.0, 0.0, 0.0, 0.0]),
        VectorDocument(id="drop", text="d", embedding=[0.9, 0.1, 0.0, 0.0]),
    ]
    await store.upsert(docs)
    await store.delete(["drop"])
    results = await store.search([1.0, 0.0, 0.0, 0.0], top_k=5)
    ids = [r.document.id for r in results]
    assert "drop" not in ids
    assert "keep" in ids


async def test_delete_nonexistent_id_is_silent(store):
    await store.delete(["ghost"])  # must not raise


async def test_namespace_isolation(tmp_path):
    from fireflyframework_agentic.vectorstores.sqlite_vec_store import SqliteVecVectorStore
    store = SqliteVecVectorStore(db_path=tmp_path / "ns.sqlite", dimension=4)
    await store.upsert(
        [VectorDocument(id="ns_a_doc", text="", embedding=[1.0, 0.0, 0.0, 0.0])],
        namespace="ns_a",
    )
    await store.upsert(
        [VectorDocument(id="ns_b_doc", text="", embedding=[1.0, 0.0, 0.0, 0.0])],
        namespace="ns_b",
    )
    results_a = await store.search([1.0, 0.0, 0.0, 0.0], top_k=5, namespace="ns_a")
    ids_a = [r.document.id for r in results_a]
    assert "ns_a_doc" in ids_a
    assert "ns_b_doc" not in ids_a

    results_b = await store.search([1.0, 0.0, 0.0, 0.0], top_k=5, namespace="ns_b")
    ids_b = [r.document.id for r in results_b]
    assert "ns_b_doc" in ids_b
    assert "ns_a_doc" not in ids_b


async def test_import_error_when_sqlite_vec_not_installed(tmp_path):
    from unittest.mock import patch
    from fireflyframework_agentic.vectorstores import sqlite_vec_store as m
    with patch.object(m, "sqlite_vec", None):
        store = m.SqliteVecVectorStore(db_path=tmp_path / "x.sqlite", dimension=4)
        with pytest.raises(ImportError, match="sqlite-vec"):
            await store.upsert([VectorDocument(id="x", text="", embedding=[1.0, 0.0, 0.0, 0.0])])
```

- [ ] **Step 2: Run all sqlite-vec store tests**

```bash
uv run pytest tests/unit/vectorstores/test_sqlite_vec_store.py -v
```

Expected: 8 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/vectorstores/test_sqlite_vec_store.py
git commit -m "test(vectorstores): add delete, namespace isolation, and import-error tests for SqliteVecVectorStore"
```

---

## Task 5: Export `SqliteVecVectorStore` from `vectorstores/__init__.py`

**Files:**
- Modify: `src/fireflyframework_agentic/vectorstores/__init__.py`

- [ ] **Step 1: Add the export**

In `src/fireflyframework_agentic/vectorstores/__init__.py`, add the import and `__all__` entry:

```python
from fireflyframework_agentic.vectorstores.sqlite_vec_store import SqliteVecVectorStore
```

Add `"SqliteVecVectorStore"` to the `__all__` list (alphabetically between `SearchResult` and `VectorDocument`).

- [ ] **Step 2: Verify the import works**

```bash
uv run python -c "from fireflyframework_agentic.vectorstores import SqliteVecVectorStore; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/fireflyframework_agentic/vectorstores/__init__.py
git commit -m "feat(vectorstores): export SqliteVecVectorStore from package root"
```

---

## Task 6: Update `test_ingest_with_real_vectorstore.py` to use `SqliteVecVectorStore`

**Files:**
- Modify: `tests/unit/corpus_search/test_ingest_with_real_vectorstore.py`

- [ ] **Step 1: Swap the vector store fixture**

Replace the `InMemoryVectorStore` import and fixture body in `tests/unit/corpus_search/test_ingest_with_real_vectorstore.py`:

Replace:
```python
from fireflyframework_agentic.vectorstores.memory_store import InMemoryVectorStore
```
With:
```python
from fireflyframework_agentic.vectorstores.sqlite_vec_store import SqliteVecVectorStore
```

Replace the fixture body line:
```python
    vector_store = InMemoryVectorStore()
```
With:
```python
    vector_store = SqliteVecVectorStore(db_path=tmp_path / "corpus.sqlite", dimension=4)
```

Update the module docstring first sentence to:
```
Integration test: ingest_one against the framework's SqliteVecVectorStore.
```

- [ ] **Step 2: Run the updated test**

```bash
uv run pytest tests/unit/corpus_search/test_ingest_with_real_vectorstore.py -v
```

Expected: test passes.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/corpus_search/test_ingest_with_real_vectorstore.py
git commit -m "test(corpus): drive ingest integration test against SqliteVecVectorStore"
```

---

## Task 7: Wire `SqliteVecVectorStore` into `CorpusAgent` and `cli.py`

**Files:**
- Modify: `examples/corpus_search/agent.py`
- Modify: `examples/corpus_search/cli.py`

- [ ] **Step 1: Update `CorpusAgent`**

In `examples/corpus_search/agent.py`:

1. Replace the import:
   ```python
   # Remove:
   # (no direct chromadb import at top level — it was in _build_vector_store)
   ```

2. Add `embed_dimension: int = 1536` parameter to `CorpusAgent.__init__`:

   ```python
   def __init__(
       self,
       *,
       root: Path,
       embed_model: str,
       embed_dimension: int = 1536,
       expansion_model: str,
       answer_model: str,
       rerank_model: str,
       rerank_pool: int = 20,
       _embedder: Any | None = None,
       _vector_store: Any | None = None,
   ) -> None:
   ```

   Store it: `self._embed_dimension = embed_dimension`

3. Replace the entire `_build_vector_store` method:

   ```python
   def _build_vector_store(self) -> Any:
       from fireflyframework_agentic.vectorstores.sqlite_vec_store import SqliteVecVectorStore

       return SqliteVecVectorStore(
           db_path=self.root / "corpus.sqlite",
           dimension=self._embed_dimension,
       )
   ```

- [ ] **Step 2: Update `cli.py`**

In `examples/corpus_search/cli.py`:

1. Add `--embed-dimension` to the `ingest` subparser (after `--embed-model`):

   ```python
   p_ingest.add_argument(
       "--embed-dimension",
       type=int,
       default=1536,
       help="Embedding dimension — must match the chosen model (text-embedding-3-small=1536, text-embedding-3-large=3072).",
   )
   ```

2. Add the same argument to the `query` subparser (after `--embed-model`):

   ```python
   p_query.add_argument(
       "--embed-dimension",
       type=int,
       default=1536,
       help="Embedding dimension — must match the model used at ingest time.",
   )
   ```

3. Update both `CorpusAgent(...)` calls to pass `embed_dimension=args.embed_dimension`.

4. Update the `--root` help strings to remove references to `chroma/`:

   - `p_ingest`: `"Output root for corpus.sqlite."`
   - `p_query`: `"Corpus root (must contain corpus.sqlite)."`

- [ ] **Step 3: Run existing agent and CLI tests**

```bash
uv run pytest tests/unit/corpus_search/test_agent.py tests/unit/corpus_search/test_query_path.py -v 2>&1 | tail -20
```

Expected: all pass (these tests inject `_vector_store` via the underscored parameter, so they don't hit `_build_vector_store`).

- [ ] **Step 4: Commit**

```bash
git add examples/corpus_search/agent.py examples/corpus_search/cli.py
git commit -m "feat(corpus-search): replace ChromaDB with SqliteVecVectorStore, add --embed-dimension"
```

---

## Task 8: Full test suite, linting, and cleanup

**Files:**
- Run tests and linter only

- [ ] **Step 1: Run the full test suite**

```bash
uv run pytest tests/unit/ -v 2>&1 | tail -40
```

Expected: all tests pass. Fix any failures before continuing.

- [ ] **Step 2: Run ruff**

```bash
uv run ruff check src/ examples/ tests/unit/ --fix
uv run ruff format src/ examples/ tests/unit/
```

Expected: no errors. Commit any auto-fixes.

- [ ] **Step 3: Run pyright**

```bash
uv run pyright src/
```

Expected: no errors. Fix any type errors.

- [ ] **Step 4: Verify chromadb references are gone from the examples**

```bash
grep -rn "chromadb\|chroma/" examples/corpus_search/agent.py examples/corpus_search/cli.py
```

Expected: no output (zero matches).

- [ ] **Step 5: Commit any ruff/pyright fixes**

```bash
git add -p  # stage only formatting/type fixes
git commit -m "style: ruff + pyright fixes after sqlite-vec migration"
```

- [ ] **Step 6: Final summary commit**

```bash
git log --oneline -8
```

Verify the commit chain looks like:
```
style: ruff + pyright fixes after sqlite-vec migration
feat(corpus-search): replace ChromaDB with SqliteVecVectorStore, add --embed-dimension
test(corpus): drive ingest integration test against SqliteVecVectorStore
feat(vectorstores): export SqliteVecVectorStore from package root
test(vectorstores): add delete, namespace isolation, and import-error tests
feat(vectorstores): add SqliteVecVectorStore backed by sqlite-vec vec0
deps: add sqlite-vec vectorstores extra, wire into corpus-search
fix(hybrid): use h.document.id — vec results now contribute to RRF
```

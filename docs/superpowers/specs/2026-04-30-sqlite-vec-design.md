# Design: Replace ChromaDB with sqlite-vec

**Date:** 2026-04-30  
**Branch:** javi/markitdown  
**Status:** Approved

## Goal

Consolidate the corpus-search persistence layout from two paths (`corpus.sqlite` + `chroma/`) into a single `corpus.sqlite` file by replacing `ChromaVectorStore` with a new `SqliteVecVectorStore` backed by the sqlite-vec `vec0` virtual table.

Benefits:
- Single-file backup and restore
- Eliminates two-phase cleanup on re-ingest (Chroma dir + SQLite rows)
- Removes `chromadb` from the `corpus-search` optional dependency
- `vec0` with `distance_metric=cosine` stays in SQLite's page cache; no Python-side matrix load per query

Re-ingestion is required after this change. No migration of existing data.

---

## Architecture

Two `aiosqlite` connections open `corpus.sqlite` simultaneously:

```
corpus.sqlite
├── chunks          (FTS5 + BM25, owned by SqliteCorpus)
├── chunks_fts      (FTS5 shadow)
├── ingestions      (ledger, owned by SqliteCorpus)
├── vec_chunks      (vec0 virtual table, owned by SqliteVecVectorStore)
└── vec_shadow      (string-id ↔ rowid map + namespace, owned by SqliteVecVectorStore)
```

SQLite WAL mode (already set by `SqliteCorpus`) allows concurrent reads and serialises writes. Since ingest is serial there is no write contention in practice.

`ChromaVectorStore` is **kept** in the framework as an optional backend for users who need it. Only the `corpus-search` extra changes.

---

## Bug Fix: hybrid.py vector ID extraction

`HybridRetriever.retrieve()` currently does:

```python
vec_ids = [getattr(h, "id", None) for h in vec_hits]
```

`vec_hits` is `list[SearchResult]`; `SearchResult` has no `.id` attribute (the id is at `h.document.id`). This means `getattr` always returns `None` and **vector results have never contributed to RRF**. Fix:

```python
vec_ids = [h.document.id for h in vec_hits]
```

---

## New Component: `SqliteVecVectorStore`

**File:** `src/fireflyframework_agentic/vectorstores/sqlite_vec_store.py`

### Schema

```sql
-- Maps string chunk_id → integer rowid for vec0
CREATE TABLE IF NOT EXISTS vec_shadow (
    rowid  INTEGER PRIMARY KEY AUTOINCREMENT,
    id     TEXT    UNIQUE NOT NULL,
    ns     TEXT    NOT NULL DEFAULT 'default'
);

-- vec0 virtual table: stores embeddings only (rowid = FK to vec_shadow)
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks
    USING vec0(embedding float[{dim}] distance_metric=cosine);
```

The table name is configurable (`table_name` parameter) so multiple stores can coexist in one file if needed.

### Constructor

```python
SqliteVecVectorStore(
    db_path: Path,
    dimension: int,
    table_name: str = "vec_chunks",     # vec0 table; shadow is table_name + "_shadow"
    **kwargs,                            # passed to BaseVectorStore (embedder=)
)
```

`dimension` must match the embedder used at ingest time. The vec0 schema encodes the dimension in the DDL; changing it requires dropping and recreating the table (i.e., re-ingestion).

### Lazy initialisation

Tables are created on first use via an `asyncio.Lock`-guarded `_ensure_ready()` coroutine — no `initialise()` method needed, no protocol change.

### `_upsert(documents, namespace)`

For each `VectorDocument`:
1. `INSERT INTO vec_shadow(id, ns) VALUES(?, ?) ON CONFLICT(id) DO UPDATE SET ns=excluded.ns` → get `rowid` via `lastrowid` or `SELECT rowid FROM vec_shadow WHERE id=?`
2. `DELETE FROM {table_name} WHERE rowid = ?` (vec0 does not support UPDATE)
3. `INSERT INTO {table_name}(rowid, embedding) VALUES(?, ?)` with `serialize_float32(doc.embedding)`

All three steps run inside a single `BEGIN`/`COMMIT`.

### `_search(query_embedding, top_k, namespace, filters)`

vec0 KNN is queried in a subquery; namespace filtering and any `SearchFilter` conditions are applied in Python on the result set (post-filter). For the RAG path there is always exactly one namespace (`"default"`) so this is equivalent to filtering in SQL.

```sql
-- Step 1: KNN — fetch top_k candidates from vec0
SELECT rowid, distance
FROM {table_name}
WHERE embedding MATCH ?
ORDER BY distance
LIMIT ?

-- Step 2: resolve rowids → string ids + namespace via vec_shadow
SELECT id, ns FROM vec_shadow WHERE rowid IN (?, ?, ...)
```

Both steps run in the same connection. Results are filtered by `namespace` and any `SearchFilter` items in Python before returning.

Returns `list[SearchResult]` with `VectorDocument(id=chunk_id, text="", metadata={})` and `score = 1.0 - distance`. With `distance_metric=cosine`, sqlite-vec returns cosine *distance* ∈ [0, 2] (0 = identical, 2 = opposite), so `1.0 - distance` maps to cosine *similarity* ∈ [-1, 1], matching the convention used by `InMemoryVectorStore`.

### `_delete(ids, namespace)`

```sql
DELETE FROM {table_name} WHERE rowid IN (
    SELECT rowid FROM vec_shadow WHERE id IN (?, ...) AND ns = ?
);
DELETE FROM vec_shadow WHERE id IN (?, ...) AND ns = ?;
```

---

## Changes to `CorpusAgent`

**File:** `examples/corpus_search/agent.py`

- Add `embed_dimension: int = 1536` to `__init__` (default matches `text-embedding-3-small`)
- `_build_vector_store()` returns:
  ```python
  SqliteVecVectorStore(
      db_path=self.root / "corpus.sqlite",
      dimension=self._embed_dimension,
  )
  ```
- Remove `chromadb` import and `chroma/` path references

---

## Changes to `cli.py`

**File:** `examples/corpus_search/cli.py`

- Add `--embed-dimension INT` argument to both `ingest` and `query` subcommands (default `1536`)
- Update `--root` help strings: remove references to `chroma/`
- Pass `embed_dimension=args.embed_dimension` to `CorpusAgent`

---

## `pyproject.toml`

```toml
vectorstores-sqlite-vec = ["sqlite-vec>=0.1.6"]

# corpus-search: swap chroma for sqlite-vec
corpus-search = [
    "fireflyframework-agentic[rag,vectorstores-sqlite-vec]",
    "python-dotenv>=1.0.0",
]

# vectorstores-chroma stays for other users
vectorstores-chroma = ["chromadb>=0.5.0"]

# dev: add sqlite-vec
dev = [
    ...,
    "sqlite-vec>=0.1.6",
]
```

---

## Tests

### New: `tests/unit/vectorstores/test_sqlite_vec_store.py`

Uses a real in-process sqlite-vec extension (no mocking — it's a shared library with no I/O side-effects).

| Test | Asserts |
|------|---------|
| `test_upsert_and_search` | Insert 3 vectors, query → closest ID returned first |
| `test_search_returns_correct_order` | Cosine order matches manual expectation |
| `test_upsert_overwrites` | Re-upsert same ID → only one row in shadow |
| `test_delete` | Delete by ID → no longer returned in search |
| `test_namespace_isolation` | Docs in `ns_a` not returned when searching `ns_b` |
| `test_empty_search` | Returns `[]` when table is empty |

### Update: `tests/unit/corpus_search/test_ingest_with_real_vectorstore.py`

Replace `InMemoryVectorStore` fixture with `SqliteVecVectorStore` pointed at a `tmp_path` file.

### Update: `tests/unit/corpus_search/test_hybrid.py`

After the bug fix, strengthen the `retrieve` tests to assert that vector-sourced IDs appear in the RRF output.

---

## Rollout / Re-ingestion Note

Any existing `kg/corpus.sqlite` + `kg/chroma/` corpus must be deleted and re-ingested. The `corpus-search` README and CLI help strings should reflect this.

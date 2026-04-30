# Design: Structure-Aware Markdown Chunker

**Date:** 2026-04-30
**Branch:** new PR → target `javi/markitdown`
**Status:** Approved

## Goal

Replace the fixed-size `TextChunker` in the corpus-search ingest path with a
structure-aware `MarkdownChunker` that splits at markdown heading boundaries,
prepends a breadcrumb path to each chunk, and falls back to `TextChunker` for
sections that exceed the token budget. The new class lives in the framework
(`src/fireflyframework_agentic/content/`) so any RAG application can use it.

## Why

Fixed-size chunking splits across sentence, paragraph, table-row, and code-block
boundaries. This degrades both BM25 (broken keyword context) and vector search
(embedding a fragment of mixed topics). Structure-aware chunking produces chunks
that correspond to real document sections and carries the section's full topic
context in the breadcrumb — directly improving embedding quality for paraphrase
and multi-hop queries where keyword overlap alone is insufficient.

---

## Architecture

### New file: `src/fireflyframework_agentic/content/markdown_chunker.py`

Single public class `MarkdownChunker`, implementing the existing `Chunker` protocol
(`chunk(content: str) -> list[Chunk]`).

```
MarkdownChunker
  chunk(content)                 → list[Chunk]
  _parse_sections(content)       → list[_Section]   # tokenise + split
  _emit_chunks(section)          → list[Chunk]       # breadcrumb + fallback split
  _estimate_tokens(text)         → int
```

`_Section` is a private dataclass:
```python
@dataclass
class _Section:
    heading_stack: list[tuple[int, str]]  # [(level, title), ...]
    body: str                              # raw text of section body
```

### Parser

Uses `markdown_it.MarkdownIt().parse(content)` to tokenise. Tokens include
`heading_open` (with `.map = [start_line, end_line]` and `.tag = "h1"…"h6"`)
and `inline` (with `.content` = heading text). Fenced code blocks (`fence`
tokens) and tables (`table_open`/`table_close`) are opaque — any `#` characters
inside them never become `heading_open` tokens, so they are never treated as
section boundaries.

**Algorithm:**

1. Call `MarkdownIt().parse(content)` → token list.
2. Walk tokens; collect `(line_number, level, title)` for every `heading_open`.
3. Split `content.splitlines()` at those line numbers to get section bodies
   (the heading line itself is excluded from the body).
4. Return `list[_Section]` in document order, including a preamble section
   (body before the first heading, if any) with an empty heading stack.

### Chunk format

```
{H1 title} > {H2 title} > {H3 title}

{section body}
```

- If no heading path (preamble): just `{section body}` with no breadcrumb line.
- Empty sections (body is blank after stripping) are skipped.
- Breadcrumb is also written to `chunk.metadata["breadcrumb"]` so callers can
  display or filter on it without parsing the content string.

### Fallback splitting

If a section body exceeds `max_chunk_tokens` (estimated), the body is split
with `TextChunker(chunk_size=max_chunk_tokens, chunk_overlap=chunk_overlap)`.
Each sub-chunk gets the same breadcrumb prepended, producing multiple `Chunk`
objects from one section. This preserves the section's context for every
sub-chunk without losing the header path.

### Constructor

```python
MarkdownChunker(
    *,
    max_chunk_tokens: int = 600,
    chunk_overlap: int = 80,
    min_body_tokens: int = 10,        # skip sections shorter than this
    breadcrumb_separator: str = " > ",
)
```

`min_body_tokens` prevents stub sections (e.g. a heading with a one-word body
that is just a link) from generating noise chunks.

---

## Files Changed

| File | Change |
|------|--------|
| `src/fireflyframework_agentic/content/markdown_chunker.py` | **New** — `MarkdownChunker` |
| `src/fireflyframework_agentic/content/__init__.py` | Export `MarkdownChunker` |
| `src/fireflyframework_agentic/rag/ingest/pipeline.py` | Widen `chunker: TextChunker` → `chunker: Chunker` |
| `examples/corpus_search/agent.py` | Swap to `MarkdownChunker(max_chunk_tokens=600, chunk_overlap=80)` |
| `tests/examples/corpus_search/benchmark/runner.py` | Swap to `MarkdownChunker(max_chunk_tokens=200, chunk_overlap=30)` |
| `pyproject.toml` | Add `markdown-it-py>=3.0` to `markitdown` extra |
| `tests/unit/content/test_markdown_chunker.py` | **New** — unit tests |

---

## Dependency

`markdown-it-py>=3.0` added to the `markitdown` optional extra. It is already
present in the lock file as a transitive dependency; making it explicit ensures
`MarkdownChunker` is available whenever `MarkitdownLoader` is installed.

No new top-level extra is needed. Users who install `corpus-search` already
pull in `markitdown`.

---

## Tests

### `tests/unit/content/test_markdown_chunker.py`

| Test | Asserts |
|------|---------|
| `test_single_h1_section` | One heading + body → one chunk, breadcrumb = heading title |
| `test_nested_headings_breadcrumb` | h1 > h2 > h3 stack → breadcrumb string correct |
| `test_heading_resets_lower_levels` | After h2 A, h2 B: stack has only h1 + h2 B (h2 A popped) |
| `test_preamble_no_breadcrumb` | Content before first heading → chunk with empty breadcrumb metadata |
| `test_code_block_not_split` | `#` inside fenced block not treated as heading |
| `test_oversized_section_fallback` | Section > max_chunk_tokens → multiple chunks, all share breadcrumb |
| `test_empty_section_skipped` | Heading with blank body → no chunk produced |
| `test_chunker_protocol` | `isinstance(MarkdownChunker(), Chunker)` is True |
| `test_metadata_breadcrumb_field` | `chunk.metadata["breadcrumb"]` matches prepended breadcrumb line |
| `test_no_headings_plain_text` | Markdown with no headings → behaves like TextChunker |

### Benchmark regression

After implementation, re-run `--mode mechanics` and `--mode real` benchmarks.
Mechanics Hit@5 is expected to improve (better BM25 boundaries). Real Hit@5
is already at 100% — watch MRR and substring_match for regressions.
Update `runs/baseline.json` and `runs/baseline_real.json` if numbers improve.

---

## What is NOT in scope

- Changing how `SqliteCorpus` stores or queries chunks — chunk text is opaque to the corpus.
- Changing the embedding call — breadcrumb is part of the chunk text, no special handling needed.
- Supporting non-markdown content — `MarkdownChunker` assumes markitdown output; pass plain text and it degrades to a single chunk (no headings found → one preamble section, split by TextChunker if needed).
- Removing `TextChunker` from the public API — it remains for non-markdown use cases.

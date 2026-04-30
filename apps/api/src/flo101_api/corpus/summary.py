"""Representative excerpt of a corpus for the Synthesizer prompt.

The full corpus goes through retrieval at evaluation time; the synthesizer
only needs enough to align rubric language with the uploaded materials.
"""

from __future__ import annotations

from flo101_api.db.corpus import list_chunks
from flo101_api.db.store import SqliteStore, get_store
from flo101_api.domain.corpus import CorpusChunk

_DEFAULT_BUDGET_CHARS = 4000


def build_corpus_summary(
    *,
    spec_id: str,
    char_budget: int = _DEFAULT_BUDGET_CHARS,
    store: SqliteStore | None = None,
) -> str | None:
    s = store or get_store()
    chunks = list_chunks(spec_id=spec_id, store=s)
    if not chunks:
        return None
    return _select_excerpt(chunks, char_budget)


def _select_excerpt(chunks: list[CorpusChunk], char_budget: int) -> str:
    # Take the first chunk of each source plus a middle chunk if the source
    # has 3+ chunks. Bounded by char_budget so the prompt stays small.
    by_source: dict[str, list[CorpusChunk]] = {}
    for c in chunks:
        by_source.setdefault(c.source, []).append(c)
    selected: list[CorpusChunk] = []
    for src_chunks in by_source.values():
        src_chunks.sort(key=lambda c: c.chunk_index)
        selected.append(src_chunks[0])
        if len(src_chunks) >= 3:
            selected.append(src_chunks[len(src_chunks) // 2])
    selected.sort(key=lambda c: (c.source, c.chunk_index))

    parts: list[str] = []
    used = 0
    for c in selected:
        header = f"--- {c.source} (chunk {c.chunk_index}) ---"
        body = c.content.strip()
        block = f"{header}\n{body}"
        if used + len(block) + 2 > char_budget:
            remaining = char_budget - used - 2 - len(header) - 1
            if remaining > 200:
                parts.append(f"{header}\n{body[:remaining]}…")
            break
        parts.append(block)
        used += len(block) + 2
    return "\n\n".join(parts)

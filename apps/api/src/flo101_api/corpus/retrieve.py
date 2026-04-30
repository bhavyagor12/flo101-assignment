"""Embed query → vec search → top-k chunks scoped to a spec."""

from __future__ import annotations

from flo101_api.db.corpus import ChunkHit, search_chunks
from flo101_api.db.store import SqliteStore, get_store
from flo101_api.llm import LLMGateway, LLMRequestMetadata, build_gateway


async def retrieve_relevant(
    *,
    spec_id: str,
    query: str,
    k: int = 8,
    gateway: LLMGateway | None = None,
    store: SqliteStore | None = None,
) -> list[ChunkHit]:
    if not query.strip():
        return []
    g = gateway or build_gateway()
    s = store or get_store()
    embedding = (
        await g.embed(
            [query],
            metadata=LLMRequestMetadata(
                operation="corpus.retrieve",
                prompt_name="<embeddings>",
                spec_id=spec_id,
            ),
        )
    )[0]
    return search_chunks(
        spec_id=spec_id,
        query_embedding=embedding,
        k=k,
        store=s,
    )


def format_hits_for_prompt(hits: list[ChunkHit]) -> str:
    if not hits:
        return "(no relevant corpus material found)"
    lines: list[str] = []
    for i, hit in enumerate(hits, 1):
        cite = f"[{i}] {hit.chunk.source} #chunk{hit.chunk.chunk_index}"
        body = hit.chunk.content.strip()
        if len(body) > 1500:
            body = body[:1500] + "…"
        lines.append(f"{cite}\n{body}")
    return "\n\n".join(lines)

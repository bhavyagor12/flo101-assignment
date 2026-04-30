"""Corpus ingest: text → chunks → embeddings → DB.

Re-uploading the same source appends rather than replaces — there's no
chunk deletion API. Build a new spec to refresh.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from flo101_api.config import Settings, get_settings
from flo101_api.corpus.chunking import chunk_text, estimate_tokens
from flo101_api.db.corpus import ChunkInsert, insert_chunks
from flo101_api.db.specs import mark_has_corpus
from flo101_api.db.store import SqliteStore, get_store
from flo101_api.domain.corpus import CorpusUploadResult
from flo101_api.llm import LLMGateway, LLMRequestMetadata, build_gateway
from flo101_api.observability import get_logger

_EMBED_BATCH_SIZE = 64


@dataclass(frozen=True, slots=True)
class IngestDocument:
    source: str
    content: str
    metadata: dict[str, str] | None = None


async def ingest_documents(
    *,
    spec_id: str,
    documents: list[IngestDocument],
    gateway: LLMGateway | None = None,
    store: SqliteStore | None = None,
    settings: Settings | None = None,
) -> CorpusUploadResult:
    log = get_logger("flo101_api.corpus.ingest")
    if not documents:
        return CorpusUploadResult(
            spec_id=spec_id, sources=[], chunks_added=0, total_tokens=0
        )

    s = store or get_store()
    g = gateway or build_gateway()
    _ = settings or get_settings()

    # Chunk all documents first so embedding calls can be batched.
    drafts: list[_ChunkDraft] = []
    for doc in documents:
        for idx, content in enumerate(chunk_text(doc.content)):
            drafts.append(
                _ChunkDraft(
                    public_id=str(uuid4()),
                    spec_id=spec_id,
                    source=doc.source,
                    content=content,
                    chunk_index=idx,
                    token_count=estimate_tokens(content),
                    metadata=doc.metadata or {},
                )
            )

    log.info(
        "corpus.ingest.start",
        spec_id=spec_id,
        documents=len(documents),
        chunks=len(drafts),
    )

    if not drafts:
        return CorpusUploadResult(
            spec_id=spec_id,
            sources=[d.source for d in documents],
            chunks_added=0,
            total_tokens=0,
        )

    embeddings: list[list[float]] = []
    metadata = LLMRequestMetadata(
        operation="corpus.embed",
        prompt_name="<embeddings>",
        spec_id=spec_id,
    )
    for batch_start in range(0, len(drafts), _EMBED_BATCH_SIZE):
        batch = drafts[batch_start : batch_start + _EMBED_BATCH_SIZE]
        batch_embeds = await g.embed(
            [d.content for d in batch], metadata=metadata
        )
        embeddings.extend(batch_embeds)

    assert len(embeddings) == len(drafts), "embedding/draft count mismatch"

    rows = [
        ChunkInsert(
            public_id=d.public_id,
            spec_id=d.spec_id,
            source=d.source,
            content=d.content,
            chunk_index=d.chunk_index,
            token_count=d.token_count,
            embedding=emb,
            metadata=d.metadata,
        )
        for d, emb in zip(drafts, embeddings, strict=True)
    ]
    inserted = insert_chunks(rows, store=s)
    mark_has_corpus(spec_id, store=s)

    sources = sorted({d.source for d in drafts})
    total_tokens = sum(d.token_count for d in drafts)
    log.info(
        "corpus.ingest.ok",
        spec_id=spec_id,
        chunks_added=inserted,
        total_tokens=total_tokens,
        sources=sources,
    )
    return CorpusUploadResult(
        spec_id=spec_id,
        sources=sources,
        chunks_added=inserted,
        total_tokens=total_tokens,
    )


@dataclass(frozen=True, slots=True)
class _ChunkDraft:
    public_id: str
    spec_id: str
    source: str
    content: str
    chunk_index: int
    token_count: int
    metadata: dict[str, str]

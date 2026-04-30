"""Reference corpus: per-spec knowledge used by Critic for grounded evidence."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from flo101_api.domain._base import DomainModel


class CorpusChunk(DomainModel):
    """A single retrievable chunk within a spec's reference corpus."""

    id: str
    spec_id: str
    source: str = Field(min_length=1, description="filename or URL the chunk came from")
    content: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    token_count: int = Field(ge=1)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime


class CorpusUploadResult(DomainModel):
    """Outcome of an ingest call."""

    spec_id: str
    sources: list[str]
    chunks_added: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

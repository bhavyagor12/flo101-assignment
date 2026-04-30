"""LLM access protocol. Agents depend on this, not on a concrete client."""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel, Field

from flo101_api.domain._base import DomainModel

T = TypeVar("T", bound=BaseModel)


class LLMRequestMetadata(DomainModel):
    operation: str = Field(description="e.g. 'synthesize', 'rubric_critique'")
    prompt_name: str
    prompt_version: str = "v1"
    spec_id: str | None = None
    artifact_id: str | None = None
    evaluation_id: str | None = None
    extra: dict[str, str] = Field(default_factory=dict)


class LLMGateway(Protocol):
    async def structured(
        self,
        *,
        model: str,
        system: str,
        user: str,
        response_model: type[T],
        metadata: LLMRequestMetadata,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        cache_system: bool = True,
        max_repair_retries: int = 2,
    ) -> T:
        """Validate JSON output against `response_model`; retries with a repair
        instruction up to `max_repair_retries` times if validation fails."""
        ...

    async def text(
        self,
        *,
        model: str,
        system: str,
        user: str,
        metadata: LLMRequestMetadata,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        cache_system: bool = True,
    ) -> str: ...

    async def embed(
        self,
        texts: list[str],
        metadata: LLMRequestMetadata,
    ) -> list[list[float]]: ...

    async def aclose(self) -> None: ...

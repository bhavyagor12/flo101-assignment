"""FakeGateway — test stub implementing the LLMGateway protocol.

Lets us drive the Critic graph + Synthesizer through their full code paths
without spending API calls. Responses are queued in FIFO order.

Usage:

    fake = FakeGateway()
    fake.queue_structured(SafetyVerdict(allow=True, reason="ok"))
    fake.queue_structured(CritiqueResult(...))
    fake.queue_structured(DispositionResult(...))

    # Then monkey-patch each call site so agents pick it up.

If the queue is empty when `structured` is called, or the queued response
is the wrong Pydantic type, the gateway raises a descriptive RuntimeError —
this is intentional, the test should fail loudly on a missed expectation.
"""

from __future__ import annotations

from collections import deque
from typing import Any, TypeVar

from pydantic import BaseModel

from flo101_api.llm.gateway import LLMRequestMetadata

T = TypeVar("T", bound=BaseModel)


class FakeGateway:
    """In-memory LLMGateway. Queues structured / text / embedding responses."""

    def __init__(self) -> None:
        self._structured: deque[BaseModel | Exception] = deque()
        self._text: deque[str | Exception] = deque()
        self._embeddings: deque[list[list[float]] | Exception] = deque()
        self.calls_structured: list[dict[str, Any]] = []
        self.calls_text: list[dict[str, Any]] = []
        self.calls_embed: list[dict[str, Any]] = []

    # ─── queue ────────────────────────────────────────────────

    def queue_structured(self, response: BaseModel) -> None:
        self._structured.append(response)

    def queue_structured_exception(self, exc: Exception) -> None:
        self._structured.append(exc)

    def queue_text(self, response: str) -> None:
        self._text.append(response)

    def queue_embedding(self, vector: list[float]) -> None:
        """Queue a single 1-vector batch (treats next embed call as size 1)."""
        self._embeddings.append([vector])

    def queue_embeddings(self, vectors: list[list[float]]) -> None:
        self._embeddings.append(vectors)

    # ─── LLMGateway surface ───────────────────────────────────

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
        _ = (system, user, max_tokens, temperature, cache_system, max_repair_retries)
        self.calls_structured.append(
            {
                "model": model,
                "metadata": metadata,
                "response_model": response_model.__name__,
            }
        )
        if not self._structured:
            raise RuntimeError(
                f"FakeGateway: no queued structured response for {response_model.__name__} "
                f"(operation={metadata.operation})"
            )
        head = self._structured.popleft()
        if isinstance(head, Exception):
            raise head
        if not isinstance(head, response_model):
            raise RuntimeError(
                f"FakeGateway: queued {type(head).__name__} but call expected "
                f"{response_model.__name__}"
            )
        return head  # type: ignore[return-value]

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
    ) -> str:
        _ = (system, user, max_tokens, temperature, cache_system)
        self.calls_text.append({"model": model, "metadata": metadata})
        if not self._text:
            raise RuntimeError("FakeGateway: no queued text response")
        head = self._text.popleft()
        if isinstance(head, Exception):
            raise head
        return head

    async def embed(
        self,
        texts: list[str],
        metadata: LLMRequestMetadata,
    ) -> list[list[float]]:
        self.calls_embed.append({"n": len(texts), "metadata": metadata})
        if not self._embeddings:
            raise RuntimeError("FakeGateway: no queued embedding response")
        head = self._embeddings.popleft()
        if isinstance(head, Exception):
            raise head
        return head

    async def aclose(self) -> None:
        return None

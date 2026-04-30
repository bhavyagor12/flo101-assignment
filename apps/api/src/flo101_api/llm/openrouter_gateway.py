"""OpenRouter implementation of LLMGateway, using the openai SDK against
OpenRouter's base URL. Anthropic `cache_control` blocks pass through
transparently for prompt caching."""

from __future__ import annotations

from typing import Any, TypeVar, cast

import httpx
from openai import AsyncOpenAI
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

try:
    from langsmith import traceable
except ImportError:  # pragma: no cover - langsmith is a hard dep, but be defensive
    def traceable(*_args: Any, **_kwargs: Any):  # type: ignore[no-redef]
        def _decorator(fn):  # type: ignore[no-untyped-def]
            return fn
        return _decorator

from flo101_api.config import Settings
from flo101_api.domain.errors import UpstreamException, ValidationFailedException
from flo101_api.llm.gateway import LLMRequestMetadata
from flo101_api.llm.tracing import Tracer
from flo101_api.observability import get_logger

T = TypeVar("T", bound=BaseModel)


# JSON-Schema features Anthropic's structured-output parser rejects.
# Pydantic still validates responses against the original constraints, so
# stripping these only affects the schema sent to the model — unsupported
# constraints become "soft" checks enforced by the repair retry loop.
_ANTHROPIC_UNSUPPORTED_SCHEMA_KEYS: frozenset[str] = frozenset({
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "pattern", "format",
    "minItems", "maxItems", "uniqueItems",
    "minProperties", "maxProperties", "multipleOf",
})


def _strip_anthropic_unsupported(node: object) -> object:
    if isinstance(node, dict):
        return {
            k: _strip_anthropic_unsupported(v)
            for k, v in node.items()
            if k not in _ANTHROPIC_UNSUPPORTED_SCHEMA_KEYS
        }
    if isinstance(node, list):
        return [_strip_anthropic_unsupported(x) for x in node]
    return node


def _network_retry() -> AsyncRetrying:
    return AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
        retry=retry_if_exception_type(
            (APIConnectionError, APITimeoutError, RateLimitError, httpx.HTTPError)
        ),
        reraise=True,
    )


class OpenRouterGateway:
    def __init__(self, settings: Settings, tracer: Tracer) -> None:
        self._tracer = tracer
        self._log = get_logger("flo101_api.llm.openrouter")
        self._chat = AsyncOpenAI(
            api_key=settings.openrouter_api_key or "missing",
            base_url=settings.openrouter_base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/flo101/critic",
                "X-Title": "flo101 Critic Agent",
            },
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
        self._embed = AsyncOpenAI(
            api_key=settings.openai_api_key or "missing",
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        self._embedding_model = settings.embedding_model
        self._has_chat_key = bool(settings.openrouter_api_key)
        self._has_embed_key = bool(settings.openai_api_key)

    @traceable(name="llm.structured")
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
        self._require_chat_key()
        schema = _strip_anthropic_unsupported(response_model.model_json_schema())
        messages = self._build_messages(system, user, cache_system)

        last_text: str | None = None
        last_error: str | None = None
        for attempt in range(max_repair_retries + 1):
            text = await self._chat_completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "schema": schema,
                        "strict": True,
                    },
                },
                metadata=metadata,
            )
            try:
                return response_model.model_validate_json(text)
            except ValidationError as exc:
                last_text = text
                last_error = str(exc)
                self._log.warning(
                    "llm.structured.validation_failed",
                    operation=metadata.operation,
                    prompt=metadata.prompt_name,
                    attempt=attempt + 1,
                    error=last_error,
                )
                if attempt == max_repair_retries:
                    break
                messages = self._append_repair_messages(messages, last_text, last_error)

        raise ValidationFailedException(
            detail=(
                f"Structured output failed validation after {max_repair_retries + 1} "
                f"attempts: {last_error}"
            ),
            path=metadata.prompt_name,
        )

    @traceable(name="llm.text")
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
        self._require_chat_key()
        messages = self._build_messages(system, user, cache_system)
        return await self._chat_completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=None,
            metadata=metadata,
        )

    @traceable(name="llm.embed")
    async def embed(
        self,
        texts: list[str],
        metadata: LLMRequestMetadata,
    ) -> list[list[float]]:
        self._require_embed_key()
        if not texts:
            return []
        async for attempt in _network_retry():
            with attempt:
                response = await self._embed.embeddings.create(
                    model=self._embedding_model,
                    input=texts,
                )
                self._log.info(
                    "llm.embed.ok",
                    operation=metadata.operation,
                    n=len(texts),
                    model=self._embedding_model,
                )
                return [item.embedding for item in response.data]
        # AsyncRetrying re-raises on exhaustion; this is unreachable.
        raise UpstreamException(provider="openai", detail="embedding retry exhausted")

    async def aclose(self) -> None:
        await self._chat.close()
        await self._embed.close()

    @staticmethod
    def _build_messages(
        system: str,
        user: str,
        cache_system: bool,
    ) -> list[dict[str, Any]]:
        # `cache_control` is OpenRouter's passthrough for Anthropic prompt
        # caching; OpenAI ignores it. Min cache size on Anthropic is 1024
        # tokens, so short systems won't actually cache.
        if cache_system:
            system_content: list[dict[str, Any]] | str = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        else:
            system_content = system
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def _append_repair_messages(
        messages: list[dict[str, Any]],
        last_text: str,
        error: str,
    ) -> list[dict[str, Any]]:
        return [
            *messages,
            {"role": "assistant", "content": last_text},
            {
                "role": "user",
                "content": (
                    "Your previous response failed JSON Schema validation:\n"
                    f"{error}\n\n"
                    "Return ONLY a JSON object that conforms to the required schema. "
                    "Do not wrap it in markdown fences. Do not add commentary."
                ),
            },
        ]

    async def _chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        response_format: dict[str, Any] | None,
        metadata: LLMRequestMetadata,
    ) -> str:
        # Retryable errors (network, timeout, 429) propagate through tenacity
        # untouched so retries actually happen; we only wrap to
        # UpstreamException after exhaustion or for non-retryable APIError.
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": cast(Any, messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        try:
            async for attempt in _network_retry():
                with attempt:
                    response = await self._chat.chat.completions.create(**kwargs)
                    content: str = response.choices[0].message.content or ""
                    usage = response.usage
                    self._log.info(
                        "llm.chat.ok",
                        operation=metadata.operation,
                        prompt=metadata.prompt_name,
                        model=model,
                        input_tokens=int(usage.prompt_tokens) if usage else None,
                        output_tokens=int(usage.completion_tokens) if usage else None,
                    )
                    return content
        except (APIConnectionError, APITimeoutError, RateLimitError, httpx.HTTPError) as exc:
            # Tenacity exhausted retries; wrap and raise.
            raise UpstreamException(
                provider="openrouter",
                detail=f"{type(exc).__name__} after retries: {exc}",
            ) from exc
        except APIError as exc:
            # Non-retryable upstream error (auth, 4xx, etc.).
            raise UpstreamException(
                provider="openrouter",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc
        raise UpstreamException(provider="openrouter", detail="chat returned without a response")

    def _require_chat_key(self) -> None:
        if not self._has_chat_key:
            raise UpstreamException(
                provider="openrouter",
                detail="OPENROUTER_API_KEY is not set",
            )

    def _require_embed_key(self) -> None:
        if not self._has_embed_key:
            raise UpstreamException(
                provider="openai",
                detail="OPENAI_API_KEY is not set",
            )

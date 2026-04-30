"""Typed errors.

Two parallel hierarchies because Pydantic models can't cleanly inherit
from Exception: data models for API serialization, exception classes for
raising. Each exception has a `.to_model()` to bridge them.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from flo101_api.domain._base import DomainModel

# ─── Data models (serialized to clients) ─────────────────────────────────────


class RefusedError(DomainModel):
    type: Literal["refused"] = "refused"
    reason: str


class ValidationFailedError(DomainModel):
    type: Literal["validation_failed"] = "validation_failed"
    detail: str
    path: str | None = None


class TimeoutError_(DomainModel):
    # Trailing underscore avoids shadowing builtin TimeoutError.
    type: Literal["timeout"] = "timeout"
    operation: str
    seconds: int = Field(ge=0)


class SandboxError(DomainModel):
    type: Literal["sandbox"] = "sandbox"
    detail: str


class UpstreamError(DomainModel):
    type: Literal["upstream"] = "upstream"
    provider: str
    detail: str


CriticError = Annotated[
    RefusedError | ValidationFailedError | TimeoutError_ | SandboxError | UpstreamError,
    Field(discriminator="type"),
]


# ─── Exception classes (raised in code) ──────────────────────────────────────


class CriticException(Exception):
    def to_model(self) -> CriticError:  # type: ignore[override]
        raise NotImplementedError


class RefusedException(CriticException):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

    def to_model(self) -> RefusedError:
        return RefusedError(reason=self.reason)


class ValidationFailedException(CriticException):
    def __init__(self, detail: str, path: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.path = path

    def to_model(self) -> ValidationFailedError:
        return ValidationFailedError(detail=self.detail, path=self.path)


class OperationTimeoutException(CriticException):
    def __init__(self, operation: str, seconds: int) -> None:
        super().__init__(f"{operation} timed out after {seconds}s")
        self.operation = operation
        self.seconds = seconds

    def to_model(self) -> TimeoutError_:
        return TimeoutError_(operation=self.operation, seconds=self.seconds)


class SandboxException(CriticException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail

    def to_model(self) -> SandboxError:
        return SandboxError(detail=self.detail)


class UpstreamException(CriticException):
    def __init__(self, provider: str, detail: str) -> None:
        super().__init__(f"{provider}: {detail}")
        self.provider = provider
        self.detail = detail

    def to_model(self) -> UpstreamError:
        return UpstreamError(provider=self.provider, detail=self.detail)

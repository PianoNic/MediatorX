from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Generic, Protocol, TypeVar, runtime_checkable

from .markers import IMessage

TMessage = TypeVar("TMessage", contravariant=True, bound=IMessage)
TResponseInv = TypeVar("TResponseInv")


class MessageHandlerDelegate(Protocol, Generic[TResponseInv]):  # type: ignore[misc]
    """Awaitable representing the rest of the pipeline. Call it to proceed."""

    async def __call__(self) -> TResponseInv:
        """Invoke the next stage and return its response."""
        ...


class StreamHandlerDelegate(Protocol, Generic[TResponseInv]):  # type: ignore[misc]
    """Returns the async iterator representing the rest of the stream pipeline."""

    def __call__(self) -> AsyncIterator[TResponseInv]:
        """Invoke the next stage and return its async iterator."""
        ...


@runtime_checkable
class IPipelineBehavior(Protocol, Generic[TMessage, TResponseInv]):
    """Wraps message handling for cross-cutting concerns (logging, validation, etc.)."""

    async def handle(
        self,
        message: TMessage,
        next: MessageHandlerDelegate[TResponseInv],
    ) -> TResponseInv:
        """Run around the next stage; await next() to proceed."""
        ...


@runtime_checkable
class IStreamPipelineBehavior(Protocol, Generic[TMessage, TResponseInv]):
    """Wraps stream handling for cross-cutting concerns."""

    def handle(
        self,
        message: TMessage,
        next: StreamHandlerDelegate[TResponseInv],
    ) -> AsyncIterator[TResponseInv]:
        """Return an async iterator that wraps next()."""
        ...

from __future__ import annotations

from typing import Generic, TypeVar

from .markers import IBaseCommand, IBaseQuery, IBaseRequest, IStreamMessage

TResponse = TypeVar("TResponse", covariant=True)


class IRequest(IBaseRequest, Generic[TResponse]):
    """Request returning TResponse. Use IRequest[Unit] for void."""


class ICommand(IBaseCommand, Generic[TResponse]):
    """Command returning TResponse. Use ICommand[Unit] for void."""


class IQuery(IBaseQuery, Generic[TResponse]):
    """Query returning TResponse. Queries should always return data."""


class IStreamRequest(IBaseRequest, IStreamMessage, Generic[TResponse]):
    """Streaming request producing a sequence of TResponse."""


class IStreamCommand(IBaseCommand, IStreamMessage, Generic[TResponse]):
    """Streaming command producing a sequence of TResponse."""


class IStreamQuery(IBaseQuery, IStreamMessage, Generic[TResponse]):
    """Streaming query producing a sequence of TResponse."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Generic, Protocol, TypeVar, runtime_checkable

from .markers import IBaseCommand, IBaseQuery, IBaseRequest, INotification

TRequest = TypeVar("TRequest", contravariant=True, bound=IBaseRequest)
TCommand = TypeVar("TCommand", contravariant=True, bound=IBaseCommand)
TQuery = TypeVar("TQuery", contravariant=True, bound=IBaseQuery)
TNotification = TypeVar("TNotification", contravariant=True, bound=INotification)
TResponseInv = TypeVar("TResponseInv")


@runtime_checkable
class IRequestHandler(Protocol, Generic[TRequest, TResponseInv]):  # type: ignore[misc]
    """Handler for an IRequest returning TResponseInv."""

    async def handle(self, request: TRequest) -> TResponseInv:
        """Handle the request and return its response."""
        ...


@runtime_checkable
class ICommandHandler(Protocol, Generic[TCommand, TResponseInv]):  # type: ignore[misc]
    """Handler for an ICommand returning TResponseInv."""

    async def handle(self, command: TCommand) -> TResponseInv:
        """Handle the command and return its response."""
        ...


@runtime_checkable
class IQueryHandler(Protocol, Generic[TQuery, TResponseInv]):  # type: ignore[misc]
    """Handler for an IQuery returning TResponseInv."""

    async def handle(self, query: TQuery) -> TResponseInv:
        """Handle the query and return its response."""
        ...


@runtime_checkable
class IStreamRequestHandler(Protocol, Generic[TRequest, TResponseInv]):  # type: ignore[misc]
    """Handler for an IStreamRequest producing an async iterator."""

    def handle(self, request: TRequest) -> AsyncIterator[TResponseInv]:
        """Return an async iterator of responses."""
        ...


@runtime_checkable
class IStreamCommandHandler(Protocol, Generic[TCommand, TResponseInv]):  # type: ignore[misc]
    """Handler for an IStreamCommand producing an async iterator."""

    def handle(self, command: TCommand) -> AsyncIterator[TResponseInv]:
        """Return an async iterator of responses."""
        ...


@runtime_checkable
class IStreamQueryHandler(Protocol, Generic[TQuery, TResponseInv]):  # type: ignore[misc]
    """Handler for an IStreamQuery producing an async iterator."""

    def handle(self, query: TQuery) -> AsyncIterator[TResponseInv]:
        """Return an async iterator of responses."""
        ...


@runtime_checkable
class INotificationHandler(Protocol, Generic[TNotification]):
    """Handler for an INotification (fire-and-forget)."""

    async def handle(self, notification: TNotification) -> None:
        """Handle the notification."""
        ...

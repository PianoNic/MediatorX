from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Protocol, runtime_checkable

from .handlers import INotificationHandler
from .markers import IMessage, INotification, IStreamMessage
from .publishers import ForeachAwaitPublisher, INotificationPublisher
from .resolvers import DictResolver, IResolver


@runtime_checkable
class ISender(Protocol):
    """Sends messages and creates streams."""

    async def send(self, message: IMessage) -> object:
        """Dispatch a message to its handler and return the response."""
        ...

    def create_stream(self, message: IStreamMessage) -> AsyncIterator[object]:
        """Dispatch a stream message and return its async iterator."""
        ...


@runtime_checkable
class IPublisher(Protocol):
    """Publishes notifications to zero or more handlers."""

    async def publish(self, notification: INotification) -> None:
        """Dispatch a notification to every registered handler."""
        ...


@runtime_checkable
class IMediator(ISender, IPublisher, Protocol):
    """Combined sender and publisher surface."""


class _RegisteredBehavior:
    """A pipeline behavior plus the marker type it is constrained to."""

    __slots__ = ("behavior_type", "constraint")

    def __init__(self, behavior_type: type, constraint: type) -> None:
        """Bind a behavior type to a marker constraint."""
        self.behavior_type = behavior_type
        self.constraint = constraint


class Mediator:
    """In-process, async-first mediator owning handler and behavior registries."""

    def __init__(
        self,
        resolver: IResolver | None = None,
        publisher: INotificationPublisher | None = None,
    ) -> None:
        """Create a mediator with an optional resolver and notification publisher."""
        self._resolver: IResolver = resolver if resolver is not None else DictResolver()  # type: ignore[assignment]
        self._publisher: INotificationPublisher = (
            publisher if publisher is not None else ForeachAwaitPublisher()
        )
        self._handlers: dict[type, type] = {}
        self._notification_handlers: dict[type, list[type]] = {}
        self._behaviors: list[_RegisteredBehavior] = []
        self._stream_behaviors: list[_RegisteredBehavior] = []

    def register(self, message_type: type, handler_type: type) -> Mediator:
        """Register a request / command / query / stream handler."""
        self._handlers[message_type] = handler_type
        return self

    def register_notification(self, notification_type: type, handler_type: type) -> Mediator:
        """Register a notification handler. Multiple per type are allowed."""
        self._notification_handlers.setdefault(notification_type, []).append(handler_type)
        return self

    def add_behavior(
        self,
        behavior_type: type,
        constraint: type = IMessage,
    ) -> Mediator:
        """Append a pipeline behavior, optionally constrained by marker."""
        self._behaviors.append(_RegisteredBehavior(behavior_type, constraint))
        return self

    def add_stream_behavior(
        self,
        behavior_type: type,
        constraint: type = IMessage,
    ) -> Mediator:
        """Append a stream pipeline behavior, optionally constrained by marker."""
        self._stream_behaviors.append(_RegisteredBehavior(behavior_type, constraint))
        return self

    async def send(self, message: IMessage) -> object:
        """Dispatch a message through the pipeline to its handler."""
        msg_type = type(message)
        handler_type = self._handlers.get(msg_type)
        if handler_type is None:
            raise KeyError(f"no handler registered for {msg_type.__name__}")

        handler: object = self._resolver.resolve(handler_type)

        async def terminal() -> object:
            return await handler.handle(message)  # type: ignore[attr-defined]

        pipeline: Callable[[], Awaitable[object]] = terminal

        for reg in reversed(self._behaviors):
            if not isinstance(message, reg.constraint):
                continue
            behavior: object = self._resolver.resolve(reg.behavior_type)
            next_call = pipeline

            async def run(
                b: object = behavior, n: Callable[[], Awaitable[object]] = next_call
            ) -> object:
                return await b.handle(message, n)  # type: ignore[attr-defined]

            pipeline = run

        return await pipeline()

    async def create_stream(self, message: IStreamMessage) -> AsyncIterator[object]:
        """Dispatch a stream message through the stream pipeline."""
        msg_type = type(message)
        handler_type = self._handlers.get(msg_type)
        if handler_type is None:
            raise KeyError(f"no stream handler registered for {msg_type.__name__}")

        handler: object = self._resolver.resolve(handler_type)

        def terminal() -> AsyncIterator[object]:
            return handler.handle(message)  # type: ignore[attr-defined,no-any-return]

        pipeline: Callable[[], AsyncIterator[object]] = terminal

        for reg in reversed(self._stream_behaviors):
            if not isinstance(message, reg.constraint):
                continue
            behavior: object = self._resolver.resolve(reg.behavior_type)
            next_call = pipeline

            def run(
                b: object = behavior, n: Callable[[], AsyncIterator[object]] = next_call
            ) -> AsyncIterator[object]:
                return b.handle(message, n)  # type: ignore[attr-defined,no-any-return]

            pipeline = run

        async for item in pipeline():
            yield item

    async def publish(self, notification: INotification) -> None:
        """Dispatch a notification through the configured publisher."""
        notif_type = type(notification)
        handler_types = self._notification_handlers.get(notif_type, [])
        if not handler_types:
            return
        handlers: list[INotificationHandler[INotification]] = [
            self._resolver.resolve(ht) for ht in handler_types
        ]
        await self._publisher.publish(handlers, notification)

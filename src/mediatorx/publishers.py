from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

from .handlers import INotificationHandler
from .markers import INotification


@runtime_checkable
class INotificationPublisher(Protocol):
    """Strategy for dispatching a notification to a list of handlers."""

    async def publish(
        self,
        handlers: list[INotificationHandler[INotification]],
        notification: INotification,
    ) -> None:
        """Dispatch the notification to each handler."""
        ...


class ForeachAwaitPublisher:
    """Sequential: await each handler in order. Default."""

    async def publish(
        self,
        handlers: list[INotificationHandler[INotification]],
        notification: INotification,
    ) -> None:
        """Await handlers one after another."""
        for handler in handlers:
            await handler.handle(notification)


class TaskWhenAllPublisher:
    """Concurrent: kick off all handlers, await with gather."""

    async def publish(
        self,
        handlers: list[INotificationHandler[INotification]],
        notification: INotification,
    ) -> None:
        """Run all handlers concurrently and wait for completion."""
        await asyncio.gather(*(h.handle(notification) for h in handlers))

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .mediator import Mediator

TCls = TypeVar("TCls", bound=type)


class Registry:
    """Decorator-based collection of handlers and notification handlers."""

    def __init__(self) -> None:
        """Create an empty registry."""
        self._handlers: dict[type, type] = {}
        self._notification_handlers: dict[type, list[type]] = {}

    def handler(self, message_type: type) -> Callable[[TCls], TCls]:
        """Register the decorated class as the handler for message_type."""

        def decorator(cls: TCls) -> TCls:
            self._handlers[message_type] = cls
            return cls

        return decorator

    def notification(self, notification_type: type) -> Callable[[TCls], TCls]:
        """Register the decorated class as a handler for notification_type."""

        def decorator(cls: TCls) -> TCls:
            self._notification_handlers.setdefault(notification_type, []).append(cls)
            return cls

        return decorator

    def apply_to(self, mediator: Mediator) -> Mediator:
        """Wire all registered handlers into the given mediator."""
        for msg_type, h in self._handlers.items():
            mediator.register(msg_type, h)
        for notif_type, handlers in self._notification_handlers.items():
            for h in handlers:
                mediator.register_notification(notif_type, h)
        return mediator

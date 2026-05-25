"""Quickstart demo — equivalent to the original mediatorx.py __main__ block."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from mediatorx import (
    DictResolver,
    INotification,
    IRequest,
    Mediator,
    TaskWhenAllPublisher,
)


@dataclass
class Ping(IRequest[str]):
    """Request that asks for a pong."""

    message: str


class PingHandler:
    """Handler that turns a Ping into a pong string."""

    async def handle(self, request: Ping) -> str:
        return f"pong: {request.message}"


@dataclass(frozen=True)
class UserRegistered(INotification):
    """Notification fired when a user signs up."""

    user_id: int


class LogRegistration:
    """Logs registrations."""

    async def handle(self, n: UserRegistered) -> None:
        print(f"[log] user {n.user_id} registered")


class WelcomeEmail:
    """Sends a welcome email."""

    async def handle(self, n: UserRegistered) -> None:
        print(f"[email] welcome user {n.user_id}")


class LoggingBehavior:
    """Logs every send through the pipeline."""

    async def handle(self, message: object, next: object) -> object:
        print(f"-> {type(message).__name__}")
        response = await next()  # type: ignore[operator]
        print(f"<- {response!r}")
        return response


async def main() -> None:
    """Run the demo."""
    resolver = (
        DictResolver()
        .add_instance(PingHandler, PingHandler())
        .add_instance(LogRegistration, LogRegistration())
        .add_instance(WelcomeEmail, WelcomeEmail())
        .add_instance(LoggingBehavior, LoggingBehavior())
    )

    mediator = Mediator(resolver=resolver, publisher=TaskWhenAllPublisher())
    mediator.register(Ping, PingHandler)
    mediator.register_notification(UserRegistered, LogRegistration)
    mediator.register_notification(UserRegistered, WelcomeEmail)
    mediator.add_behavior(LoggingBehavior)

    response = await mediator.send(Ping("hello"))
    print(f"got: {response}")

    await mediator.publish(UserRegistered(user_id=42))


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from mediatorx import (
    ForeachAwaitPublisher,
    INotification,
    Mediator,
    TaskWhenAllPublisher,
)


@dataclass
class Evt(INotification):
    val: int = 1


async def test_publish_with_no_handlers_is_a_noop(mediator: Mediator) -> None:
    await mediator.publish(Evt())  # nothing registered → just returns


async def test_publish_invokes_every_registered_handler() -> None:
    seen: list[str] = []

    class H1:
        async def handle(self, n: Evt) -> None:
            seen.append("h1")

    class H2:
        async def handle(self, n: Evt) -> None:
            seen.append("h2")

    m = Mediator()
    m.register_notification(Evt, H1)
    m.register_notification(Evt, H2)
    await m.publish(Evt())
    assert sorted(seen) == ["h1", "h2"]


async def test_foreach_await_runs_in_registration_order() -> None:
    order: list[int] = []

    class A:
        async def handle(self, n: Evt) -> None:
            await asyncio.sleep(0.02)
            order.append(1)

    class B:
        async def handle(self, n: Evt) -> None:
            order.append(2)

    m = Mediator(publisher=ForeachAwaitPublisher())
    m.register_notification(Evt, A)
    m.register_notification(Evt, B)
    await m.publish(Evt())
    assert order == [1, 2]


async def test_task_when_all_runs_concurrently() -> None:
    delay = 0.1

    class Slow:
        async def handle(self, n: Evt) -> None:
            await asyncio.sleep(delay)

    m = Mediator(publisher=TaskWhenAllPublisher())
    m.register_notification(Evt, Slow)
    m.register_notification(Evt, Slow)
    m.register_notification(Evt, Slow)

    start = time.perf_counter()
    await m.publish(Evt())
    elapsed = time.perf_counter() - start
    # 3 handlers × 0.1s sequential = 0.3s; concurrent should be well under 0.25s.
    assert elapsed < 0.25
